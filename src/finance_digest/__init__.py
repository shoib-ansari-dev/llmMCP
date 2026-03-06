"""
FinanceDigest - Financial Report Analyzer
Specialized analysis for financial documents like 10-K, 10-Q, earnings reports.
"""

from .analyzer import FinancialAnalyzer
from .prompts import FINANCIAL_PROMPTS, get_financial_prompt
from .models import (
    FinancialAnalysis,
    RevenueMetrics,
    ProfitabilityMetrics,
    RiskFactor,
    ManagementOutlook,
    InvestmentThesis,
    FinancialComparison,
    CompanyWatchlist,
    FinancialAlert,
    SECFiling
)
from .comparator import FinancialComparator
from .watchlist import WatchlistManager
from .sec_client import SECEdgarClient
from .router import router as finance_router

__all__ = [
    # Router
    "finance_router",
    # Analyzer
    "FinancialAnalyzer",
    # Prompts
    "FINANCIAL_PROMPTS",
    "get_financial_prompt",
    # Models
    "FinancialAnalysis",
    "RevenueMetrics",
    "ProfitabilityMetrics",
    "RiskFactor",
    "ManagementOutlook",
    "InvestmentThesis",
    "FinancialComparison",
    "CompanyWatchlist",
    "FinancialAlert",
    "SECFiling",
    # Comparator
    "FinancialComparator",
    # Watchlist
    "WatchlistManager",
    # SEC
    "SECEdgarClient",
]

