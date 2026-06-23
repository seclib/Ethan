"""PostgreSQL implementation of PersistentState."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import asyncpg

from kernel.state.interface import PersistentState

logger = logging.getLogger(__name__)


class PostgresPersistentState(PersistentState):
    """Persistent state using PostgreSQL via asyncpg."""

    def __init__(self, dsn: str = "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan"):
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Connect to PostgreSQL."""
        logger.info(f"Connecting to PostgreSQL: {self._dsn.split('@')[1]}")
        self._pool = await asyncpg.create_pool(self._dsn, min_size=2, max_size=10)
        logger.info("PostgreSQL connected")

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL connection closed")

    async def execute(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        if not self._pool:
            raise RuntimeError("PostgreSQL not connected")
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a row and return the full record."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        rows = await self.execute(query, *data.values())
        return rows[0] if rows else {}

    async def update(
        self, table: str, where: Dict[str, Any], data: Dict[str, Any]
    ) -> None:
        """Update rows matching where clause."""
        set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(data.keys()))
        where_clause = " AND ".join(
            f"{k} = ${len(data) + i + 1}" for i, k in enumerate(where.keys())
        )
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        await self.execute(query, *data.values(), *where.values())

    # ── Convenience methods ───────────────────────────────

    async def create_goal(
        self, user_id: str, intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new goal and return it."""
        return await self.insert("goals", {
            "user_id": user_id,
            "intent": intent,
            "status": "pending",
        })

    async def update_goal_status(self, goal_id: str, status: str) -> None:
        """Update goal status."""
        await self.update(
            "goals",
            where={"id": goal_id},
            data={"status": status, "updated_at": "NOW()"},
        )

    async def insert_outbox(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Insert an event into the outbox."""
        return await self.insert("events_outbox", {
            "topic": topic,
            "payload": payload,
            "status": "pending",
        })