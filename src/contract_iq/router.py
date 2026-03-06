"""
ContractIQ API Router
FastAPI endpoints for contract analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, List
import logging
from io import BytesIO

from .models import (
    ContractAnalysis,
    ContractComparison,
    ClauseTemplate,
    ContractTemplate,
    AnalyzeContractRequest,
    CompareContractsRequest,
    GenerateReportRequest,
    RiskLevel
)
from .analyzer import ContractAnalyzer
from .risk_scorer import RiskScorer
from .comparator import ContractComparator
from .templates import TemplateLibrary
from .export import ContractExporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contracts", tags=["contracts"])

# Initialize services
analyzer = ContractAnalyzer()
risk_scorer = RiskScorer()
comparator = ContractComparator()
template_library = TemplateLibrary()
exporter = ContractExporter()

# In-memory storage for demo (use database in production)
_contract_cache: dict = {}


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@router.post("/analyze", response_model=ContractAnalysis)
async def analyze_contract(
    document_id: str = Form(...),
    analysis_depth: str = Form("full"),
    focus_areas: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Analyze a contract document.

    Parameters:
    - document_id: Unique identifier for the document
    - file: Optional file upload (PDF, DOCX, TXT)
    - analysis_depth: "quick", "standard", or "full"
    - focus_areas: Comma-separated list of areas to focus on
    """
    try:
        # Get contract text
        text = None

        # If file is uploaded, extract text from it
        if file and file.filename:
            logger.info(f"Processing uploaded file: {file.filename}")
            file_content = await file.read()

            # Parse based on file type
            if file.filename.endswith('.pdf'):
                from ..parsers import PDFParser
                parser = PDFParser()
                pdf_data = parser.parse_bytes(file_content)
                text = pdf_data.text
            elif file.filename.endswith(('.docx', '.doc')):
                from docx import Document
                doc = Document(BytesIO(file_content))
                text = '\n'.join([p.text for p in doc.paragraphs])
            else:
                # Assume text file
                text = file_content.decode('utf-8', errors='ignore')

            logger.info(f"Extracted {len(text)} characters from file")

        # Fallback to cache if no file
        if not text:
            if document_id in _contract_cache:
                text = _contract_cache[document_id]
                logger.info(f"Using cached document: {document_id}")
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No file uploaded and document not found in cache. Please upload a document."
                )

        # Parse focus areas
        focus_areas_list = None
        if focus_areas:
            focus_areas_list = [area.strip() for area in focus_areas.split(',')]

        logger.info(f"Starting analysis for document: {document_id}")

        # Perform analysis
        analysis = await analyzer.analyze_contract(
            document_id=document_id,
            contract_text=text,
            analysis_depth=analysis_depth,
            focus_areas=focus_areas_list
        )

        # Calculate risk score
        risk_score, risk_level = risk_scorer.calculate_risk_score(analysis)
        analysis.risk_score = risk_score
        analysis.risk_level = risk_level

        # Cache the analysis
        _contract_cache[f"analysis_{document_id}"] = analysis

        logger.info(f"Analysis completed for document: {document_id}")
        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing contract: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/text", response_model=ContractAnalysis)
async def analyze_contract_text(
    contract_text: str,
    analysis_depth: str = "full",
    focus_areas: Optional[List[str]] = None
):
    """
    Analyze contract text directly without uploading.
    """
    import uuid
    doc_id = str(uuid.uuid4())

    analysis = await analyzer.analyze_contract(
        document_id=doc_id,
        contract_text=contract_text,
        analysis_depth=analysis_depth,
        focus_areas=focus_areas
    )

    risk_score, risk_level = risk_scorer.calculate_risk_score(analysis)
    analysis.risk_score = risk_score
    analysis.risk_level = risk_level

    return analysis


@router.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    """
    Upload a contract document for analysis.

    Supports PDF and text files.
    """
    import uuid

    # Read file content
    content = await file.read()

    # Extract text based on file type
    filename = file.filename or "unknown"

    if filename.endswith(".pdf"):
        # Parse PDF
        from ..parsers.pdf_parser import PDFParser
        parser = PDFParser()
        text = parser.extract_text(content)
    elif filename.endswith((".txt", ".md")):
        text = content.decode("utf-8")
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use PDF or TXT."
        )

    # Generate document ID
    doc_id = str(uuid.uuid4())

    # Cache the text
    _contract_cache[doc_id] = text

    return {
        "document_id": doc_id,
        "filename": filename,
        "text_length": len(text),
        "message": "Contract uploaded. Use /analyze endpoint to analyze."
    }


# ============================================================================
# RISK ENDPOINTS
# ============================================================================

@router.get("/risk/{document_id}")
async def get_risk_breakdown(document_id: str):
    """
    Get detailed risk breakdown for an analyzed contract.
    """
    analysis_key = f"analysis_{document_id}"
    if analysis_key not in _contract_cache:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Analyze the contract first."
        )

    analysis = _contract_cache[analysis_key]
    return risk_scorer.get_risk_breakdown(analysis)


@router.get("/risk/{document_id}/problematic-clauses")
async def get_problematic_clauses(document_id: str):
    """
    Get list of problematic clauses that need attention.
    """
    analysis_key = f"analysis_{document_id}"
    if analysis_key not in _contract_cache:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Analyze the contract first."
        )

    analysis = _contract_cache[analysis_key]
    return risk_scorer.highlight_problematic_clauses(analysis)


# ============================================================================
# COMPARISON ENDPOINTS
# ============================================================================

@router.post("/compare", response_model=ContractComparison)
async def compare_contracts(request: CompareContractsRequest):
    """
    Compare two contracts side-by-side.
    """
    # Get both contracts
    if request.contract_a_id not in _contract_cache:
        raise HTTPException(status_code=404, detail=f"Contract A not found: {request.contract_a_id}")

    if request.contract_b_id not in _contract_cache:
        raise HTTPException(status_code=404, detail=f"Contract B not found: {request.contract_b_id}")

    text_a = _contract_cache[request.contract_a_id]
    text_b = _contract_cache[request.contract_b_id]

    comparison = await comparator.compare_contracts(
        contract_a_id=request.contract_a_id,
        contract_a_text=text_a,
        contract_b_id=request.contract_b_id,
        contract_b_text=text_b,
        comparison_type=request.comparison_type
    )

    return comparison


@router.get("/compare/{document_id_a}/{document_id_b}/side-by-side")
async def get_side_by_side(document_id_a: str, document_id_b: str):
    """
    Get side-by-side comparison view.
    """
    # Check if comparison exists
    comparison_key = f"comparison_{document_id_a}_{document_id_b}"

    if comparison_key in _contract_cache:
        comparison = _contract_cache[comparison_key]
    else:
        # Need to compare first
        raise HTTPException(
            status_code=404,
            detail="Comparison not found. Use /compare endpoint first."
        )

    return comparator.get_side_by_side_view(comparison)


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@router.post("/export/html/{document_id}")
async def export_to_html(
    document_id: str,
    include_sections: Optional[List[str]] = None
):
    """
    Export contract analysis to HTML.
    """
    analysis_key = f"analysis_{document_id}"
    if analysis_key not in _contract_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = _contract_cache[analysis_key]
    html = exporter.export_to_html(analysis, include_sections)

    return {"html": html}


@router.post("/export/pdf/{document_id}")
async def export_to_pdf(
    document_id: str,
    include_sections: Optional[List[str]] = None
):
    """
    Export contract analysis to PDF.

    Returns base64 encoded PDF.
    """
    import base64

    analysis_key = f"analysis_{document_id}"
    if analysis_key not in _contract_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = _contract_cache[analysis_key]

    try:
        pdf_bytes = exporter.export_to_pdf(analysis, include_sections)
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return {
            "pdf_base64": pdf_base64,
            "filename": f"contract_analysis_{document_id}.pdf"
        }
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF export not available: {str(e)}"
        )


@router.post("/export/docx/{document_id}")
async def export_to_docx(
    document_id: str,
    include_sections: Optional[List[str]] = None
):
    """
    Export contract analysis to Word document.

    Returns base64 encoded DOCX.
    """
    import base64

    analysis_key = f"analysis_{document_id}"
    if analysis_key not in _contract_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = _contract_cache[analysis_key]

    try:
        docx_bytes = exporter.export_to_docx(analysis, include_sections)
        docx_base64 = base64.b64encode(docx_bytes).decode("utf-8")

        return {
            "docx_base64": docx_base64,
            "filename": f"contract_analysis_{document_id}.docx"
        }
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DOCX export not available: {str(e)}"
        )


@router.post("/export/email/{document_id}")
async def get_email_content(
    document_id: str,
    recipient_name: Optional[str] = None
):
    """
    Get email content for sharing analysis.
    """
    analysis_key = f"analysis_{document_id}"
    if analysis_key not in _contract_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = _contract_cache[analysis_key]
    return exporter.get_email_content(analysis, recipient_name)


# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================

@router.get("/templates/clauses")
async def list_clause_templates(
    category: Optional[str] = None,
    risk_level: Optional[str] = None
):
    """
    List available clause templates.
    """
    level = RiskLevel(risk_level) if risk_level else None
    clauses = template_library.list_clauses(category=category, risk_level=level)

    return {
        "clauses": [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "description": c.description,
                "risk_level": c.risk_level.value,
                "variables": c.variables
            }
            for c in clauses
        ]
    }


@router.get("/templates/clauses/{clause_id}")
async def get_clause_template(clause_id: str):
    """
    Get a specific clause template.
    """
    clause = template_library.get_clause(clause_id)
    if not clause:
        raise HTTPException(status_code=404, detail="Clause template not found")

    return clause.model_dump()


@router.post("/templates/clauses/{clause_id}/render")
async def render_clause(clause_id: str, variables: dict):
    """
    Render a clause template with variables.
    """
    rendered = template_library.render_clause(clause_id, variables)
    if not rendered:
        raise HTTPException(status_code=404, detail="Clause template not found")

    return {"rendered_text": rendered}


@router.get("/templates/contracts")
async def list_contract_templates(contract_type: Optional[str] = None):
    """
    List available contract templates.
    """
    from .models import ContractType

    ct = ContractType(contract_type) if contract_type else None
    templates = template_library.list_contract_templates(contract_type=ct)

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "contract_type": t.contract_type.value,
                "description": t.description,
                "clause_count": len(t.clauses),
                "variables": t.variables
            }
            for t in templates
        ]
    }


@router.get("/templates/contracts/{template_id}")
async def get_contract_template(template_id: str):
    """
    Get a specific contract template with all clauses.
    """
    template = template_library.get_contract_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Contract template not found")

    return {
        "id": template.id,
        "name": template.name,
        "contract_type": template.contract_type.value,
        "description": template.description,
        "variables": template.variables,
        "clauses": [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "template_text": c.template_text,
                "best_practice_notes": c.best_practice_notes
            }
            for c in template.clauses
        ]
    }


@router.post("/templates/contracts/{template_id}/render")
async def render_contract_template(template_id: str, variables: dict):
    """
    Render a full contract template with variables.
    """
    rendered = template_library.render_contract_template(template_id, variables)
    if not rendered:
        raise HTTPException(status_code=404, detail="Contract template not found")

    return {"rendered_text": rendered}


@router.get("/templates/best-practices/{category}")
async def get_best_practices(category: str):
    """
    Get best practices for a clause category.
    """
    practices = template_library.get_best_practices(category)
    return {"category": category, "best_practices": practices}


@router.post("/templates/suggest-missing")
async def suggest_missing_clauses(
    contract_type: str,
    existing_categories: List[str]
):
    """
    Suggest missing clauses based on contract type.
    """
    from .models import ContractType

    ct = ContractType(contract_type)
    suggestions = template_library.suggest_missing_clauses(ct, existing_categories)

    return {
        "suggestions": [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "description": c.description,
                "importance": "Recommended for this contract type"
            }
            for c in suggestions
        ]
    }


# ============================================================================
# QUICK EXTRACTION ENDPOINTS
# ============================================================================

@router.post("/extract/parties")
async def extract_parties(contract_text: str):
    """
    Quick extraction of parties from contract text.
    """
    parties = await analyzer.extract_parties(contract_text)
    return {"parties": [p.model_dump() for p in parties]}


@router.post("/extract/dates")
async def extract_dates(contract_text: str):
    """
    Quick extraction of key dates from contract text.
    """
    dates = await analyzer.extract_key_dates(contract_text)
    return {"dates": [d.model_dump() for d in dates]}


@router.post("/extract/risks")
async def extract_risks(contract_text: str):
    """
    Quick extraction of risks from contract text.
    """
    risks = await analyzer.identify_risks(contract_text)
    return {"risks": [r.model_dump() for r in risks]}

