"""
MCP Tool Definitions
Individual tools for document analysis operations.
"""

from typing import Any, Optional
from dataclasses import dataclass
import json


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    parameters: dict
    handler: callable

    def to_schema(self) -> dict:
        """Convert to MCP tool schema format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
                "required": [k for k, v in self.parameters.items() if v.get("required", False)]
            }
        }


# Tool: Analyze PDF
async def _analyze_pdf_handler(file_path: str = None, document_id: str = None, **kwargs) -> ToolResult:
    """Handler for analyze_pdf tool."""
    from ..agents import get_document_agent

    try:
        agent = get_document_agent()

        if file_path:
            result = await agent.analyze_pdf(file_path=file_path, document_id=document_id)
        else:
            return ToolResult(
                success=False,
                data=None,
                error="file_path is required"
            )

        return ToolResult(
            success=True,
            data={
                "document_id": result.document_id,
                "summary": result.summary,
                "insights": result.key_insights,
                "metadata": result.metadata
            }
        )
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


analyze_pdf_tool = ToolDefinition(
    name="analyze_pdf",
    description="Analyze a PDF document and extract summary and insights",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the PDF file to analyze",
            "required": True
        },
        "document_id": {
            "type": "string",
            "description": "Optional unique identifier for the document",
            "required": False
        }
    },
    handler=_analyze_pdf_handler
)


# Tool: Analyze Spreadsheet
async def _analyze_spreadsheet_handler(file_path: str, document_id: str = None, **kwargs) -> ToolResult:
    """Handler for analyze_spreadsheet tool."""
    from ..agents import get_document_agent

    try:
        agent = get_document_agent()
        result = await agent.analyze_spreadsheet(file_path=file_path, document_id=document_id)

        return ToolResult(
            success=True,
            data={
                "document_id": result.document_id,
                "summary": result.summary,
                "insights": result.key_insights,
                "metadata": result.metadata
            }
        )
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


analyze_spreadsheet_tool = ToolDefinition(
    name="analyze_spreadsheet",
    description="Analyze an Excel or CSV spreadsheet and extract summary and insights",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the spreadsheet file (xlsx, xls, or csv)",
            "required": True
        },
        "document_id": {
            "type": "string",
            "description": "Optional unique identifier for the document",
            "required": False
        }
    },
    handler=_analyze_spreadsheet_handler
)


# Tool: Analyze Webpage
async def _analyze_webpage_handler(url: str, document_id: str = None, **kwargs) -> ToolResult:
    """Handler for analyze_webpage tool."""
    from ..agents import get_document_agent

    try:
        agent = get_document_agent()
        result = await agent.analyze_webpage(url=url, document_id=document_id)

        return ToolResult(
            success=True,
            data={
                "document_id": result.document_id,
                "summary": result.summary,
                "insights": result.key_insights,
                "metadata": result.metadata
            }
        )
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


analyze_webpage_tool = ToolDefinition(
    name="analyze_webpage",
    description="Fetch and analyze content from a web page URL",
    parameters={
        "url": {
            "type": "string",
            "description": "URL of the web page to analyze",
            "required": True
        },
        "document_id": {
            "type": "string",
            "description": "Optional unique identifier for the document",
            "required": False
        }
    },
    handler=_analyze_webpage_handler
)


# Tool: Ask Question
async def _ask_question_handler(question: str, document_id: str = None, **kwargs) -> ToolResult:
    """Handler for ask_question tool."""
    from ..agents import get_document_agent

    try:
        agent = get_document_agent()
        result = await agent.ask_question(question=question, document_id=document_id)

        return ToolResult(
            success=True,
            data={
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"]
            }
        )
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


ask_question_tool = ToolDefinition(
    name="ask_question",
    description="Ask a question about uploaded documents using RAG",
    parameters={
        "question": {
            "type": "string",
            "description": "The question to ask about the documents",
            "required": True
        },
        "document_id": {
            "type": "string",
            "description": "Optional document ID to scope the question to a specific document",
            "required": False
        }
    },
    handler=_ask_question_handler
)


# Tool: Get Insights
async def _get_insights_handler(document_id: str, **kwargs) -> ToolResult:
    """Handler for get_insights tool."""
    from ..agents import get_document_agent

    try:
        agent = get_document_agent()
        insights = await agent.get_insights(document_id=document_id)

        return ToolResult(
            success=True,
            data={
                "document_id": document_id,
                "insights": insights
            }
        )
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


get_insights_tool = ToolDefinition(
    name="get_insights",
    description="Extract key insights from a previously analyzed document",
    parameters={
        "document_id": {
            "type": "string",
            "description": "ID of the document to extract insights from",
            "required": True
        }
    },
    handler=_get_insights_handler
)


# Tool: List Documents
async def _list_documents_handler(**kwargs) -> ToolResult:
    """Handler for list_documents tool."""
    from ..agents import get_document_agent

    try:
        agent = get_document_agent()
        documents = [
            {
                "document_id": doc_id,
                "doc_type": doc.get("doc_type", "unknown"),
                "metadata": doc.get("metadata", {})
            }
            for doc_id, doc in agent.documents.items()
        ]

        return ToolResult(
            success=True,
            data={
                "count": len(documents),
                "documents": documents
            }
        )
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


list_documents_tool = ToolDefinition(
    name="list_documents",
    description="List all documents that have been analyzed",
    parameters={},
    handler=_list_documents_handler
)


# Registry of all tools
ALL_TOOLS = [
    analyze_pdf_tool,
    analyze_spreadsheet_tool,
    analyze_webpage_tool,
    ask_question_tool,
    get_insights_tool,
    list_documents_tool
]


def get_tool_by_name(name: str) -> Optional[ToolDefinition]:
    """Get a tool definition by name."""
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None

