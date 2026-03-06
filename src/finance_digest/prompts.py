"""
FinanceDigest Prompts
Specialized prompts for financial report analysis.
"""

from typing import Dict


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

FINANCIAL_SYSTEM_PROMPT = """You are FinanceDigest, an expert financial analyst AI.
You specialize in analyzing financial reports, SEC filings, and earnings releases.

Your analysis should be:
- Data-driven with specific numbers and percentages
- Objective and balanced (both bullish and bearish perspectives)
- Professional, suitable for investors and analysts
- Actionable with clear insights

Always cite specific numbers from the report when available.
Express growth rates as percentages.
Flag any unusual items or red flags.
"""


# ============================================================================
# EXTRACTION PROMPTS
# ============================================================================

FINANCIAL_PROMPTS: Dict[str, str] = {

    # -------------------------------------------------------------------------
    # REVENUE ANALYSIS
    # -------------------------------------------------------------------------
    "analyze_revenue": """Analyze the revenue and growth metrics from this financial report.

Extract:
1. Total revenue
2. Revenue growth (YoY and QoQ)
3. Revenue by segment/product line
4. Revenue by geography
5. Recurring revenue (if applicable)
6. Revenue guidance

Report text:
{report_text}

Respond in this exact JSON format:
{
    "total_revenue": 1000000000,
    "revenue_growth_yoy": 15.5,
    "revenue_growth_qoq": 3.2,
    "revenue_by_segment": {
        "Segment A": 500000000,
        "Segment B": 300000000
    },
    "revenue_by_geography": {
        "North America": 600000000,
        "International": 400000000
    },
    "recurring_revenue": 750000000,
    "recurring_revenue_percentage": 75.0,
    "currency": "USD",
    "period": "Q3 2025",
    "guidance_next_quarter": "$1.05B - $1.1B",
    "guidance_full_year": "$4.2B - $4.3B"
}""",

    # -------------------------------------------------------------------------
    # PROFITABILITY ANALYSIS
    # -------------------------------------------------------------------------
    "analyze_profitability": """Analyze the profitability metrics from this financial report.

Extract:
1. Gross profit and margin
2. Operating income and margin
3. Net income and margin
4. EBITDA and margin
5. EPS (basic and diluted)
6. Margin trends

Report text:
{report_text}

Respond in this exact JSON format:
{
    "gross_profit": 500000000,
    "gross_margin": 50.0,
    "operating_income": 200000000,
    "operating_margin": 20.0,
    "net_income": 150000000,
    "net_margin": 15.0,
    "ebitda": 250000000,
    "ebitda_margin": 25.0,
    "eps": 2.50,
    "eps_diluted": 2.45,
    "eps_growth_yoy": 12.0
}""",

    # -------------------------------------------------------------------------
    # RISK ANALYSIS
    # -------------------------------------------------------------------------
    "analyze_risks": """Identify key risks from this financial report.

Categorize risks by type:
- Market Risk (competition, demand, pricing)
- Operational Risk (supply chain, technology, workforce)
- Financial Risk (debt, liquidity, currency)
- Regulatory Risk (compliance, legal, policy)
- Strategic Risk (M&A, expansion, innovation)

Report text:
{report_text}

Respond in this exact JSON format:
{
    "risk_factors": [
        {
            "category": "Market Risk",
            "title": "Competitive Pressure",
            "description": "Detailed description of the risk",
            "severity": "moderate",
            "is_new": false,
            "trend": "increasing",
            "mitigation": "Company's mitigation strategy",
            "source_section": "Risk Factors"
        }
    ]
}""",

    # -------------------------------------------------------------------------
    # MANAGEMENT OUTLOOK
    # -------------------------------------------------------------------------
    "analyze_management": """Analyze management's outlook and commentary from this report.

Extract:
1. Overall sentiment (positive/neutral/negative)
2. Key themes discussed
3. Growth expectations
4. Challenges mentioned
5. Opportunities mentioned
6. Strategic initiatives
7. Guidance provided
8. Notable quotes

Report text:
{report_text}

Respond in this exact JSON format:
{
    "overall_sentiment": "positive",
    "key_themes": ["AI investment", "Cost optimization", "Market expansion"],
    "growth_expectations": "Management expects continued double-digit growth",
    "challenges_mentioned": ["Supply chain constraints", "Hiring difficulties"],
    "opportunities_mentioned": ["New market entry", "Product launches"],
    "strategic_initiatives": ["Cloud migration", "AI integration"],
    "guidance_revenue": "$4.2B - $4.3B for FY2025",
    "guidance_earnings": "EPS of $10.50 - $11.00",
    "guidance_other": {
        "Operating margin": "20-22%"
    },
    "notable_quotes": ["We are confident in our long-term strategy"]
}""",

    # -------------------------------------------------------------------------
    # RED FLAGS
    # -------------------------------------------------------------------------
    "detect_red_flags": """Detect potential red flags or warning signs in this financial report.

Look for:
1. Revenue quality issues (one-time items, aggressive recognition)
2. Margin deterioration
3. Rising debt levels
4. Management turnover
5. Audit concerns
6. Guidance cuts
7. Related party transactions
8. Unusual accounting changes
9. Cash flow vs earnings divergence
10. Insider selling mentions

Report text:
{report_text}

Respond in this exact JSON format:
{
    "red_flags": [
        {
            "flag_type": "Revenue Quality",
            "severity": "high",
            "description": "Significant revenue from one-time contract",
            "evidence": "Quote from report showing the issue",
            "recommendation": "Monitor recurring revenue trends"
        }
    ]
}""",

    # -------------------------------------------------------------------------
    # INVESTMENT THESIS
    # -------------------------------------------------------------------------
    "generate_thesis": """Generate an investment thesis based on this financial analysis.

Provide:
1. Recommendation (Buy/Hold/Sell/Avoid)
2. Confidence level (0-100%)
3. Executive summary
4. Bull case arguments
5. Bear case arguments
6. Key catalysts
7. Key risks
8. Target price analysis (if data available)

Financial data:
{financial_data}

Report text:
{report_text}

Respond in this exact JSON format:
{
    "recommendation": "Buy",
    "confidence": 75.0,
    "summary": "2-3 sentence investment thesis",
    "bull_case": [
        "Strong revenue growth momentum",
        "Expanding margins",
        "Market leadership position"
    ],
    "bear_case": [
        "High valuation relative to peers",
        "Competitive pressure increasing"
    ],
    "key_catalysts": [
        "New product launch in Q4",
        "Potential M&A activity"
    ],
    "key_risks": [
        "Economic slowdown impact",
        "Regulatory changes"
    ],
    "target_price_analysis": "Based on 25x forward PE, fair value range is $150-$175",
    "time_horizon": "12 months"
}""",

    # -------------------------------------------------------------------------
    # FULL ANALYSIS
    # -------------------------------------------------------------------------
    "full_analysis": """Perform comprehensive analysis of this financial report.

Provide:
1. Company identification
2. Executive summary
3. Key highlights (3-5 points)
4. Overall sentiment
5. Key metrics summary
6. Recommendations

Report text:
{report_text}

Respond in this exact JSON format:
{
    "company_name": "Company Name",
    "ticker": "TICK",
    "filing_type": "10-Q",
    "period": "Q3 2025",
    "summary": "2-3 sentence executive summary",
    "key_highlights": [
        "Revenue grew 15% YoY to $1.2B",
        "Operating margin expanded 200bps",
        "Raised full-year guidance"
    ],
    "overall_sentiment": "positive",
    "action_items": [
        "Monitor competitive dynamics",
        "Track margin trajectory"
    ]
}""",

    # -------------------------------------------------------------------------
    # COMPARISON
    # -------------------------------------------------------------------------
    "compare_reports": """Compare these two financial reports and identify key changes.

Report A ({period_a}):
{report_a_text}

Report B ({period_b}):
{report_b_text}

Provide:
1. Summary of key changes
2. Revenue changes
3. Profitability changes
4. New risks emerged
5. Risks resolved
6. Overall trend assessment
7. Recommendations

Respond in this exact JSON format:
{
    "summary": "Brief comparison summary",
    "key_changes": [
        "Revenue accelerated from 10% to 15% growth",
        "Operating margin improved 200bps"
    ],
    "overall_trend": "improving",
    "revenue_changes": [
        {
            "metric_name": "Total Revenue",
            "period_a_value": 1000000000,
            "period_b_value": 1150000000,
            "percentage_change": 15.0,
            "trend": "improving",
            "significance": "significant"
        }
    ],
    "profitability_changes": [
        {
            "metric_name": "Operating Margin",
            "period_a_value": 18.0,
            "period_b_value": 20.0,
            "absolute_change": 2.0,
            "trend": "improving",
            "significance": "significant"
        }
    ],
    "new_risks": [],
    "resolved_risks": [],
    "analysis": "Detailed analysis paragraph",
    "recommendations": [
        "Action item based on comparison"
    ]
}"""
}


def get_financial_prompt(
    prompt_type: str,
    report_text: str = "",
    report_a_text: str = "",
    report_b_text: str = "",
    period_a: str = "",
    period_b: str = "",
    financial_data: str = ""
) -> str:
    """
    Get a formatted financial analysis prompt.

    Args:
        prompt_type: Type of prompt
        report_text: Report text to analyze
        report_a_text: First report for comparison
        report_b_text: Second report for comparison
        period_a: First period label
        period_b: Second period label
        financial_data: Pre-extracted financial data (for thesis)

    Returns:
        Formatted prompt string
    """
    if prompt_type not in FINANCIAL_PROMPTS:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    prompt = FINANCIAL_PROMPTS[prompt_type]

    return prompt.format(
        report_text=report_text,
        report_a_text=report_a_text,
        report_b_text=report_b_text,
        period_a=period_a,
        period_b=period_b,
        financial_data=financial_data
    )


def get_system_prompt() -> str:
    """Get the system prompt for financial analysis."""
    return FINANCIAL_SYSTEM_PROMPT

