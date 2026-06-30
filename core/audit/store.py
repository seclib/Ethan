"""AuditStore — stockage append-only des entrées d'audit.

Deux modes de stockage :
1. PostgreSQL (primaire) — table `audit_log`, requêtable, persistant
2. JSON Lines (fallback) — fichier local, sans base de données

Le store publie chaque entrée sur l'EventBus pour que les autres
modules puissent réagir aux événements d'audit en temps réel.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from core.audit.types import AuditCategory, AuditDecision, AuditEntry

logger = logging.getLogger(__name__)

# Default paths
_AUDIT_DIR = Path.home() / ".ethan" / "audit"
_AUDIT_FILE = _AUDIT_DIR / "audit.jsonl"

# Maximum entries in memory ring buffer before flush
_MAX_MEMORY_ENTRIES = 10_000


class AuditStore:
    """Journal d'audit immuable — append-only.

    Les entrées sont :
    - Stockées en mémoire (ring buffer pour accès rapide)
    - Flushées vers PostgreSQL ou fichier JSONL
    - Publiées sur l'EventBus pour abonnés temps réel
    """

    def __init__(
        self,
        pg_conn: Any = None,
        jsonl_path: str | Path | None = None,
        publish_fn: Callable[[AuditEntry], None] | None = None,
        max_memory: int = _MAX_MEMORY_ENTRIES,
    ) -> None:
        self._pg_conn = pg_conn
        self._jsonl_path = Path(jsonl_path) if jsonl_path else _AUDIT_FILE
        self._publish_fn = publish_fn
        self._max_memory = max_memory

        # Ring buffer en mémoire (les plus récentes à la fin)
        self._buffer: list[AuditEntry] = []
        self._offset = 0  # pour gérer le ring buffer

        self._ensure_storage()
        self._load_existing()

    # ── Initialisation ──────────────────────────────────────────────

    def _ensure_storage(self) -> None:
        """Crée le répertoire de stockage si nécessaire et la table PG."""
        if self._pg_conn is not None:
            self._init_pg()
        else:
            self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("AuditStore: storage ready at %s", self._jsonl_path)

    def _init_pg(self) -> None:
        """Crée la table audit_log dans PostgreSQL."""
        try:
            cursor = self._pg_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    category TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    action TEXT NOT NULL DEFAULT '',
                    actor TEXT NOT NULL DEFAULT 'system',
                    source TEXT NOT NULL DEFAULT 'system',
                    details JSONB NOT NULL DEFAULT '{}',
                    correlation_id TEXT NOT NULL DEFAULT '',
                    tags TEXT[] NOT NULL DEFAULT '{}'
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                    ON audit_log(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_category
                    ON audit_log(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_decision
                    ON audit_log(decision)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_correlation
                    ON audit_log(correlation_id)
            """)
            self._pg_conn.commit()
            logger.info("AuditStore: PostgreSQL table audit_log ready")
        except Exception as e:
            logger.error("AuditStore: PostgreSQL init failed, fallback to JSONL: %s", e)
            self._pg_conn = None
            self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_existing(self) -> None:
        """Recharge les entrées existantes depuis le stockage persistant."""
        count = 0
        if self._pg_conn is not None:
            try:
                cursor = self._pg_conn.cursor()
                cursor.execute(
                    "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT %s",
                    (self._max_memory,),
                )
                for row in cursor.fetchall():
                    entry = AuditEntry(
                        id=row[0],
                        timestamp=row[1],
                        category=AuditCategory(row[2]),
                        decision=AuditDecision(row[3]),
                        action=row[4],
                        actor=row[5],
                        source=row[6],
                        details=row[7] or {},
                        correlation_id=row[8] or "",
                        tags=list(row[9]) if row[9] else [],
                    )
                    self._buffer.append(entry)
                    count += 1
            except Exception as e:
                logger.warning("AuditStore: PG load failed: %s", e)

        elif self._jsonl_path.exists():
            try:
                with self._jsonl_path.open("r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                entry = AuditEntry.from_dict(data)
                                self._buffer.append(entry)
                                count += 1
                            except (json.JSONDecodeError, KeyError) as e:
                                logger.warning("AuditStore: skipping malformed line: %s", e)
            except Exception as e:
                logger.warning("AuditStore: JSONL load failed: %s", e)

        logger.info("AuditStore: loaded %d existing entries", count)

    # ── API publique ────────────────────────────────────────────────

    def log(
        self,
        category: AuditCategory | str,
        decision: AuditDecision | str,
        action: str = "",
        actor: str = "system",
        source: str = "system",
        details: dict[str, Any] | None = None,
        correlation_id: str = "",
        tags: list[str] | None = None,
    ) -> AuditEntry:
        """Crée une entrée d'audit et la persiste.

        Retourne l'entrée créée (immuable).
        """
        if isinstance(category, str):
            category = AuditCategory(category)
        if isinstance(decision, str):
            decision = AuditDecision(decision)

        entry = AuditEntry(
            category=category,
            decision=decision,
            action=action,
            actor=actor,
            source=source,
            details=details or {},
            correlation_id=correlation_id,
            tags=tags or [],
        )

        self._append(entry)
        return entry

    def _append(self, entry: AuditEntry) -> None:
        """Ajoute une entrée au buffer et la persiste."""
        # Ring buffer
        if len(self._buffer) >= self._max_memory:
            self._buffer.pop(0)
        self._buffer.append(entry)

        # Persistance
        self._persist(entry)

        # Publication temps réel
        if self._publish_fn is not None:
            try:
                self._publish_fn(entry)
            except Exception as e:
                logger.warning("AuditStore: publish failed: %s", e)

    def _persist(self, entry: AuditEntry) -> None:
        """Écrit une entrée dans le stockage persistant."""
        data = entry.to_dict()

        if self._pg_conn is not None:
            try:
                cursor = self._pg_conn.cursor()
                cursor.execute(
                    """INSERT INTO audit_log
                       (id, timestamp, category, decision, action, actor, source, details, correlation_id, tags)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        data["id"],
                        data["timestamp"],
                        data["category"],
                        data["decision"],
                        data["action"],
                        data["actor"],
                        data["source"],
                        json.dumps(data["details"]),
                        data["correlation_id"],
                        data["tags"],
                    ),
                )
                self._pg_conn.commit()
            except Exception as e:
                logger.error("AuditStore: PG write failed: %s", e)

        else:
            try:
                with self._jsonl_path.open("a") as f:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error("AuditStore: JSONL write failed: %s", e)

    # ── Requêtes ────────────────────────────────────────────────────

    def recent(
        self,
        limit: int = 50,
        category: AuditCategory | str | None = None,
        decision: AuditDecision | str | None = None,
        actor: str | None = None,
        since: datetime | None = None,
    ) -> list[AuditEntry]:
        """Retourne les entrées d'audit les plus récentes, filtrées."""
        results = list(self._buffer)

        # Filtres
        if category is not None:
            cat_val = category.value if isinstance(category, AuditCategory) else category
            results = [e for e in results if e.category.value == cat_val]
        if decision is not None:
            dec_val = decision.value if isinstance(decision, AuditDecision) else decision
            results = [e for e in results if e.decision.value == dec_val]
        if actor is not None:
            results = [e for e in results if e.actor == actor]
        if since is not None:
            results = [e for e in results if e.timestamp >= since]

        # Tri décroissant par timestamp
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]

    def count(
        self,
        category: AuditCategory | str | None = None,
        since: datetime | None = None,
    ) -> int:
        """Compte les entrées d'audit."""
        results = list(self._buffer)
        if category is not None:
            cat_val = category.value if isinstance(category, AuditCategory) else category
            results = [e for e in results if e.category.value == cat_val]
        if since is not None:
            results = [e for e in results if e.timestamp >= since]
        return len(results)

    def search(self, query: str, limit: int = 20) -> list[AuditEntry]:
        """Recherche textuelle simple dans les entrées d'audit."""
        query_lower = query.lower()
        results = []
        for entry in reversed(self._buffer):
            if (
                query_lower in entry.action.lower()
                or query_lower in entry.actor.lower()
                or query_lower in entry.source.lower()
                or query_lower in entry.correlation_id.lower()
                or any(query_lower in str(v).lower() for v in entry.details.values())
            ):
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def summary(
        self,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Retourne un résumé des entrées d'audit."""
        entries = self._buffer
        if since is not None:
            entries = [e for e in entries if e.timestamp >= since]

        categories: dict[str, int] = {}
        decisions: dict[str, int] = {}
        actors: set[str] = set()

        for e in entries:
            cat = e.category.value
            categories[cat] = categories.get(cat, 0) + 1
            dec = e.decision.value
            decisions[dec] = decisions.get(dec, 0) + 1
            actors.add(e.actor)

        return {
            "total": len(entries),
            "categories": dict(sorted(categories.items(), key=lambda x: -x[1])),
            "decisions": dict(sorted(decisions.items(), key=lambda x: -x[1])),
            "actors": len(actors),
            "since": since.isoformat() if since else None,
        }

    def clear_buffer(self) -> None:
        """Vide le buffer mémoire (ne touche pas au stockage persistant)."""
        self._buffer.clear()
        logger.info("AuditStore: memory buffer cleared")