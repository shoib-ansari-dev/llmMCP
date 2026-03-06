"""
ContractIQ Models
Pydantic models for contract analysis.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContractType(str, Enum):
    """Types of contracts."""
    EMPLOYMENT = "employment"
    NDA = "nda"
    SERVICE = "service"
    SALES = "sales"
    LEASE = "lease"
    LICENSE = "license"
    PARTNERSHIP = "partnership"
    VENDOR = "vendor"
    CONSULTING = "consulting"
    OTHER = "other"


# ============================================================================
# EXTRACTED DATA MODELS
# ============================================================================

class ContractParty(BaseModel):
    """Party involved in the contract."""
    name: str
    role: str  # e.g., "Buyer", "Seller", "Licensor", "Employee"
    address: Optional[str] = None
    contact: Optional[str] = None
    entity_type: Optional[str] = None  # e.g., "Corporation", "Individual", "LLC"


class KeyDate(BaseModel):
    """Important date in the contract."""
    date_type: str  # e.g., "Effective Date", "Expiration", "Renewal Deadline"
    date_value: Optional[date] = None
    date_text: str  # Original text from contract
    is_recurring: bool = False
    reminder_days: Optional[int] = None  # Days before to remind


class PaymentTerms(BaseModel):
    """Payment terms extracted from contract."""
    amount: Optional[float] = None
    currency: str = "USD"
    frequency: Optional[str] = None  # e.g., "Monthly", "One-time", "Annual"
    due_date: Optional[str] = None
    payment_method: Optional[str] = None
    late_fee: Optional[str] = None
    late_fee_percentage: Optional[float] = None
    net_days: Optional[int] = None  # Net 30, Net 60, etc.
    description: str = ""


class TerminationClause(BaseModel):
    """Termination clause details."""
    termination_type: str  # "for_cause", "for_convenience", "mutual", "automatic"
    notice_period: Optional[str] = None  # e.g., "30 days", "90 days"
    notice_period_days: Optional[int] = None
    conditions: List[str] = Field(default_factory=list)
    penalties: Optional[str] = None
    survival_clauses: List[str] = Field(default_factory=list)
    original_text: str = ""


class LiabilityClause(BaseModel):
    """Liability and indemnification details."""
    liability_type: str  # "limitation", "indemnification", "warranty", "disclaimer"
    cap_amount: Optional[float] = None
    cap_description: Optional[str] = None
    excluded_damages: List[str] = Field(default_factory=list)
    indemnifying_party: Optional[str] = None
    indemnified_party: Optional[str] = None
    scope: Optional[str] = None
    original_text: str = ""


class RiskFlag(BaseModel):
    """Risk or red flag identified in contract."""
    risk_type: str
    severity: RiskLevel
    clause_reference: Optional[str] = None
    description: str
    recommendation: Optional[str] = None
    original_text: Optional[str] = None


class ConfidentialityClause(BaseModel):
    """Confidentiality/NDA clause details."""
    duration: Optional[str] = None
    duration_years: Optional[int] = None
    scope: str = ""
    exceptions: List[str] = Field(default_factory=list)
    return_of_materials: bool = False
    original_text: str = ""


class IntellectualPropertyClause(BaseModel):
    """IP ownership and licensing details."""
    ip_type: str  # "ownership", "license", "assignment", "work_for_hire"
    owner: Optional[str] = None
    scope: str = ""
    restrictions: List[str] = Field(default_factory=list)
    original_text: str = ""


class DisputeResolution(BaseModel):
    """Dispute resolution clause details."""
    method: str  # "litigation", "arbitration", "mediation", "negotiation"
    venue: Optional[str] = None
    governing_law: Optional[str] = None
    arbitration_rules: Optional[str] = None
    original_text: str = ""


# ============================================================================
# MAIN ANALYSIS MODEL
# ============================================================================

class ContractAnalysis(BaseModel):
    """Complete contract analysis result."""
    # Metadata
    document_id: str
    contract_type: ContractType = ContractType.OTHER
    contract_title: Optional[str] = None
    analyzed_at: str = ""

    # Executive Summary
    summary: str = ""
    key_points: List[str] = Field(default_factory=list)

    # Parties
    parties: List[ContractParty] = Field(default_factory=list)

    # Key Dates
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    key_dates: List[KeyDate] = Field(default_factory=list)

    # Financial Terms
    payment_terms: List[PaymentTerms] = Field(default_factory=list)
    total_value: Optional[float] = None

    # Key Clauses
    termination_clauses: List[TerminationClause] = Field(default_factory=list)
    liability_clauses: List[LiabilityClause] = Field(default_factory=list)
    confidentiality: Optional[ConfidentialityClause] = None
    intellectual_property: List[IntellectualPropertyClause] = Field(default_factory=list)
    dispute_resolution: Optional[DisputeResolution] = None

    # Risk Assessment
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: int = 0  # 0-100
    risk_flags: List[RiskFlag] = Field(default_factory=list)

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    missing_clauses: List[str] = Field(default_factory=list)

    # Raw extracted text sections
    extracted_sections: Dict[str, str] = Field(default_factory=dict)


# ============================================================================
# COMPARISON MODELS
# ============================================================================

class ClauseDifference(BaseModel):
    """Difference between clauses in two contracts."""
    clause_type: str
    contract_a_text: Optional[str] = None
    contract_b_text: Optional[str] = None
    difference_type: str  # "added", "removed", "modified", "same"
    significance: RiskLevel = RiskLevel.LOW
    analysis: str = ""


class ContractComparison(BaseModel):
    """Comparison between two contracts."""
    contract_a_id: str
    contract_b_id: str
    compared_at: str = ""

    # Summary
    similarity_score: float = 0.0  # 0-100%
    summary: str = ""

    # Differences
    differences: List[ClauseDifference] = Field(default_factory=list)

    # Key differences highlighted
    key_differences: List[str] = Field(default_factory=list)

    # Risk comparison
    contract_a_risk: RiskLevel = RiskLevel.LOW
    contract_b_risk: RiskLevel = RiskLevel.LOW
    risk_comparison: str = ""

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# TEMPLATE MODELS
# ============================================================================

class ClauseTemplate(BaseModel):
    """Template for a contract clause."""
    id: str
    name: str
    category: str  # e.g., "Termination", "Liability", "Confidentiality"
    description: str
    template_text: str
    variables: List[str] = Field(default_factory=list)  # Placeholders like {PARTY_NAME}
    risk_level: RiskLevel = RiskLevel.LOW
    best_practice_notes: str = ""
    jurisdiction: Optional[str] = None  # e.g., "US", "UK", "EU"


class ContractTemplate(BaseModel):
    """Full contract template."""
    id: str
    name: str
    contract_type: ContractType
    description: str
    clauses: List[ClauseTemplate] = Field(default_factory=list)
    variables: Dict[str, str] = Field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeContractRequest(BaseModel):
    """Request to analyze a contract."""
    document_id: str
    analysis_depth: str = "full"  # "quick", "standard", "full"
    focus_areas: List[str] = Field(default_factory=list)  # e.g., ["risk", "payment", "termination"]


class CompareContractsRequest(BaseModel):
    """Request to compare two contracts."""
    contract_a_id: str
    contract_b_id: str
    comparison_type: str = "full"  # "full", "clauses_only", "risk_only"


class GenerateReportRequest(BaseModel):
    """Request to generate a contract report."""
    document_id: str
    report_format: str = "pdf"  # "pdf", "docx", "html"
    include_sections: List[str] = Field(default_factory=list)
    recipient_email: Optional[str] = None

