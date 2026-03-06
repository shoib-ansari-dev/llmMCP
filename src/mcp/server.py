"""
MCP Server
Model Context Protocol server for document analysis.
"""

import json
import asyncio
from typing import Any, Optional
from dataclasses import dataclass

from .tools import (
    ALL_TOOLS,
    get_tool_by_name,
    ToolResult,
    ToolDefinition
)


@dataclass
class MCPRequest:
    """Incoming MCP request."""
    method: str
    params: dict
    id: Optional[str] = None


@dataclass
class MCPResponse:
    """Outgoing MCP response."""
    result: Any
    error: Optional[dict] = None
    id: Optional[str] = None

    def to_dict(self) -> dict:
        response = {"jsonrpc": "2.0", "id": self.id}
        if self.error:
            response["error"] = self.error
        else:
            response["result"] = self.result
        return response


class MCPServer:
    """
    MCP Server for document analysis tools.

    Implements the Model Context Protocol for tool orchestration.
    """

    def __init__(self):
        self.tools = {tool.name: tool for tool in ALL_TOOLS}
        self.server_info = {
            "name": "document-analysis-agent",
            "version": "1.0.0",
            "description": "AI-powered document analysis with RAG capabilities"
        }

    def list_tools(self) -> list[dict]:
        """List all available tools in MCP format."""
        return [tool.to_schema() for tool in self.tools.values()]

    async def call_tool(self, name: str, arguments: dict) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            name: Tool name to execute
            arguments: Tool arguments

        Returns:
            ToolResult with success status and data
        """
        tool = self.tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{name}' not found"
            )

        try:
            result = await tool.handler(**arguments)
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """
        Handle an incoming MCP request.

        Args:
            request: The MCP request to handle

        Returns:
            MCPResponse with result or error
        """
        method = request.method
        params = request.params or {}

        try:
            if method == "initialize":
                return MCPResponse(
                    result={
                        "protocolVersion": "2024-11-05",
                        "serverInfo": self.server_info,
                        "capabilities": {
                            "tools": {"listChanged": False}
                        }
                    },
                    id=request.id
                )

            elif method == "tools/list":
                return MCPResponse(
                    result={"tools": self.list_tools()},
                    id=request.id
                )

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                result = await self.call_tool(tool_name, arguments)

                if result.success:
                    return MCPResponse(
                        result={
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result.data, indent=2)
                                }
                            ]
                        },
                        id=request.id
                    )
                else:
                    return MCPResponse(
                        result=None,
                        error={
                            "code": -32000,
                            "message": result.error or "Tool execution failed"
                        },
                        id=request.id
                    )

            else:
                return MCPResponse(
                    result=None,
                    error={
                        "code": -32601,
                        "message": f"Method '{method}' not found"
                    },
                    id=request.id
                )

        except Exception as e:
            return MCPResponse(
                result=None,
                error={
                    "code": -32603,
                    "message": str(e)
                },
                id=request.id
            )

    async def handle_json(self, json_str: str) -> str:
        """
        Handle a JSON-RPC request string.

        Args:
            json_str: JSON-RPC request as string

        Returns:
            JSON-RPC response as string
        """
        try:
            data = json.loads(json_str)
            request = MCPRequest(
                method=data.get("method", ""),
                params=data.get("params", {}),
                id=data.get("id")
            )
            response = await self.handle_request(request)
            return json.dumps(response.to_dict())
        except json.JSONDecodeError as e:
            return json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}"
                },
                "id": None
            })

    async def run_stdio(self):
        """
        Run the MCP server using stdio transport.

        Reads JSON-RPC requests from stdin and writes responses to stdout.
        """
        import sys

        while True:
            try:
                # Read line from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                # Handle request
                response = await self.handle_json(line)

                # Write response to stdout
                sys.stdout.write(response + "\n")
                sys.stdout.flush()

            except Exception as e:
                error_response = json.dumps({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    },
                    "id": None
                })
                sys.stdout.write(error_response + "\n")
                sys.stdout.flush()


# Singleton instance
_mcp_server: Optional[MCPServer] = None


def create_mcp_server() -> MCPServer:
    """Create or get MCP server singleton."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


# Entry point for running MCP server
if __name__ == "__main__":
    server = create_mcp_server()
    asyncio.run(server.run_stdio())

