"""Core-owned channel store — discussion channels and messages.

ETHAN Core owns channel persistence.  The WebUI only renders channels
and sends messages through the API.
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


class ChannelStore:
    """Own discussion channels and their messages."""

    _DOMAIN = "channels"
    _MESSAGES_DOMAIN = "channel-messages"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create_channel(
        self,
        name: str,
        description: str = "",
        user_id: str = "anonymous",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new discussion channel."""
        channel = {
            "id": str(uuid4()),
            "name": name.strip(),
            "description": description,
            "user_id": user_id,
            "members": [user_id],
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, channel["id"], channel)
        await self._publish(EventType.CHANNEL_CREATED, "channel.created", {"channel": channel})
        return channel

    async def get_channel(self, channel_id: str) -> dict[str, Any] | None:
        """Retrieve a channel by id."""
        return await self._store.get(self._DOMAIN, channel_id)

    async def list_channels(self) -> list[dict[str, Any]]:
        """List all channels."""
        return await self._store.list(self._DOMAIN)

    async def update_channel(self, channel_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a channel."""
        channel = await self.get_channel(channel_id)
        if channel is None:
            return None
        for key in ("name", "description", "metadata"):
            if key in data:
                channel[key] = data[key]
        channel["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, channel_id, channel)
        await self._publish(EventType.CHANNEL_UPDATED, "channel.updated", {"channel_id": channel_id})
        return channel

    async def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel and its messages."""
        existed = await self._store.delete(self._DOMAIN, channel_id)
        for message in await self._store.list(self._MESSAGES_DOMAIN):
            if message.get("channel_id") == channel_id:
                await self._store.delete(self._MESSAGES_DOMAIN, message["id"])
        if existed:
            await self._publish(EventType.CHANNEL_DELETED, "channel.deleted", {"channel_id": channel_id})
        return existed

    async def add_message(
        self,
        channel_id: str,
        role: str,
        content: str,
        user_id: str = "anonymous",
    ) -> dict[str, Any]:
        """Append a message to a channel."""
        channel = await self.get_channel(channel_id)
        if channel is None:
            raise ValueError(f"Channel {channel_id} not found")
        message = {
            "id": str(uuid4()),
            "channel_id": channel_id,
            "role": role,
            "content": content,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._MESSAGES_DOMAIN, message["id"], message)
        await self._publish(EventType.CHANNEL_MESSAGE, "channel.message", {"message": message})
        return message

    async def list_messages(self, channel_id: str) -> list[dict[str, Any]]:
        """Return all messages in a channel."""
        messages = await self._store.list(self._MESSAGES_DOMAIN)
        return [m for m in messages if m.get("channel_id") == channel_id]

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="channel-store", payload=payload))
