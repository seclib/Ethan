"""Vrai serveur MCP (SDK officiel `mcp`) — transport stdio, tool `echo`.

Utilisé par les tests pour valider le round-trip complet MCP :
ToolServerManager.sync_tools → MCPClient (stdio) → tool découvert.
Ce n'est PAS un mock : c'est un serveur MCP conforme parlant le vrai
protocole (initialize → tools/list → tools/call) via le SDK `mcp`.
"""

from __future__ import annotations

import asyncio

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server


async def _list_tools(ctx, params) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="echo",
                description="Renvoie le message reçu",
                inputSchema={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"],
                },
            )
        ]
    )


async def _call_tool(ctx, params) -> types.CallToolResult:
    if params.name != "echo":
        raise ValueError(f"Unknown tool: {params.name}")
    message = str((params.arguments or {}).get("message", ""))
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=message)]
    )


server = Server("ethan-echo-test", on_list_tools=_list_tools, on_call_tool=_call_tool)


async def serve() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(serve())
