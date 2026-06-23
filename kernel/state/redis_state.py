"""Redis implementation of LiveState."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from kernel.state.interface import LiveState

logger = logging.getLogger(__name__)


class RedisLiveState(LiveState):
    """Live state using Redis with JSON serialization."""

    def __init__(self, url: str = "redis://localhost:6379/0"):
        self._url = url
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        logger.info(f"Connecting to Redis: {self._url}")
        self._redis = await aioredis.from_url(
            self._url, decode_responses=True
        )
        await self._redis.ping()
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

    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> None:
        """Set JSON value with TTL."""
        if not self._redis:
            return
        raw = json.dumps(value)
        await self._redis.setex(key, ttl, raw)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        if self._redis:
            await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._redis:
            return False
        return await self._redis.exists(key) > 0

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