"""
Document Analysis Agent
Orchestrates document parsing, summarization, and Q&A.
"""

from dataclasses import dataclass
from typing import Optional, Any
from .local_llm_client import get_local_llm_client
from ..parsers import PDFParser, SpreadsheetParser, WebPageParser
from ..utils import chunk_text
from ..rag import get_retriever, DocumentRetriever


@dataclass
class AnalysisResult:
    """Result of document analysis."""
    document_id: str
    summary: str
    key_insights: list[str]
    metadata: dict


class DocumentAgent:
    """Agent for analyzing documents and extracting insights."""

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        retriever: Optional[DocumentRetriever] = None
    ):
        self.llm = llm_client or get_local_llm_client()
        self.retriever = retriever or get_retriever()
        self.pdf_parser = PDFParser()
        self.spreadsheet_parser = SpreadsheetParser()
        self.web_parser = WebPageParser()

        # In-memory storage for document content (replace with DB in production)
        self.documents: dict[str, dict] = {}

    def store_document(self, document_id: str, content: str, doc_type: str, metadata: dict = None):
        """Store document content and index for RAG retrieval."""
        self.documents[document_id] = {
            "content": content,
            "doc_type": doc_type,
            "metadata": metadata or {}
        }

        # Index in vector store for RAG
        self.retriever.index_document(
            document_id=document_id,
            content=content,
            doc_type=doc_type,
            metadata=metadata
        )

    def get_document(self, document_id: str) -> Optional[dict]:
        """Retrieve stored document."""
        return self.documents.get(document_id)

    async def analyze_pdf(self, file_path: str = None, file_bytes: bytes = None, document_id: str = None) -> AnalysisResult:
        """Analyze a PDF document."""
        if file_bytes:
            pdf_content = self.pdf_parser.parse_bytes(file_bytes)
        else:
            pdf_content = self.pdf_parser.parse(file_path)

        content = pdf_content.text

        # Store for Q&A
        if document_id:
            self.store_document(document_id, content, "pdf", pdf_content.metadata)

        # Analyze with Claude
        result = await self.llm.analyze_document(content, "PDF document")

        return AnalysisResult(
            document_id=document_id or "temp",
            summary=result["summary"],
            key_insights=result["insights"],
            metadata=pdf_content.metadata
        )

    async def analyze_spreadsheet(self, file_path: str, document_id: str = None) -> AnalysisResult:
        """Analyze a spreadsheet."""
        spreadsheet_content = self.spreadsheet_parser.parse(file_path)
        content = self.spreadsheet_parser.to_text(spreadsheet_content)

        # Store for Q&A
        if document_id:
            self.store_document(document_id, content, "spreadsheet", {
                "sheet_names": spreadsheet_content.sheet_names,
                "row_count": spreadsheet_content.row_count
            })

        # Analyze with Claude
        result = await self.llm.analyze_document(content, "spreadsheet")

        return AnalysisResult(
            document_id=document_id or "temp",
            summary=result["summary"],
            key_insights=result["insights"],
            metadata={
                "sheet_names": spreadsheet_content.sheet_names,
                "row_count": spreadsheet_content.row_count,
                "column_count": spreadsheet_content.column_count
            }
        )

    async def analyze_webpage(self, url: str, document_id: str = None) -> AnalysisResult:
        """Analyze a web page."""
        web_content = self.web_parser.parse(url)
        content = f"Title: {web_content.title}\n\n{web_content.text}"

        # Store for Q&A
        if document_id:
            self.store_document(document_id, content, "webpage", web_content.metadata)

        # Analyze with Claude
        result = await self.llm.analyze_document(content, "web page")

        return AnalysisResult(
            document_id=document_id or "temp",
            summary=result["summary"],
            key_insights=result["insights"],
            metadata=web_content.metadata
        )

    async def summarize(self, document_id: str) -> str:
        """Generate a summary for a stored document."""
        doc = self.get_document(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        return await self.llm.summarize(doc["content"], doc["doc_type"])

    async def ask_question(self, question: str, document_id: str = None) -> dict:
        """Answer a question about documents using RAG."""
        # Use RAG to retrieve relevant context
        context = self.retriever.get_context(
            query=question,
            n_results=5,
            document_id=document_id,
            max_context_length=8000
        )

        if not context:
            # Fallback to in-memory documents if vector store is empty
            if document_id:
                doc = self.get_document(document_id)
                if doc:
                    context = doc["content"][:8000]
            else:
                all_content = []
                for doc_id, doc in self.documents.items():
                    all_content.append(f"[Document: {doc_id}]\n{doc['content'][:4000]}")
                context = "\n\n---\n\n".join(all_content)

        if not context:
            return {
                "answer": "No documents have been uploaded yet. Please upload a document first.",
                "sources": []
            }

        answer = await self.llm.answer_question(question, context)

        # Get source documents from retrieval
        results = self.retriever.retrieve(question, n_results=3, document_id=document_id)
        sources = list(set(r["metadata"].get("document_id", "") for r in results if r.get("metadata")))

        return {
            "answer": answer,
            "sources": sources if sources else ([document_id] if document_id else list(self.documents.keys()))
        }

    async def get_insights(self, document_id: str) -> list[str]:
        """Extract key insights from a document."""
        doc = self.get_document(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        return await self.llm.extract_insights(doc["content"])


# Singleton instance
_agent: Optional[DocumentAgent] = None


def get_document_agent() -> DocumentAgent:
    """Get or create DocumentAgent singleton."""
    global _agent
    if _agent is None:
        _agent = DocumentAgent()
    return _agent

