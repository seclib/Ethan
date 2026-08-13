"""Core-owned user management — registration, profiles, roles.

ETHAN Core owns user data.  The WebUI only renders user profiles
and sends management actions through the API.
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


class UserManager:
    """Own user accounts, profiles and lifecycle."""

    _DOMAIN = "users"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create(
        self,
        username: str,
        email: str,
        role: str = "user",
        password_hash: str = "",
        profile: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new user."""
        user = {
            "id": str(uuid4()),
            "username": username.strip(),
            "email": email.strip(),
            "role": role,
            "password_hash": password_hash,
            "active": True,
            "profile": dict(profile or {}),
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, user["id"], user)
        await self._publish(EventType.USER_CREATED, "user.created", {"user": {k: v for k, v in user.items() if k != "password_hash"}})
        return user

    async def get(self, user_id: str) -> dict[str, Any] | None:
        """Retrieve a user by id."""
        return await self._store.get(self._DOMAIN, user_id)

    async def list(self) -> list[dict[str, Any]]:
        """List all users."""
        return await self._store.list(self._DOMAIN)

    async def update(self, user_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update user profile or state."""
        user = await self.get(user_id)
        if user is None:
            return None
        for key in ("username", "email", "role", "active", "profile", "metadata"):
            if key in data:
                user[key] = data[key]
        user["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, user_id, user)
        await self._publish(EventType.USER_UPDATED, "user.updated", {"user_id": user_id})
        return user

    async def delete(self, user_id: str) -> bool:
        """Delete a user."""
        existed = await self._store.delete(self._DOMAIN, user_id)
        if existed:
            await self._publish(EventType.USER_DELETED, "user.deleted", {"user_id": user_id})
        return existed

    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        """Find a user by email."""
        users = await self.list()
        for user in users:
            if user.get("email") == email:
                return user
        return None

    async def find_by_username(self, username: str) -> dict[str, Any] | None:
        """Find a user by username."""
        users = await self.list()
        for user in users:
            if user.get("username") == username:
                return user
        return None

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="user-manager", payload=payload))