"""
ContractIQ Comparator
Compare two contracts side-by-side.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .models import (
    ContractAnalysis,
    ContractComparison,
    ClauseDifference,
    RiskLevel
)
from .prompts import get_contract_prompt, get_system_prompt
from .risk_scorer import RiskScorer

logger = logging.getLogger(__name__)


class ContractComparator:
    """
    Compare two contracts and identify differences.
    Useful for:
    - Comparing current vs proposed terms
    - Standard template vs actual contract
    - Version comparison
    """

    def __init__(self, llm_client=None):
        """
        Initialize comparator.

        Args:
            llm_client: LLM client for analysis
        """
        self._llm_client = llm_client
        self.risk_scorer = RiskScorer()

    @property
    def llm_client(self):
        """Lazy load LLM client."""
        if self._llm_client is None:
            from ..agents.groq_client import GroqClient
            self._llm_client = GroqClient()
        return self._llm_client

    async def compare_contracts(
        self,
        contract_a_id: str,
        contract_a_text: str,
        contract_b_id: str,
        contract_b_text: str,
        comparison_type: str = "full"
    ) -> ContractComparison:
        """
        Compare two contracts.

        Args:
            contract_a_id: ID of first contract
            contract_a_text: Text of first contract
            contract_b_id: ID of second contract
            contract_b_text: Text of second contract
            comparison_type: "full", "clauses_only", or "risk_only"

        Returns:
            ContractComparison with differences and analysis
        """
        logger.info(f"Comparing contracts: {contract_a_id} vs {contract_b_id}")

        result = ContractComparison(
            contract_a_id=contract_a_id,
            contract_b_id=contract_b_id,
            compared_at=datetime.utcnow().isoformat()
        )

        # LLM-based comparison
        if comparison_type in ["full", "clauses_only"]:
            await self._llm_compare(
                result,
                contract_a_text,
                contract_b_text
            )

        # Calculate similarity
        result.similarity_score = self._calculate_similarity(
            contract_a_text,
            contract_b_text
        )

        return result

    async def compare_analyses(
        self,
        analysis_a: ContractAnalysis,
        analysis_b: ContractAnalysis
    ) -> ContractComparison:
        """
        Compare two already-analyzed contracts.

        Args:
            analysis_a: Analysis of first contract
            analysis_b: Analysis of second contract

        Returns:
            ContractComparison with differences
        """
        result = ContractComparison(
            contract_a_id=analysis_a.document_id,
            contract_b_id=analysis_b.document_id,
            compared_at=datetime.utcnow().isoformat()
        )

        # Compare key sections
        differences = []

        # Compare parties
        diff = self._compare_section(
            "Parties",
            self._parties_to_text(analysis_a.parties),
            self._parties_to_text(analysis_b.parties)
        )
        if diff:
            differences.append(diff)

        # Compare dates
        diff = self._compare_section(
            "Key Dates",
            f"Effective: {analysis_a.effective_date}, Expires: {analysis_a.expiration_date}",
            f"Effective: {analysis_b.effective_date}, Expires: {analysis_b.expiration_date}"
        )
        if diff:
            differences.append(diff)

        # Compare payment terms
        diff = self._compare_section(
            "Payment Terms",
            self._payment_to_text(analysis_a.payment_terms),
            self._payment_to_text(analysis_b.payment_terms)
        )
        if diff:
            differences.append(diff)

        # Compare termination
        diff = self._compare_section(
            "Termination",
            self._termination_to_text(analysis_a.termination_clauses),
            self._termination_to_text(analysis_b.termination_clauses)
        )
        if diff:
            differences.append(diff)

        # Compare liability
        diff = self._compare_section(
            "Liability",
            self._liability_to_text(analysis_a.liability_clauses),
            self._liability_to_text(analysis_b.liability_clauses)
        )
        if diff:
            differences.append(diff)

        result.differences = differences

        # Risk comparison
        result.contract_a_risk = analysis_a.risk_level
        result.contract_b_risk = analysis_b.risk_level
        result.risk_comparison = self._compare_risks(analysis_a, analysis_b)

        # Key differences
        result.key_differences = [
            d.analysis for d in differences
            if d.significance in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ][:5]

        # Summary
        result.summary = self._generate_summary(result)

        # Recommendations
        result.recommendations = self._generate_recommendations(result, analysis_a, analysis_b)

        return result

    async def _llm_compare(
        self,
        result: ContractComparison,
        contract_a_text: str,
        contract_b_text: str
    ):
        """Use LLM to compare contracts."""
        try:
            prompt = get_contract_prompt(
                "compare_contracts",
                contract_a_text=contract_a_text[:15000],  # Limit text
                contract_b_text=contract_b_text[:15000]
            )

            response = await self.llm_client.chat(
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            import json
            data = self._parse_json_response(response)

            if data:
                result.similarity_score = data.get("similarity_score", 0)
                result.summary = data.get("summary", "")
                result.key_differences = data.get("key_differences", [])
                result.risk_comparison = data.get("risk_comparison", "")
                result.recommendations = data.get("recommendations", [])

                # Parse differences
                for diff_data in data.get("differences", []):
                    result.differences.append(ClauseDifference(
                        clause_type=diff_data.get("clause_type", ""),
                        contract_a_text=diff_data.get("contract_a_text"),
                        contract_b_text=diff_data.get("contract_b_text"),
                        difference_type=diff_data.get("difference_type", "modified"),
                        significance=RiskLevel(diff_data.get("significance", "low")),
                        analysis=diff_data.get("analysis", "")
                    ))
        except Exception as e:
            logger.error(f"LLM comparison failed: {e}")

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from LLM response."""
        import json
        try:
            response = response.strip()
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            if response.startswith("{"):
                end = response.rfind("}") + 1
                response = response[:end]

            return json.loads(response)
        except:
            return None

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate text similarity percentage."""
        # Simple word-based Jaccard similarity
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        intersection = words_a & words_b
        union = words_a | words_b

        return round((len(intersection) / len(union)) * 100, 1)

    def _compare_section(
        self,
        section_name: str,
        text_a: str,
        text_b: str
    ) -> Optional[ClauseDifference]:
        """Compare a section between two contracts."""
        if text_a == text_b:
            return None

        if not text_a and text_b:
            diff_type = "added"
            significance = RiskLevel.MEDIUM
        elif text_a and not text_b:
            diff_type = "removed"
            significance = RiskLevel.HIGH
        else:
            diff_type = "modified"
            significance = RiskLevel.LOW

        return ClauseDifference(
            clause_type=section_name,
            contract_a_text=text_a or None,
            contract_b_text=text_b or None,
            difference_type=diff_type,
            significance=significance,
            analysis=f"{section_name} differs between contracts"
        )

    def _parties_to_text(self, parties: list) -> str:
        """Convert parties to text for comparison."""
        if not parties:
            return ""
        return "; ".join([f"{p.name} ({p.role})" for p in parties])

    def _payment_to_text(self, payment_terms: list) -> str:
        """Convert payment terms to text for comparison."""
        if not payment_terms:
            return ""
        return "; ".join([
            f"{p.amount} {p.currency} {p.frequency or ''}"
            for p in payment_terms
        ])

    def _termination_to_text(self, termination: list) -> str:
        """Convert termination clauses to text."""
        if not termination:
            return ""
        return "; ".join([
            f"{t.termination_type}: {t.notice_period or 'No notice'}"
            for t in termination
        ])

    def _liability_to_text(self, liability: list) -> str:
        """Convert liability clauses to text."""
        if not liability:
            return ""
        return "; ".join([
            f"{l.liability_type}: Cap {l.cap_amount or 'None'}"
            for l in liability
        ])

    def _compare_risks(
        self,
        analysis_a: ContractAnalysis,
        analysis_b: ContractAnalysis
    ) -> str:
        """Generate risk comparison text."""
        score_a = analysis_a.risk_score
        score_b = analysis_b.risk_score

        if score_a == score_b:
            return f"Both contracts have similar risk levels ({analysis_a.risk_level.value})"
        elif score_a < score_b:
            diff = score_b - score_a
            return (
                f"Contract A is less risky (score: {score_a}) than Contract B (score: {score_b}). "
                f"Difference: {diff} points"
            )
        else:
            diff = score_a - score_b
            return (
                f"Contract B is less risky (score: {score_b}) than Contract A (score: {score_a}). "
                f"Difference: {diff} points"
            )

    def _generate_summary(self, comparison: ContractComparison) -> str:
        """Generate comparison summary."""
        diff_count = len(comparison.differences)
        high_risk_diffs = sum(
            1 for d in comparison.differences
            if d.significance in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )

        summary_parts = [
            f"Found {diff_count} difference(s) between contracts",
            f"Similarity: {comparison.similarity_score:.1f}%"
        ]

        if high_risk_diffs:
            summary_parts.append(f"{high_risk_diffs} significant difference(s) requiring attention")

        return ". ".join(summary_parts) + "."

    def _generate_recommendations(
        self,
        comparison: ContractComparison,
        analysis_a: ContractAnalysis,
        analysis_b: ContractAnalysis
    ) -> List[str]:
        """Generate recommendations based on comparison."""
        recommendations = []

        # Risk-based recommendations
        if analysis_a.risk_score > analysis_b.risk_score + 10:
            recommendations.append(
                f"Contract A has significantly higher risk. Consider using terms from Contract B."
            )
        elif analysis_b.risk_score > analysis_a.risk_score + 10:
            recommendations.append(
                f"Contract B has significantly higher risk. Consider using terms from Contract A."
            )

        # Difference-based recommendations
        for diff in comparison.differences:
            if diff.significance == RiskLevel.CRITICAL:
                recommendations.append(
                    f"[CRITICAL] Review {diff.clause_type}: {diff.analysis}"
                )
            elif diff.significance == RiskLevel.HIGH:
                recommendations.append(
                    f"[HIGH] Attention needed for {diff.clause_type}"
                )

        return recommendations[:10]

    def get_side_by_side_view(
        self,
        comparison: ContractComparison
    ) -> List[Dict[str, str]]:
        """
        Get differences in side-by-side format for UI display.

        Returns:
            List of differences with A and B text side by side
        """
        return [
            {
                "clause": diff.clause_type,
                "contract_a": diff.contract_a_text or "(Not present)",
                "contract_b": diff.contract_b_text or "(Not present)",
                "change_type": diff.difference_type,
                "significance": diff.significance.value,
                "analysis": diff.analysis
            }
            for diff in comparison.differences
        ]

