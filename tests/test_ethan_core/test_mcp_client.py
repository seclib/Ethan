import pytest
from core.tools.mcp_client import MCPClient, MCP_AVAILABLE

def test_mcp_client_init():
    client = MCPClient()
    if not MCP_AVAILABLE:
        assert client.session is None
    else:
        # If it's available, session is None before connect anyway
        assert client.session is None

@pytest.mark.asyncio
async def test_mcp_client_connect_missing():
    client = MCPClient()
    if not MCP_AVAILABLE:
        with pytest.raises(RuntimeError, match="MCP package is not installed"):
            await client.connect("http://localhost:8000")
