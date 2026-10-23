"""PostgreSQL Store — Long-term Memory.

Stockage persistant pour :
- Event log (append-only)
- Goals (state machine)
- Module snapshots
- Apprentissages
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from core.memory.interface import MemoryStore, SearchResult

logger = logging.getLogger(__name__)


class PGStore(MemoryStore):
    """Implémentation PostgreSQL du MemoryStore.

    Utilise PostgreSQL comme long-term memory :
    - Events append-only (jamais modifiés)
    - Goals avec historique
    - Snapshots de modules
    - Support pgvector optionnel pour embeddings
    """

    def __init__(
        self,
        url: str = "postgresql://ethan:ethan@localhost:5432/ethan",
        pool_size: int = 5,
    ):
        self._url = url
        self._pool_size = pool_size
        self._pool: Any = None  # asyncpg.Pool

    async def connect(self) -> None:
        """Connexion à PostgreSQL."""
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self._url,
                min_size=1,
                max_size=self._pool_size,
            )
            logger.info(f"PGStore connected to {self._url}")
        except ImportError:
            raise RuntimeError(
                "asyncpg not installed. Install with: pip install asyncpg"
            )
        except Exception as e:
            raise ConnectionError(f"Cannot connect to PostgreSQL at {self._url}: {e}")

    async def close(self) -> None:
        """Ferme la connexion."""
        if self._pool:
            await self._pool.close()

    async def store(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Stocke une valeur (avec timestamp)."""
        if not self._pool:
            await self.connect()

        data = json.dumps(value) if not isinstance(value, str) else value
        now = datetime.utcnow()

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO memory_store (namespace, key, value, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (namespace, key) DO UPDATE
                SET value = $3, updated_at = $5
                """,
                namespace,
                key,
                data,
                now,
                now,
            )

    async def get(self, namespace: str, key: str) -> Any | None:
        """Récupère une valeur."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT value FROM memory_store WHERE namespace = $1 AND key = $2",
                namespace,
                key,
            )
            if not row:
                return None

            try:
                return json.loads(row["value"])
            except json.JSONDecodeError:
                return row["value"]

    async def delete(self, namespace: str, key: str) -> None:
        """Supprime une valeur."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM memory_store WHERE namespace = $1 AND key = $2",
                namespace,
                key,
            )

    async def list_namespace(self, namespace: str) -> list[str]:
        """Liste toutes les clés dans un namespace."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT key FROM memory_store WHERE namespace = $1",
                namespace,
            )
            return [row["key"] for row in rows]

    async def search(
        self,
        namespace: str,
        query: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Recherche simple (LIKE) dans PostgreSQL.

        Pour la recherche sémantique, utiliser VectorStore.
        """
        if not self._pool:
            await self.connect()

        pattern = f"%{query}%"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT key, value, created_at
                FROM memory_store
                WHERE namespace = $1 AND value ILIKE $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                namespace,
                pattern,
                limit,
            )

            results = []
            for row in rows:
                try:
                    value = json.loads(row["value"])
                except json.JSONDecodeError:
                    value = row["value"]

                results.append(SearchResult(
                    key=row["key"],
                    value=value,
                    score=1.0,
                    metadata={"created_at": row["created_at"].isoformat()},
                ))

            return results

    async def exists(self, namespace: str, key: str) -> bool:
        """Vérifie si une clé existe."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM memory_store WHERE namespace = $1 AND key = $2",
                namespace,
                key,
            )
            return row is not None

    async def ttl(self, namespace: str, key: str) -> int | None:
        """PostgreSQL n'a pas de TTL natif. Retourne None."""
        return None

    # ─── Méthodes spécifiques ────────────────────────────────────────

    async def store_event(self, event: dict[str, Any]) -> str:
        """Stocke un événement dans l'event log.

        Args:
            event: Dict avec id, type, source, timestamp, payload, metadata

        Returns:
            ID de l'événement
        """
        if not self._pool:
            await self.connect()

        event_id = event.get("id", "")
        now = datetime.utcnow()

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO event_log (id, type, source, timestamp, payload, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO NOTHING
                """,
                event_id,
                event.get("type"),
                event.get("source"),
                datetime.fromisoformat(event.get("timestamp", now.isoformat())),
                json.dumps(event.get("payload", {})),
                json.dumps(event.get("metadata", {})),
                now,
            )

        return event_id

    async def get_events(
        self,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Récupère les événements de l'event log.

        Args:
            event_type: Filtrer par type d'événement
            limit: Nombre max de résultats
            offset: Offset pour pagination

        Returns:
            Liste d'événements
        """
        if not self._pool:
            await self.connect()

        query = "SELECT * FROM event_log"
        params = []
        if event_type:
            query += " WHERE type = $1"
            params.append(event_type)
        query += f" ORDER BY timestamp DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        params.extend([limit, offset])

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            events = []
            for row in rows:
                events.append({
                    "id": row["id"],
                    "type": row["type"],
                    "source": row["source"],
                    "timestamp": row["timestamp"].isoformat(),
                    "payload": json.loads(row["payload"]),
                    "metadata": json.loads(row["metadata"]),
                })

            return events

    async def init_schema(self) -> None:
        """Crée les tables si elles n'existent pas."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            # Table memory_store
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_store (
                    namespace VARCHAR(255) NOT NULL,
                    key VARCHAR(255) NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (namespace, key)
                )
            """)

            # Table event_log (append-only)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS event_log (
                    id VARCHAR(255) PRIMARY KEY,
                    type VARCHAR(255) NOT NULL,
                    source VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    payload JSONB,
                    metadata JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)

            # Index pour les requêtes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_log_type
                ON event_log(type)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_log_timestamp
                ON event_log(timestamp DESC)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_store_namespace
                ON memory_store(namespace)
            """)

            logger.info("✅ PostgreSQL schema initialized")