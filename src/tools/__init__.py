"""MCP tools for document analysis."""


"""
Legacy tools module - MCP tools have moved to src/mcp/
This module is kept for backward compatibility.
"""

# Re-export from new location
from ..mcp import (
    MCPServer,
    create_mcp_server,
    analyze_pdf_tool,
    analyze_spreadsheet_tool,
    analyze_webpage_tool,
    ask_question_tool,
    get_insights_tool,
    list_documents_tool
)

__all__ = [
    "MCPServer",
    "create_mcp_server"
]
