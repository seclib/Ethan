"""Core-owned file store — upload metadata, storage, retrieval.

ETHAN Core owns file persistence.  The WebUI only renders files and
sends upload actions through the API.
"""

from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class FileStore:
    """Own file metadata and references to physical storage."""

    _DOMAIN = "files"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
        storage_dir: str | Path | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()
        self._storage_dir = Path(storage_dir) if storage_dir else None

    async def register(
        self,
        filename: str,
        content_type: str,
        size: int,
        user_id: str = "anonymous",
        storage_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register file metadata after an upload."""
        file_id = str(uuid4())
        record = {
            "id": file_id,
            "filename": filename,
            "content_type": content_type,
            "size": size,
            "user_id": user_id,
            "storage_path": storage_path,
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, file_id, record)
        await self._publish(EventType.FILE_UPLOADED, "file.uploaded", {"file": record})
        return record

    async def get(self, file_id: str) -> dict[str, Any] | None:
        """Retrieve file metadata by id."""
        return await self._store.get(self._DOMAIN, file_id)

    async def list(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List files, optionally by owner."""
        files = await self._store.list(self._DOMAIN)
        if user_id is not None:
            files = [f for f in files if f.get("user_id") == user_id]
        return files

    async def delete(self, file_id: str) -> bool:
        """Delete file metadata."""
        existed = await self._store.delete(self._DOMAIN, file_id)
        if existed:
            await self._publish(EventType.FILE_DELETED, "file.deleted", {"file_id": file_id})
        return existed

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="file-store", payload=payload))