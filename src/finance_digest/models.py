"""
FinanceDigest Models
Pydantic models for financial report analysis.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class FilingType(str, Enum):
    """SEC filing types."""
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    EARNINGS = "earnings"
    ANNUAL_REPORT = "annual_report"
    QUARTERLY_REPORT = "quarterly_report"
    OTHER = "other"


class Sentiment(str, Enum):
    """Sentiment classification."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class RiskSeverity(str, Enum):
    """Risk severity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""
    NEW_FILING = "new_filing"
    PRICE_CHANGE = "price_change"
    EARNINGS_RELEASE = "earnings_release"
    RISK_CHANGE = "risk_change"
    GUIDANCE_CHANGE = "guidance_change"


# ============================================================================
# FINANCIAL METRICS
# ============================================================================

class RevenueMetrics(BaseModel):
    """Revenue and growth metrics."""
    total_revenue: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None  # Year-over-year %
    revenue_growth_qoq: Optional[float] = None  # Quarter-over-quarter %
    revenue_by_segment: Dict[str, float] = Field(default_factory=dict)
    revenue_by_geography: Dict[str, float] = Field(default_factory=dict)
    recurring_revenue: Optional[float] = None
    recurring_revenue_percentage: Optional[float] = None
    currency: str = "USD"
    period: str = ""  # e.g., "Q3 2025", "FY 2025"
    guidance_next_quarter: Optional[str] = None
    guidance_full_year: Optional[str] = None


class ProfitabilityMetrics(BaseModel):
    """Profitability and margin metrics."""
    gross_profit: Optional[float] = None
    gross_margin: Optional[float] = None  # %
    operating_income: Optional[float] = None
    operating_margin: Optional[float] = None  # %
    net_income: Optional[float] = None
    net_margin: Optional[float] = None  # %
    ebitda: Optional[float] = None
    ebitda_margin: Optional[float] = None  # %
    eps: Optional[float] = None  # Earnings per share
    eps_diluted: Optional[float] = None
    eps_growth_yoy: Optional[float] = None  # %


class CashFlowMetrics(BaseModel):
    """Cash flow metrics."""
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    total_debt: Optional[float] = None
    net_debt: Optional[float] = None


class ValuationMetrics(BaseModel):
    """Valuation ratios."""
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    ps_ratio: Optional[float] = None  # Price to sales
    pb_ratio: Optional[float] = None  # Price to book
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    market_cap: Optional[float] = None


class FinancialRatios(BaseModel):
    """Key financial ratios."""
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    return_on_equity: Optional[float] = None  # ROE %
    return_on_assets: Optional[float] = None  # ROA %
    return_on_invested_capital: Optional[float] = None  # ROIC %
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None


# ============================================================================
# ANALYSIS MODELS
# ============================================================================

class RiskFactor(BaseModel):
    """Risk factor identified in financial report."""
    category: str  # e.g., "Market Risk", "Operational Risk", "Regulatory Risk"
    title: str
    description: str
    severity: RiskSeverity = RiskSeverity.MODERATE
    is_new: bool = False  # New risk vs existing
    trend: str = "stable"  # "increasing", "stable", "decreasing"
    mitigation: Optional[str] = None
    source_section: Optional[str] = None


class ManagementOutlook(BaseModel):
    """Management's outlook and guidance."""
    overall_sentiment: Sentiment = Sentiment.NEUTRAL
    key_themes: List[str] = Field(default_factory=list)
    growth_expectations: Optional[str] = None
    challenges_mentioned: List[str] = Field(default_factory=list)
    opportunities_mentioned: List[str] = Field(default_factory=list)
    strategic_initiatives: List[str] = Field(default_factory=list)
    guidance_revenue: Optional[str] = None
    guidance_earnings: Optional[str] = None
    guidance_other: Dict[str, str] = Field(default_factory=dict)
    notable_quotes: List[str] = Field(default_factory=list)


class InvestmentThesis(BaseModel):
    """AI-generated investment thesis."""
    recommendation: str  # "Buy", "Hold", "Sell", "Avoid"
    confidence: float = 0.0  # 0-100%
    summary: str = ""
    bull_case: List[str] = Field(default_factory=list)
    bear_case: List[str] = Field(default_factory=list)
    key_catalysts: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    target_price_analysis: Optional[str] = None
    time_horizon: str = "12 months"


class RedFlag(BaseModel):
    """Red flag or warning sign."""
    flag_type: str
    severity: RiskSeverity
    description: str
    evidence: str
    recommendation: str


# ============================================================================
# MAIN ANALYSIS MODEL
# ============================================================================

class FinancialAnalysis(BaseModel):
    """Complete financial analysis result."""
    # Metadata
    document_id: str
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    filing_type: FilingType = FilingType.OTHER
    filing_date: Optional[str] = None
    period: str = ""  # e.g., "Q3 2025"
    analyzed_at: str = ""

    # Executive Summary
    summary: str = ""
    key_highlights: List[str] = Field(default_factory=list)
    overall_sentiment: Sentiment = Sentiment.NEUTRAL

    # Metrics
    revenue: Optional[RevenueMetrics] = None
    profitability: Optional[ProfitabilityMetrics] = None
    cash_flow: Optional[CashFlowMetrics] = None
    valuation: Optional[ValuationMetrics] = None
    ratios: Optional[FinancialRatios] = None

    # Analysis
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    management_outlook: Optional[ManagementOutlook] = None
    investment_thesis: Optional[InvestmentThesis] = None
    red_flags: List[RedFlag] = Field(default_factory=list)

    # Comparison data
    yoy_changes: Dict[str, float] = Field(default_factory=dict)
    qoq_changes: Dict[str, float] = Field(default_factory=dict)

    # Recommendations
    action_items: List[str] = Field(default_factory=list)


# ============================================================================
# COMPARISON MODELS
# ============================================================================

class MetricChange(BaseModel):
    """Change in a metric between periods."""
    metric_name: str
    period_a_value: Optional[float] = None
    period_b_value: Optional[float] = None
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    trend: str = "stable"  # "improving", "stable", "declining"
    significance: str = "normal"  # "significant", "normal", "minor"


class FinancialComparison(BaseModel):
    """Comparison between two financial reports."""
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    period_a: str  # e.g., "Q2 2025"
    period_b: str  # e.g., "Q3 2025"
    comparison_type: str  # "sequential", "yoy", "competitor"
    compared_at: str = ""

    # Summary
    summary: str = ""
    key_changes: List[str] = Field(default_factory=list)
    overall_trend: str = ""  # "improving", "stable", "declining"

    # Detailed changes
    revenue_changes: List[MetricChange] = Field(default_factory=list)
    profitability_changes: List[MetricChange] = Field(default_factory=list)
    other_changes: List[MetricChange] = Field(default_factory=list)

    # Risk changes
    new_risks: List[RiskFactor] = Field(default_factory=list)
    resolved_risks: List[str] = Field(default_factory=list)

    # Analysis
    analysis: str = ""
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# WATCHLIST & ALERTS
# ============================================================================

class WatchlistItem(BaseModel):
    """A company in the watchlist."""
    ticker: str
    company_name: str
    added_at: str = ""
    notes: Optional[str] = None
    alert_on_filings: bool = True
    alert_on_price_change: bool = False
    price_alert_threshold: Optional[float] = None  # % change
    last_filing_date: Optional[str] = None
    last_price: Optional[float] = None


class CompanyWatchlist(BaseModel):
    """User's company watchlist."""
    user_id: str
    items: List[WatchlistItem] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class FinancialAlert(BaseModel):
    """Alert notification."""
    id: str
    user_id: str
    alert_type: AlertType
    ticker: str
    company_name: str
    title: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""
    read: bool = False
    sent: bool = False


# ============================================================================
# SEC FILING MODELS
# ============================================================================

class SECFiling(BaseModel):
    """SEC filing metadata."""
    accession_number: str
    filing_type: str
    company_name: str
    cik: str
    ticker: Optional[str] = None
    filing_date: str
    accepted_date: str
    document_url: str
    filing_url: str
    period_of_report: Optional[str] = None
    size: Optional[int] = None


class SECSearchResult(BaseModel):
    """SEC filing search results."""
    query: str
    total_results: int
    filings: List[SECFiling] = Field(default_factory=list)


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeReportRequest(BaseModel):
    """Request to analyze a financial report."""
    document_id: str
    filing_type: Optional[str] = None
    company_ticker: Optional[str] = None
    include_thesis: bool = True


class CompareReportsRequest(BaseModel):
    """Request to compare two reports."""
    document_a_id: str
    document_b_id: str
    comparison_type: str = "sequential"  # "sequential", "yoy", "competitor"


class WatchlistAddRequest(BaseModel):
    """Request to add company to watchlist."""
    ticker: str
    company_name: Optional[str] = None
    notes: Optional[str] = None
    alert_on_filings: bool = True
    alert_on_price_change: bool = False
    price_alert_threshold: Optional[float] = None


class SECSearchRequest(BaseModel):
    """Request to search SEC filings."""
    ticker: Optional[str] = None
    cik: Optional[str] = None
    filing_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 10

