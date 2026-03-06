"""
ContractIQ - Contract Analysis Module
Specialized prompts and analysis for legal contracts.
"""

# Models first (no dependencies)
from .models import (
    ContractAnalysis,
    ContractParty,
    KeyDate,
    PaymentTerms,
    TerminationClause,
    LiabilityClause,
    RiskFlag,
    RiskLevel,
    ContractComparison,
    ClauseTemplate,
    ContractTemplate,
    ContractType
)

# Prompts (depends on nothing)
from .prompts import CONTRACT_PROMPTS, get_contract_prompt

# Templates (depends on models)
from .templates import TemplateLibrary, CLAUSE_TEMPLATES, CONTRACT_TEMPLATES

# Risk scorer (depends on models)
from .risk_scorer import RiskScorer

# Export (depends on models)
from .export import ContractExporter

# Analyzer (depends on models, prompts)
from .analyzer import ContractAnalyzer

# Comparator (depends on models, prompts, risk_scorer)
from .comparator import ContractComparator

# Router last (depends on everything)
from .router import router as contract_router

__all__ = [
    # Router
    "contract_router",
    # Analyzer
    "ContractAnalyzer",
    # Prompts
    "CONTRACT_PROMPTS",
    "get_contract_prompt",
    # Models
    "ContractAnalysis",
    "ContractParty",
    "KeyDate",
    "PaymentTerms",
    "TerminationClause",
    "LiabilityClause",
    "RiskFlag",
    "RiskLevel",
    "ContractComparison",
    "ClauseTemplate",
    "ContractTemplate",
    "ContractType",
    # Risk
    "RiskScorer",
    # Comparison
    "ContractComparator",
    # Templates
    "TemplateLibrary",
    "CLAUSE_TEMPLATES",
    "CONTRACT_TEMPLATES",
    # Export
    "ContractExporter",
]

