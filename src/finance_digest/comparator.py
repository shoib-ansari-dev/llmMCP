"""
FinanceDigest Comparator
Compare financial reports across periods.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime

from .models import (
    FinancialAnalysis,
    FinancialComparison,
    MetricChange,
    RiskFactor,
    RiskSeverity
)
from .prompts import get_financial_prompt, get_system_prompt

logger = logging.getLogger(__name__)


class FinancialComparator:
    """
    Compare financial reports across different periods.
    Supports sequential (Q2 vs Q3), YoY, and competitor comparisons.
    """

    def __init__(self, llm_client=None):
        """Initialize comparator."""
        self._llm_client = llm_client

    @property
    def llm_client(self):
        """Lazy load LLM client."""
        if self._llm_client is None:
            from ..agents.groq_client import GroqClient
            self._llm_client = GroqClient()
        return self._llm_client

    async def compare_reports(
        self,
        report_a_text: str,
        report_b_text: str,
        period_a: str,
        period_b: str,
        comparison_type: str = "sequential",
        company_name: Optional[str] = None,
        ticker: Optional[str] = None
    ) -> FinancialComparison:
        """
        Compare two financial reports.

        Args:
            report_a_text: First report text
            report_b_text: Second report text
            period_a: First period label (e.g., "Q2 2025")
            period_b: Second period label (e.g., "Q3 2025")
            comparison_type: Type of comparison
            company_name: Company name
            ticker: Stock ticker

        Returns:
            FinancialComparison with differences
        """
        logger.info(f"Comparing reports: {period_a} vs {period_b}")

        result = FinancialComparison(
            company_name=company_name,
            ticker=ticker,
            period_a=period_a,
            period_b=period_b,
            comparison_type=comparison_type,
            compared_at=datetime.utcnow().isoformat()
        )

        # LLM comparison
        await self._llm_compare(
            result,
            report_a_text[:15000],
            report_b_text[:15000],
            period_a,
            period_b
        )

        return result

    async def compare_analyses(
        self,
        analysis_a: FinancialAnalysis,
        analysis_b: FinancialAnalysis
    ) -> FinancialComparison:
        """
        Compare two already-analyzed reports.

        Args:
            analysis_a: First analysis
            analysis_b: Second analysis

        Returns:
            FinancialComparison with differences
        """
        result = FinancialComparison(
            company_name=analysis_a.company_name or analysis_b.company_name,
            ticker=analysis_a.ticker or analysis_b.ticker,
            period_a=analysis_a.period,
            period_b=analysis_b.period,
            comparison_type="sequential",
            compared_at=datetime.utcnow().isoformat()
        )

        # Compare revenue
        if analysis_a.revenue and analysis_b.revenue:
            result.revenue_changes = self._compare_revenue(
                analysis_a.revenue,
                analysis_b.revenue
            )

        # Compare profitability
        if analysis_a.profitability and analysis_b.profitability:
            result.profitability_changes = self._compare_profitability(
                analysis_a.profitability,
                analysis_b.profitability
            )

        # Compare risks
        result.new_risks = self._find_new_risks(
            analysis_a.risk_factors,
            analysis_b.risk_factors
        )
        result.resolved_risks = self._find_resolved_risks(
            analysis_a.risk_factors,
            analysis_b.risk_factors
        )

        # Determine overall trend
        result.overall_trend = self._determine_trend(result)

        # Generate key changes
        result.key_changes = self._generate_key_changes(result)

        # Generate summary
        result.summary = self._generate_summary(result)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    async def _llm_compare(
        self,
        result: FinancialComparison,
        report_a_text: str,
        report_b_text: str,
        period_a: str,
        period_b: str
    ):
        """Use LLM to compare reports."""
        try:
            prompt = get_financial_prompt(
                "compare_reports",
                report_a_text=report_a_text,
                report_b_text=report_b_text,
                period_a=period_a,
                period_b=period_b
            )

            response = await self.llm_client.chat(
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )

            data = self._parse_json_response(response)
            if not data:
                return

            result.summary = data.get("summary", "")
            result.key_changes = data.get("key_changes", [])
            result.overall_trend = data.get("overall_trend", "stable")
            result.analysis = data.get("analysis", "")
            result.recommendations = data.get("recommendations", [])

            # Parse revenue changes
            for change in data.get("revenue_changes", []):
                result.revenue_changes.append(MetricChange(
                    metric_name=change.get("metric_name", ""),
                    period_a_value=change.get("period_a_value"),
                    period_b_value=change.get("period_b_value"),
                    absolute_change=change.get("absolute_change"),
                    percentage_change=change.get("percentage_change"),
                    trend=change.get("trend", "stable"),
                    significance=change.get("significance", "normal")
                ))

            # Parse profitability changes
            for change in data.get("profitability_changes", []):
                result.profitability_changes.append(MetricChange(
                    metric_name=change.get("metric_name", ""),
                    period_a_value=change.get("period_a_value"),
                    period_b_value=change.get("period_b_value"),
                    absolute_change=change.get("absolute_change"),
                    percentage_change=change.get("percentage_change"),
                    trend=change.get("trend", "stable"),
                    significance=change.get("significance", "normal")
                ))

            # Parse new risks
            for risk in data.get("new_risks", []):
                if isinstance(risk, dict):
                    result.new_risks.append(RiskFactor(
                        category=risk.get("category", "Other"),
                        title=risk.get("title", ""),
                        description=risk.get("description", ""),
                        severity=RiskSeverity(risk.get("severity", "moderate"))
                    ))

            result.resolved_risks = data.get("resolved_risks", [])

        except Exception as e:
            logger.error(f"LLM comparison failed: {e}")

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from response."""
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

    def _compare_revenue(self, rev_a, rev_b) -> List[MetricChange]:
        """Compare revenue metrics."""
        changes = []

        # Total revenue
        if rev_a.total_revenue and rev_b.total_revenue:
            pct_change = ((rev_b.total_revenue - rev_a.total_revenue) / rev_a.total_revenue) * 100
            changes.append(MetricChange(
                metric_name="Total Revenue",
                period_a_value=rev_a.total_revenue,
                period_b_value=rev_b.total_revenue,
                absolute_change=rev_b.total_revenue - rev_a.total_revenue,
                percentage_change=round(pct_change, 2),
                trend="improving" if pct_change > 0 else "declining",
                significance="significant" if abs(pct_change) > 10 else "normal"
            ))

        # Revenue growth YoY
        if rev_a.revenue_growth_yoy is not None and rev_b.revenue_growth_yoy is not None:
            change = rev_b.revenue_growth_yoy - rev_a.revenue_growth_yoy
            changes.append(MetricChange(
                metric_name="Revenue Growth YoY",
                period_a_value=rev_a.revenue_growth_yoy,
                period_b_value=rev_b.revenue_growth_yoy,
                absolute_change=round(change, 2),
                trend="improving" if change > 0 else "declining",
                significance="significant" if abs(change) > 5 else "normal"
            ))

        return changes

    def _compare_profitability(self, prof_a, prof_b) -> List[MetricChange]:
        """Compare profitability metrics."""
        changes = []

        metrics_to_compare = [
            ("gross_margin", "Gross Margin"),
            ("operating_margin", "Operating Margin"),
            ("net_margin", "Net Margin"),
            ("eps", "EPS")
        ]

        for attr, name in metrics_to_compare:
            val_a = getattr(prof_a, attr, None)
            val_b = getattr(prof_b, attr, None)

            if val_a is not None and val_b is not None:
                change = val_b - val_a
                changes.append(MetricChange(
                    metric_name=name,
                    period_a_value=val_a,
                    period_b_value=val_b,
                    absolute_change=round(change, 2),
                    trend="improving" if change > 0 else "declining",
                    significance="significant" if abs(change) > 2 else "normal"
                ))

        return changes

    def _find_new_risks(
        self,
        risks_a: List[RiskFactor],
        risks_b: List[RiskFactor]
    ) -> List[RiskFactor]:
        """Find risks in B that weren't in A."""
        titles_a = {r.title.lower() for r in risks_a}
        return [r for r in risks_b if r.title.lower() not in titles_a]

    def _find_resolved_risks(
        self,
        risks_a: List[RiskFactor],
        risks_b: List[RiskFactor]
    ) -> List[str]:
        """Find risks in A that aren't in B."""
        titles_b = {r.title.lower() for r in risks_b}
        return [r.title for r in risks_a if r.title.lower() not in titles_b]

    def _determine_trend(self, comparison: FinancialComparison) -> str:
        """Determine overall trend from comparison."""
        improving = 0
        declining = 0

        for change in comparison.revenue_changes + comparison.profitability_changes:
            if change.trend == "improving":
                improving += 1
            elif change.trend == "declining":
                declining += 1

        if improving > declining:
            return "improving"
        elif declining > improving:
            return "declining"
        return "stable"

    def _generate_key_changes(self, comparison: FinancialComparison) -> List[str]:
        """Generate list of key changes."""
        changes = []

        # Significant revenue changes
        for change in comparison.revenue_changes:
            if change.significance == "significant":
                if change.percentage_change:
                    direction = "increased" if change.percentage_change > 0 else "decreased"
                    changes.append(
                        f"{change.metric_name} {direction} {abs(change.percentage_change):.1f}%"
                    )

        # Significant profitability changes
        for change in comparison.profitability_changes:
            if change.significance == "significant":
                if change.absolute_change:
                    direction = "expanded" if change.absolute_change > 0 else "contracted"
                    changes.append(
                        f"{change.metric_name} {direction} {abs(change.absolute_change):.1f}pp"
                    )

        # New risks
        if comparison.new_risks:
            changes.append(f"{len(comparison.new_risks)} new risk(s) identified")

        return changes[:10]

    def _generate_summary(self, comparison: FinancialComparison) -> str:
        """Generate comparison summary."""
        parts = [
            f"Comparing {comparison.period_a} to {comparison.period_b}:"
        ]

        if comparison.key_changes:
            parts.append(comparison.key_changes[0])

        parts.append(f"Overall trend: {comparison.overall_trend}")

        return " ".join(parts)

    def _generate_recommendations(
        self,
        comparison: FinancialComparison
    ) -> List[str]:
        """Generate recommendations from comparison."""
        recommendations = []

        # Based on trend
        if comparison.overall_trend == "declining":
            recommendations.append("Monitor closely for continued deterioration")
        elif comparison.overall_trend == "improving":
            recommendations.append("Positive momentum - consider increasing position")

        # Based on new risks
        for risk in comparison.new_risks:
            if risk.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]:
                recommendations.append(f"Evaluate new risk: {risk.title}")

        return recommendations[:5]

