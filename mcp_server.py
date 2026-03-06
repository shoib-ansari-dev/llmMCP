#!/usr/bin/env python
"""
MCP Server Runner
Run the document analysis MCP server.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.mcp import create_mcp_server


def main():
    """Run the MCP server."""
    server = create_mcp_server()

    print("Document Analysis MCP Server", file=sys.stderr)
    print("Tools available:", file=sys.stderr)
    for tool in server.list_tools():
        print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)
    print("\nReady for connections...", file=sys.stderr)

    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()

