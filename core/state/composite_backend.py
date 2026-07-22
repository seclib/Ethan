"""Composite State Backend - Unifie Redis et PostgreSQL.

CLEAN ARCHITECTURE: Le Kernel dépend uniquement de StateBackend (l'interface),
et reçoit une instance de CompositeStateBackend qui combine les deux backends.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from core.state.interface import StateBackend
from core.state.redis_state import RedisLiveState
from core.state.postgres_state import PostgresPersistentState

logger = logging.getLogger(__name__)


class CompositeStateBackend(StateBackend):
    """Combine Redis (live) et PostgreSQL (persistent) en un seul backend.
    
    Cette classe permet au Kernel de respecter le principe de Clean Architecture
    en dépendant uniquement de l'interface StateBackend.
    """

    def __init__(self, live: RedisLiveState, persistent: PostgresPersistentState):
        self._live = live
        self._persistent = persistent

    async def connect(self) -> None:
        """Connect both backends."""
        await self._live.connect()
        await self._persistent.connect()
        logger.info("Composite state backend connected")

    async def close(self) -> None:
        """Close both backends."""
        await self._live.close()
        await self._persistent.close()
        logger.info("Composite state backend closed")

    async def get(self, key: str) -> Optional[Any]:
        """Get from live cache first, then persistent."""
        result = await self._live.get(key)
        if result is not None:
            return result
        return await self._persistent.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in live cache only (ephemeral)."""
        await self._live.set(key, value, ttl=ttl)

    async def insert(self, table: str, payload: dict) -> Optional[Any]:
        """Insert into persistent storage."""
        return await self._persistent.insert(table, payload)

    async def query(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """Query persistent storage."""
        return await self._persistent.query(sql, params=params)

    async def sync_event(self, event_id: str, payload: dict) -> None:
        """Synchroniser un événement dans les deux backends (Redis + PostgreSQL)."""
        await self._live.set(f"event:{event_id}", payload, ttl=3600)
        await self._persistent.insert("events", payload)

    async def set_live(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in live cache only."""
        await self._live.set(key, value, ttl=ttl)

    async def insert_persistent(self, table: str, payload: dict) -> Optional[Any]:
        """Insert into persistent storage."""
        return await self._persistent.insert(table, payload)
