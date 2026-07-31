"""Memory State Backend — In-memory implementation for tests."""

from __future__ import annotations

import logging
from typing import Any, Optional

from core.state.interface import StateBackend

logger = logging.getLogger(__name__)


class MemoryStateBackend(StateBackend):
    """Backend mémoire pour tests."""

    def __init__(self):
        self._store: dict[str, Any] = {}
        self._ttl: dict[str, int] = {}

    async def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = value
        if ttl is not None:
            self._ttl[key] = ttl

    async def insert(self, table: str, payload: dict) -> Optional[Any]:
        import uuid
        _id = str(uuid.uuid4())
        key = f"{table}:{_id}"
        self._store[key] = payload
        return payload

    async def query(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        return []

    async def sync_event(self, event_id: str, payload: dict) -> None:
        await self.insert("events", {"id": event_id, **payload})

    async def close(self) -> None:
        """Ferme le backend."""
        self._store.clear()
        self._ttl.clear()
