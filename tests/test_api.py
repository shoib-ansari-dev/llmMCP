"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_root_endpoint(self):
        """Test the root endpoint returns healthy status."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestDocumentEndpoints:
    """Tests for document endpoints."""

    def test_list_documents_empty(self):
        """Test listing documents when none exist."""
        response = client.get("/documents")
        assert response.status_code == 200
        assert "documents" in response.json()

    def test_analyze_nonexistent_document(self):
        """Test analyzing a document that doesn't exist."""
        response = client.post("/analyze/nonexistent-id")
        assert response.status_code == 404

    def test_delete_nonexistent_document(self):
        """Test deleting a document that doesn't exist."""
        response = client.delete("/documents/nonexistent-id")
        assert response.status_code == 404


class TestAskEndpoint:
    """Tests for Q&A endpoint."""

    def test_ask_question(self):
        """Test asking a question."""
        response = client.post(
            "/ask",
            json={"question": "What is this about?"}
        )
        assert response.status_code == 200
        assert "answer" in response.json()

