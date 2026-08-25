"""Core-owned tool server management — external MCP/tool servers.

ETHAN Core owns tool server registration and lifecycle.  The WebUI only
renders the server list and sends enable/disable actions through the API.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore
from core.tools.mcp_client import MCP_AVAILABLE, MCPClient

logger = logging.getLogger(__name__)


class ToolServerManager:
    """Own external tool server registration and lifecycle."""

    _DOMAIN = "tool-servers"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
        registry: Any | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()
        self._registry = registry  # Optional ToolRegistry for MCP tools

    async def register(
        self,
        name: str,
        url: str,
        description: str = "",
        auth_type: str = "none",
        auth_config: dict[str, Any] | None = None,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a new tool server."""
        server = {
            "id": str(uuid4()),
            "name": name.strip(),
            "url": url,
            "description": description,
            "auth_type": auth_type,
            "auth_config": dict(auth_config or {}),
            "enabled": enabled,
            "status": "disconnected",
            "last_connected_at": None,
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, server["id"], server)
        await self._publish(
            EventType.TOOL_SERVER_REGISTERED,
            "tool.server.registered",
            {"server": server},
        )
        return server

    async def get(self, server_id: str) -> dict[str, Any] | None:
        """Retrieve a tool server by id."""
        return await self._store.get(self._DOMAIN, server_id)

    async def list(self, enabled: bool | None = None) -> list[dict[str, Any]]:
        """List tool servers, optionally filtered by enabled state."""
        servers = await self._store.list(self._DOMAIN)
        if enabled is not None:
            servers = [s for s in servers if s.get("enabled") == enabled]
        return servers

    async def update(
        self, server_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a tool server."""
        server = await self.get(server_id)
        if server is None:
            return None
        for key in (
            "name",
            "url",
            "description",
            "auth_type",
            "auth_config",
            "enabled",
            "metadata",
        ):
            if key in data:
                server[key] = data[key]
        server["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, server_id, server)
        await self._publish(
            EventType.TOOL_SERVER_UPDATED,
            "tool.server.updated",
            {"server_id": server_id},
        )
        return server

    async def delete(self, server_id: str) -> bool:
        """Delete a tool server."""
        existed = await self._store.delete(self._DOMAIN, server_id)
        if existed:
            self._remove_registered_tools(server_id)
            await self._publish(
                EventType.TOOL_SERVER_DELETED,
                "tool.server.deleted",
                {"server_id": server_id},
            )
        return existed

    async def set_status(self, server_id: str, status: str) -> dict[str, Any] | None:
        """Update a tool server's connection status."""
        server = await self.get(server_id)
        if server is None:
            return None
        server["status"] = status
        server["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, server_id, server)
        return server

    async def sync_tools(self, server_id: str) -> list[dict[str, Any]]:
        """Connect to the tool server via MCP, fetch tools, and register them."""
        server = await self.get(server_id)
        if server is None:
            raise ValueError(f"Server {server_id} not found")

        if not MCP_AVAILABLE:
            logger.warning("MCP client not available. Cannot sync tools.")
            return []

        client = MCPClient()
        try:
            # Build headers from auth_config if bearer token provided
            headers = None
            auth_config = server.get("auth_config") or {}
            if server.get("auth_type") == "bearer" and auth_config.get("token"):
                headers = {"Authorization": f"Bearer {auth_config['token']}"}

            # Determine transport
            transport = server.get("metadata", {}).get("transport", "http")
            command = server.get("metadata", {}).get("command")
            args = server.get("metadata", {}).get("args")

            await client.connect(
                server["url"],
                headers=headers,
                transport=transport,
                command=command,
                args=args,
                auth_type=server.get("auth_type", "none"),
                auth_config=auth_config,
            )
            tools = await client.list_tool_specs()
            await self.set_status(server_id, "connected")

            # If a registry was provided, register them automatically
            if self._registry is not None:
                from core.tools.types import Tool
                self._remove_registered_tools(server_id)
                for spec in tools:
                    # Create Tool object based on spec
                    tool = Tool(
                        id=f"mcp_{server_id}_{spec['name']}",
                        name=spec['name'],
                        description=spec['description'],
                        parameters=spec.get('parameters', {}),
                        provider="mcp",
                        category="mcp",
                        is_available=True,
                        tags=["mcp", server.get("name", "mcp")],
                        metadata={
                            "mcp_server_id": server_id,
                            "mcp_server_url": server["url"],
                            "mcp_transport": transport,
                            "mcp_command": command,
                            "mcp_args": args,
                            "mcp_auth_type": server.get("auth_type", "none"),
                        },
                    )
                    self._registry.register(tool)

            return tools
        except Exception as e:
            logger.error(f"Failed to sync tools for server {server_id}: {e}")
            await self.set_status(server_id, "error")
            raise
        finally:
            await client.disconnect()

    def _remove_registered_tools(self, server_id: str) -> None:
        """Remove stale MCP tools previously discovered from one server."""
        if self._registry is None:
            return
        for tool in self._registry.list_all():
            if tool.metadata.get("mcp_server_id") == server_id:
                self._registry.unregister(tool.id)

    async def _publish(
        self, event_type: EventType, subject: str, payload: dict[str, Any]
    ) -> None:
        if self._bus is None:
            return
        await self._bus.publish(
            subject,
            Event(
                type=event_type,
                source="tool-server-manager",
                payload=payload,
            ),
        )
