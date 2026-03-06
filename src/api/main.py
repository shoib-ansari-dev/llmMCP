"""
FastAPI Application
Main API endpoints for document analysis.
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional
import uuid
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..agents.document_agent import get_document_agent
from ..utils.validation import (
    validate_file,
    validate_url,
    validate_question,
    validate_document_id,
    sanitize_filename,
    sanitize_string,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
)
from ..middleware import (
    RateLimitMiddleware,
    LoggingMiddleware,
    get_query_cache,
    get_session_manager,
    get_metrics_collector,
    setup_logging,
    DDoSProtectionMiddleware,
    get_ddos_protection,
)
from ..middleware.security import (
    SameSiteMiddleware,
    get_same_site_validator,
    get_cors_origins,
)
from ..auth import auth_router, get_auth_config
from ..payments import payment_router
from ..contract_iq import contract_router
from ..finance_digest import finance_router

# Setup logging
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=os.getenv("LOG_FORMAT", "text").lower() == "json"
)

app = FastAPI(
    title="Document Analysis Agent",
    description="AI-powered document analysis for PDFs, spreadsheets, and web pages",
    version="0.1.0"
)

# Get configuration from environment
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
SAME_SITE_ENFORCE = os.getenv("SAME_SITE_ENFORCE", "true").lower() == "true"
DDOS_PROTECTION_ENABLED = os.getenv("DDOS_PROTECTION_ENABLED", "true").lower() == "true"
DDOS_PATTERN_THRESHOLD = int(os.getenv("DDOS_PATTERN_THRESHOLD", "5"))
DDOS_TIME_WINDOW = int(os.getenv("DDOS_TIME_WINDOW", "60"))
DDOS_BLOCK_DURATION = int(os.getenv("DDOS_BLOCK_DURATION", "300"))

# Add DDoS Protection middleware (fingerprint-based, detects patterns across IPs)
if DDOS_PROTECTION_ENABLED:
    app.add_middleware(
        DDoSProtectionMiddleware,
        pattern_threshold=DDOS_PATTERN_THRESHOLD,
        time_window=DDOS_TIME_WINDOW,
        block_duration=DDOS_BLOCK_DURATION,
        exclude_paths=["/health", "/docs", "/openapi.json", "/favicon.ico", "/payments/webhook"]
    )

# Add Rate Limiting middleware (IP-based)
if RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT_PER_MINUTE)

# Add Same-Site Security middleware
if SAME_SITE_ENFORCE:
    app.add_middleware(SameSiteMiddleware, validator=get_same_site_validator())

# Add Logging/Monitoring middleware
app.add_middleware(LoggingMiddleware)

# CORS middleware - restricted to allowed origins from env
allowed_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-ID", "X-CSRF-Token"],
)

# Initialize shared services
query_cache = get_query_cache(max_size=100, ttl_seconds=300)
session_manager = get_session_manager(session_ttl=3600)
metrics_collector = get_metrics_collector()
auth_config = get_auth_config()

# Include auth router
app.include_router(auth_router)

# Include payment router
app.include_router(payment_router)

# Include contract router (ContractIQ)
app.include_router(contract_router)

# Include finance router (FinanceDigest)
app.include_router(finance_router)

# In-memory document store (replace with proper DB in production)
documents: dict = {}

# Thread pool for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)


# Request/Response Models
class AnalyzeURLRequest(BaseModel):
    url: HttpUrl

    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v):
        url_str = str(v)
        result = validate_url(url_str)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))
        return v


class AskQuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None

    @field_validator('question')
    @classmethod
    def validate_question_field(cls, v):
        result = validate_question(v)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))
        return sanitize_string(v, max_length=1000)

    @field_validator('document_id')
    @classmethod
    def validate_document_id_field(cls, v):
        if v is not None:
            result = validate_document_id(v)
            if not result.is_valid:
                raise ValueError("; ".join(result.errors))
        return v


class DocumentResponse(BaseModel):
    document_id: str
    status: str
    message: str


class SummaryResponse(BaseModel):
    document_id: str
    summary: str
    insights: list[str]


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]


class JobStatusResponse(BaseModel):
    document_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# Background task for async processing
async def process_document_async(document_id: str, doc_info: dict):
    """Process document in background."""
    try:
        documents[document_id]["status"] = "processing"

        agent = get_document_agent()
        content_type = doc_info.get("content_type", "")

        if content_type == "application/pdf":
            result = await agent.analyze_pdf(
                file_bytes=doc_info["content"],
                document_id=document_id
            )
        elif content_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              "application/vnd.ms-excel", "text/csv"]:
            suffix = ".xlsx" if "spreadsheet" in content_type else ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(doc_info["content"])
                tmp_path = tmp.name

            try:
                result = await agent.analyze_spreadsheet(tmp_path, document_id)
            finally:
                os.unlink(tmp_path)
        else:
            documents[document_id]["status"] = "error"
            documents[document_id]["error"] = "Unknown document type"
            return

        documents[document_id]["status"] = "completed"
        documents[document_id]["result"] = {
            "summary": result.summary,
            "insights": result.key_insights,
            "metadata": result.metadata
        }
    except Exception as e:
        documents[document_id]["status"] = "error"
        documents[document_id]["error"] = str(e)


# Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Document Analysis Agent"}


@app.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    async_processing: bool = False,
    auto_analyze: bool = True
):
    """
    Upload a document (PDF, Excel, CSV) for analysis.
    Set async_processing=true for large files to process in background.
    Set auto_analyze=true (default) to automatically analyze after upload.
    """
    document_id = str(uuid.uuid4())

    # Sanitize filename
    filename = sanitize_filename(file.filename or "unnamed")

    # Read file content first to get size
    content = await file.read()
    file_size = len(content)

    # Comprehensive file validation
    validation_result = validate_file(
        filename=filename,
        content_type=file.content_type or "",
        size=file_size,
        content=content
    )

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "File validation failed",
                "errors": validation_result.errors
            }
        )

    # Check file size for automatic async processing (> 5MB)
    should_process_async = async_processing or file_size > 5 * 1024 * 1024

    # Store document info
    documents[document_id] = {
        "filename": filename,
        "content_type": file.content_type,
        "size": file_size,
        "content": content,
        "status": "uploaded" if not should_process_async else "queued"
    }

    # Process in background for large files
    if should_process_async and background_tasks:
        background_tasks.add_task(
            process_document_async,
            document_id,
            documents[document_id]
        )
        return DocumentResponse(
            document_id=document_id,
            status="queued",
            message=f"Document '{file.filename}' queued for async processing"
        )

    # Auto-analyze if enabled
    if auto_analyze:
        try:
            await process_document_async(document_id, documents[document_id])
            return DocumentResponse(
                document_id=document_id,
                status="analyzed",
                message=f"Document '{file.filename}' uploaded and analyzed successfully"
            )
        except Exception as e:
            # Still return success for upload, but note analysis failed
            return DocumentResponse(
                document_id=document_id,
                status="uploaded",
                message=f"Document '{file.filename}' uploaded. Analysis pending."
            )

    return DocumentResponse(
        document_id=document_id,
        status="uploaded",
        message=f"Document '{file.filename}' uploaded successfully"
    )


@app.get("/status/{document_id}", response_model=JobStatusResponse)
async def get_job_status(document_id: str):
    """Get the processing status of a document."""
    # Validate document_id format
    validation_result = validate_document_id(document_id)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid document ID", "errors": validation_result.errors}
        )

    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = documents[document_id]
    return JobStatusResponse(
        document_id=document_id,
        status=doc.get("status", "unknown"),
        progress=doc.get("progress"),
        result=doc.get("result"),
        error=doc.get("error")
    )


@app.post("/analyze/url", response_model=SummaryResponse)
async def analyze_url(request: AnalyzeURLRequest):
    """
    Analyze content from a web page URL.
    """
    document_id = str(uuid.uuid4())

    try:
        agent = get_document_agent()
        result = await agent.analyze_webpage(str(request.url), document_id)

        # Store document info
        documents[document_id] = {
            "url": str(request.url),
            "type": "webpage",
            "status": "analyzed"
        }

        return SummaryResponse(
            document_id=document_id,
            summary=result.summary,
            insights=result.key_insights
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/{document_id}", response_model=SummaryResponse)
async def analyze_document(document_id: str):
    """
    Analyze an uploaded document and return summary.
    """
    # Validate document_id format
    validation_result = validate_document_id(document_id)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid document ID", "errors": validation_result.errors}
        )

    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = documents[document_id]
    agent = get_document_agent()

    try:
        content_type = doc.get("content_type", "")

        if content_type == "application/pdf":
            result = await agent.analyze_pdf(
                file_bytes=doc["content"],
                document_id=document_id
            )
        elif content_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              "application/vnd.ms-excel", "text/csv"]:
            # Save to temp file for spreadsheet parsing
            suffix = ".xlsx" if "spreadsheet" in content_type else ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(doc["content"])
                tmp_path = tmp.name

            try:
                result = await agent.analyze_spreadsheet(tmp_path, document_id)
            finally:
                os.unlink(tmp_path)
        elif doc.get("type") == "webpage":
            # Already analyzed during upload
            stored_doc = agent.get_document(document_id)
            if stored_doc:
                return SummaryResponse(
                    document_id=document_id,
                    summary="Document already analyzed",
                    insights=[]
                )
            result = await agent.analyze_webpage(doc["url"], document_id)
        else:
            raise HTTPException(status_code=400, detail="Unknown document type")

        # Update status
        documents[document_id]["status"] = "analyzed"

        return SummaryResponse(
            document_id=document_id,
            summary=result.summary,
            insights=result.key_insights
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summarize/{document_id}", response_model=SummaryResponse)
async def get_summary(document_id: str):
    """
    Get the summary of an analyzed document.
    """
    # Validate document_id format
    validation_result = validate_document_id(document_id)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid document ID", "errors": validation_result.errors}
        )

    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        agent = get_document_agent()
        summary = await agent.summarize(document_id)
        insights = await agent.get_insights(document_id)

        return SummaryResponse(
            document_id=document_id,
            summary=summary,
            insights=insights
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: AskQuestionRequest):
    """
    Ask a question about uploaded documents.
    Uses caching for repeated queries.
    """
    try:
        # Check cache first
        cached_result = await query_cache.get(request.question, request.document_id)
        if cached_result:
            return AnswerResponse(
                question=request.question,
                answer=cached_result["answer"],
                sources=cached_result["sources"]
            )

        # Get fresh result
        agent = get_document_agent()
        result = await agent.ask_question(request.question, request.document_id)

        # Cache the result
        await query_cache.set(request.question, result, request.document_id)

        return AnswerResponse(
            question=request.question,
            answer=result["answer"],
            sources=result["sources"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """
    List all uploaded documents.
    """
    return {
        "documents": [
            {
                "id": doc_id,
                "filename": doc.get("filename", doc.get("url", "unknown")),
                "status": doc.get("status", "unknown")
            }
            for doc_id, doc in documents.items()
        ]
    }


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document.
    """
    # Validate document_id format
    validation_result = validate_document_id(document_id)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid document ID", "errors": validation_result.errors}
        )

    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")

    del documents[document_id]

    # Also remove from agent's storage
    agent = get_document_agent()
    if document_id in agent.documents:
        del agent.documents[document_id]

    # Invalidate cache for this document
    await query_cache.invalidate(document_id)

    return {"status": "deleted", "document_id": document_id}


# =================================
# Session Management Endpoints
# =================================

@app.post("/session/create")
async def create_session(request: Request):
    """
    Create a new session and get CSRF token.
    """
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() \
        or request.headers.get("X-Real-IP") \
        or (request.client.host if request.client else "unknown")

    session_data = await session_manager.create_session(client_ip)

    return {
        "session_id": session_data["session_id"],
        "csrf_token": session_data["csrf_token"],
        "message": "Session created. Include X-Session-ID and X-CSRF-Token headers in subsequent requests."
    }


# =================================
# Monitoring Endpoints
# =================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Document Analysis Agent",
        "version": "0.1.0"
    }


@app.get("/security/ddos-stats")
async def get_ddos_stats():
    """
    Get DDoS protection statistics.
    Shows active patterns and blocked fingerprints.
    """
    ddos = get_ddos_protection()
    if ddos:
        return {
            "enabled": True,
            "config": {
                "pattern_threshold": ddos.pattern_threshold,
                "time_window": ddos.time_window,
                "block_duration": ddos.block_duration
            },
            "stats": ddos.get_stats()
        }
    return {
        "enabled": False,
        "message": "DDoS protection is disabled"
    }


@app.get("/metrics")
async def get_metrics():
    """Get API metrics."""
    metrics = await metrics_collector.get_metrics()
    cache_stats = await query_cache.stats()

    return {
        "api": metrics,
        "cache": cache_stats
    }


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    return await query_cache.stats()


@app.post("/cache/invalidate")
async def invalidate_cache(document_id: Optional[str] = None):
    """
    Invalidate cache entries.
    If document_id provided, only invalidate entries for that document.
    Otherwise, invalidate all entries.
    """
    count = await query_cache.invalidate(document_id)
    return {
        "message": f"Invalidated {count} cache entries",
        "document_id": document_id
    }


# =================================
# Feedback Endpoints
# =================================

class FeedbackRequest(BaseModel):
    document_id: str
    feedback: str
    feedback_type: str = "summary"  # summary, insights, answer

    @field_validator('feedback')
    @classmethod
    def validate_feedback(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Feedback must be at least 10 characters")
        if len(v) > 2000:
            raise ValueError("Feedback must be less than 2000 characters")
        return v.strip()

    @field_validator('document_id')
    @classmethod
    def validate_doc_id(cls, v):
        result = validate_document_id(v)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))
        return v


class FeedbackResponse(BaseModel):
    document_id: str
    improved_summary: str
    message: str


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback on a summary to get an improved version.
    The system will use the feedback to regenerate a better summary.
    """
    if request.document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = documents[request.document_id]
    agent = get_document_agent()

    # Get original document content
    stored_doc = agent.get_document(request.document_id)
    if not stored_doc:
        raise HTTPException(status_code=404, detail="Document content not found")

    try:
        # Get previous summary from cache or generate
        previous_result = doc.get("result", {})
        previous_summary = previous_result.get("summary", "")

        if not previous_summary:
            raise HTTPException(
                status_code=400,
                detail="No previous summary found. Analyze the document first."
            )

        # Generate improved summary based on feedback
        improved_summary = await agent.llm.improve_summary(
            content=stored_doc["content"],
            doc_type=stored_doc.get("doc_type", "document"),
            previous_summary=previous_summary,
            feedback=request.feedback
        )

        # Update stored result
        documents[request.document_id]["result"]["summary"] = improved_summary

        # Invalidate cache for this document
        await query_cache.invalidate(request.document_id)

        return FeedbackResponse(
            document_id=request.document_id,
            improved_summary=improved_summary,
            message="Summary improved based on your feedback"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



