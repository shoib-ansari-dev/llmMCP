"""
Document Retriever
Retrieves relevant context for RAG-based question answering.
"""

from typing import Optional

from .vector_store import VectorStore, get_vector_store
from ..utils import chunk_text


class DocumentRetriever:
    """Retrieves relevant document chunks for RAG."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or get_vector_store()

    def index_document(
        self,
        document_id: str,
        content: str,
        doc_type: str = "document",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Index a document for retrieval.

        Args:
            document_id: Unique document identifier
            content: Full document text
            doc_type: Type of document (pdf, spreadsheet, webpage)
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
            metadata: Additional metadata

        Returns:
            Number of chunks indexed
        """
        # Chunk the document
        chunks = chunk_text(content, chunk_size=chunk_size, overlap=chunk_overlap)

        # Prepare metadata
        doc_metadata = {
            "doc_type": doc_type,
            **(metadata or {})
        }

        # Add to vector store
        return self.vector_store.add_document(document_id, chunks, doc_metadata)

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None
    ) -> list[dict]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Search query
            n_results: Number of results to return
            document_id: Optional filter by document ID

        Returns:
            List of relevant chunks with metadata
        """
        return self.vector_store.search(query, n_results, document_id)

    def get_context(
        self,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None,
        max_context_length: int = 8000
    ) -> str:
        """
        Get formatted context string for LLM.

        Args:
            query: Search query
            n_results: Number of chunks to retrieve
            document_id: Optional filter by document ID
            max_context_length: Maximum context length in characters

        Returns:
            Formatted context string
        """
        results = self.retrieve(query, n_results, document_id)

        if not results:
            return ""

        context_parts = []
        total_length = 0

        for result in results:
            chunk = result["content"]
            chunk_length = len(chunk)

            if total_length + chunk_length > max_context_length:
                # Truncate if needed
                remaining = max_context_length - total_length
                if remaining > 100:
                    context_parts.append(chunk[:remaining] + "...")
                break

            context_parts.append(chunk)
            total_length += chunk_length

        return "\n\n---\n\n".join(context_parts)

    def delete_document(self, document_id: str) -> int:
        """
        Remove a document from the index.

        Args:
            document_id: Document ID to remove

        Returns:
            Number of chunks removed
        """
        return self.vector_store.delete_document(document_id)

    def get_indexed_chunks_count(self, document_id: str) -> int:
        """
        Get number of indexed chunks for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of chunks
        """
        chunks = self.vector_store.get_document_chunks(document_id)
        return len(chunks)


# Singleton instance
_retriever: Optional[DocumentRetriever] = None


def get_retriever() -> DocumentRetriever:
    """Get or create DocumentRetriever singleton."""
    global _retriever
    if _retriever is None:
        _retriever = DocumentRetriever()
    return _retriever

