"""Redis implementation of LiveState."""

from __future__ import annotations

import json
import logging
import asyncio
import os
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from core.state.interface import StateBackend as LiveState

logger = logging.getLogger(__name__)


class RedisLiveState(LiveState):
    """Live state using Redis with JSON serialization."""

    def __init__(self, url: str = "redis://localhost:6379/0"):
        self._url = url
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        logger.info(f"Connecting to Redis: {self._url}")
        self._redis = aioredis.from_url(
            self._url, decode_responses=True, protocol=2
        )
        timeout = float(os.getenv("REDIS_CONNECT_TIMEOUT", "10"))
        await asyncio.wait_for(self._redis.ping(), timeout=timeout)
        logger.info("Redis connected")

    async def close(self) -> None:
        """Close connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value by key."""
        if not self._redis:
            return None
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set JSON value with TTL (defaults to 1 hour)."""
        if not self._redis:
            return
        actual_ttl = ttl if ttl is not None else 3600
        raw = json.dumps(value)
        await self._redis.setex(key, actual_ttl, raw)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        if self._redis:
            await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._redis:
            return False
        return await self._redis.exists(key) > 0

    async def query(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """Execute a query - Redis doesn't support SQL, returns empty list."""
        # Redis doesn't have SQL, this is a no-op for compatibility
        return []

    async def insert(self, table: str, payload: dict) -> Optional[Any]:
        """Insert - Redis doesn't support relational insert, return None."""
        return None

    # ── Convenience methods ───────────────────────────────

    async def set_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session data with 24h TTL."""
        await self.set(f"session:{session_id}", data, ttl=86400)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        return await self.get(f"session:{session_id}")

    async def set_goal(self, goal_id: str, data: Dict[str, Any]) -> None:
        """Store active goal with 72h TTL."""
        await self.set(f"goal:{goal_id}", data, ttl=259200)

    async def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve active goal."""
        return await self.get(f"goal:{goal_id}")

    async def set_heartbeat(self, module_id: str) -> None:
        """Update module heartbeat (30s TTL)."""
        await self.set(f"module:{module_id}:heartbeat", {"status": "alive"}, ttl=30)
