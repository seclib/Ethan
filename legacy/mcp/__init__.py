"""MCP (Model Context Protocol) layer for Ethan."""

from ethan.mcp.client import MCPClient
from ethan.mcp.protocol import MCPError, MCPNotification, MCPRequest, MCPResponse
from ethan.mcp.server import MCPServer
from ethan.mcp.transport import (
    InProcessTransport,
    MCPTransport,
    SSETransport,
    StdioTransport,
    StreamableHTTPTransport,
)

__all__ = [
    "MCPClient",
    "MCPError",
    "MCPNotification",
    "MCPRequest",
    "MCPResponse",
    "MCPServer",
    "MCPTransport",
    "InProcessTransport",
    "SSETransport",
    "StdioTransport",
    "StreamableHTTPTransport",
]
