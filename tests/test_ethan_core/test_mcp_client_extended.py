"""Tests étendus pour le client MCP — stdio, token storage, executor MCP."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from core.tools.executor import ToolExecutor
from core.tools.mcp_client import InMemoryTokenStorage, MCPClient
from core.tools.servers import ToolServerManager
from core.tools.types import Tool, ToolContext


def _mcp_tool():
    return Tool(
        id="test-echo",
        name="echo",
        description="Echo tool",
        parameters={},
        provider="mcp",
        category="mcp",
        is_available=True,
        tags=["mcp"],
        metadata={
            "mcp_server_url": "stdio://test-echo",
            "mcp_transport": "stdio",
            "mcp_command": sys.executable,
            "mcp_args": [str(Path(__file__).parent / "mcp_test_server.py")],
        },
    )


class FakeMCPClient:
    """Fake MCPClient for testing executor."""

    def __init__(self):
        self.session = MagicMock()

    async def connect(self, *args, **kwargs):
        return None

    async def list_tool_specs(self):
        return []

    async def call_tool(self, function_name, function_args):
        return [
            {"type": "text", "text": f"echo: {function_args.get('text', '')}"}
        ]

    async def disconnect(self):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.disconnect()


class TestMCPClientInit:
    def test_init(self):
        client = MCPClient()
        assert client.session is None


class TestInMemoryTokenStorage:
    @pytest.mark.asyncio
    async def test_save_get_tokens(self):
        storage = InMemoryTokenStorage()
        tokens = {"access_token": "abc", "refresh_token": "def"}
        await storage.save_tokens("http://localhost", tokens)
        result = await storage.get_tokens("http://localhost")
        assert result == tokens

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self):
        storage = InMemoryTokenStorage()
        result = await storage.get_tokens("http://localhost")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_tokens(self):
        storage = InMemoryTokenStorage()
        tokens = {"access_token": "abc"}
        await storage.save_tokens("http://localhost", tokens)
        await storage.delete_tokens("http://localhost")
        result = await storage.get_tokens("http://localhost")
        assert result is None


class TestToolServerManager:
    @pytest.mark.asyncio
    async def test_register(self):
        manager = ToolServerManager()
        server = await manager.register(
            name="test-server",
            url="http://localhost:8080",
            description="Test server",
        )
        assert server["name"] == "test-server"
        assert server["url"] == "http://localhost:8080"
        assert server["status"] == "disconnected"


class TestToolExecutorMCP:
    @pytest.mark.asyncio
    async def test_execute_mcp_tool_returns_failed_no_url(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that executing an MCP tool without a URL fails."""
        executor = ToolExecutor()
        tool = Tool(
            id="test-echo-no-url",
            name="echo",
            description="Echo tool",
            parameters={},
            provider="mcp",
            category="mcp",
            is_available=True,
            tags=["mcp"],
        )
        result = await executor.execute(
            tool, {"text": "hello"}, ToolContext(query="echo")
        )
        assert result.status == "failed"

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_mock_connection(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that executing an MCP tool with mock connection returns success."""
        executor = ToolExecutor()
        tool = _mcp_tool()
        # Monkeypatch MCPClient to use our fake
        monkeypatch.setattr(
            "core.tools.mcp_client.MCPClient", FakeMCPClient
        )
        result = await executor.execute(
            tool, {"text": "hello"}, ToolContext(query="echo")
        )
        assert result.status == "success"
        assert result.output == [{"type": "text", "text": "echo: hello"}]
