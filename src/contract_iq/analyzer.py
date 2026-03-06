"""
ContractIQ Analyzer
Main contract analysis engine.
"""

import json
import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import (
    ContractAnalysis,
    ContractParty,
    KeyDate,
    PaymentTerms,
    TerminationClause,
    LiabilityClause,
    RiskFlag,
    RiskLevel,
    ContractType,
    ConfidentialityClause,
    IntellectualPropertyClause,
    DisputeResolution
)
from .prompts import get_contract_prompt, get_system_prompt, CONTRACT_PROMPTS

logger = logging.getLogger(__name__)


class ContractAnalyzer:
    """
    Contract analysis engine using LLM.
    Extracts key information and identifies risks in legal contracts.
    """

    def __init__(self, llm_client=None):
        """
        Initialize the contract analyzer.

        Args:
            llm_client: LLM client for analysis (uses default if not provided)
        """
        self._llm_client = llm_client

    @property
    def llm_client(self):
        """Lazy load LLM client."""
        if self._llm_client is None:
            from ..agents.local_llm_client import LocalLLMClient
            self._llm_client = LocalLLMClient()
        return self._llm_client

    async def analyze_contract(
        self,
        document_id: str,
        contract_text: str,
        analysis_depth: str = "full",
        focus_areas: Optional[List[str]] = None
    ) -> ContractAnalysis:
        """
        Perform comprehensive contract analysis.

        Args:
            document_id: Unique identifier for the document
            contract_text: The contract text to analyze
            analysis_depth: "quick", "standard", or "full"
            focus_areas: Specific areas to focus on

        Returns:
            ContractAnalysis with all extracted information
        """
        logger.info(f"Analyzing contract {document_id}, depth: {analysis_depth}")

        # Initialize result
        result = ContractAnalysis(
            document_id=document_id,
            analyzed_at=datetime.utcnow().isoformat()
        )

        # Determine what to analyze based on depth
        if analysis_depth == "quick":
            analyses = ["full_analysis"]
        elif analysis_depth == "standard":
            analyses = [
                "full_analysis",
                "extract_parties",
                "extract_dates",
                "extract_payment",
                "identify_risks"
            ]
        else:  # full
            analyses = [
                "full_analysis",
                "extract_parties",
                "extract_dates",
                "extract_payment",
                "extract_termination",
                "extract_liability",
                "extract_confidentiality",
                "extract_ip",
                "extract_dispute",
                "identify_risks"
            ]

        # Filter by focus areas if specified
        if focus_areas:
            area_mapping = {
                "parties": "extract_parties",
                "dates": "extract_dates",
                "payment": "extract_payment",
                "termination": "extract_termination",
                "liability": "extract_liability",
                "confidentiality": "extract_confidentiality",
                "ip": "extract_ip",
                "dispute": "extract_dispute",
                "risk": "identify_risks"
            }
            analyses = ["full_analysis"] + [
                area_mapping[area] for area in focus_areas
                if area in area_mapping
            ]

        # Run analyses
        llm_success = False
        for analysis_type in analyses:
            try:
                success = await self._run_analysis(result, analysis_type, contract_text)
                if success:
                    llm_success = True
            except Exception as e:
                logger.error(f"Error in {analysis_type}: {e}")

        # If LLM failed to extract anything useful, use regex fallback
        if not llm_success or (not result.summary and not result.parties and not result.key_points):
            logger.warning("LLM extraction failed, using regex fallback")
            self._extract_with_regex(result, contract_text)

        return result

    async def _run_analysis(
        self,
        result: ContractAnalysis,
        analysis_type: str,
        contract_text: str
    ) -> bool:
        """Run a specific analysis and update the result. Returns True if successful."""
        prompt = get_contract_prompt(analysis_type, contract_text=contract_text)

        response = await self._call_llm(prompt)
        if not response:
            return False

        # Parse response based on analysis type
        try:
            data = self._parse_json_response(response)
            if not data:
                return False

            # Update result based on analysis type
            if analysis_type == "full_analysis":
                self._update_from_full_analysis(result, data)
            elif analysis_type == "extract_parties":
                self._update_parties(result, data)
            elif analysis_type == "extract_dates":
                self._update_dates(result, data)
            elif analysis_type == "extract_payment":
                self._update_payment(result, data)
            elif analysis_type == "extract_termination":
                self._update_termination(result, data)
            elif analysis_type == "extract_liability":
                self._update_liability(result, data)
            elif analysis_type == "extract_confidentiality":
                self._update_confidentiality(result, data)
            elif analysis_type == "extract_ip":
                self._update_ip(result, data)
            elif analysis_type == "extract_dispute":
                self._update_dispute(result, data)
            elif analysis_type == "identify_risks":
                self._update_risks(result, data)

            return True

        except Exception as e:
            logger.error(f"Error parsing {analysis_type} response: {e}")
            return False

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call the LLM with the given prompt."""
        try:
            system_prompt = get_system_prompt()
            response = await self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from LLM response."""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Find JSON block
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            # Try to find JSON object
            if response.startswith("{"):
                end = response.rfind("}") + 1
                response = response[:end]

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None

    # =========================================================================
    # FALLBACK EXTRACTION (when LLM fails)
    # =========================================================================

    def _extract_with_regex(self, result: ContractAnalysis, contract_text: str):
        """Extract key information using regex patterns when LLM fails."""
        logger.info("Using fallback regex extraction")

        text_lower = contract_text.lower()
        text = contract_text

        # Extract contract type
        if "employment" in text_lower or "employee" in text_lower:
            result.contract_type = ContractType.EMPLOYMENT
        elif "non-disclosure" in text_lower or "nda" in text_lower or "confidential" in text_lower:
            result.contract_type = ContractType.NDA
        elif "service" in text_lower or "services agreement" in text_lower:
            result.contract_type = ContractType.SERVICE
        elif "lease" in text_lower or "rental" in text_lower:
            result.contract_type = ContractType.LEASE
        elif "license" in text_lower or "licensing" in text_lower:
            result.contract_type = ContractType.LICENSE
        elif "sale" in text_lower or "purchase" in text_lower:
            result.contract_type = ContractType.SALES
        elif "consulting" in text_lower or "consultant" in text_lower:
            result.contract_type = ContractType.CONSULTING
        elif "vendor" in text_lower or "supplier" in text_lower:
            result.contract_type = ContractType.VENDOR

        # Extract parties using common patterns
        party_patterns = [
            r'(?:between|by and between)\s+([A-Z][A-Za-z\s,\.]+?)(?:\s+\(|,?\s+and\s+)',
            r'(?:Party|PARTY)\s*(?:A|1|ONE)[:.]?\s*([A-Z][A-Za-z\s,\.]+?)(?:\n|,)',
            r'(?:Employer|EMPLOYER|Company|COMPANY)[:.]?\s*([A-Z][A-Za-z\s,\.]+?)(?:\n|,)',
            r'(?:Client|CLIENT)[:.]?\s*([A-Z][A-Za-z\s,\.]+?)(?:\n|,)',
        ]

        for pattern in party_patterns:
            matches = re.findall(pattern, text)
            for match in matches[:2]:  # Limit to 2 parties
                name = match.strip().rstrip(',.')
                if len(name) > 3 and len(name) < 100:
                    result.parties.append(ContractParty(
                        name=name,
                        role="Party"
                    ))

        # Extract dates
        date_patterns = [
            r'(?:effective\s+date|dated|as\s+of)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:effective\s+date|dated|as\s+of)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\w+\s+\d{1,2},?\s+\d{4})',
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:1]:  # Just get first date as effective
                result.effective_date = match.strip()
                break
            if result.effective_date:
                break

        # Extract payment amounts
        money_pattern = r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:per\s+(\w+))?'
        money_matches = re.findall(money_pattern, text)
        for amount, frequency in money_matches[:3]:
            try:
                amount_float = float(amount.replace(',', ''))
                result.payment_terms.append(PaymentTerms(
                    amount=amount_float,
                    currency="USD",
                    frequency=frequency if frequency else "One-time",
                    description=f"${amount}"
                ))
            except ValueError:
                pass

        # Generate summary from first paragraph
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
        if paragraphs:
            result.summary = paragraphs[0][:500] + "..." if len(paragraphs[0]) > 500 else paragraphs[0]

        # Extract key points (sentences with important keywords)
        important_keywords = ['shall', 'must', 'agree', 'obligation', 'responsible', 'warranty', 'termination']
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30 and len(sentence) < 200:
                if any(kw in sentence.lower() for kw in important_keywords):
                    result.key_points.append(sentence)
                    if len(result.key_points) >= 5:
                        break

        # Check for termination clauses
        if 'terminat' in text_lower:
            term_pattern = r'(?:termination|terminate)[^.]*(?:notice|days|written)[^.]*\.'
            term_matches = re.findall(term_pattern, text, re.IGNORECASE)
            for match in term_matches[:2]:
                result.termination_clauses.append(TerminationClause(
                    termination_type="for_convenience",
                    original_text=match.strip()
                ))

        # Check for confidentiality
        if 'confidential' in text_lower:
            conf_pattern = r'confidential[^.]*\.'
            conf_matches = re.findall(conf_pattern, text, re.IGNORECASE)
            if conf_matches:
                result.confidentiality = ConfidentialityClause(
                    scope="Standard confidentiality provisions",
                    original_text=conf_matches[0][:300]
                )

        # Add basic risk flags
        risk_keywords = {
            'unlimited liability': ('high', 'Unlimited liability clause detected'),
            'indemnify and hold harmless': ('medium', 'Broad indemnification clause'),
            'automatic renewal': ('medium', 'Auto-renewal provision'),
            'non-compete': ('medium', 'Non-compete clause'),
            'exclusive': ('low', 'Exclusivity provision'),
        }

        for keyword, (severity, description) in risk_keywords.items():
            if keyword in text_lower:
                result.risk_flags.append(RiskFlag(
                    risk_type="contract_term",
                    severity=RiskLevel(severity),
                    description=description
                ))

        logger.info(f"Fallback extraction complete: {len(result.parties)} parties, {len(result.key_points)} key points")

    # =========================================================================
    # UPDATE METHODS
    # =========================================================================

    def _update_from_full_analysis(self, result: ContractAnalysis, data: Dict):
        """Update result from full analysis response."""
        if "contract_type" in data:
            try:
                result.contract_type = ContractType(data["contract_type"])
            except ValueError:
                result.contract_type = ContractType.OTHER

        result.contract_title = data.get("contract_title")
        result.summary = data.get("summary", "")
        result.key_points = data.get("key_points", [])

        if "risk_level" in data:
            try:
                result.risk_level = RiskLevel(data["risk_level"])
            except ValueError:
                pass

        result.risk_score = data.get("risk_score", 0)
        result.recommendations = data.get("recommendations", [])

    def _update_parties(self, result: ContractAnalysis, data: Dict):
        """Update parties from extraction response."""
        parties = data.get("parties", [])
        result.parties = [
            ContractParty(
                name=p.get("name", "Unknown"),
                role=p.get("role", "Unknown"),
                address=p.get("address"),
                contact=p.get("contact"),
                entity_type=p.get("entity_type")
            )
            for p in parties
        ]

    def _update_dates(self, result: ContractAnalysis, data: Dict):
        """Update dates from extraction response."""
        result.effective_date = data.get("effective_date")
        result.expiration_date = data.get("expiration_date")

        key_dates = data.get("key_dates", [])
        result.key_dates = [
            KeyDate(
                date_type=d.get("date_type", "Unknown"),
                date_value=d.get("date_value"),
                date_text=d.get("date_text", ""),
                is_recurring=d.get("is_recurring", False),
                reminder_days=d.get("reminder_days")
            )
            for d in key_dates
        ]

    def _update_payment(self, result: ContractAnalysis, data: Dict):
        """Update payment terms from extraction response."""
        payment_terms = data.get("payment_terms", [])
        result.payment_terms = [
            PaymentTerms(
                amount=p.get("amount"),
                currency=p.get("currency", "USD"),
                frequency=p.get("frequency"),
                due_date=p.get("due_date"),
                payment_method=p.get("payment_method"),
                late_fee=p.get("late_fee"),
                late_fee_percentage=p.get("late_fee_percentage"),
                net_days=p.get("net_days"),
                description=p.get("description", "")
            )
            for p in payment_terms
        ]
        result.total_value = data.get("total_value")

    def _update_termination(self, result: ContractAnalysis, data: Dict):
        """Update termination clauses from extraction response."""
        termination = data.get("termination_clauses", [])
        result.termination_clauses = [
            TerminationClause(
                termination_type=t.get("termination_type", "unknown"),
                notice_period=t.get("notice_period"),
                notice_period_days=t.get("notice_period_days"),
                conditions=t.get("conditions", []),
                penalties=t.get("penalties"),
                survival_clauses=t.get("survival_clauses", []),
                original_text=t.get("original_text", "")
            )
            for t in termination
        ]

    def _update_liability(self, result: ContractAnalysis, data: Dict):
        """Update liability clauses from extraction response."""
        liability = data.get("liability_clauses", [])
        result.liability_clauses = [
            LiabilityClause(
                liability_type=l.get("liability_type", "unknown"),
                cap_amount=l.get("cap_amount"),
                cap_description=l.get("cap_description"),
                excluded_damages=l.get("excluded_damages", []),
                indemnifying_party=l.get("indemnifying_party"),
                indemnified_party=l.get("indemnified_party"),
                scope=l.get("scope"),
                original_text=l.get("original_text", "")
            )
            for l in liability
        ]

    def _update_confidentiality(self, result: ContractAnalysis, data: Dict):
        """Update confidentiality from extraction response."""
        conf = data.get("confidentiality")
        if conf:
            result.confidentiality = ConfidentialityClause(
                duration=conf.get("duration"),
                duration_years=conf.get("duration_years"),
                scope=conf.get("scope", ""),
                exceptions=conf.get("exceptions", []),
                return_of_materials=conf.get("return_of_materials", False),
                original_text=conf.get("original_text", "")
            )

    def _update_ip(self, result: ContractAnalysis, data: Dict):
        """Update intellectual property from extraction response."""
        ip_list = data.get("intellectual_property", [])
        result.intellectual_property = [
            IntellectualPropertyClause(
                ip_type=ip.get("ip_type", "unknown"),
                owner=ip.get("owner"),
                scope=ip.get("scope", ""),
                restrictions=ip.get("restrictions", []),
                original_text=ip.get("original_text", "")
            )
            for ip in ip_list
        ]

    def _update_dispute(self, result: ContractAnalysis, data: Dict):
        """Update dispute resolution from extraction response."""
        dispute = data.get("dispute_resolution")
        if dispute:
            result.dispute_resolution = DisputeResolution(
                method=dispute.get("method", "unknown"),
                venue=dispute.get("venue"),
                governing_law=dispute.get("governing_law"),
                arbitration_rules=dispute.get("arbitration_rules"),
                original_text=dispute.get("original_text", "")
            )

    def _update_risks(self, result: ContractAnalysis, data: Dict):
        """Update risk flags from extraction response."""
        risks = data.get("risk_flags", [])
        result.risk_flags = [
            RiskFlag(
                risk_type=r.get("risk_type", "unknown"),
                severity=RiskLevel(r.get("severity", "low")),
                clause_reference=r.get("clause_reference"),
                description=r.get("description", ""),
                recommendation=r.get("recommendation"),
                original_text=r.get("original_text")
            )
            for r in risks
        ]
        result.missing_clauses = data.get("missing_clauses", [])

    # =========================================================================
    # INDIVIDUAL EXTRACTION METHODS
    # =========================================================================

    async def extract_parties(self, contract_text: str) -> List[ContractParty]:
        """Extract only parties from a contract."""
        prompt = get_contract_prompt("extract_parties", contract_text=contract_text)
        response = await self._call_llm(prompt)
        if not response:
            return []

        data = self._parse_json_response(response)
        if not data:
            return []

        return [
            ContractParty(
                name=p.get("name", "Unknown"),
                role=p.get("role", "Unknown"),
                address=p.get("address"),
                contact=p.get("contact"),
                entity_type=p.get("entity_type")
            )
            for p in data.get("parties", [])
        ]

    async def extract_key_dates(self, contract_text: str) -> List[KeyDate]:
        """Extract only key dates from a contract."""
        prompt = get_contract_prompt("extract_dates", contract_text=contract_text)
        response = await self._call_llm(prompt)
        if not response:
            return []

        data = self._parse_json_response(response)
        if not data:
            return []

        return [
            KeyDate(
                date_type=d.get("date_type", "Unknown"),
                date_value=d.get("date_value"),
                date_text=d.get("date_text", ""),
                is_recurring=d.get("is_recurring", False),
                reminder_days=d.get("reminder_days")
            )
            for d in data.get("key_dates", [])
        ]

    async def identify_risks(self, contract_text: str) -> List[RiskFlag]:
        """Identify only risks in a contract."""
        prompt = get_contract_prompt("identify_risks", contract_text=contract_text)
        response = await self._call_llm(prompt)
        if not response:
            return []

        data = self._parse_json_response(response)
        if not data:
            return []

        return [
            RiskFlag(
                risk_type=r.get("risk_type", "unknown"),
                severity=RiskLevel(r.get("severity", "low")),
                clause_reference=r.get("clause_reference"),
                description=r.get("description", ""),
                recommendation=r.get("recommendation"),
                original_text=r.get("original_text")
            )
            for r in data.get("risk_flags", [])
        ]

