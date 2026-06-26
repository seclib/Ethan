"""Memory State Backend — In-memory implementation for tests."""

from __future__ import annotations

import logging
from typing import Any

from core.state.interface import StateBackend

logger = logging.getLogger(__name__)


class MemoryStateBackend(StateBackend):
    """Backend mémoire pour tests."""

    def __init__(self):
        self._store: dict[str, bytes] = {}
        self._ttl: dict[str, int] = {}

    async def get(self, key: str, namespace: str = "") -> bytes | None:
        full_key = f"{namespace}:{key}" if namespace else key
        return self._store.get(full_key)

    async def set(
        self,
        key: str,
        value: bytes,
        ttl: int | None = None,
        namespace: str = "",
    ) -> None:
        full_key = f"{namespace}:{key}" if namespace else key
        self._store[full_key] = value
        if ttl is not None:
            self._ttl[full_key] = ttl

    async def delete(self, key: str, namespace: str = "") -> None:
        full_key = f"{namespace}:{key}" if namespace else key
        self._store.pop(full_key, None)
        self._ttl.pop(full_key, None)

    async def persist(self, event: Any) -> None:
        """Persiste un événement."""
        key = f"event:{event.id}"
        import json
        data = json.dumps(event.to_dict() if hasattr(event, 'to_dict') else dict(event))
        await self.set(key, data.encode(), ttl=3600)

    async def close(self) -> None:
        """Ferme le backend."""
        self._store.clear()
        self._ttl.clear()