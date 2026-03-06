"""
FinanceDigest API Router
FastAPI endpoints for financial analysis.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Form
from typing import Optional, List
import logging
import uuid
from io import BytesIO

from .models import (
    FinancialAnalysis,
    FinancialComparison,
    CompanyWatchlist,
    FinancialAlert,
    SECFiling,
    SECSearchResult,
    AnalyzeReportRequest,
    CompareReportsRequest,
    WatchlistAddRequest,
    SECSearchRequest
)
from .analyzer import FinancialAnalyzer
from .comparator import FinancialComparator
from .watchlist import WatchlistManager
from .sec_client import SECEdgarClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finance", tags=["finance"])

# Initialize services
analyzer = FinancialAnalyzer()
comparator = FinancialComparator()
watchlist_manager = WatchlistManager()
sec_client = SECEdgarClient()

# In-memory storage
_report_cache: dict = {}


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@router.post("/analyze", response_model=FinancialAnalysis)
async def analyze_report(
    document_id: str = Form(...),
    filing_type: Optional[str] = Form(None),
    company_ticker: Optional[str] = Form(None),
    include_thesis: bool = Form(True),
    file: Optional[UploadFile] = File(None)
):
    """
    Analyze a financial report.

    Parameters:
    - document_id: Unique identifier for the document
    - file: Optional file upload (PDF, TXT, DOCX)
    - filing_type: Type of filing (10-K, 10-Q, 8-K, etc.)
    - company_ticker: Stock ticker symbol
    - include_thesis: Whether to generate investment thesis
    """
    report_text = None

    # If file is uploaded, extract text
    if file:
        file_content = await file.read()

        if file.filename.endswith('.pdf'):
            from ..parsers import PDFParser
            parser = PDFParser()
            pdf_data = parser.parse_bytes(file_content)
            report_text = pdf_data.text
        elif file.filename.endswith(('.docx', '.doc')):
            from docx import Document
            doc = Document(BytesIO(file_content))
            report_text = '\n'.join([p.text for p in doc.paragraphs])
        else:
            # Assume text file
            report_text = file_content.decode('utf-8', errors='ignore')

    # Fallback to cache
    if not report_text:
        if document_id not in _report_cache:
            raise HTTPException(
                status_code=400,
                detail="No file uploaded and document not found in cache. Please upload a document."
            )
        report_text = _report_cache[document_id]

    analysis = await analyzer.analyze_report(
        document_id=document_id,
        report_text=report_text,
        filing_type=filing_type,
        company_ticker=company_ticker,
        include_thesis=include_thesis
    )

    _report_cache[f"analysis_{document_id}"] = analysis

    return analysis


@router.post("/analyze/text", response_model=FinancialAnalysis)
async def analyze_report_text(
    report_text: str,
    filing_type: Optional[str] = None,
    company_ticker: Optional[str] = None,
    include_thesis: bool = True
):
    """
    Analyze report text directly.
    """
    doc_id = str(uuid.uuid4())

    analysis = await analyzer.analyze_report(
        document_id=doc_id,
        report_text=report_text,
        filing_type=filing_type,
        company_ticker=company_ticker,
        include_thesis=include_thesis
    )

    return analysis


@router.post("/upload")
async def upload_report(file: UploadFile = File(...)):
    """
    Upload a financial report for analysis.

    Supports PDF and text files.
    """
    content = await file.read()
    filename = file.filename or "unknown"

    # Extract text
    if filename.endswith(".pdf"):
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

    doc_id = str(uuid.uuid4())
    _report_cache[doc_id] = text

    return {
        "document_id": doc_id,
        "filename": filename,
        "text_length": len(text),
        "message": "Report uploaded. Use /analyze endpoint."
    }


# ============================================================================
# EXTRACTION ENDPOINTS
# ============================================================================

@router.post("/extract/revenue")
async def extract_revenue(report_text: str):
    """Extract revenue metrics from report text."""
    metrics = await analyzer.extract_revenue_metrics(report_text)
    if not metrics:
        raise HTTPException(status_code=422, detail="Could not extract revenue metrics")
    return metrics.model_dump()


@router.post("/extract/risks")
async def extract_risks(report_text: str):
    """Extract risk factors from report text."""
    risks = await analyzer.extract_risk_factors(report_text)
    return {"risks": [r.model_dump() for r in risks]}


@router.post("/extract/red-flags")
async def extract_red_flags(report_text: str):
    """Detect red flags in report text."""
    flags = await analyzer.detect_red_flags(report_text)
    return {"red_flags": [f.model_dump() for f in flags]}


# ============================================================================
# COMPARISON ENDPOINTS
# ============================================================================

@router.post("/compare", response_model=FinancialComparison)
async def compare_reports(request: CompareReportsRequest):
    """
    Compare two financial reports.
    """
    if request.document_a_id not in _report_cache:
        raise HTTPException(status_code=404, detail="Report A not found")
    if request.document_b_id not in _report_cache:
        raise HTTPException(status_code=404, detail="Report B not found")

    text_a = _report_cache[request.document_a_id]
    text_b = _report_cache[request.document_b_id]

    # Get analysis if available for better comparison
    analysis_a = _report_cache.get(f"analysis_{request.document_a_id}")
    analysis_b = _report_cache.get(f"analysis_{request.document_b_id}")

    if analysis_a and analysis_b:
        comparison = await comparator.compare_analyses(analysis_a, analysis_b)
    else:
        comparison = await comparator.compare_reports(
            report_a_text=text_a,
            report_b_text=text_b,
            period_a="Period A",
            period_b="Period B",
            comparison_type=request.comparison_type
        )

    return comparison


@router.post("/compare/text")
async def compare_reports_text(
    report_a_text: str,
    report_b_text: str,
    period_a: str = "Period A",
    period_b: str = "Period B",
    comparison_type: str = "sequential"
):
    """
    Compare two report texts directly.
    """
    comparison = await comparator.compare_reports(
        report_a_text=report_a_text,
        report_b_text=report_b_text,
        period_a=period_a,
        period_b=period_b,
        comparison_type=comparison_type
    )

    return comparison


# ============================================================================
# WATCHLIST ENDPOINTS
# ============================================================================

@router.get("/watchlist", response_model=CompanyWatchlist)
async def get_watchlist(user_id: str = Query(..., description="User ID")):
    """Get user's company watchlist."""
    return watchlist_manager.get_watchlist(user_id)


@router.post("/watchlist/add")
async def add_to_watchlist(
    user_id: str,
    request: WatchlistAddRequest
):
    """Add a company to watchlist."""
    # Try to get company name from SEC if not provided
    company_name = request.company_name
    if not company_name:
        info = await sec_client.get_company_info(request.ticker)
        if info:
            company_name = info.get("name", request.ticker)
        else:
            company_name = request.ticker

    item = watchlist_manager.add_to_watchlist(
        user_id=user_id,
        ticker=request.ticker,
        company_name=company_name,
        notes=request.notes,
        alert_on_filings=request.alert_on_filings,
        alert_on_price_change=request.alert_on_price_change,
        price_alert_threshold=request.price_alert_threshold
    )

    return {"message": f"Added {item.ticker} to watchlist", "item": item.model_dump()}


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    user_id: str = Query(..., description="User ID")
):
    """Remove a company from watchlist."""
    removed = watchlist_manager.remove_from_watchlist(user_id, ticker)
    if not removed:
        raise HTTPException(status_code=404, detail="Company not in watchlist")

    return {"message": f"Removed {ticker} from watchlist"}


# ============================================================================
# ALERT ENDPOINTS
# ============================================================================

@router.get("/alerts")
async def get_alerts(
    user_id: str = Query(..., description="User ID"),
    unread_only: bool = False,
    limit: int = 50
):
    """Get user's alerts."""
    alerts = watchlist_manager.get_alerts(user_id, unread_only, limit)
    return {"alerts": [a.model_dump() for a in alerts]}


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Mark an alert as read."""
    success = watchlist_manager.mark_alert_read(user_id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"message": "Alert marked as read"}


@router.post("/alerts/read-all")
async def mark_all_alerts_read(
    user_id: str = Query(..., description="User ID")
):
    """Mark all alerts as read."""
    count = watchlist_manager.mark_all_read(user_id)
    return {"message": f"Marked {count} alerts as read"}


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    user_id: str = Query(..., description="User ID")
):
    """Delete an alert."""
    success = watchlist_manager.delete_alert(user_id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"message": "Alert deleted"}


@router.post("/alerts/check-filings")
async def check_for_new_filings(
    user_id: str = Query(..., description="User ID")
):
    """
    Check for new filings for watchlist companies.
    Creates alerts for any new filings found.
    """
    alerts = await watchlist_manager.check_for_new_filings(sec_client, user_id)
    return {
        "message": f"Found {len(alerts)} new filing(s)",
        "alerts": [a.model_dump() for a in alerts]
    }


# ============================================================================
# SEC EDGAR ENDPOINTS
# ============================================================================

@router.get("/sec/filings/{ticker}")
async def get_company_filings(
    ticker: str,
    filing_type: Optional[str] = None,
    limit: int = 10
) -> List[dict]:
    """
    Get SEC filings for a company.

    Args:
        ticker: Stock ticker (e.g., AAPL, MSFT)
        filing_type: Filter by type (10-K, 10-Q, 8-K)
        limit: Maximum results
    """
    filings = await sec_client.get_company_filings(
        ticker=ticker,
        filing_type=filing_type,
        limit=limit
    )

    return [f.model_dump() for f in filings]


@router.get("/sec/filings/{ticker}/10k")
async def get_10k_filings(ticker: str, limit: int = 5):
    """Get 10-K annual reports."""
    filings = await sec_client.get_10k_filings(ticker, limit)
    return [f.model_dump() for f in filings]


@router.get("/sec/filings/{ticker}/10q")
async def get_10q_filings(ticker: str, limit: int = 4):
    """Get 10-Q quarterly reports."""
    filings = await sec_client.get_10q_filings(ticker, limit)
    return [f.model_dump() for f in filings]


@router.get("/sec/filings/{ticker}/8k")
async def get_8k_filings(ticker: str, limit: int = 10):
    """Get 8-K current reports."""
    filings = await sec_client.get_8k_filings(ticker, limit)
    return [f.model_dump() for f in filings]


@router.post("/sec/search")
async def search_sec_filings(request: SECSearchRequest):
    """
    Search SEC filings.
    """
    result = await sec_client.search_filings(
        query=request.ticker or request.cik or "",
        filing_types=[request.filing_type] if request.filing_type else None,
        start_date=request.start_date,
        end_date=request.end_date,
        limit=request.limit
    )

    return result.model_dump()


@router.get("/sec/company/{ticker}")
async def get_company_info(ticker: str):
    """Get company information from SEC."""
    info = await sec_client.get_company_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail="Company not found")

    return info


@router.post("/sec/download")
async def download_and_analyze_filing(
    ticker: str,
    filing_type: str = "10-K",
    include_thesis: bool = True
):
    """
    Download latest filing from SEC and analyze it.

    This is a convenience endpoint that:
    1. Fetches the latest filing of specified type
    2. Downloads the document
    3. Analyzes it

    Args:
        ticker: Stock ticker
        filing_type: Type of filing (10-K, 10-Q)
        include_thesis: Generate investment thesis
    """
    # Get latest filing
    filings = await sec_client.get_company_filings(
        ticker=ticker,
        filing_type=filing_type,
        limit=1
    )

    if not filings:
        raise HTTPException(
            status_code=404,
            detail=f"No {filing_type} filings found for {ticker}"
        )

    filing = filings[0]

    # Download content
    content = await sec_client.download_filing(filing)
    if not content:
        raise HTTPException(
            status_code=500,
            detail="Failed to download filing"
        )

    # Store
    doc_id = str(uuid.uuid4())
    _report_cache[doc_id] = content

    # Analyze
    analysis = await analyzer.analyze_report(
        document_id=doc_id,
        report_text=content,
        filing_type=filing_type,
        company_ticker=ticker,
        include_thesis=include_thesis
    )

    _report_cache[f"analysis_{doc_id}"] = analysis

    return {
        "filing": filing.model_dump(),
        "document_id": doc_id,
        "analysis": analysis.model_dump()
    }

