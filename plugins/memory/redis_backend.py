"""Redis Memory Backend — Cache & mémoire courte agent."""

import json
import logging
import time
from typing import Any

from core.memory import MemoryBackend, MemoryEntry, MemoryResult

# Lazy import de redis pour respecter ADR-1005
def _get_redis():
    try:
        import redis.asyncio as aioredis
        return aioredis
    except ImportError:
        raise ImportError(
            "Redis package not installed. Install: pip install redis"
        )

logger = logging.getLogger(__name__)


class RedisBackend(MemoryBackend):
    """Redis backend for short-term memory and caching.

    Used for:
    - Conversation cache (recent messages)
    - Agent short-term memory
    - Session storage
    - Rate limiting counters
    - Temporary data with TTL
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        prefix: str = "jarvis:",
    ):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._prefix = prefix
        self._client = None

    async def _ensure_client(self):
        """Initialize Redis client if not already done."""
        if self._client is not None:
            return

        try:
            aioredis = _get_redis()
            self._client = aioredis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self._client.ping()
            logger.info(f"Connected to Redis: {self._host}:{self._port}")
        except ImportError:
            raise
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            raise

    def _make_key(self, key: str, namespace: str = "default") -> str:
        """Create a namespaced Redis key."""
        return f"{self._prefix}{namespace}:{key}"

    async def store(self, entry: MemoryEntry) -> None:
        """Store an entry in Redis."""
        await self._ensure_client()

        key = self._make_key(entry.key, entry.namespace)
        value = json.dumps(entry.value) if not isinstance(entry.value, str) else entry.value

        data = {
            "value": value,
            "namespace": entry.namespace,
            "timestamp": entry.timestamp or time.time(),
        }
        if entry.metadata:
            data["metadata"] = json.dumps(entry.metadata)

        # Store with optional TTL
        ttl = entry.ttl if entry.ttl else None
        await self._client.hset(key, mapping=data)
        if ttl:
            await self._client.expire(key, ttl)

    async def retrieve(self, key: str, namespace: str = "default") -> MemoryEntry | None:
        """Retrieve an entry by key."""
        await self._ensure_client()

        redis_key = self._make_key(key, namespace)
        data = await self._client.hgetall(redis_key)

        if not data:
            return None

        # Check if key has expired
        ttl = await self._client.ttl(redis_key)
        if ttl == -2:  # Key does not exist
            return None

        # Parse value
        try:
            value = json.loads(data.get("value", "{}"))
        except json.JSONDecodeError:
            value = data.get("value", "")

        # Parse metadata
        metadata = None
        if "metadata" in data:
            try:
                metadata = json.loads(data["metadata"])
            except json.JSONDecodeError:
                pass

        return MemoryEntry(
            key=key,
            value=value,
            namespace=namespace,
            metadata=metadata,
            timestamp=float(data.get("timestamp", time.time())),
        )

    async def search(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 10,
        threshold: float = 0.0,
    ) -> list[MemoryResult]:
        """Search entries by pattern matching (Redis SCAN)."""
        await self._ensure_client()

        pattern = self._make_key("*", namespace)
        results = []
        count = 0

        # Use SCAN for efficient iteration
        async for key in self._client.scan_iter(match=pattern, count=100):
            if count >= limit:
                break

            data = await self._client.hgetall(key)
            if not data:
                continue

            # Simple relevance: check if query is in value
            value_str = str(data.get("value", ""))
            if query.lower() in value_str.lower():
                # Extract the original key from the Redis key
                original_key = key.replace(f"{self._prefix}{namespace}:", "")

                try:
                    value = json.loads(value_str)
                except json.JSONDecodeError:
                    value = value_str

                results.append(MemoryResult(
                    key=original_key,
                    value=value,
                    namespace=namespace,
                    score=1.0,
                    timestamp=float(data.get("timestamp", 0)),
                ))
                count += 1

        return results[:limit]

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete an entry."""
        await self._ensure_client()

        redis_key = self._make_key(key, namespace)
        result = await self._client.delete(redis_key)
        return result > 0

    async def list_namespaces(self) -> list[str]:
        """List all namespaces (by scanning keys)."""
        await self._ensure_client()

        pattern = f"{self._prefix}*"
        namespaces = set()

        async for key in self._client.scan_iter(match=pattern, count=1000):
            # Extract namespace from key: prefix:namespace:key
            parts = key.replace(self._prefix, "").split(":", 1)
            if len(parts) >= 2:
                namespaces.add(parts[0])

        return sorted(namespaces)

    async def clear(self, namespace: str | None = None) -> None:
        """Clear entries, optionally for a namespace."""
        await self._ensure_client()

        if namespace:
            pattern = self._make_key("*", namespace)
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=1000):
                keys.append(key)
            if keys:
                await self._client.delete(*keys)
        else:
            # Clear all keys with prefix
            pattern = f"{self._prefix}*"
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=1000):
                keys.append(key)
            if keys:
                await self._client.delete(*keys)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    # ─── Additional Redis-specific methods ───────────────────────────────────

    async def get_ttl(self, key: str, namespace: str = "default") -> int:
        """Get TTL for a key in seconds."""
        await self._ensure_client()
        redis_key = self._make_key(key, namespace)
        ttl = await self._client.ttl(redis_key)
        return max(ttl, 0)

    async def set_ttl(self, key: str, ttl: int, namespace: str = "default") -> bool:
        """Set TTL for an existing key."""
        await self._ensure_client()
        redis_key = self._make_key(key, namespace)
        return await self._client.expire(redis_key, ttl)

    async def increment(self, key: str, amount: int = 1, namespace: str = "default") -> int:
        """Increment a counter (useful for rate limiting)."""
        await self._ensure_client()
        redis_key = self._make_key(key, namespace)
        return await self._client.incrby(redis_key, amount)

    async def expire(self, key: str, ttl: int, namespace: str = "default") -> bool:
        """Set expiration on a key."""
        await self._ensure_client()
        redis_key = self._make_key(key, namespace)
        return await self._client.expire(redis_key, ttl)