"""SQLite Memory Backend — Lightweight persistent storage (development default)."""

import json
import logging
import time
from pathlib import Path
from typing import Any

# Lazy import de sqlite3 pour respecter ADR-1005
def _get_sqlite():
    import sqlite3
    return sqlite3

from core.memory import MemoryBackend, MemoryEntry, MemoryResult

logger = logging.getLogger(__name__)


class SQLiteBackend(MemoryBackend):
    """SQLite backend for persistent memory storage.

    Used for:
    - Short-term conversation memory
    - Key-value storage
    - Development/testing (no external deps)
    """

    def __init__(self, db_path: str = "memory.db"):
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self):
        """Get or create database connection."""
        if self._conn is None:
            sqlite3 = _get_sqlite()
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        sqlite3 = _get_sqlite()
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                namespace TEXT NOT NULL DEFAULT 'default',
                metadata TEXT DEFAULT '{}',
                embedding BLOB DEFAULT NULL,
                timestamp REAL NOT NULL,
                ttl INTEGER DEFAULT NULL,
                PRIMARY KEY (key, namespace)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_namespace
            ON memory(namespace)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_timestamp
            ON memory(timestamp)
        """)
        conn.commit()

    async def store(self, entry: MemoryEntry) -> None:
        """Store an entry."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO memory (key, value, namespace, metadata, timestamp, ttl)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry.key,
                json.dumps(entry.value) if not isinstance(entry.value, str) else entry.value,
                entry.namespace,
                json.dumps(entry.metadata or {}),
                entry.timestamp or time.time(),
                entry.ttl,
            ),
        )
        conn.commit()

    async def retrieve(self, key: str, namespace: str = "default") -> MemoryEntry | None:
        """Retrieve an entry by key."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM memory WHERE key = ? AND namespace = ?",
            (key, namespace),
        )
        row = cursor.fetchone()
        if row:
            # Check TTL
            if row["ttl"] and time.time() > row["timestamp"] + row["ttl"]:
                conn.execute(
                    "DELETE FROM memory WHERE key = ? AND namespace = ?",
                    (key, namespace),
                )
                conn.commit()
                return None

            return MemoryEntry(
                key=row["key"],
                value=row["value"],
                namespace=row["namespace"],
                metadata=json.loads(row["metadata"]),
                timestamp=row["timestamp"],
                ttl=row["ttl"],
            )
        return None

    async def search(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 10,
        threshold: float = 0.0,
    ) -> list[MemoryResult]:
        """Search entries by keyword matching within namespace."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT * FROM memory
            WHERE namespace = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (namespace, limit),
        )

        results = []
        query_lower = query.lower()
        for row in cursor.fetchall():
            value_lower = row["value"].lower()
            # Simple relevance scoring based on keyword match
            score = 1.0 if query_lower in value_lower else 0.0
            if score >= threshold:
                results.append(MemoryResult(
                    key=row["key"],
                    value=row["value"],
                    namespace=row["namespace"],
                    metadata=json.loads(row["metadata"]),
                    score=score,
                    timestamp=row["timestamp"],
                ))

        return results

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete an entry."""
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM memory WHERE key = ? AND namespace = ?",
            (key, namespace),
        )
        conn.commit()
        return cursor.rowcount > 0

    async def list_namespaces(self) -> list[str]:
        """List all namespaces."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT DISTINCT namespace FROM memory")
        return [row["namespace"] for row in cursor.fetchall()]

    async def clear(self, namespace: str | None = None) -> None:
        """Clear entries, optionally for a namespace."""
        conn = self._get_conn()
        if namespace:
            conn.execute("DELETE FROM memory WHERE namespace = ?", (namespace,))
        else:
            conn.execute("DELETE FROM memory")
        conn.commit()