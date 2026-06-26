"""ETHAN State Manager — Redis + PostgreSQL state persistence"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional


class StateManager:
    """State Manager — manages system state with Redis (live) and PostgreSQL (persistent)"""
    
    def __init__(self):
        self._redis_client = None
        self._pg_pool = None
        self._memory_store: Dict[str, Any] = {}
        self._running = False
        
    async def start(self) -> None:
        """Initialize the state manager"""
        self._running = True
        
        # Try Redis connection
        try:
            import redis.asyncio as aioredis
            self._redis_client = await aioredis.from_url(
                "redis://redis:6379/0",
                decode_responses=True
            )
            await self._redis_client.ping()
        except (ImportError, Exception):
            # Fallback to in-memory store
            pass
        
        # Try PostgreSQL connection
        try:
            import asyncpg
            self._pg_pool = await asyncpg.create_pool(
                "postgresql://ethan:ethan_dev_pass@postgres:5432/ethan"
            )
        except (ImportError, Exception):
            pass
    
    async def stop(self) -> None:
        """Stop the state manager"""
        self._running = False
        if self._redis_client:
            await self._redis_client.close()
        if self._pg_pool:
            await self._pg_pool.close()
    
    # ── Live State (Redis / In-Memory) ─────────────────────────────────
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a state value"""
        if self._redis_client:
            await self._redis_client.set(key, json.dumps(value))
            if ttl:
                await self._redis_client.expire(key, ttl)
        else:
            self._memory_store[key] = value
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a state value"""
        if self._redis_client:
            data = await self._redis_client.get(key)
            return json.loads(data) if data else None
        return self._memory_store.get(key)
    
    async def delete(self, key: str) -> None:
        """Delete a state value"""
        if self._redis_client:
            await self._redis_client.delete(key)
        else:
            self._memory_store.pop(key, None)
    
    async def hset(self, name: str, key: str, value: Any) -> None:
        """Set a hash field"""
        if self._redis_client:
            await self._redis_client.hset(name, key, json.dumps(value))
        else:
            if name not in self._memory_store:
                self._memory_store[name] = {}
            self._memory_store[name][key] = value
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get a hash field"""
        if self._redis_client:
            data = await self._redis_client.hget(name, key)
            return json.loads(data) if data else None
        store = self._memory_store.get(name, {})
        return store.get(key)
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        if self._redis_client:
            data = await self._redis_client.hgetall(name)
            return {k: json.loads(v) for k, v in data.items()}
        return self._memory_store.get(name, {})
    
    # ── Persistent State (PostgreSQL) ──────────────────────────────────
    
    async def store_event(self, event_id: str, event_type: str, source: str,
                          payload: Dict[str, Any], context: Optional[Dict[str, str]] = None) -> None:
        """Store an event in PostgreSQL"""
        if not self._pg_pool:
            return
        
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO events (id, type, source, timestamp, payload, context)
                   VALUES ($1, $2, $3, NOW(), $4::jsonb, $5::jsonb)""",
                event_id, event_type, source,
                json.dumps(payload), json.dumps(context or {})
            )
    
    async def store_goal(self, goal_id: str, description: str, state: str = "created",
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a goal in PostgreSQL"""
        if not self._pg_pool:
            return
        
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO goals (id, description, state, metadata)
                   VALUES ($1, $2, $3, $4::jsonb)
                   ON CONFLICT (id) DO UPDATE SET state = $3, updated_at = NOW()""",
                goal_id, description, state, json.dumps(metadata or {})
            )
    
    async def store_snapshot(self, module: str, state: Dict[str, Any]) -> str:
        """Store a module snapshot"""
        if not self._pg_pool:
            return ""
        
        snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO snapshots (id, module, state)
                   VALUES ($1, $2, $3::jsonb)""",
                snapshot_id, module, json.dumps(state)
            )
        return snapshot_id
    
    async def store_outcome(self, goal_id: str, success: bool, metrics: Dict[str, Any]) -> None:
        """Store a learning outcome"""
        if not self._pg_pool:
            return
        
        async with self._pg_pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO outcomes (id, goal_id, success, metrics)
                   VALUES ($1, $2, $3, $4::jsonb)""",
                f"out-{uuid.uuid4().hex[:8]}", goal_id, success, json.dumps(metrics)
            )
    
    # ── Utility ────────────────────────────────────────────────────────
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists"""
        if self._redis_client:
            return await self._redis_client.exists(key) > 0
        return key in self._memory_store
    
    async def keys(self, pattern: str) -> List[str]:
        """Find keys matching a pattern"""
        if self._redis_client:
            return await self._redis_client.keys(pattern)
        return [k for k in self._memory_store.keys() if pattern.replace("*", "") in k]
    
    async def flush(self) -> None:
        """Clear all state (development only)"""
        if self._redis_client:
            await self._redis_client.flushdb()
        self._memory_store.clear()
    
    @property
    def is_connected(self) -> bool:
        return self._redis_client is not None or len(self._memory_store) > 0
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, *args):
        await self.stop()