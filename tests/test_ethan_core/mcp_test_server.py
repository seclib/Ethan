"""MCP test server for testing ETHAN Core MCP client."""

from __future__ import annotations

import asyncio

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)


async def handle_list_tools() -> ListToolsResult:
    """Handle list_tools request."""
    return ListToolsResult(
        tools=[
            Tool(
                name="echo",
                description="Echo tool",
                inputSchema={},
            )
        ]
    )


async def handle_call_tool(
    context, params: CallToolRequestParams
) -> CallToolResult:
    """Handle call_tool request."""
    if params.name == "echo":
        text = (params.arguments or {}).get("text", "")
        return CallToolResult(content=[TextContent(text=f"echo: {text}")])
    return CallToolResult(content=[])


async def main():
    async with stdio_server() as (read_stream, write_stream):
        async with Server(read_stream, write_stream) as server:
            server.add_request_handler("list_tools", handle_list_tools)
            server.add_request_handler("call_tool", handle_call_tool)
            await server.run()  # type: ignore


if __name__ == "__main__":
    asyncio.run(main())
