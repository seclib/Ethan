"""Core-owned file store — upload metadata, storage, retrieval.

ETHAN Core owns file persistence.  The WebUI only renders files and
sends upload actions through the API.

This store supports two modes:
- metadata-only (``storage_path`` provided by the caller; e.g. an object store)
- binary storage in Core (``content`` provided; bytes are persisted alongside
  the metadata record)
"""

from __future__ import annotations

import base64
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
    """Own file metadata, physical storage and download.

    ETHAN Core is the source of truth for files.  The WebUI only renders
    files and sends upload/download actions through the API gateway.
    """

    _DOMAIN = "files"
    _CONTENT_DOMAIN = "files_content"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
        storage_dir: str | Path | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()
        self._storage_dir = Path(storage_dir) if storage_dir else None
        if self._storage_dir:
            self._storage_dir.mkdir(parents=True, exist_ok=True)

    async def register(
        self,
        filename: str,
        content_type: str,
        size: int,
        user_id: str = "anonymous",
        storage_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        content: bytes | None = None,
    ) -> dict[str, Any]:
        """Register file metadata after an upload.

        If ``content`` is provided, the raw bytes are persisted in the Core
        record store so ``download()`` can serve them without an external
        object store.
        """
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

        # Persist binary content in the Core store (if provided).
        # The record store is JSON-safe, so binary content is base64-encoded.
        if content is not None:
            await self._store.save(
                self._CONTENT_DOMAIN,
                file_id,
                {"data": base64.b64encode(content).decode("ascii")},
            )
            record["has_content"] = True
        else:
            record["has_content"] = False

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
        """Delete file metadata (and binary content if stored in Core)."""
        existed = await self._store.delete(self._DOMAIN, file_id)
        if existed:
            try:
                await self._store.delete(self._CONTENT_DOMAIN, file_id)
            except Exception as exc:
                logger.warning("Failed to delete file content %s: %s", file_id, exc)
            await self._publish(EventType.FILE_DELETED, "file.deleted", {"file_id": file_id})
        return existed

    async def download(self, file_id: str) -> tuple[bytes, dict[str, Any]] | None:
        """Return the binary content and metadata for a file.

        Resolution order:
        1. In-Core binary content (``files_content`` record).
        2. ``storage_path`` on the local filesystem (when set).
        """
        record = await self.get(file_id)
        if record is None:
            return None

        # 1. In-Core binary content
        if record.get("has_content"):
            content_record = await self._store.get(self._CONTENT_DOMAIN, file_id)
            if content_record is not None:
                raw = content_record.get("data", "")
                try:
                    content = base64.b64decode(raw)
                except Exception as exc:
                    logger.warning("Failed to decode file content %s: %s", file_id, exc)
                    content = b""
                return content, record

        # 2. Local filesystem via storage_path (or storage_dir/filename)
        path: Path | None = None
        storage_path = record.get("storage_path")
        if storage_path:
            path = Path(storage_path)
        elif self._storage_dir is not None:
            path = self._storage_dir / str(record.get("filename", file_id))
        if path is not None and path.exists():
            return path.read_bytes(), record

        return None

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="file-store", payload=payload))