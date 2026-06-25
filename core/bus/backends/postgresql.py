"""PostgreSQL Backend — Stockage via PostgreSQL."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, AsyncIterator

from core.bus.backends.base import StorageBackend
from core.bus.store import StoredEvent, Checkpoint
from core.bus.snapshot import Snapshot

logger = logging.getLogger(__name__)


class PostgreSQLBackend(StorageBackend):
    """Backend PostgreSQL.
    
    Pour archive et requêtes complexes.
    - SQL puissant
    - Durable
    - pgvector pour embeddings
    """

    def __init__(self, connection_string: str):
        self._connection_string = connection_string
        self._pool = None

    async def initialize(self) -> None:
        """Initialise la connexion."""
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(self._connection_string)
            logger.info("PostgreSQL backend initialized")
        except ImportError:
            logger.warning("asyncpg not installed")

    async def write(self, stored_event: StoredEvent) -> None:
        """Écrit un événement."""
        if not self._pool:
            raise RuntimeError("PostgreSQL not initialized")

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO events (id, type, source, timestamp, payload, metadata, position)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                stored_event.event.id,
                stored_event.event.type.value,
                stored_event.event.source,
                stored_event.event.timestamp,
                stored_event.event.payload,
                stored_event.event.metadata,
                stored_event.position,
            )

    async def read(
        self,
        subject_pattern: str,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> AsyncIterator[StoredEvent]:
        """Lit les événements."""
        if not self._pool:
            return

        async with self._pool.acquire() as conn:
            query = """
                SELECT id, type, source, timestamp, payload, metadata, position
                FROM events
                WHERE timestamp >= $1
            """
            params = [start_time]

            if end_time:
                query += " AND timestamp <= $2"
                params.append(end_time)

            query += " ORDER BY position ASC"

            rows = await conn.fetch(query, *params)

            for row in rows:
                from core.types.event import Event, EventType
                event = Event(
                    id=row["id"],
                    type=EventType(row["type"]),
                    source=row["source"],
                    timestamp=row["timestamp"],
                    payload=row["payload"],
                    metadata=row["metadata"],
                )
                yield StoredEvent(
                    event=event,
                    position=row["position"],
                    stored_at=row["timestamp"],
                    size_bytes=len(str(row["payload"])),
                )

    async def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Sauvegarde un checkpoint."""
        if not self._pool:
            return

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO checkpoints (id, subject_pattern, timestamp, position, metadata)
                VALUES ($1, $2, $3, $4, $5)
                """,
                checkpoint.id,
                checkpoint.subject_pattern,
                checkpoint.timestamp,
                checkpoint.position,
                checkpoint.metadata,
            )

    async def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Récupère un checkpoint."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM checkpoints WHERE id = $1",
                checkpoint_id,
            )

            if row:
                return Checkpoint(
                    id=row["id"],
                    subject_pattern=row["subject_pattern"],
                    timestamp=row["timestamp"],
                    position=row["position"],
                    metadata=row["metadata"],
                )
            return None

    async def get_latest_checkpoint(self, subject_pattern: str) -> Checkpoint | None:
        """Récupère le dernier checkpoint."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM checkpoints
                WHERE subject_pattern = $1
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                subject_pattern,
            )

            if row:
                return Checkpoint(
                    id=row["id"],
                    subject_pattern=row["subject_pattern"],
                    timestamp=row["timestamp"],
                    position=row["position"],
                    metadata=row["metadata"],
                )
            return None

    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Sauvegarde un snapshot."""
        if not self._pool:
            return

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO snapshots (id, position, state, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5)
                """,
                snapshot.id,
                snapshot.position,
                snapshot.state,
                snapshot.created_at,
                snapshot.metadata,
            )

    async def get_snapshot(self, snapshot_id: str) -> Snapshot | None:
        """Récupère un snapshot."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM snapshots WHERE id = $1",
                snapshot_id,
            )

            if row:
                return Snapshot(
                    id=row["id"],
                    position=row["position"],
                    state=row["state"],
                    created_at=row["created_at"],
                    metadata=row["metadata"],
                )
            return None

    async def get_latest_snapshot(self) -> Snapshot | None:
        """Récupère le dernier snapshot."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM snapshots ORDER BY created_at DESC LIMIT 1"
            )

            if row:
                return Snapshot(
                    id=row["id"],
                    position=row["position"],
                    state=row["state"],
                    created_at=row["created_at"],
                    metadata=row["metadata"],
                )
            return None

    async def get_snapshot_at_position(self, position: int) -> Snapshot | None:
        """Récupère le snapshot le plus proche."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM snapshots
                WHERE position <= $1
                ORDER BY position DESC
                LIMIT 1
                """,
                position,
            )

            if row:
                return Snapshot(
                    id=row["id"],
                    position=row["position"],
                    state=row["state"],
                    created_at=row["created_at"],
                    metadata=row["metadata"],
                )
            return None

    async def delete_snapshot(self, snapshot_id: str) -> None:
        """Supprime un snapshot."""
        if not self._pool:
            return

        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM snapshots WHERE id = $1",
                snapshot_id,
            )