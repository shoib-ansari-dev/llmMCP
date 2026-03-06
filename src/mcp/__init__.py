"""MCP (Model Context Protocol) module for document analysis tools."""

from .server import MCPServer, create_mcp_server
from .tools import (
    analyze_pdf_tool,
    analyze_spreadsheet_tool,
    analyze_webpage_tool,
    ask_question_tool,
    get_insights_tool,
    list_documents_tool
)

__all__ = [
    "MCPServer",
    "create_mcp_server",
    "analyze_pdf_tool",
    "analyze_spreadsheet_tool",
    "analyze_webpage_tool",
    "ask_question_tool",
    "get_insights_tool",
    "list_documents_tool"
]

