"""
Groq Embedding Service
Since Groq doesn't have embeddings API, we use a simple TF-IDF based approach
or fall back to sentence-transformers for local embeddings.
"""

import os
import hashlib
from typing import Optional
import numpy as np


class GroqEmbeddingService:
    """
    Embedding service for use with Groq.
    Uses local sentence-transformers model since Groq doesn't provide embeddings.
    Falls back to simple hash-based embeddings if sentence-transformers not available.
    """

    def __init__(self):
        self.model = None
        self.dimensions = 384  # Default for all-MiniLM-L6-v2
        self._try_load_model()

    def _try_load_model(self):
        """Try to load sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.dimensions = 384
        except ImportError:
            # Fallback to simple hash-based embeddings
            self.model = None
            self.dimensions = 256

    def _hash_embedding(self, text: str) -> list[float]:
        """Generate a simple hash-based embedding (fallback method)."""
        # Create multiple hashes for different aspects of the text
        embeddings = []

        # Normalize text
        text = text.lower().strip()

        for i in range(self.dimensions):
            # Create different hash seeds
            seed = f"{i}_{text}"
            hash_val = int(hashlib.md5(seed.encode()).hexdigest(), 16)
            # Normalize to [-1, 1]
            normalized = (hash_val % 10000) / 5000 - 1
            embeddings.append(normalized)

        # Normalize the vector
        norm = np.linalg.norm(embeddings)
        if norm > 0:
            embeddings = [e / norm for e in embeddings]

        return embeddings

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if self.model is not None:
            embedding = self.model.encode(text)
            return embedding.tolist()
        else:
            return self._hash_embedding(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        if self.model is not None:
            embeddings = self.model.encode(texts)
            return [emb.tolist() for emb in embeddings]
        else:
            return [self._hash_embedding(text) for text in texts]


# Singleton instance
_embedding_service: Optional[GroqEmbeddingService] = None


def get_groq_embedding_service() -> GroqEmbeddingService:
    """Get or create GroqEmbeddingService singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = GroqEmbeddingService()
    return _embedding_service

