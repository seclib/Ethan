"""Core-owned group management — groups, memberships, permissions.

ETHAN Core owns group data.  The WebUI only renders groups and
sends management actions through the API.
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


class GroupManager:
    """Own groups, memberships and permission scopes."""

    _DOMAIN = "groups"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create(
        self,
        name: str,
        description: str = "",
        permissions: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new group."""
        group = {
            "id": str(uuid4()),
            "name": name.strip(),
            "description": description,
            "permissions": dict(permissions or {}),
            "members": [],
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, group["id"], group)
        await self._publish(EventType.GROUP_CREATED, "group.created", {"group": group})
        return group

    async def get(self, group_id: str) -> dict[str, Any] | None:
        """Retrieve a group by id."""
        return await self._store.get(self._DOMAIN, group_id)

    async def list(self) -> list[dict[str, Any]]:
        """List all groups."""
        return await self._store.list(self._DOMAIN)

    async def update(self, group_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update group metadata or permissions."""
        group = await self.get(group_id)
        if group is None:
            return None
        for key in ("name", "description", "permissions", "metadata"):
            if key in data:
                group[key] = data[key]
        group["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, group_id, group)
        await self._publish(EventType.GROUP_UPDATED, "group.updated", {"group_id": group_id})
        return group

    async def delete(self, group_id: str) -> bool:
        """Delete a group."""
        existed = await self._store.delete(self._DOMAIN, group_id)
        if existed:
            await self._publish(EventType.GROUP_DELETED, "group.deleted", {"group_id": group_id})
        return existed

    async def add_member(self, group_id: str, user_id: str) -> dict[str, Any] | None:
        """Add a user to a group."""
        group = await self.get(group_id)
        if group is None:
            return None
        if user_id not in group["members"]:
            group["members"].append(user_id)
            group["updated_at"] = datetime.utcnow().isoformat()
            await self._store.save(self._DOMAIN, group_id, group)
        return group

    async def remove_member(self, group_id: str, user_id: str) -> dict[str, Any] | None:
        """Remove a user from a group."""
        group = await self.get(group_id)
        if group is None:
            return None
        if user_id in group["members"]:
            group["members"].remove(user_id)
            group["updated_at"] = datetime.utcnow().isoformat()
            await self._store.save(self._DOMAIN, group_id, group)
        return group

    async def list_members(self, group_id: str) -> list[str]:
        """Return member user ids for a group."""
        group = await self.get(group_id)
        return list(group.get("members", [])) if group else []

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="group-manager", payload=payload))