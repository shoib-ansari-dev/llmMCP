"""
ContractIQ Prompts
Specialized prompts for contract analysis.
"""

from typing import Dict, Optional


# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

CONTRACT_SYSTEM_PROMPT = """You are ContractIQ, an expert legal contract analyzer. 
You specialize in extracting key information from legal contracts and identifying risks.

Your analysis should be:
- Precise and legally accurate
- Structured and easy to understand
- Focused on actionable insights
- Highlighting potential risks and red flags

Always cite the specific clause or section when referencing contract terms.
Use clear, professional language suitable for legal and business professionals.
"""


# ============================================================================
# EXTRACTION PROMPTS
# ============================================================================

CONTRACT_PROMPTS: Dict[str, str] = {

    # -------------------------------------------------------------------------
    # PARTIES EXTRACTION
    # -------------------------------------------------------------------------
    "extract_parties": """Analyze this contract and extract ALL parties involved.

For each party, identify:
1. Full legal name
2. Role in the contract (e.g., Buyer, Seller, Licensor, Employee, Contractor)
3. Address (if mentioned)
4. Contact information (if mentioned)
5. Entity type (Corporation, LLC, Individual, Partnership, etc.)

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "parties": [
        {
            "name": "Party legal name",
            "role": "Role in contract",
            "address": "Address or null",
            "contact": "Contact info or null",
            "entity_type": "Corporation/LLC/Individual/etc or null"
        }
    ]
}""",

    # -------------------------------------------------------------------------
    # KEY DATES EXTRACTION
    # -------------------------------------------------------------------------
    "extract_dates": """Extract ALL important dates and deadlines from this contract.

For each date, identify:
1. Type of date (Effective Date, Expiration, Renewal Deadline, Payment Due, Notice Period, etc.)
2. The actual date (in YYYY-MM-DD format if possible)
3. Original text describing the date
4. Whether it's recurring
5. How many days in advance a reminder should be sent

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "effective_date": "YYYY-MM-DD or null",
    "expiration_date": "YYYY-MM-DD or null",
    "key_dates": [
        {
            "date_type": "Type of date",
            "date_value": "YYYY-MM-DD or null",
            "date_text": "Original text from contract",
            "is_recurring": true/false,
            "reminder_days": 30
        }
    ]
}""",

    # -------------------------------------------------------------------------
    # PAYMENT TERMS EXTRACTION
    # -------------------------------------------------------------------------
    "extract_payment": """Extract ALL payment terms and financial obligations from this contract.

For each payment term, identify:
1. Amount (numeric value)
2. Currency
3. Payment frequency (One-time, Monthly, Annual, etc.)
4. Due date or payment schedule
5. Payment method (if specified)
6. Late fees or penalties
7. Net payment terms (Net 30, Net 60, etc.)

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "payment_terms": [
        {
            "amount": 10000.00,
            "currency": "USD",
            "frequency": "Monthly",
            "due_date": "Description of when payment is due",
            "payment_method": "Wire transfer or null",
            "late_fee": "Description of late fee or null",
            "late_fee_percentage": 1.5,
            "net_days": 30,
            "description": "Brief description of what this payment is for"
        }
    ],
    "total_value": 120000.00
}""",

    # -------------------------------------------------------------------------
    # TERMINATION CLAUSES
    # -------------------------------------------------------------------------
    "extract_termination": """Extract ALL termination clauses and conditions from this contract.

For each termination clause, identify:
1. Type (for_cause, for_convenience, mutual, automatic)
2. Notice period required
3. Conditions that trigger termination
4. Penalties for early termination
5. Survival clauses (what survives after termination)

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "termination_clauses": [
        {
            "termination_type": "for_cause/for_convenience/mutual/automatic",
            "notice_period": "30 days written notice",
            "notice_period_days": 30,
            "conditions": ["List of conditions that allow termination"],
            "penalties": "Description of penalties or null",
            "survival_clauses": ["Confidentiality", "Indemnification"],
            "original_text": "Exact quote from contract"
        }
    ]
}""",

    # -------------------------------------------------------------------------
    # LIABILITY & INDEMNIFICATION
    # -------------------------------------------------------------------------
    "extract_liability": """Extract ALL liability limitations and indemnification clauses from this contract.

For each clause, identify:
1. Type (limitation_of_liability, indemnification, warranty, disclaimer)
2. Liability cap (monetary limit)
3. Excluded damages (consequential, punitive, etc.)
4. Who indemnifies whom
5. Scope of indemnification

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "liability_clauses": [
        {
            "liability_type": "limitation/indemnification/warranty/disclaimer",
            "cap_amount": 100000.00,
            "cap_description": "e.g., 'limited to fees paid in last 12 months'",
            "excluded_damages": ["consequential", "punitive", "lost profits"],
            "indemnifying_party": "Party providing indemnification or null",
            "indemnified_party": "Party receiving indemnification or null",
            "scope": "Description of what's covered",
            "original_text": "Exact quote from contract"
        }
    ]
}""",

    # -------------------------------------------------------------------------
    # RISK FLAGS & RED FLAGS
    # -------------------------------------------------------------------------
    "identify_risks": """Analyze this contract and identify ALL potential risks, red flags, and problematic clauses.

Look for:
1. Unusual or one-sided terms
2. Missing standard protections
3. Unlimited liability exposure
4. Automatic renewal traps
5. Non-compete restrictions
6. Unfavorable dispute resolution terms
7. Broad indemnification requirements
8. IP assignment issues
9. Vague or ambiguous language
10. Compliance concerns

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "risk_flags": [
        {
            "risk_type": "Category of risk",
            "severity": "low/medium/high/critical",
            "clause_reference": "Section or clause number",
            "description": "Clear explanation of the risk",
            "recommendation": "Suggested action or negotiation point",
            "original_text": "Relevant quote from contract"
        }
    ],
    "missing_clauses": [
        "List of standard clauses that are missing"
    ]
}""",

    # -------------------------------------------------------------------------
    # CONFIDENTIALITY / NDA
    # -------------------------------------------------------------------------
    "extract_confidentiality": """Extract confidentiality and NDA terms from this contract.

Identify:
1. Duration of confidentiality obligation
2. Scope of confidential information
3. Exceptions to confidentiality
4. Return/destruction of materials requirements

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "confidentiality": {
        "duration": "5 years from disclosure",
        "duration_years": 5,
        "scope": "Description of what's covered",
        "exceptions": ["Publicly available", "Prior knowledge", "Court order"],
        "return_of_materials": true/false,
        "original_text": "Key confidentiality language"
    }
}""",

    # -------------------------------------------------------------------------
    # INTELLECTUAL PROPERTY
    # -------------------------------------------------------------------------
    "extract_ip": """Extract intellectual property terms from this contract.

Identify:
1. IP ownership (who owns what)
2. IP licensing terms
3. Work-for-hire provisions
4. Assignment clauses
5. Restrictions on IP use

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "intellectual_property": [
        {
            "ip_type": "ownership/license/assignment/work_for_hire",
            "owner": "Party who owns/licenses the IP",
            "scope": "Description of IP covered",
            "restrictions": ["List of restrictions"],
            "original_text": "Relevant IP language"
        }
    ]
}""",

    # -------------------------------------------------------------------------
    # DISPUTE RESOLUTION
    # -------------------------------------------------------------------------
    "extract_dispute": """Extract dispute resolution terms from this contract.

Identify:
1. Resolution method (litigation, arbitration, mediation)
2. Venue/jurisdiction
3. Governing law
4. Arbitration rules (if applicable)

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "dispute_resolution": {
        "method": "litigation/arbitration/mediation/negotiation",
        "venue": "City, State or Country",
        "governing_law": "State/Country law that governs",
        "arbitration_rules": "AAA/JAMS/ICC rules or null",
        "original_text": "Dispute resolution language"
    }
}""",

    # -------------------------------------------------------------------------
    # FULL ANALYSIS
    # -------------------------------------------------------------------------
    "full_analysis": """Perform a comprehensive analysis of this contract.

Provide:
1. Contract type classification
2. Executive summary (2-3 sentences)
3. Key points (bullet points of most important terms)
4. Overall risk assessment

Contract text:
{contract_text}

Respond in this exact JSON format:
{
    "contract_type": "employment/nda/service/sales/lease/license/partnership/vendor/consulting/other",
    "contract_title": "Title or description of contract",
    "summary": "2-3 sentence executive summary",
    "key_points": [
        "Most important term 1",
        "Most important term 2",
        "Most important term 3"
    ],
    "risk_level": "low/medium/high/critical",
    "risk_score": 35,
    "recommendations": [
        "Action item or suggestion 1",
        "Action item or suggestion 2"
    ]
}""",

    # -------------------------------------------------------------------------
    # CONTRACT COMPARISON
    # -------------------------------------------------------------------------
    "compare_contracts": """Compare these two contracts and identify key differences.

Contract A:
{contract_a_text}

Contract B:
{contract_b_text}

For each significant difference, analyze:
1. What clause or term differs
2. How they differ
3. Which is more favorable and to whom
4. Risk implications

Respond in this exact JSON format:
{
    "similarity_score": 75.5,
    "summary": "Overall comparison summary",
    "differences": [
        {
            "clause_type": "Type of clause",
            "contract_a_text": "Text from Contract A",
            "contract_b_text": "Text from Contract B",
            "difference_type": "added/removed/modified",
            "significance": "low/medium/high/critical",
            "analysis": "Explanation of difference and implications"
        }
    ],
    "key_differences": [
        "Most important difference 1",
        "Most important difference 2"
    ],
    "risk_comparison": "Which contract is riskier and why",
    "recommendations": [
        "Recommendation based on comparison"
    ]
}"""
}


def get_contract_prompt(
    prompt_type: str,
    contract_text: str = "",
    contract_a_text: str = "",
    contract_b_text: str = ""
) -> str:
    """
    Get a formatted contract analysis prompt.

    Args:
        prompt_type: Type of prompt (e.g., "extract_parties", "identify_risks")
        contract_text: The contract text to analyze
        contract_a_text: First contract for comparison
        contract_b_text: Second contract for comparison

    Returns:
        Formatted prompt string
    """
    if prompt_type not in CONTRACT_PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    prompt = CONTRACT_PROMPTS[prompt_type]

    return prompt.format(
        contract_text=contract_text,
        contract_a_text=contract_a_text,
        contract_b_text=contract_b_text
    )


def get_system_prompt() -> str:
    """Get the system prompt for contract analysis."""
    return CONTRACT_SYSTEM_PROMPT

