"""
Vector Store
ChromaDB-based vector storage for document embeddings.
"""

import os
from typing import Optional
import chromadb
from chromadb.config import Settings

from .groq_embeddings import get_groq_embedding_service, GroqEmbeddingService


class VectorStore:
    """ChromaDB-based vector store for document chunks."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_service: Optional[GroqEmbeddingService] = None
    ):
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY",
            "./data/chroma"
        )
        self.embedding_service = embedding_service or get_groq_embedding_service()

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create the documents collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Document chunks for RAG"}
        )

    def add_document(
        self,
        document_id: str,
        chunks: list[str],
        metadata: Optional[dict] = None
    ) -> int:
        """
        Add document chunks to the vector store.

        Args:
            document_id: Unique document identifier
            chunks: List of text chunks from the document
            metadata: Optional metadata for the document

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        # Generate embeddings for all chunks
        embeddings = self.embedding_service.embed_texts(chunks)

        # Prepare data for ChromaDB
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": i,
                **(metadata or {})
            }
            for i in range(len(chunks))
        ]

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        return len(chunks)

    def search(
        self,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None
    ) -> list[dict]:
        """
        Search for similar chunks.

        Args:
            query: Search query text
            n_results: Number of results to return
            document_id: Optional filter by document ID

        Returns:
            List of matching chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Build where filter if document_id specified
        where_filter = None
        if document_id:
            where_filter = {"document_id": document_id}

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })

        return formatted_results

    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete

        Returns:
            Number of chunks deleted
        """
        # Get all chunk IDs for this document
        results = self.collection.get(
            where={"document_id": document_id},
            include=[]
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])

        return 0

    def get_document_chunks(self, document_id: str) -> list[dict]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document ID

        Returns:
            List of chunks with metadata
        """
        results = self.collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"]
        )

        chunks = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                chunks.append({
                    "content": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })

        # Sort by chunk index
        chunks.sort(key=lambda x: x["metadata"].get("chunk_index", 0))
        return chunks

    def count(self) -> int:
        """Get total number of chunks in the store."""
        return self.collection.count()


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create VectorStore singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
