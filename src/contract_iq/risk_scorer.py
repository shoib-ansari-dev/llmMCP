"""
ContractIQ Risk Scorer
Analyzes contract risk level and provides scoring.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .models import (
    ContractAnalysis,
    RiskFlag,
    RiskLevel,
    TerminationClause,
    LiabilityClause
)

logger = logging.getLogger(__name__)


@dataclass
class RiskWeight:
    """Weight configuration for risk scoring."""
    category: str
    weight: float
    description: str


# Risk scoring weights
RISK_WEIGHTS: Dict[str, float] = {
    # High impact areas
    "unlimited_liability": 15,
    "no_liability_cap": 12,
    "broad_indemnification": 10,
    "auto_renewal_trap": 8,
    "one_sided_termination": 8,
    "ip_assignment": 8,

    # Medium impact areas
    "no_termination_for_convenience": 6,
    "short_notice_period": 5,
    "unfavorable_dispute_resolution": 5,
    "non_compete_restrictions": 5,
    "exclusivity_clause": 5,

    # Lower impact areas
    "vague_language": 3,
    "missing_clause": 3,
    "compliance_concern": 4,
    "unusual_terms": 3,
}

# Severity multipliers
SEVERITY_MULTIPLIERS: Dict[RiskLevel, float] = {
    RiskLevel.LOW: 1.0,
    RiskLevel.MEDIUM: 1.5,
    RiskLevel.HIGH: 2.0,
    RiskLevel.CRITICAL: 3.0,
}

# Missing clause penalties
MISSING_CLAUSE_PENALTIES: Dict[str, int] = {
    "limitation_of_liability": 10,
    "indemnification": 8,
    "termination": 7,
    "confidentiality": 6,
    "dispute_resolution": 5,
    "force_majeure": 4,
    "notice_provisions": 3,
    "assignment_clause": 3,
    "entire_agreement": 2,
    "severability": 2,
}


class RiskScorer:
    """
    Scores contract risk level based on multiple factors.

    Risk Score: 0-100
    - 0-25: Low Risk (Green)
    - 26-50: Medium Risk (Yellow)
    - 51-75: High Risk (Orange)
    - 76-100: Critical Risk (Red)
    """

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialize risk scorer.

        Args:
            custom_weights: Custom risk weights to override defaults
        """
        self.weights = {**RISK_WEIGHTS}
        if custom_weights:
            self.weights.update(custom_weights)

    def calculate_risk_score(self, analysis: ContractAnalysis) -> Tuple[int, RiskLevel]:
        """
        Calculate overall risk score for a contract.

        Args:
            analysis: ContractAnalysis object

        Returns:
            Tuple of (risk_score, risk_level)
        """
        total_score = 0
        max_possible = 100

        # 1. Score from identified risk flags
        risk_flag_score = self._score_risk_flags(analysis.risk_flags)

        # 2. Score from missing clauses
        missing_clause_score = self._score_missing_clauses(analysis.missing_clauses)

        # 3. Score from liability analysis
        liability_score = self._score_liability(analysis.liability_clauses)

        # 4. Score from termination analysis
        termination_score = self._score_termination(analysis.termination_clauses)

        # 5. Score from structural issues
        structural_score = self._score_structural(analysis)

        # Combine scores (weighted)
        total_score = (
            risk_flag_score * 0.35 +
            missing_clause_score * 0.20 +
            liability_score * 0.20 +
            termination_score * 0.15 +
            structural_score * 0.10
        )

        # Normalize to 0-100
        risk_score = min(100, max(0, int(total_score)))

        # Determine risk level
        risk_level = self._score_to_level(risk_score)

        logger.info(
            f"Risk score calculated: {risk_score} ({risk_level.value}) - "
            f"Flags: {risk_flag_score:.1f}, Missing: {missing_clause_score:.1f}, "
            f"Liability: {liability_score:.1f}, Termination: {termination_score:.1f}"
        )

        return risk_score, risk_level

    def _score_risk_flags(self, risk_flags: List[RiskFlag]) -> float:
        """Score based on identified risk flags."""
        if not risk_flags:
            return 0

        score = 0
        for flag in risk_flags:
            # Get base weight for risk type
            base_weight = self.weights.get(
                flag.risk_type.lower().replace(" ", "_"),
                5  # Default weight
            )

            # Apply severity multiplier
            multiplier = SEVERITY_MULTIPLIERS.get(flag.severity, 1.0)

            score += base_weight * multiplier

        # Cap at 100
        return min(100, score)

    def _score_missing_clauses(self, missing_clauses: List[str]) -> float:
        """Score based on missing standard clauses."""
        if not missing_clauses:
            return 0

        score = 0
        for clause in missing_clauses:
            clause_key = clause.lower().replace(" ", "_")
            score += MISSING_CLAUSE_PENALTIES.get(clause_key, 3)

        return min(100, score)

    def _score_liability(self, liability_clauses: List[LiabilityClause]) -> float:
        """Score based on liability analysis."""
        if not liability_clauses:
            # No liability clauses is risky
            return 50

        score = 0

        for clause in liability_clauses:
            # Check for unlimited liability
            if clause.cap_amount is None and clause.cap_description is None:
                if clause.liability_type == "limitation":
                    score += 20  # No cap on limitation clause

            # Check for broad indemnification
            if clause.liability_type == "indemnification":
                if not clause.excluded_damages:
                    score += 15  # No excluded damages
                if clause.scope and "all" in clause.scope.lower():
                    score += 10  # Very broad scope

        return min(100, score)

    def _score_termination(self, termination_clauses: List[TerminationClause]) -> float:
        """Score based on termination analysis."""
        if not termination_clauses:
            return 40  # No termination clause is concerning

        score = 0
        has_convenience = False

        for clause in termination_clauses:
            if clause.termination_type == "for_convenience":
                has_convenience = True

            # Short notice periods
            if clause.notice_period_days:
                if clause.notice_period_days < 15:
                    score += 15  # Very short notice
                elif clause.notice_period_days < 30:
                    score += 8

            # Check for penalties
            if clause.penalties:
                score += 10

        if not has_convenience:
            score += 20  # No termination for convenience

        return min(100, score)

    def _score_structural(self, analysis: ContractAnalysis) -> float:
        """Score based on structural contract issues."""
        score = 0

        # No effective date
        if not analysis.effective_date:
            score += 10

        # No expiration date (could be perpetual)
        if not analysis.expiration_date:
            score += 5

        # No parties identified
        if not analysis.parties:
            score += 15

        # No payment terms in commercial contract
        if not analysis.payment_terms and analysis.contract_type in [
            "service", "sales", "vendor", "consulting"
        ]:
            score += 10

        # No dispute resolution
        if not analysis.dispute_resolution:
            score += 10

        return min(100, score)

    def _score_to_level(self, score: int) -> RiskLevel:
        """Convert numeric score to risk level."""
        if score <= 25:
            return RiskLevel.LOW
        elif score <= 50:
            return RiskLevel.MEDIUM
        elif score <= 75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def get_risk_breakdown(self, analysis: ContractAnalysis) -> Dict[str, any]:
        """
        Get detailed risk breakdown.

        Returns:
            Dictionary with risk breakdown by category
        """
        risk_flag_score = self._score_risk_flags(analysis.risk_flags)
        missing_clause_score = self._score_missing_clauses(analysis.missing_clauses)
        liability_score = self._score_liability(analysis.liability_clauses)
        termination_score = self._score_termination(analysis.termination_clauses)
        structural_score = self._score_structural(analysis)

        overall_score, overall_level = self.calculate_risk_score(analysis)

        return {
            "overall_score": overall_score,
            "overall_level": overall_level.value,
            "breakdown": {
                "risk_flags": {
                    "score": round(risk_flag_score, 1),
                    "weight": "35%",
                    "count": len(analysis.risk_flags),
                    "critical_count": sum(
                        1 for f in analysis.risk_flags
                        if f.severity == RiskLevel.CRITICAL
                    ),
                    "high_count": sum(
                        1 for f in analysis.risk_flags
                        if f.severity == RiskLevel.HIGH
                    )
                },
                "missing_clauses": {
                    "score": round(missing_clause_score, 1),
                    "weight": "20%",
                    "count": len(analysis.missing_clauses),
                    "clauses": analysis.missing_clauses
                },
                "liability": {
                    "score": round(liability_score, 1),
                    "weight": "20%",
                    "has_cap": any(
                        c.cap_amount or c.cap_description
                        for c in analysis.liability_clauses
                    ),
                    "clause_count": len(analysis.liability_clauses)
                },
                "termination": {
                    "score": round(termination_score, 1),
                    "weight": "15%",
                    "has_convenience": any(
                        c.termination_type == "for_convenience"
                        for c in analysis.termination_clauses
                    ),
                    "clause_count": len(analysis.termination_clauses)
                },
                "structural": {
                    "score": round(structural_score, 1),
                    "weight": "10%",
                    "has_dates": bool(analysis.effective_date),
                    "has_parties": bool(analysis.parties),
                    "has_dispute_resolution": bool(analysis.dispute_resolution)
                }
            },
            "recommendations": self._generate_recommendations(analysis, overall_score)
        }

    def _generate_recommendations(
        self,
        analysis: ContractAnalysis,
        score: int
    ) -> List[str]:
        """Generate recommendations based on risk analysis."""
        recommendations = []

        # Critical risks
        critical_flags = [
            f for f in analysis.risk_flags
            if f.severity == RiskLevel.CRITICAL
        ]
        for flag in critical_flags:
            if flag.recommendation:
                recommendations.append(f"[CRITICAL] {flag.recommendation}")

        # High risks
        high_flags = [
            f for f in analysis.risk_flags
            if f.severity == RiskLevel.HIGH
        ]
        for flag in high_flags[:3]:  # Top 3
            if flag.recommendation:
                recommendations.append(f"[HIGH] {flag.recommendation}")

        # Missing clauses
        for clause in analysis.missing_clauses[:3]:  # Top 3
            recommendations.append(f"Add missing clause: {clause}")

        # Liability concerns
        if not any(c.cap_amount for c in analysis.liability_clauses):
            recommendations.append("Negotiate a liability cap to limit exposure")

        # Termination concerns
        if not any(
            c.termination_type == "for_convenience"
            for c in analysis.termination_clauses
        ):
            recommendations.append("Negotiate termination for convenience clause")

        # General based on score
        if score > 75:
            recommendations.insert(0, "⚠️ HIGH RISK: Consider rejecting or substantially renegotiating this contract")
        elif score > 50:
            recommendations.insert(0, "⚠️ Significant issues identified - negotiate key terms before signing")

        return recommendations[:10]  # Limit to top 10

    def highlight_problematic_clauses(
        self,
        analysis: ContractAnalysis
    ) -> List[Dict[str, str]]:
        """
        Highlight the most problematic clauses for review.

        Returns:
            List of problematic clauses with explanations
        """
        problematic = []

        # Add from risk flags
        for flag in sorted(
            analysis.risk_flags,
            key=lambda f: SEVERITY_MULTIPLIERS.get(f.severity, 1),
            reverse=True
        ):
            problematic.append({
                "type": flag.risk_type,
                "severity": flag.severity.value,
                "description": flag.description,
                "clause_text": flag.original_text or "",
                "recommendation": flag.recommendation or ""
            })

        # Check liability clauses
        for clause in analysis.liability_clauses:
            if clause.cap_amount is None and clause.liability_type == "limitation":
                problematic.append({
                    "type": "Unlimited Liability",
                    "severity": "high",
                    "description": "No cap on liability - potentially unlimited exposure",
                    "clause_text": clause.original_text,
                    "recommendation": "Negotiate a liability cap (e.g., fees paid in last 12 months)"
                })

        # Check termination
        for clause in analysis.termination_clauses:
            if clause.notice_period_days and clause.notice_period_days < 15:
                problematic.append({
                    "type": "Short Notice Period",
                    "severity": "medium",
                    "description": f"Only {clause.notice_period_days} days notice required for termination",
                    "clause_text": clause.original_text,
                    "recommendation": "Negotiate longer notice period (30-90 days)"
                })

        return problematic

