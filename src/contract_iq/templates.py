"""
ContractIQ Template Library
Common contract templates and clause library.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .models import (
    ClauseTemplate,
    ContractTemplate,
    ContractType,
    RiskLevel
)

logger = logging.getLogger(__name__)


# ============================================================================
# CLAUSE TEMPLATES
# ============================================================================

CLAUSE_TEMPLATES: Dict[str, ClauseTemplate] = {

    # -------------------------------------------------------------------------
    # LIMITATION OF LIABILITY
    # -------------------------------------------------------------------------
    "limitation_of_liability_standard": ClauseTemplate(
        id="lol_standard",
        name="Standard Limitation of Liability",
        category="Liability",
        description="Caps liability at fees paid in last 12 months",
        template_text="""
LIMITATION OF LIABILITY. IN NO EVENT SHALL EITHER PARTY'S TOTAL LIABILITY 
ARISING OUT OF OR RELATED TO THIS AGREEMENT EXCEED THE AMOUNTS PAID BY 
{CLIENT_NAME} TO {PROVIDER_NAME} DURING THE TWELVE (12) MONTH PERIOD 
IMMEDIATELY PRECEDING THE EVENT GIVING RISE TO SUCH LIABILITY.

NEITHER PARTY SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, 
CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF 
PROFITS, DATA, OR USE, REGARDLESS OF THE THEORY OF LIABILITY.
        """.strip(),
        variables=["CLIENT_NAME", "PROVIDER_NAME"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="Standard clause that protects both parties. The 12-month cap is industry standard."
    ),

    "limitation_of_liability_mutual": ClauseTemplate(
        id="lol_mutual",
        name="Mutual Limitation of Liability",
        category="Liability",
        description="Mutual liability cap with carve-outs",
        template_text="""
LIMITATION OF LIABILITY. EXCEPT FOR (I) A PARTY'S INDEMNIFICATION OBLIGATIONS, 
(II) A PARTY'S BREACH OF CONFIDENTIALITY, OR (III) A PARTY'S GROSS NEGLIGENCE 
OR WILLFUL MISCONDUCT:

(a) NEITHER PARTY SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, 
CONSEQUENTIAL, OR PUNITIVE DAMAGES; AND

(b) EACH PARTY'S TOTAL CUMULATIVE LIABILITY SHALL NOT EXCEED {LIABILITY_CAP}.
        """.strip(),
        variables=["LIABILITY_CAP"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="Includes standard carve-outs for serious breaches."
    ),

    # -------------------------------------------------------------------------
    # INDEMNIFICATION
    # -------------------------------------------------------------------------
    "indemnification_mutual": ClauseTemplate(
        id="indem_mutual",
        name="Mutual Indemnification",
        category="Indemnification",
        description="Balanced indemnification for both parties",
        template_text="""
INDEMNIFICATION.

{PARTY_A} agrees to indemnify, defend, and hold harmless {PARTY_B} from and 
against any claims, damages, losses, and expenses arising out of:
(a) {PARTY_A}'s breach of this Agreement;
(b) {PARTY_A}'s negligence or willful misconduct;
(c) {PARTY_A}'s violation of applicable law.

{PARTY_B} agrees to indemnify, defend, and hold harmless {PARTY_A} from and 
against any claims, damages, losses, and expenses arising out of:
(a) {PARTY_B}'s breach of this Agreement;
(b) {PARTY_B}'s negligence or willful misconduct;
(c) {PARTY_B}'s violation of applicable law.
        """.strip(),
        variables=["PARTY_A", "PARTY_B"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="Mutual and balanced. Each party is responsible for their own actions."
    ),

    "indemnification_ip": ClauseTemplate(
        id="indem_ip",
        name="IP Indemnification",
        category="Indemnification",
        description="Protection against IP infringement claims",
        template_text="""
IP INDEMNIFICATION. {PROVIDER_NAME} shall indemnify, defend, and hold harmless 
{CLIENT_NAME} from and against any third-party claim that the Services or 
Deliverables infringe any patent, copyright, trademark, or trade secret of 
such third party.

{PROVIDER_NAME}'s obligations shall not apply to the extent a claim arises from:
(a) modifications made by {CLIENT_NAME};
(b) combination with third-party materials not provided by {PROVIDER_NAME};
(c) {CLIENT_NAME}'s specifications that caused the infringement.
        """.strip(),
        variables=["PROVIDER_NAME", "CLIENT_NAME"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="Standard IP indemnification with reasonable carve-outs."
    ),

    # -------------------------------------------------------------------------
    # TERMINATION
    # -------------------------------------------------------------------------
    "termination_for_convenience": ClauseTemplate(
        id="term_convenience",
        name="Termination for Convenience",
        category="Termination",
        description="Either party can terminate with notice",
        template_text="""
TERMINATION FOR CONVENIENCE. Either party may terminate this Agreement at any 
time, for any reason or no reason, upon {NOTICE_DAYS} days' prior written 
notice to the other party.

Upon termination for convenience by {CLIENT_NAME}, {CLIENT_NAME} shall pay 
for all Services rendered through the effective date of termination.
        """.strip(),
        variables=["NOTICE_DAYS", "CLIENT_NAME"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="30-60 days notice is standard. Ensures either party can exit."
    ),

    "termination_for_cause": ClauseTemplate(
        id="term_cause",
        name="Termination for Cause",
        category="Termination",
        description="Termination upon material breach",
        template_text="""
TERMINATION FOR CAUSE. Either party may terminate this Agreement immediately 
upon written notice if:
(a) The other party materially breaches this Agreement and fails to cure such 
    breach within {CURE_PERIOD_DAYS} days after receiving written notice;
(b) The other party becomes insolvent, files for bankruptcy, or makes an 
    assignment for the benefit of creditors;
(c) The other party ceases to conduct business in the normal course.
        """.strip(),
        variables=["CURE_PERIOD_DAYS"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="30-day cure period is standard. Include insolvency provisions."
    ),

    # -------------------------------------------------------------------------
    # CONFIDENTIALITY
    # -------------------------------------------------------------------------
    "confidentiality_mutual": ClauseTemplate(
        id="conf_mutual",
        name="Mutual Confidentiality",
        category="Confidentiality",
        description="Standard mutual NDA provisions",
        template_text="""
CONFIDENTIALITY. Each party agrees to hold in confidence all Confidential 
Information disclosed by the other party and to use such information only 
for purposes of this Agreement.

"Confidential Information" means any non-public information disclosed by 
either party, whether orally or in writing, that is designated as confidential 
or that reasonably should be understood to be confidential.

Exceptions: Confidential Information does not include information that:
(a) was publicly known at the time of disclosure;
(b) becomes publicly known through no fault of the receiving party;
(c) was rightfully in the receiving party's possession prior to disclosure;
(d) is independently developed by the receiving party;
(e) is rightfully obtained from a third party without restriction.

This confidentiality obligation shall survive for {CONFIDENTIALITY_YEARS} years 
following termination of this Agreement.
        """.strip(),
        variables=["CONFIDENTIALITY_YEARS"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="3-5 years is standard. Mutual obligations are preferred."
    ),

    # -------------------------------------------------------------------------
    # DISPUTE RESOLUTION
    # -------------------------------------------------------------------------
    "dispute_arbitration": ClauseTemplate(
        id="dispute_arb",
        name="Binding Arbitration",
        category="Dispute Resolution",
        description="Disputes resolved through binding arbitration",
        template_text="""
DISPUTE RESOLUTION. Any dispute arising out of or relating to this Agreement 
shall be resolved by binding arbitration administered by {ARBITRATION_BODY} 
in accordance with its Commercial Arbitration Rules.

The arbitration shall be conducted in {ARBITRATION_LOCATION} before a single 
arbitrator. The arbitrator's decision shall be final and binding, and judgment 
on the award may be entered in any court having jurisdiction.

Each party shall bear its own costs and expenses, and the parties shall share 
equally the fees of the arbitrator.
        """.strip(),
        variables=["ARBITRATION_BODY", "ARBITRATION_LOCATION"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="AAA or JAMS are common arbitration bodies. Arbitration is often faster and cheaper than litigation."
    ),

    "dispute_litigation": ClauseTemplate(
        id="dispute_lit",
        name="Court Litigation",
        category="Dispute Resolution",
        description="Disputes resolved in court",
        template_text="""
GOVERNING LAW AND JURISDICTION. This Agreement shall be governed by and 
construed in accordance with the laws of the State of {GOVERNING_STATE}, 
without regard to its conflict of laws principles.

Any legal action or proceeding arising under this Agreement shall be brought 
exclusively in the federal or state courts located in {COURT_LOCATION}, and 
the parties hereby consent to personal jurisdiction and venue therein.
        """.strip(),
        variables=["GOVERNING_STATE", "COURT_LOCATION"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="Choose a neutral jurisdiction or one favorable to your business."
    ),

    # -------------------------------------------------------------------------
    # FORCE MAJEURE
    # -------------------------------------------------------------------------
    "force_majeure": ClauseTemplate(
        id="force_maj",
        name="Force Majeure",
        category="Force Majeure",
        description="Excuses performance during extraordinary events",
        template_text="""
FORCE MAJEURE. Neither party shall be liable for any failure or delay in 
performing its obligations under this Agreement if such failure or delay 
results from circumstances beyond the reasonable control of that party, 
including but not limited to:
(a) acts of God, natural disasters, or extreme weather events;
(b) war, terrorism, or civil unrest;
(c) pandemic, epidemic, or public health emergency;
(d) government actions, laws, or regulations;
(e) labor disputes or strikes;
(f) failure of third-party telecommunications or power supply.

The affected party shall give prompt written notice to the other party and 
shall use reasonable efforts to mitigate the effects of the force majeure event.

If a force majeure event continues for more than {FORCE_MAJEURE_DAYS} days, 
either party may terminate this Agreement upon written notice.
        """.strip(),
        variables=["FORCE_MAJEURE_DAYS"],
        risk_level=RiskLevel.LOW,
        best_practice_notes="90-180 days is typical before termination right kicks in."
    ),

    # -------------------------------------------------------------------------
    # ASSIGNMENT
    # -------------------------------------------------------------------------
    "assignment": ClauseTemplate(
        id="assignment",
        name="Assignment Clause",
        category="Assignment",
        description="Restricts assignment without consent",
        template_text="""
ASSIGNMENT. Neither party may assign or transfer this Agreement, or any rights 
or obligations hereunder, without the prior written consent of the other party, 
except that either party may assign this Agreement to an affiliate or in 
connection with a merger, acquisition, or sale of all or substantially all 
of its assets.

Any attempted assignment in violation of this section shall be void.
        """.strip(),
        variables=[],
        risk_level=RiskLevel.LOW,
        best_practice_notes="Standard clause. The M&A carve-out is important for business flexibility."
    ),
}


# ============================================================================
# CONTRACT TEMPLATES
# ============================================================================

CONTRACT_TEMPLATES: Dict[str, ContractTemplate] = {

    "service_agreement": ContractTemplate(
        id="svc_agreement",
        name="Service Agreement",
        contract_type=ContractType.SERVICE,
        description="Standard service agreement template",
        clauses=[
            CLAUSE_TEMPLATES["limitation_of_liability_standard"],
            CLAUSE_TEMPLATES["indemnification_mutual"],
            CLAUSE_TEMPLATES["termination_for_convenience"],
            CLAUSE_TEMPLATES["termination_for_cause"],
            CLAUSE_TEMPLATES["confidentiality_mutual"],
            CLAUSE_TEMPLATES["dispute_arbitration"],
            CLAUSE_TEMPLATES["force_majeure"],
            CLAUSE_TEMPLATES["assignment"],
        ],
        variables={
            "CLIENT_NAME": "",
            "PROVIDER_NAME": "",
            "NOTICE_DAYS": "30",
            "CURE_PERIOD_DAYS": "30",
            "CONFIDENTIALITY_YEARS": "5",
            "ARBITRATION_BODY": "American Arbitration Association",
            "ARBITRATION_LOCATION": "New York, NY",
            "FORCE_MAJEURE_DAYS": "90"
        },
        created_at=datetime.utcnow().isoformat()
    ),

    "nda_mutual": ContractTemplate(
        id="nda_mutual",
        name="Mutual NDA",
        contract_type=ContractType.NDA,
        description="Mutual non-disclosure agreement",
        clauses=[
            CLAUSE_TEMPLATES["confidentiality_mutual"],
            CLAUSE_TEMPLATES["dispute_litigation"],
        ],
        variables={
            "CONFIDENTIALITY_YEARS": "3",
            "GOVERNING_STATE": "Delaware",
            "COURT_LOCATION": "Wilmington, Delaware"
        },
        created_at=datetime.utcnow().isoformat()
    ),
}


# ============================================================================
# TEMPLATE LIBRARY CLASS
# ============================================================================

class TemplateLibrary:
    """
    Manages contract and clause templates.
    Provides search, retrieval, and customization.
    """

    def __init__(self):
        """Initialize template library with default templates."""
        self.clause_templates = dict(CLAUSE_TEMPLATES)
        self.contract_templates = dict(CONTRACT_TEMPLATES)

    # =========================================================================
    # CLAUSE METHODS
    # =========================================================================

    def get_clause(self, clause_id: str) -> Optional[ClauseTemplate]:
        """Get a clause template by ID."""
        return self.clause_templates.get(clause_id)

    def list_clauses(
        self,
        category: Optional[str] = None,
        risk_level: Optional[RiskLevel] = None
    ) -> List[ClauseTemplate]:
        """
        List clause templates with optional filtering.

        Args:
            category: Filter by category (e.g., "Liability", "Termination")
            risk_level: Filter by risk level

        Returns:
            List of matching clause templates
        """
        clauses = list(self.clause_templates.values())

        if category:
            clauses = [c for c in clauses if c.category.lower() == category.lower()]

        if risk_level:
            clauses = [c for c in clauses if c.risk_level == risk_level]

        return clauses

    def get_clauses_by_category(self) -> Dict[str, List[ClauseTemplate]]:
        """Get all clauses grouped by category."""
        grouped: Dict[str, List[ClauseTemplate]] = {}

        for clause in self.clause_templates.values():
            if clause.category not in grouped:
                grouped[clause.category] = []
            grouped[clause.category].append(clause)

        return grouped

    def search_clauses(self, query: str) -> List[ClauseTemplate]:
        """Search clauses by name or description."""
        query = query.lower()
        results = []

        for clause in self.clause_templates.values():
            if (query in clause.name.lower() or
                query in clause.description.lower() or
                query in clause.template_text.lower()):
                results.append(clause)

        return results

    def render_clause(
        self,
        clause_id: str,
        variables: Dict[str, str]
    ) -> Optional[str]:
        """
        Render a clause template with variables filled in.

        Args:
            clause_id: ID of the clause template
            variables: Dictionary of variable values

        Returns:
            Rendered clause text
        """
        clause = self.get_clause(clause_id)
        if not clause:
            return None

        text = clause.template_text
        for var, value in variables.items():
            text = text.replace(f"{{{var}}}", value)

        return text

    def add_clause(self, clause: ClauseTemplate):
        """Add a custom clause template."""
        self.clause_templates[clause.id] = clause

    # =========================================================================
    # CONTRACT TEMPLATE METHODS
    # =========================================================================

    def get_contract_template(self, template_id: str) -> Optional[ContractTemplate]:
        """Get a contract template by ID."""
        return self.contract_templates.get(template_id)

    def list_contract_templates(
        self,
        contract_type: Optional[ContractType] = None
    ) -> List[ContractTemplate]:
        """
        List contract templates with optional filtering.

        Args:
            contract_type: Filter by contract type

        Returns:
            List of matching contract templates
        """
        templates = list(self.contract_templates.values())

        if contract_type:
            templates = [t for t in templates if t.contract_type == contract_type]

        return templates

    def render_contract_template(
        self,
        template_id: str,
        variables: Dict[str, str]
    ) -> Optional[str]:
        """
        Render a full contract template with all clauses.

        Args:
            template_id: ID of the contract template
            variables: Dictionary of variable values

        Returns:
            Rendered contract text
        """
        template = self.get_contract_template(template_id)
        if not template:
            return None

        # Merge template default variables with provided variables
        all_vars = {**template.variables, **variables}

        # Render each clause
        rendered_clauses = []
        for i, clause in enumerate(template.clauses, 1):
            rendered = self.render_clause(clause.id, all_vars)
            if rendered:
                rendered_clauses.append(f"{i}. {clause.name.upper()}\n\n{rendered}")

        return "\n\n---\n\n".join(rendered_clauses)

    def add_contract_template(self, template: ContractTemplate):
        """Add a custom contract template."""
        self.contract_templates[template.id] = template

    # =========================================================================
    # BEST PRACTICES
    # =========================================================================

    def get_best_practices(self, category: str) -> List[Dict[str, str]]:
        """
        Get best practice notes for a category.

        Returns:
            List of best practices with clause info
        """
        practices = []

        for clause in self.clause_templates.values():
            if clause.category.lower() == category.lower() and clause.best_practice_notes:
                practices.append({
                    "clause_name": clause.name,
                    "best_practice": clause.best_practice_notes,
                    "risk_level": clause.risk_level.value
                })

        return practices

    def suggest_missing_clauses(
        self,
        contract_type: ContractType,
        existing_categories: List[str]
    ) -> List[ClauseTemplate]:
        """
        Suggest clauses that might be missing from a contract.

        Args:
            contract_type: Type of contract
            existing_categories: Categories already present

        Returns:
            List of suggested clause templates
        """
        # Essential categories by contract type
        essential = {
            ContractType.SERVICE: [
                "Liability", "Indemnification", "Termination",
                "Confidentiality", "Dispute Resolution"
            ],
            ContractType.NDA: ["Confidentiality", "Dispute Resolution"],
            ContractType.EMPLOYMENT: [
                "Termination", "Confidentiality", "Dispute Resolution"
            ],
            ContractType.SALES: [
                "Liability", "Payment", "Termination", "Dispute Resolution"
            ],
        }

        required = essential.get(contract_type, [
            "Liability", "Termination", "Dispute Resolution"
        ])

        existing_lower = [c.lower() for c in existing_categories]
        missing = [c for c in required if c.lower() not in existing_lower]

        suggestions = []
        for category in missing:
            clauses = self.list_clauses(category=category)
            if clauses:
                suggestions.append(clauses[0])  # Suggest first/default

        return suggestions

