"""
Grok Client (xAI)
Handles all interactions with the xAI Grok API (OpenAI-compatible).
Uses OPENAI_API_KEY environment variable for the xAI API key.
"""

import os
from openai import OpenAI
from typing import Optional

from .prompts import (
    get_summary_prompt,
    get_insights_prompt,
    get_qa_prompt,
    get_analysis_prompt,
    get_improved_summary_prompt
)


class GroqClient:
    """Client for interacting with xAI Grok API (OpenAI-compatible)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # xAI Grok uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-2-latest"

    async def summarize(self, content: str, doc_type: str = "document") -> str:
        """
        Generate a summary of the document content.

        Args:
            content: The document text to summarize
            doc_type: Type of document (pdf, spreadsheet, webpage)

        Returns:
            Summary string
        """
        prompts = get_summary_prompt(content, doc_type)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"]}
            ]
        )

        return response.choices[0].message.content

    async def extract_insights(self, content: str, doc_type: str = "document") -> list[str]:
        """
        Extract key insights from the document.

        Args:
            content: The document text
            doc_type: Type of document

        Returns:
            List of insight strings
        """
        prompts = get_insights_prompt(content, doc_type)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"]}
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
        prompts = get_qa_prompt(question, context)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"]}
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
        prompts = get_analysis_prompt(content, doc_type)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2500,
            messages=[
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"]}
            ]
        )

        response_text = response.choices[0].message.content

        # Parse response into summary and insights
        summary = response_text
        insights = []

        # Try to extract Key Findings section
        if "## Key Findings" in response_text:
            parts = response_text.split("## Key Findings")
            summary_part = parts[0]
            findings_part = parts[1] if len(parts) > 1 else ""

            # Clean up summary
            summary = summary_part.replace("## Document Overview", "").replace("## Executive Summary", "").strip()

            # Extract insights from findings
            for line in findings_part.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    cleaned = line.lstrip("0123456789.-) ").strip()
                    if cleaned:
                        insights.append(cleaned)

        return {
            "summary": summary,
            "insights": insights[:5]  # Limit to 5 insights
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
        prompts = get_improved_summary_prompt(content, doc_type, previous_summary, feedback)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"]}
            ]
        )

        return response.choices[0].message.content


# Singleton instance
_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Get or create Groq client singleton."""
    global _client
    if _client is None:
        _client = GroqClient()
    return _client

