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
        *,
        parent_id: str | None = None,
        model: str | None = None,
        files: list[dict[str, Any]] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        sources: list[dict[str, Any]] | None = None,
        status: str = "done",
        done: bool = True,
    ) -> dict[str, Any]:
        """Append a message to a conversation.

        Supports the Open-WebUI message tree contract: each message carries
        ``parent_id`` and ``children_ids`` so branching (edit/regenerate)
        creates children instead of overwriting history.
        """
        chat = await self.get_chat(chat_id)
        if chat is None:
            raise ValueError(f"Chat {chat_id} not found")
        message = {
            "id": str(uuid4()),
            "chat_id": chat_id,
            "parent_id": parent_id,
            "children_ids": [],
            "role": role,
            "content": content,
            "user_id": user_id,
            "model": model,
            "files": list(files or []),
            "tool_calls": list(tool_calls or []),
            "sources": list(sources or []),
            "status": status,
            "done": done,
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._MESSAGES_DOMAIN, message["id"], message)

        # Lier l'enfant au parent (arbre de messages).
        if parent_id:
            parent = await self._store.get(self._MESSAGES_DOMAIN, parent_id)
            if parent is not None:
                parent.setdefault("children_ids", []).append(message["id"])
                parent["updated_at"] = datetime.utcnow().isoformat()
                await self._store.save(self._MESSAGES_DOMAIN, parent_id, parent)

        chat.setdefault("messages", []).append(message["id"])
        chat["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, chat_id, chat)
        await self._publish(EventType.CHAT_MESSAGE, "chat.message", {"message": message})
        return message

    async def get_message(self, chat_id: str, message_id: str) -> dict[str, Any] | None:
        """Return a single message in a conversation."""
        message = await self._store.get(self._MESSAGES_DOMAIN, message_id)
        if message is None or message.get("chat_id") != chat_id:
            return None
        return message

    async def update_message(
        self,
        chat_id: str,
        message_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update a message (content, status, done, tool_calls, sources, ...)."""
        message = await self.get_message(chat_id, message_id)
        if message is None:
            return None
        for key in ("content", "status", "done", "model", "files", "tool_calls", "sources", "metadata"):
            if key in data:
                message[key] = data[key]
        message["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._MESSAGES_DOMAIN, message_id, message)
        await self._publish(EventType.CHAT_MESSAGE, "chat.message.updated", {"message": message})
        return message

    async def list_messages(self, chat_id: str) -> list[dict[str, Any]]:
        """Return all messages in a conversation, ordered by creation time."""
        messages = await self._store.list(self._MESSAGES_DOMAIN)
        ordered = [m for m in messages if m.get("chat_id") == chat_id]
        ordered.sort(key=lambda m: m.get("created_at", ""))
        return ordered

    async def get_branch(self, chat_id: str, message_id: str | None = None) -> list[dict[str, Any]]:
        """Return the current message path (branch) of a conversation.

        If ``message_id`` is provided, the path from the root to that message
        is returned.  Otherwise the latest leaf (deepest message) is used.
        """
        messages = await self.list_messages(chat_id)
        if not messages:
            return []

        by_id = {m["id"]: m for m in messages}

        # Trouver le nœud de départ : message_id fourni, sinon la feuille la plus récente.
        if message_id is None:
            leaves = [m for m in messages if not m.get("children_ids")]
            if not leaves:
                leaves = messages
            start = max(leaves, key=lambda m: m.get("created_at", ""))
        else:
            start = by_id.get(message_id)
            if start is None:
                return []

        # Remonter jusqu'à la racine.
        path: list[dict[str, Any]] = []
        current: dict[str, Any] | None = start
        while current is not None:
            path.append(current)
            current = by_id.get(current.get("parent_id") or "")
        path.reverse()
        return path

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