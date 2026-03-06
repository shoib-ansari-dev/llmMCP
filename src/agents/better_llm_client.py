"""
Better LLM Client with Model Selection
Uses larger, better-quality models for improved responses
"""

import os
import logging
from typing import Optional
from openai import OpenAI


logger = logging.getLogger(__name__)

# Available models (ranked by quality)
AVAILABLE_MODELS = {
    "neural-chat-7b": {
        "url": "http://localhost:8000/v1",  # ollama default
        "description": "7B params, optimized for chat, better quality"
    },
    "mistral-7b": {
        "url": "http://localhost:8000/v1",
        "description": "7B params, fast and accurate"
    },
    "llama2-13b": {
        "url": "http://localhost:8000/v1",
        "description": "13B params, higher quality but slower"
    },
    "smollm2-360m": {
        "url": "http://localhost:12434/engines/v1",
        "description": "360M params, CPU-friendly but lower quality"
    }
}

# Default model selection (ordered by preference)
DEFAULT_MODELS = [
    "neural-chat-7b",
    "mistral-7b",
    "llama2-13b",
    "smollm2-360m"  # Fallback
]


class BetterLLMClient:
    """LLM Client with intelligent model selection and quality checks."""

    def __init__(self, model: str = None, base_url: str = None):
        """
        Initialize with model selection.

        Args:
            model: Specific model to use
            base_url: Base URL override
        """
        self.model = model or os.getenv("LLM_MODEL", "mistral-7b")
        self.base_url = base_url or os.getenv("LOCAL_LLM_URL")

        # If no base URL, try to determine from model
        if not self.base_url:
            if self.model in AVAILABLE_MODELS:
                self.base_url = AVAILABLE_MODELS[self.model]["url"]
            else:
                self.base_url = "http://localhost:8000/v1"  # Default ollama

        self.client = OpenAI(base_url=self.base_url, api_key="not-needed")
        logger.info(f"Initialized BetterLLMClient with model: {self.model} at {self.base_url}")

    def _is_quality_response(self, text: str) -> bool:
        """Check if response meets quality standards."""
        if not text:
            return False

        # Too short
        if len(text) < 10:
            return False

        # Check for repetition (bad sign)
        lines = text.split('\n')
        if len(lines) > 1:
            # If first line appears again too soon, it's likely bad
            if lines[0] in '\n'.join(lines[1:5]):
                return False

        # Check for excessive repetition of single phrase
        words = text.split()
        if len(words) > 0:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            # If any word appears more than 20% of the time, likely bad
            for count in word_counts.values():
                if count / len(words) > 0.2:
                    return False

        return True

    def _call_llm(self, messages: list[dict], max_tokens: int = 1500, temperature: float = 0.3) -> str:
        """Call LLM with quality checks."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            result = response.choices[0].message.content.strip()

            # Quality check
            if not self._is_quality_response(result):
                logger.warning(f"Low quality response detected from {self.model}")
                return "I'm having trouble generating a proper response. Please try rephrasing your question or uploading a clearer document."

            return result

        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"Error: Unable to process your request: {str(e)}"

    async def answer_question(self, question: str, context: str) -> str:
        """Answer question with quality context."""
        context = context[:3000].strip()  # Give model more context
        question = question.strip()

        if not context:
            return "No relevant context found. Please upload a document first."

        # More explicit instructions for small models
        messages = [
            {
                "role": "system",
                "content": "Answer the question using ONLY the provided document. Be concise, direct, and accurate. Do not make up information."
            },
            {
                "role": "user",
                "content": f"""DOCUMENT:
{context}

QUESTION: {question}

Answer this question based on the document above:"""
            }
        ]
        return self._call_llm(messages, max_tokens=500, temperature=0.2)  # Lower temp for Q&A

    async def summarize(self, content: str, doc_type: str = "document") -> str:
        """Summarize with clear instructions."""
        content = content[:3000].strip()

        messages = [
            {
                "role": "system",
                "content": f"Summarize the {doc_type} in 3-5 sentences. Focus on main points."
            },
            {
                "role": "user",
                "content": f"Summarize this {doc_type}:\n\n{content}"
            }
        ]
        return self._call_llm(messages, max_tokens=300, temperature=0.3)

    async def extract_insights(self, content: str, doc_type: str = "document") -> list[str]:
        """Extract insights with structured output."""
        content = content[:3000].strip()

        messages = [
            {
                "role": "system",
                "content": "Extract 3-5 key insights. Return as numbered list only."
            },
            {
                "role": "user",
                "content": f"Extract key insights from this {doc_type}:\n\n{content}\n\nKey insights (numbered list):"
            }
        ]
        response = self._call_llm(messages, max_tokens=400, temperature=0.3)

        # Parse
        insights = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                cleaned = line.lstrip('0123456789.-) ').strip()
                if cleaned and len(cleaned) > 10:
                    insights.append(cleaned)

        return insights

    async def analyze_document(self, content: str, doc_type: str = "document") -> dict:
        """Full analysis."""
        content = content[:3000].strip()

        messages = [
            {
                "role": "system",
                "content": f"Analyze the {doc_type}. Provide summary and key findings."
            },
            {
                "role": "user",
                "content": f"Analyze this {doc_type}:\n\n{content}\n\nProvide summary and key findings:"
            }
        ]
        response = self._call_llm(messages, max_tokens=400, temperature=0.3)

        insights = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                cleaned = line.lstrip('0123456789.-) ').strip()
                if cleaned and len(cleaned) > 10:
                    insights.append(cleaned)

        return {"summary": response, "insights": insights[:5]}


# For compatibility with existing code
class LocalLLMClient(BetterLLMClient):
    """Alias for backward compatibility."""
    pass


_client: Optional[LocalLLMClient] = None


def get_local_llm_client() -> LocalLLMClient:
    """Get or create singleton."""
    global _client
    if _client is None:
        _client = LocalLLMClient()
    return _client

