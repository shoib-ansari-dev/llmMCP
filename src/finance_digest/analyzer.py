"""
FinanceDigest Analyzer
Main financial report analysis engine.
"""

import json
import logging
import re
from typing import Optional, List, Dict
from datetime import datetime

from .models import (
    FinancialAnalysis,
    RevenueMetrics,
    ProfitabilityMetrics,
    CashFlowMetrics,
    RiskFactor,
    ManagementOutlook,
    InvestmentThesis,
    RedFlag,
    FilingType,
    Sentiment,
    RiskSeverity
)
from .prompts import get_financial_prompt, get_system_prompt

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """
    Financial report analysis engine.
    Analyzes 10-K, 10-Q, earnings reports and other financial documents.
    """

    def __init__(self, llm_client=None):
        """
        Initialize analyzer.

        Args:
            llm_client: LLM client for analysis
        """
        self._llm_client = llm_client

    @property
    def llm_client(self):
        """Lazy load LLM client."""
        if self._llm_client is None:
            from ..agents.local_llm_client import LocalLLMClient
            self._llm_client = LocalLLMClient()
        return self._llm_client

    async def analyze_report(
        self,
        document_id: str,
        report_text: str,
        filing_type: Optional[str] = None,
        company_ticker: Optional[str] = None,
        include_thesis: bool = True
    ) -> FinancialAnalysis:
        """
        Perform comprehensive financial report analysis.

        Args:
            document_id: Unique document identifier
            report_text: Report text to analyze
            filing_type: Type of filing (10-K, 10-Q, etc.)
            company_ticker: Company stock ticker
            include_thesis: Whether to generate investment thesis

        Returns:
            FinancialAnalysis with all extracted data
        """
        logger.info(f"Analyzing financial report: {document_id}")

        result = FinancialAnalysis(
            document_id=document_id,
            ticker=company_ticker,
            analyzed_at=datetime.utcnow().isoformat()
        )

        if filing_type:
            try:
                result.filing_type = FilingType(filing_type)
            except ValueError:
                result.filing_type = FilingType.OTHER

        # Run analyses
        llm_success = False
        analyses = [
            ("full_analysis", self._update_full_analysis),
            ("analyze_revenue", self._update_revenue),
            ("analyze_profitability", self._update_profitability),
            ("analyze_risks", self._update_risks),
            ("analyze_management", self._update_management),
            ("detect_red_flags", self._update_red_flags),
        ]

        for analysis_type, update_func in analyses:
            try:
                data = await self._run_extraction(analysis_type, report_text)
                if data:
                    update_func(result, data)
                    llm_success = True
            except Exception as e:
                logger.error(f"Error in {analysis_type}: {e}")

        # Use regex fallback if LLM failed
        if not llm_success or (not result.summary and not result.key_highlights):
            logger.warning("LLM extraction failed, using regex fallback")
            self._extract_with_regex(result, report_text)

        # Generate investment thesis if requested
        if include_thesis:
            try:
                await self._generate_thesis(result, report_text)
            except Exception as e:
                logger.error(f"Error generating thesis: {e}")

        return result

    def _extract_with_regex(self, result: FinancialAnalysis, report_text: str):
        """Extract key financial information using regex when LLM fails."""
        logger.info("Using fallback regex extraction for financial report")

        text = report_text
        text_lower = text.lower()

        # Extract company name
        company_patterns = [
            r'^([A-Z][A-Za-z\s]+(?:Inc|Corp|LLC|Ltd|Company|Co)\.?)',
            r'(?:Company|COMPANY):\s*([A-Za-z\s]+)',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                result.company_name = match.group(1).strip()
                break

        # Extract revenue figures
        revenue_patterns = [
            r'(?:total\s+)?revenue[s]?\s*(?:of|was|were|:)?\s*\$?\s*([\d,\.]+)\s*(million|billion|M|B)?',
            r'\$\s*([\d,\.]+)\s*(million|billion|M|B)?\s*(?:in\s+)?(?:total\s+)?revenue',
        ]
        for pattern in revenue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    multiplier = match.group(2).lower() if match.group(2) else ''
                    if multiplier in ['billion', 'b']:
                        amount *= 1_000_000_000
                    elif multiplier in ['million', 'm']:
                        amount *= 1_000_000
                    result.revenue = RevenueMetrics(
                        total_revenue=amount,
                        currency="USD"
                    )
                except (ValueError, AttributeError):
                    pass
                break

        # Extract profit/income figures
        profit_patterns = [
            r'net\s+income\s*(?:of|was|:)?\s*\$?\s*([\d,\.]+)\s*(million|billion|M|B)?',
            r'operating\s+income\s*(?:of|was|:)?\s*\$?\s*([\d,\.]+)\s*(million|billion|M|B)?',
        ]
        for pattern in profit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    multiplier = match.group(2).lower() if match.group(2) else ''
                    if multiplier in ['billion', 'b']:
                        amount *= 1_000_000_000
                    elif multiplier in ['million', 'm']:
                        amount *= 1_000_000
                    result.profitability = ProfitabilityMetrics(
                        net_income=amount
                    )
                except (ValueError, AttributeError):
                    pass
                break

        # Generate summary from first meaningful paragraph
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 100]
        if paragraphs:
            result.summary = paragraphs[0][:500] + "..." if len(paragraphs[0]) > 500 else paragraphs[0]

        # Extract key highlights (sentences with financial keywords)
        financial_keywords = ['revenue', 'profit', 'growth', 'increase', 'decrease', 'margin', 'earnings']
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 40 and len(sentence) < 250:
                if any(kw in sentence.lower() for kw in financial_keywords):
                    result.key_highlights.append(sentence)
                    if len(result.key_highlights) >= 5:
                        break

        # Detect risk keywords
        risk_keywords = {
            'competition': 'Competitive pressure mentioned',
            'regulatory': 'Regulatory risks present',
            'debt': 'Debt-related concerns',
            'litigation': 'Legal/litigation risks',
            'supply chain': 'Supply chain risks',
        }
        for keyword, description in risk_keywords.items():
            if keyword in text_lower:
                result.risk_factors.append(RiskFactor(
                    category=keyword.title(),
                    severity=RiskSeverity.MEDIUM,
                    description=description
                ))

        logger.info(f"Fallback extraction complete: {len(result.key_highlights)} highlights, {len(result.risk_factors)} risks")

    async def _run_extraction(
        self,
        prompt_type: str,
        report_text: str
    ) -> Optional[Dict]:
        """Run an extraction prompt and return parsed data."""
        prompt = get_financial_prompt(prompt_type, report_text=report_text)

        response = await self._call_llm(prompt)
        if not response:
            return None

        return self._parse_json_response(response)

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM with prompt."""
        try:
            response = await self.llm_client.chat(
                messages=[
                    {"role": "system", "content": get_system_prompt()},
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
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None

    # =========================================================================
    # UPDATE METHODS
    # =========================================================================

    def _update_full_analysis(self, result: FinancialAnalysis, data: Dict):
        """Update from full analysis."""
        result.company_name = data.get("company_name")
        if not result.ticker:
            result.ticker = data.get("ticker")
        result.period = data.get("period", "")
        result.summary = data.get("summary", "")
        result.key_highlights = data.get("key_highlights", [])
        result.action_items = data.get("action_items", [])

        sentiment = data.get("overall_sentiment", "neutral")
        try:
            result.overall_sentiment = Sentiment(sentiment)
        except ValueError:
            result.overall_sentiment = Sentiment.NEUTRAL

        filing_type = data.get("filing_type")
        if filing_type:
            try:
                result.filing_type = FilingType(filing_type)
            except ValueError:
                pass

    def _update_revenue(self, result: FinancialAnalysis, data: Dict):
        """Update revenue metrics."""
        result.revenue = RevenueMetrics(
            total_revenue=data.get("total_revenue"),
            revenue_growth_yoy=data.get("revenue_growth_yoy"),
            revenue_growth_qoq=data.get("revenue_growth_qoq"),
            revenue_by_segment=data.get("revenue_by_segment", {}),
            revenue_by_geography=data.get("revenue_by_geography", {}),
            recurring_revenue=data.get("recurring_revenue"),
            recurring_revenue_percentage=data.get("recurring_revenue_percentage"),
            currency=data.get("currency", "USD"),
            period=data.get("period", ""),
            guidance_next_quarter=data.get("guidance_next_quarter"),
            guidance_full_year=data.get("guidance_full_year")
        )

    def _update_profitability(self, result: FinancialAnalysis, data: Dict):
        """Update profitability metrics."""
        result.profitability = ProfitabilityMetrics(
            gross_profit=data.get("gross_profit"),
            gross_margin=data.get("gross_margin"),
            operating_income=data.get("operating_income"),
            operating_margin=data.get("operating_margin"),
            net_income=data.get("net_income"),
            net_margin=data.get("net_margin"),
            ebitda=data.get("ebitda"),
            ebitda_margin=data.get("ebitda_margin"),
            eps=data.get("eps"),
            eps_diluted=data.get("eps_diluted"),
            eps_growth_yoy=data.get("eps_growth_yoy")
        )

    def _update_risks(self, result: FinancialAnalysis, data: Dict):
        """Update risk factors."""
        risks = data.get("risk_factors", [])
        result.risk_factors = [
            RiskFactor(
                category=r.get("category", "Other"),
                title=r.get("title", ""),
                description=r.get("description", ""),
                severity=RiskSeverity(r.get("severity", "moderate")),
                is_new=r.get("is_new", False),
                trend=r.get("trend", "stable"),
                mitigation=r.get("mitigation"),
                source_section=r.get("source_section")
            )
            for r in risks
        ]

    def _update_management(self, result: FinancialAnalysis, data: Dict):
        """Update management outlook."""
        sentiment = data.get("overall_sentiment", "neutral")
        try:
            sentiment_enum = Sentiment(sentiment)
        except ValueError:
            sentiment_enum = Sentiment.NEUTRAL

        result.management_outlook = ManagementOutlook(
            overall_sentiment=sentiment_enum,
            key_themes=data.get("key_themes", []),
            growth_expectations=data.get("growth_expectations"),
            challenges_mentioned=data.get("challenges_mentioned", []),
            opportunities_mentioned=data.get("opportunities_mentioned", []),
            strategic_initiatives=data.get("strategic_initiatives", []),
            guidance_revenue=data.get("guidance_revenue"),
            guidance_earnings=data.get("guidance_earnings"),
            guidance_other=data.get("guidance_other", {}),
            notable_quotes=data.get("notable_quotes", [])
        )

    def _update_red_flags(self, result: FinancialAnalysis, data: Dict):
        """Update red flags."""
        flags = data.get("red_flags", [])
        result.red_flags = [
            RedFlag(
                flag_type=f.get("flag_type", "Other"),
                severity=RiskSeverity(f.get("severity", "moderate")),
                description=f.get("description", ""),
                evidence=f.get("evidence", ""),
                recommendation=f.get("recommendation", "")
            )
            for f in flags
        ]

    async def _generate_thesis(
        self,
        result: FinancialAnalysis,
        report_text: str
    ):
        """Generate investment thesis."""
        # Prepare financial data summary
        financial_data = {
            "revenue": result.revenue.model_dump() if result.revenue else None,
            "profitability": result.profitability.model_dump() if result.profitability else None,
            "risk_count": len(result.risk_factors),
            "red_flag_count": len(result.red_flags)
        }

        prompt = get_financial_prompt(
            "generate_thesis",
            report_text=report_text[:10000],
            financial_data=json.dumps(financial_data, indent=2)
        )

        response = await self._call_llm(prompt)
        if not response:
            return

        data = self._parse_json_response(response)
        if not data:
            return

        result.investment_thesis = InvestmentThesis(
            recommendation=data.get("recommendation", "Hold"),
            confidence=data.get("confidence", 50.0),
            summary=data.get("summary", ""),
            bull_case=data.get("bull_case", []),
            bear_case=data.get("bear_case", []),
            key_catalysts=data.get("key_catalysts", []),
            key_risks=data.get("key_risks", []),
            target_price_analysis=data.get("target_price_analysis"),
            time_horizon=data.get("time_horizon", "12 months")
        )

    # =========================================================================
    # INDIVIDUAL EXTRACTION METHODS
    # =========================================================================

    async def extract_revenue_metrics(
        self,
        report_text: str
    ) -> Optional[RevenueMetrics]:
        """Extract only revenue metrics."""
        data = await self._run_extraction("analyze_revenue", report_text)
        if not data:
            return None

        return RevenueMetrics(
            total_revenue=data.get("total_revenue"),
            revenue_growth_yoy=data.get("revenue_growth_yoy"),
            revenue_growth_qoq=data.get("revenue_growth_qoq"),
            revenue_by_segment=data.get("revenue_by_segment", {}),
            revenue_by_geography=data.get("revenue_by_geography", {}),
            recurring_revenue=data.get("recurring_revenue"),
            recurring_revenue_percentage=data.get("recurring_revenue_percentage"),
            currency=data.get("currency", "USD"),
            period=data.get("period", ""),
            guidance_next_quarter=data.get("guidance_next_quarter"),
            guidance_full_year=data.get("guidance_full_year")
        )

    async def extract_risk_factors(
        self,
        report_text: str
    ) -> List[RiskFactor]:
        """Extract only risk factors."""
        data = await self._run_extraction("analyze_risks", report_text)
        if not data:
            return []

        return [
            RiskFactor(
                category=r.get("category", "Other"),
                title=r.get("title", ""),
                description=r.get("description", ""),
                severity=RiskSeverity(r.get("severity", "moderate")),
                is_new=r.get("is_new", False),
                trend=r.get("trend", "stable"),
                mitigation=r.get("mitigation"),
                source_section=r.get("source_section")
            )
            for r in data.get("risk_factors", [])
        ]

    async def detect_red_flags(
        self,
        report_text: str
    ) -> List[RedFlag]:
        """Detect red flags only."""
        data = await self._run_extraction("detect_red_flags", report_text)
        if not data:
            return []

        return [
            RedFlag(
                flag_type=f.get("flag_type", "Other"),
                severity=RiskSeverity(f.get("severity", "moderate")),
                description=f.get("description", ""),
                evidence=f.get("evidence", ""),
                recommendation=f.get("recommendation", "")
            )
            for f in data.get("red_flags", [])
        ]

