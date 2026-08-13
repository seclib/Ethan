"""Core-owned note store — notes, pinning, search.

ETHAN Core owns note persistence.  The WebUI only renders notes and
sends create/update actions through the API.
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


class NoteStore:
    """Own notes, pinning and search."""

    _DOMAIN = "notes"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create(
        self,
        title: str,
        content: str,
        user_id: str = "anonymous",
        pinned: bool = False,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new note."""
        note = {
            "id": str(uuid4()),
            "title": title.strip(),
            "content": content,
            "user_id": user_id,
            "pinned": pinned,
            "tags": list(tags or []),
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, note["id"], note)
        await self._publish(EventType.NOTE_CREATED, "note.created", {"note": note})
        return note

    async def get(self, note_id: str) -> dict[str, Any] | None:
        """Retrieve a note by id."""
        return await self._store.get(self._DOMAIN, note_id)

    async def list(self, user_id: str | None = None, pinned: bool | None = None) -> list[dict[str, Any]]:
        """List notes, optionally filtered."""
        notes = await self._store.list(self._DOMAIN)
        if user_id is not None:
            notes = [n for n in notes if n.get("user_id") == user_id]
        if pinned is not None:
            notes = [n for n in notes if n.get("pinned") == pinned]
        return notes

    async def update(self, note_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a note."""
        note = await self.get(note_id)
        if note is None:
            return None
        for key in ("title", "content", "pinned", "tags", "metadata"):
            if key in data:
                note[key] = data[key]
        note["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, note_id, note)
        await self._publish(EventType.NOTE_UPDATED, "note.updated", {"note_id": note_id})
        return note

    async def delete(self, note_id: str) -> bool:
        """Delete a note."""
        existed = await self._store.delete(self._DOMAIN, note_id)
        if existed:
            await self._publish(EventType.NOTE_DELETED, "note.deleted", {"note_id": note_id})
        return existed

    async def search(self, query: str, user_id: str | None = None) -> list[dict[str, Any]]:
        """Search notes by content or title."""
        notes = await self.list(user_id=user_id)
        query_lower = query.lower()
        return [
            n for n in notes
            if query_lower in n.get("title", "").lower()
            or query_lower in n.get("content", "").lower()
        ]

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="note-store", payload=payload))
