"""
Local LLM Client
Handles all interactions with the local Docker-based LLM.
Uses OpenAI-compatible API at http://localhost:12434/engines/v1
Model: ai/smollm2:360M-Q4_K_M
"""

import os
import logging
from typing import Optional
from openai import OpenAI


logger = logging.getLogger(__name__)

# Default local LLM configuration
DEFAULT_LLM_BASE_URL = "http://localhost:12000/engines/v1"
DEFAULT_LLM_MODEL = "ai/smollm2:360M-Q4_K_M"


class LocalLLMClient:
    """Client for interacting with local Docker-based LLM via OpenAI-compatible API."""

    def __init__(self, base_url: str = None, model: str = None):
        """
        Initialize local LLM client.

        Args:
            base_url: Base URL for the local LLM API (defaults to LOCAL_LLM_URL env var)
            model: Model name to use (defaults to LLM_MODEL env var)
        """
        self.base_url = base_url or os.getenv("LOCAL_LLM_URL", DEFAULT_LLM_BASE_URL)
        self.model = model or os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)

        # Initialize OpenAI client with local endpoint
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="not-needed"  # Local models don't need API key
        )

        logger.info(f"Initialized LocalLLMClient with model: {self.model} at {self.base_url}")

    def _call_llm(self, messages: list[dict], max_tokens: int = 1500) -> str:
        """
        Call the local LLM via OpenAI-compatible API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response

        Returns:
            Model response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3  # Lower temperature for more focused responses
            )
            result = response.choices[0].message.content.strip()

            # Check for repetitive/poor quality responses
            if result and len(result) > 200:
                # Count repeated phrases (sign of model degradation)
                lines = result.split('\n')
                if len(lines) > 1 and lines[0] in result[100:]:
                    logger.warning("Detected repetitive output from LLM")

            return result

        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            return f"Error communicating with local LLM: {str(e)}"

    async def summarize(self, content: str, doc_type: str = "document") -> str:
        """
        Generate a summary of the document content.

        Args:
            content: The document text to summarize
            doc_type: Type of document (pdf, spreadsheet, webpage)

        Returns:
            Summary string
        """
        # Truncate content to avoid overwhelming the model
        content = content[:3000].strip()

        messages = [
            {
                "role": "system",
                "content": f"You are a professional document summarizer. Summarize the {doc_type} concisely in 3-5 sentences. Focus on the most important information."
            },
            {
                "role": "user",
                "content": f"""Please summarize this {doc_type}:

{content}

SUMMARY (3-5 sentences):"""
            }
        ]
        return self._call_llm(messages, max_tokens=300)

    async def extract_insights(self, content: str, doc_type: str = "document") -> list[str]:
        """
        Extract key insights from the document.

        Args:
            content: The document text
            doc_type: Type of document

        Returns:
            List of insight strings
        """
        content = content[:3000].strip()

        messages = [
            {
                "role": "system",
                "content": "You are an expert at extracting key insights from documents. Extract 3-5 important points as a numbered list."
            },
            {
                "role": "user",
                "content": f"""Extract key insights from this {doc_type}:

{content}

KEY INSIGHTS:
1."""
            }
        ]
        response = self._call_llm(messages, max_tokens=400)

        # Parse response into list
        insights = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering/bullets
                cleaned = line.lstrip('0123456789.-) ').strip()
                if cleaned and len(cleaned) > 10:  # Only include meaningful insights
                    insights.append(cleaned)

        return insights if insights else [response] if response and not response.startswith("Error") else []

    async def answer_question(self, question: str, context: str) -> str:
        """
        Answer a question based on document context.

        Args:
            question: The user's question
            context: Relevant document content

        Returns:
            Answer string
        """
        # Truncate context to avoid overwhelming the model
        context = context[:2500].strip()
        question = question.strip()

        if not context:
            return "No relevant context found to answer this question. Please upload a document first."

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer the question using ONLY the provided document context. Be concise and accurate. If the answer is not in the context, say 'I cannot find this information in the provided document.'"
            },
            {
                "role": "user",
                "content": f"""DOCUMENT CONTEXT:
{context}

QUESTION: {question}

ANSWER (concise and based only on the context above):"""
            }
        ]
        return self._call_llm(messages, max_tokens=500)

    async def analyze_document(self, content: str, doc_type: str = "document") -> dict:
        """
        Perform full document analysis: summary + insights.

        Args:
            content: The document text
            doc_type: Type of document

        Returns:
            Dict with summary and insights
        """
        content = content[:3000].strip()

        messages = [
            {
                "role": "system",
                "content": f"You are an expert document analyst. Provide a brief summary followed by key findings."
            },
            {
                "role": "user",
                "content": f"""Analyze this {doc_type}:

{content}

Provide:
1. A brief summary (2-3 sentences)
2. Key findings (3-5 bullet points)

Analysis:"""
            }
        ]
        response = self._call_llm(messages, max_tokens=400)

        # Parse response
        summary = response
        insights = []

        # Try to extract any listed items as insights
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                cleaned = line.lstrip('0123456789.-•) ').strip()
                if cleaned and len(cleaned) > 10:
                    insights.append(cleaned)

        return {
            "summary": summary,
            "insights": insights[:5]
        }

    async def improve_summary(
        self,
        content: str,
        doc_type: str,
        previous_summary: str,
        feedback: str
    ) -> str:
        """
        Improve a summary based on user feedback.

        Args:
            content: The original document content
            doc_type: Type of document
            previous_summary: The summary to improve
            feedback: User's feedback

        Returns:
            Improved summary string
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that improves summaries based on user feedback. Address the feedback while maintaining accuracy."
            },
            {
                "role": "user",
                "content": f"""Improve this summary based on the feedback:

PREVIOUS SUMMARY:
{previous_summary[:500]}

USER FEEDBACK: {feedback}

ORIGINAL CONTENT:
{content[:1500]}

IMPROVED SUMMARY:"""
            }
        ]
        return self._call_llm(messages, max_tokens=400)

    async def chat(self, messages: list[dict], **kwargs) -> str:
        """
        Chat interface compatible with OpenAI-style messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional arguments (passed to _call_llm)

        Returns:
            Model response text
        """
        return self._call_llm(messages, **kwargs)

    # Contract analysis methods
    async def analyze_contract_full(self, contract_text: str) -> str:
        """Analyze a contract and return key information."""
        messages = [
            {"role": "system", "content": "You are a legal expert that analyzes contracts."},
            {"role": "user", "content": f"Analyze this contract and identify:\n1. Parties involved\n2. Key dates\n3. Payment terms\n4. Important clauses\n5. Potential risks\n\nContract:\n{contract_text[:3000]}"}
        ]
        return self._call_llm(messages)

    async def extract_contract_parties(self, contract_text: str) -> str:
        """Extract parties from a contract."""
        messages = [
            {"role": "system", "content": "You are a legal expert that extracts party information from contracts."},
            {"role": "user", "content": f"List all parties in this contract with their roles:\n\n{contract_text[:3000]}"}
        ]
        return self._call_llm(messages)

    async def identify_contract_risks(self, contract_text: str) -> str:
        """Identify risks in a contract."""
        messages = [
            {"role": "system", "content": "You are a legal expert that identifies risks in contracts."},
            {"role": "user", "content": f"Identify potential risks and red flags in this contract:\n\n{contract_text[:3000]}"}
        ]
        return self._call_llm(messages)

    # Financial analysis methods
    async def analyze_financial_report(self, report_text: str) -> str:
        """Analyze a financial report."""
        messages = [
            {"role": "system", "content": "You are a financial analyst that analyzes reports."},
            {"role": "user", "content": f"Analyze this financial report and summarize:\n1. Key financial metrics\n2. Revenue and profitability\n3. Risk factors\n4. Management outlook\n\nReport:\n{report_text[:3000]}"}
        ]
        return self._call_llm(messages)

    async def analyze_revenue(self, report_text: str) -> str:
        """Analyze revenue from a financial report."""
        messages = [
            {"role": "system", "content": "You are a financial analyst specializing in revenue analysis."},
            {"role": "user", "content": f"Extract and analyze revenue information from this report:\n\n{report_text[:3000]}"}
        ]
        return self._call_llm(messages)

    async def detect_red_flags(self, report_text: str) -> str:
        """Detect red flags in financial report."""
        messages = [
            {"role": "system", "content": "You are a financial analyst that detects red flags in reports."},
            {"role": "user", "content": f"Identify any red flags or concerns in this financial report:\n\n{report_text[:3000]}"}
        ]
        return self._call_llm(messages)


# Singleton instance
_client: Optional[LocalLLMClient] = None


def get_local_llm_client() -> LocalLLMClient:
    """Get or create local LLM client singleton."""
    global _client
    if _client is None:
        _client = LocalLLMClient()
    return _client

