"""Core-owned chat store — conversations, messages, sharing, archiving.

ETHAN Core owns chat persistence.  The WebUI only renders conversations
and sends user actions through the API.
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


class ChatStore:
    """Own chat conversations, messages, sharing and archiving."""

    _DOMAIN = "chats"
    _MESSAGES_DOMAIN = "chat-messages"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create_chat(
        self,
        title: str,
        user_id: str = "anonymous",
        folder_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new conversation."""
        chat = {
            "id": str(uuid4()),
            "title": title.strip() or "New Chat",
            "user_id": user_id,
            "folder_id": folder_id,
            "archived": False,
            "pinned": False,
            "share_id": None,
            "messages": [],
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, chat["id"], chat)
        await self._publish(EventType.CHAT_CREATED, "chat.created", {"chat": chat})
        return chat

    async def get_chat(self, chat_id: str) -> dict[str, Any] | None:
        """Retrieve a conversation by id."""
        return await self._store.get(self._DOMAIN, chat_id)

    async def list_chats(
        self,
        user_id: str | None = None,
        folder_id: str | None = None,
        archived: bool | None = None,
    ) -> list[dict[str, Any]]:
        """List conversations, optionally filtered."""
        chats = await self._store.list(self._DOMAIN)
        if user_id is not None:
            chats = [c for c in chats if c.get("user_id") == user_id]
        if folder_id is not None:
            chats = [c for c in chats if c.get("folder_id") == folder_id]
        if archived is not None:
            chats = [c for c in chats if c.get("archived") == archived]
        return chats

    async def update_chat(self, chat_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update conversation metadata or state."""
        chat = await self.get_chat(chat_id)
        if chat is None:
            return None
        for key in ("title", "folder_id", "archived", "pinned", "metadata"):
            if key in data:
                chat[key] = data[key]
        chat["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, chat_id, chat)
        await self._publish(EventType.CHAT_UPDATED, "chat.updated", {"chat": chat})
        return chat

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a conversation and its messages."""
        existed = await self._store.delete(self._DOMAIN, chat_id)
        for message in await self._store.list(self._MESSAGES_DOMAIN):
            if message.get("chat_id") == chat_id:
                await self._store.delete(self._MESSAGES_DOMAIN, message["id"])
        if existed:
            await self._publish(EventType.CHAT_DELETED, "chat.deleted", {"chat_id": chat_id})
        return existed

    async def add_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        user_id: str = "anonymous",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append a message to a conversation."""
        chat = await self.get_chat(chat_id)
        if chat is None:
            raise ValueError(f"Chat {chat_id} not found")
        message = {
            "id": str(uuid4()),
            "chat_id": chat_id,
            "role": role,
            "content": content,
            "user_id": user_id,
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._MESSAGES_DOMAIN, message["id"], message)
        chat.setdefault("messages", []).append(message["id"])
        chat["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, chat_id, chat)
        await self._publish(EventType.CHAT_MESSAGE, "chat.message", {"message": message})
        return message

    async def list_messages(self, chat_id: str) -> list[dict[str, Any]]:
        """Return all messages in a conversation."""
        messages = await self._store.list(self._MESSAGES_DOMAIN)
        return [m for m in messages if m.get("chat_id") == chat_id]

    async def share_chat(self, chat_id: str) -> dict[str, Any] | None:
        """Generate a share link for a conversation."""
        chat = await self.get_chat(chat_id)
        if chat is None:
            return None
        chat["share_id"] = str(uuid4())
        chat["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, chat_id, chat)
        return chat

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="chat-store", payload=payload))