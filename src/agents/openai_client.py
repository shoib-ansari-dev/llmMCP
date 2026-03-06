"""
OpenAI Client
Handles all interactions with the OpenAI API.
"""

import os
from openai import OpenAI
from typing import Optional


class OpenAIClient:
    """Client for interacting with OpenAI API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"

    async def summarize(self, content: str, doc_type: str = "document") -> str:
        """
        Generate a summary of the document content.

        Args:
            content: The document text to summarize
            doc_type: Type of document (pdf, spreadsheet, webpage)

        Returns:
            Summary string
        """
        prompt = f"""Analyze the following {doc_type} content and provide a clear, concise summary.
Focus on the main points, key information, and important details.

Content:
{content[:50000]}

Provide a well-structured summary:"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    async def extract_insights(self, content: str) -> list[str]:
        """
        Extract key insights from the document.

        Args:
            content: The document text

        Returns:
            List of insight strings
        """
        prompt = f"""Analyze the following content and extract 3-5 key insights.
Each insight should be a concise, actionable observation.

Content:
{content[:50000]}

Return the insights as a numbered list (1., 2., 3., etc.):"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse numbered list into array
        response_text = response.choices[0].message.content
        insights = []
        for line in response_text.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering/bullets
                cleaned = line.lstrip('0123456789.-) ').strip()
                if cleaned:
                    insights.append(cleaned)

        return insights if insights else [response_text]

    async def answer_question(self, question: str, context: str) -> str:
        """
        Answer a question based on document context.

        Args:
            question: The user's question
            context: Relevant document content

        Returns:
            Answer string
        """
        prompt = f"""Based on the following document content, answer the user's question.
If the answer cannot be found in the content, say so clearly.

Document Content:
{context[:50000]}

Question: {question}

Answer:"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    async def analyze_document(self, content: str, doc_type: str = "document") -> dict:
        """
        Perform full document analysis: summary + insights.

        Args:
            content: The document text
            doc_type: Type of document

        Returns:
            Dict with summary and insights
        """
        prompt = f"""Analyze the following {doc_type} content thoroughly.

Content:
{content[:50000]}

Provide your analysis in the following format:

SUMMARY:
[Write a clear, comprehensive summary of the document]

KEY INSIGHTS:
1. [First key insight]
2. [Second key insight]
3. [Third key insight]
4. [Fourth key insight if applicable]
5. [Fifth key insight if applicable]"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = response.choices[0].message.content

        # Parse response
        summary = ""
        insights = []

        if "SUMMARY:" in response_text and "KEY INSIGHTS:" in response_text:
            parts = response_text.split("KEY INSIGHTS:")
            summary = parts[0].replace("SUMMARY:", "").strip()

            insights_text = parts[1] if len(parts) > 1 else ""
            for line in insights_text.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    cleaned = line.lstrip('0123456789.-) ').strip()
                    if cleaned:
                        insights.append(cleaned)
        else:
            summary = response_text

        return {
            "summary": summary,
            "insights": insights
        }


# Singleton instance
_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """Get or create OpenAI client singleton."""
    global _client
    if _client is None:
        _client = OpenAIClient()
    return _client

