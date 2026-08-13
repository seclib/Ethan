"""Core-owned tool server management — external MCP/tool servers.

ETHAN Core owns tool server registration and lifecycle.  The WebUI only
renders the server list and sends enable/disable actions through the API.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class ToolServerManager:
    """Own external tool server registration and lifecycle."""

    _DOMAIN = "tool-servers"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

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
        await self._publish(EventType.TOOL_SERVER_REGISTERED, "tool.server.registered", {"server": server})
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

    async def update(self, server_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a tool server."""
        server = await self.get(server_id)
        if server is None:
            return None
        for key in ("name", "url", "description", "auth_type", "auth_config", "enabled", "metadata"):
            if key in data:
                server[key] = data[key]
        server["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, server_id, server)
        await self._publish(EventType.TOOL_SERVER_UPDATED, "tool.server.updated", {"server_id": server_id})
        return server

    async def delete(self, server_id: str) -> bool:
        """Delete a tool server."""
        existed = await self._store.delete(self._DOMAIN, server_id)
        if existed:
            await self._publish(EventType.TOOL_SERVER_DELETED, "tool.server.deleted", {"server_id": server_id})
        return existed

    async def set_status(self, server_id: str, status: str) -> dict[str, Any] | None:
        """Update a tool server's connection status."""
        server = await self.get(server_id)
        if server is None:
            return None
        server["status"] = status
        if status == "connected":
            server["last_connected_at"] = datetime.utcnow().isoformat()
        server["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, server_id, server)
        return server

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="tool-server-manager", payload=payload))