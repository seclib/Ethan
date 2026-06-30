"""FactStore — Stockage des faits atomiques avec observations et relations.

Stockage principal : PostgreSQL (table facts, fact_observations, fact_relations)
Fallback : SQLite (via sqlite3 stdlib, avec FTS5)

Inspiré du MemoryKernel de Jarvis-OS, adapté pour l'architecture Ethan :
- PostgreSQL comme backend principal (vs SQLite dans Jarvis)
- Mêmes invariants (jamais de delete, archive/superseded)
- Recherche FTS5 avec BM25 (PostgreSQL tsvector ou SQLite FTS5)
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from core.facts.types import (
    Fact,
    FactCategory,
    FactObservation,
    FactRelation,
    FactRelationType,
    FactSearchResult,
    FactStatus,
    ObservationType,
)

logger = logging.getLogger(__name__)

_FACTS_DIR = Path.home() / ".ethan" / "facts"
_FACTS_DB = _FACTS_DIR / "facts.db"

_DEFAULT_PG_SCHEMA = """
    CREATE SCHEMA IF NOT EXISTS ethan;
"""

_PG_TABLES = """
    CREATE TABLE IF NOT EXISTS ethan.facts (
        id TEXT PRIMARY KEY,
        subject TEXT NOT NULL,
        predicate TEXT NOT NULL,
        object TEXT NOT NULL,
        category TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        confidence REAL NOT NULL DEFAULT 0.5,
        importance REAL NOT NULL DEFAULT 0.5,
        source TEXT NOT NULL DEFAULT 'system',
        source_event_id TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        tags TEXT[] NOT NULL DEFAULT '{}',
        metadata JSONB NOT NULL DEFAULT '{}'
    );

    CREATE TABLE IF NOT EXISTS ethan.fact_observations (
        id TEXT PRIMARY KEY,
        fact_id TEXT NOT NULL REFERENCES ethan.facts(id),
        event_id TEXT NOT NULL DEFAULT '',
        observation_type TEXT NOT NULL,
        confidence_delta REAL NOT NULL DEFAULT 0.0,
        source TEXT NOT NULL DEFAULT 'system',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS ethan.fact_relations (
        id TEXT PRIMARY KEY,
        from_fact_id TEXT NOT NULL REFERENCES ethan.facts(id),
        to_fact_id TEXT NOT NULL REFERENCES ethan.facts(id),
        relation_type TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_facts_subject ON ethan.facts(lower(subject));
    CREATE INDEX IF NOT EXISTS idx_facts_category ON ethan.facts(category, status);
    CREATE INDEX IF NOT EXISTS idx_facts_status ON ethan.facts(status);
    CREATE INDEX IF NOT EXISTS idx_facts_search ON ethan.facts USING gin(
        to_tsvector('english', subject || ' ' || predicate || ' ' || object)
    );
    CREATE INDEX IF NOT EXISTS idx_obs_fact_id ON ethan.fact_observations(fact_id);
    CREATE INDEX IF NOT EXISTS idx_rel_from ON ethan.fact_relations(from_fact_id);
    CREATE INDEX IF NOT EXISTS idx_rel_to ON ethan.fact_relations(to_fact_id);
"""

_SQLITE_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS facts (
        id TEXT PRIMARY KEY,
        subject TEXT NOT NULL,
        predicate TEXT NOT NULL,
        object TEXT NOT NULL,
        category TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        confidence REAL NOT NULL DEFAULT 0.5,
        importance REAL NOT NULL DEFAULT 0.5,
        source TEXT NOT NULL DEFAULT 'system',
        source_event_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        tags TEXT NOT NULL DEFAULT '[]',
        metadata TEXT NOT NULL DEFAULT '{}'
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sqlite_facts_subject ON facts(lower(subject))
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sqlite_facts_status ON facts(status)
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_observations (
        id TEXT PRIMARY KEY,
        fact_id TEXT NOT NULL,
        event_id TEXT NOT NULL DEFAULT '',
        observation_type TEXT NOT NULL,
        confidence_delta REAL NOT NULL DEFAULT 0.0,
        source TEXT NOT NULL DEFAULT 'system',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sqlite_obs_fact ON fact_observations(fact_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_relations (
        id TEXT PRIMARY KEY,
        from_fact_id TEXT NOT NULL,
        to_fact_id TEXT NOT NULL,
        relation_type TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sqlite_rel_from ON fact_relations(from_fact_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sqlite_rel_to ON fact_relations(to_fact_id)
    """,
    # FTS5 virtual table for full-text search
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
        fact_id UNINDEXED,
        text,
        tokenize='unicode61 remove_diacritics 1'
    )
    """,
    # Trigger to keep FTS index in sync
    """
    CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
        INSERT INTO facts_fts(fact_id, text)
        VALUES (new.id, lower(new.subject || ' ' || new.predicate || ' ' || new.object));
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
        INSERT INTO facts_fts(facts_fts, fact_id, text) VALUES('delete', old.id, '');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON facts BEGIN
        INSERT INTO facts_fts(facts_fts, fact_id, text) VALUES('delete', old.id, '');
        INSERT INTO facts_fts(fact_id, text)
        VALUES (new.id, lower(new.subject || ' ' || new.predicate || ' ' || new.object));
    END
    """,
]


class FactStore:
    """Stockage des faits atomiques.

    Deux modes :
    1. PostgreSQL (primaire) — tables dans schema ethan, recherche tsvector
    2. SQLite (fallback) — stdlib + FTS5, aucune dépendance externe
    """

    def __init__(
        self,
        pg_conn: Any = None,
        sqlite_path: str | Path | None = None,
        publish_fn: Any = None,
    ) -> None:
        self._pg_conn = pg_conn
        self._sqlite_path = Path(sqlite_path) if sqlite_path else _FACTS_DB
        self._publish_fn = publish_fn
        self._ensure_storage()

    # ── Initialisation ──────────────────────────────────────────────

    def _ensure_storage(self) -> None:
        if self._pg_conn is not None:
            self._init_pg()
        else:
            self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()

    def _init_pg(self) -> None:
        try:
            cursor = self._pg_conn.cursor()
            cursor.execute(_DEFAULT_PG_SCHEMA)
            cursor.execute(_PG_TABLES)
            self._pg_conn.commit()
            logger.info("FactStore: PostgreSQL schema ethan.facts ready")
        except Exception as e:
            logger.error("FactStore: PostgreSQL init failed, fallback SQLite: %s", e)
            self._pg_conn = None
            self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        with self._sqlite_conn() as conn:
            for stmt in _SQLITE_SCHEMA:
                conn.execute(stmt)
            conn.commit()
        logger.info("FactStore: SQLite ready at %s", self._sqlite_path)

    @contextmanager
    def _sqlite_conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self._sqlite_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    # ── Insertion / Mise à jour ─────────────────────────────────────

    def insert(self, fact: Fact) -> None:
        """Insère un nouveau fait."""
        if self._pg_conn is not None:
            self._pg_insert(fact)
        else:
            self._sqlite_insert(fact)

        self._publish("fact.created", {
            "fact_id": fact.id,
            "subject": fact.subject,
            "predicate": fact.predicate,
            "object": fact.object,
            "category": fact.category.value,
        })

    def _pg_insert(self, fact: Fact) -> None:
        cursor = self._pg_conn.cursor()
        cursor.execute(
            """INSERT INTO ethan.facts
               (id, subject, predicate, object, category, status, confidence, importance,
                source, source_event_id, created_at, updated_at, last_seen_at, tags, metadata)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                fact.id, fact.subject, fact.predicate, fact.object,
                fact.category.value, fact.status.value, fact.confidence, fact.importance,
                fact.source, fact.source_event_id,
                fact.created_at.isoformat(), fact.updated_at.isoformat(),
                fact.last_seen_at.isoformat(),
                fact.tags, json.dumps(fact.metadata),
            ),
        )
        self._pg_conn.commit()

    def _sqlite_insert(self, fact: Fact) -> None:
        with self._sqlite_conn() as conn:
            conn.execute(
                """INSERT INTO facts
                   (id, subject, predicate, object, category, status, confidence, importance,
                    source, source_event_id, created_at, updated_at, last_seen_at, tags, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fact.id, fact.subject, fact.predicate, fact.object,
                    fact.category.value, fact.status.value, fact.confidence, fact.importance,
                    fact.source, fact.source_event_id,
                    fact.created_at.isoformat(), fact.updated_at.isoformat(),
                    fact.last_seen_at.isoformat(),
                    json.dumps(fact.tags), json.dumps(fact.metadata),
                ),
            )
            conn.commit()

    def update(self, fact: Fact) -> None:
        """Met à jour un fait existant."""
        if self._pg_conn is not None:
            self._pg_update(fact)
        else:
            self._sqlite_update(fact)

        self._publish("fact.updated", {
            "fact_id": fact.id,
            "status": fact.status.value,
            "confidence": fact.confidence,
        })

    def _pg_update(self, fact: Fact) -> None:
        cursor = self._pg_conn.cursor()
        cursor.execute(
            """UPDATE ethan.facts SET
               status=%s, confidence=%s, importance=%s, updated_at=%s,
               last_seen_at=%s, tags=%s, metadata=%s
               WHERE id=%s""",
            (
                fact.status.value, fact.confidence, fact.importance,
                fact.updated_at.isoformat(), fact.last_seen_at.isoformat(),
                fact.tags, json.dumps(fact.metadata), fact.id,
            ),
        )
        self._pg_conn.commit()

    def _sqlite_update(self, fact: Fact) -> None:
        now = datetime.utcnow().isoformat()
        with self._sqlite_conn() as conn:
            conn.execute(
                """UPDATE facts SET status=?, confidence=?, importance=?,
                   updated_at=?, last_seen_at=?, tags=?, metadata=?
                   WHERE id=?""",
                (
                    fact.status.value, fact.confidence, fact.importance,
                    now, fact.last_seen_at.isoformat(),
                    json.dumps(fact.tags), json.dumps(fact.metadata), fact.id,
                ),
            )
            conn.commit()

    def upsert(self, fact: Fact) -> bool:
        """Insère ou met à jour. Retourne True si insertion, False si update."""
        existing = self.get(fact.id)
        if existing is not None:
            self.update(fact)
            return False
        self.insert(fact)
        return True

    # ── Lecture ─────────────────────────────────────────────────────

    def get(self, fact_id: str) -> Fact | None:
        """Récupère un fait par son ID."""
        if self._pg_conn is not None:
            return self._pg_get(fact_id)
        return self._sqlite_get(fact_id)

    def _pg_get(self, fact_id: str) -> Fact | None:
        cursor = self._pg_conn.cursor()
        cursor.execute("SELECT * FROM ethan.facts WHERE id=%s", (fact_id,))
        row = cursor.fetchone()
        return self._row_to_fact(row) if row else None

    def _sqlite_get(self, fact_id: str) -> Fact | None:
        with self._sqlite_conn() as conn:
            row = conn.execute("SELECT * FROM facts WHERE id=?", (fact_id,)).fetchone()
        return self._sqlite_row_to_fact(row) if row else None

    def find_active(
        self, subject: str, predicate: str, category: str | None = None
    ) -> Fact | None:
        """Cherche un fait ACTIF avec subject+predicate normalisé."""
        s, p = subject.strip().lower(), predicate.strip().lower()
        if self._pg_conn is not None:
            cursor = self._pg_conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM ethan.facts WHERE lower(subject)=%s AND lower(predicate)=%s AND category=%s AND status='active' ORDER BY last_seen_at DESC LIMIT 1",
                    (s, p, category),
                )
            else:
                cursor.execute(
                    "SELECT * FROM ethan.facts WHERE lower(subject)=%s AND lower(predicate)=%s AND status='active' ORDER BY last_seen_at DESC LIMIT 1",
                    (s, p),
                )
            row = cursor.fetchone()
            return self._row_to_fact(row) if row else None
        else:
            with self._sqlite_conn() as conn:
                if category:
                    row = conn.execute(
                        "SELECT * FROM facts WHERE lower(subject)=? AND lower(predicate)=? AND category=? AND status='active' ORDER BY last_seen_at DESC LIMIT 1",
                        (s, p, category),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT * FROM facts WHERE lower(subject)=? AND lower(predicate)=? AND status='active' ORDER BY last_seen_at DESC LIMIT 1",
                        (s, p),
                    ).fetchone()
            return self._sqlite_row_to_fact(row) if row else None

    def list_by_status(self, status: FactStatus, limit: int = 50) -> list[Fact]:
        """Liste les faits par statut."""
        if self._pg_conn is not None:
            cursor = self._pg_conn.cursor()
            cursor.execute(
                "SELECT * FROM ethan.facts WHERE status=%s ORDER BY last_seen_at DESC LIMIT %s",
                (status.value, limit),
            )
            return [self._row_to_fact(r) for r in cursor.fetchall()]
        else:
            with self._sqlite_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM facts WHERE status=? ORDER BY last_seen_at DESC LIMIT ?",
                    (status.value, limit),
                ).fetchall()
            return [self._sqlite_row_to_fact(r) for r in rows]

    def list_by_category(self, category: FactCategory, status: FactStatus = FactStatus.ACTIVE, limit: int = 50) -> list[Fact]:
        """Liste les faits par catégorie et statut."""
        if self._pg_conn is not None:
            cursor = self._pg_conn.cursor()
            cursor.execute(
                "SELECT * FROM ethan.facts WHERE category=%s AND status=%s ORDER BY last_seen_at DESC LIMIT %s",
                (category.value, status.value, limit),
            )
            return [self._row_to_fact(r) for r in cursor.fetchall()]
        else:
            with self._sqlite_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM facts WHERE category=? AND status=? ORDER BY last_seen_at DESC LIMIT ?",
                    (category.value, status.value, limit),
                ).fetchall()
            return [self._sqlite_row_to_fact(r) for r in rows]

    def count(self, status: FactStatus | None = None) -> int:
        """Compte les faits."""
        if self._pg_conn is not None:
            cursor = self._pg_conn.cursor()
            if status:
                cursor.execute("SELECT COUNT(*) FROM ethan.facts WHERE status=%s", (status.value,))
            else:
                cursor.execute("SELECT COUNT(*) FROM ethan.facts")
            return int(cursor.fetchone()[0])
        else:
            with self._sqlite_conn() as conn:
                if status:
                    row = conn.execute("SELECT COUNT(*) FROM facts WHERE status=?", (status.value,)).fetchone()
                else:
                    row = conn.execute("SELECT COUNT(*) FROM facts").fetchone()
            return int(row[0]) if row else 0

    # ── Recherche FTS ───────────────────────────────────────────────

    def search(self, query: str, k: int = 10) -> list[FactSearchResult]:
        """Recherche plein texte dans les faits."""
        if not query.strip():
            return []
        if self._pg_conn is not None:
            return self._pg_search(query, k)
        return self._sqlite_search(query, k)

    def _pg_search(self, query: str, k: int) -> list[FactSearchResult]:
        cursor = self._pg_conn.cursor()
        cursor.execute(
            """SELECT *, ts_rank(to_tsvector('english', subject || ' ' || predicate || ' ' || object),
                       plainto_tsquery('english', %s)) AS rank
               FROM ethan.facts
               WHERE to_tsvector('english', subject || ' ' || predicate || ' ' || object) @@
                     plainto_tsquery('english', %s)
               ORDER BY rank DESC LIMIT %s""",
            (query, query, k),
        )
        results = []
        for row in cursor.fetchall():
            fact = self._row_to_fact(row)
            rank = float(row[-1]) if row[-1] else 0.0
            results.append(FactSearchResult(fact=fact, score=rank, bm25=rank))
        return results

    def _sqlite_search(self, query: str, k: int) -> list[FactSearchResult]:
        safe_query = '"' + query.replace('"', ' ') + '"'
        with self._sqlite_conn() as conn:
            try:
                rows = conn.execute(
                    """SELECT facts.*, bm25(facts_fts) AS score
                       FROM facts_fts JOIN facts ON facts.id = facts_fts.fact_id
                       WHERE facts_fts MATCH ?
                       ORDER BY score LIMIT ?""",
                    (safe_query, k),
                ).fetchall()
            except sqlite3.OperationalError:
                return []
        results = []
        for row in rows:
            fact = self._sqlite_row_to_fact(row)
            score = float(row["score"]) if isinstance(row, sqlite3.Row) else 0.0
            bm25 = score
            results.append(FactSearchResult(fact=fact, score=bm25, bm25=bm25))
        return results

    # ── Observations ────────────────────────────────────────────────

    def record_observation(
        self,
        fact_id: str,
        observation_type: ObservationType,
        confidence_delta: float = 0.0,
        source: str = "system",
        event_id: str = "",
    ) -> FactObservation:
        """Enregistre une observation sur un fait."""
        obs = FactObservation(
            fact_id=fact_id,
            event_id=event_id,
            observation_type=observation_type,
            confidence_delta=confidence_delta,
            source=source,
        )
        if self._pg_conn is not None:
            cursor = self._pg_conn.cursor()
            cursor.execute(
                "INSERT INTO ethan.fact_observations(id, fact_id, event_id, observation_type, confidence_delta, source, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (obs.id, obs.fact_id, obs.event_id, obs.observation_type.value, obs.confidence_delta, obs.source, obs.created_at.isoformat()),
            )
            self._pg_conn.commit()
        else:
            with self._sqlite_conn() as conn:
                conn.execute(
                    "INSERT INTO fact_observations(id, fact_id, event_id, observation_type, confidence_delta, source, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (obs.id, obs.fact_id, obs.event_id, obs.observation_type.value, obs.confidence_delta, obs.source, obs.created_at.isoformat()),
                )
                conn.commit()
        return obs

    def list_observations(self, fact_id: str) -> list[FactObservation]:
        """Liste les observations d'un fait."""
        if self._pg_conn is not None:
            cursor = self._pg_conn.cursor()
            cursor.execute(
                "SELECT * FROM ethan.fact_observations WHERE fact_id=%s ORDER BY created_at",
                (fact_id,),
            )
            return [FactObservation(
                id=r[0], fact_id=r[1], event_id=r[2],
                observation_type=ObservationType(r[3]),
                confidence_delta=float(r[4]), source=r[5],
                created_at=datetime.fromisoformat(r[6]),
            ) for r in cursor.fetchall()]
        else:
            with self._sqlite_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM fact_observations WHERE fact_id=? ORDER BY created_at",
                    (fact_id,),
                ).fetchall()
            return [FactObservation(
                id=r["id"], fact_id=r["fact_id"], event_id=r["event_id"],
                observation_type=ObservationType(r["observation_type"]),
                confidence_delta=float(r["confidence_delta"]), source=r["source"],
                created_at=datetime.fromisoformat(r["created_at"]),
            ) for r in rows]

    # ── Relations ───────────────────────────────────────────────────

    def link(
        self, from_fact_id: str, to_fact_id: str, relation_type: FactRelationType
    ) -> FactRelation:
        """Crée une relation entre deux faits."""
        rel = FactRelation(
            from_fact_id=from_fact_id,
            to_fact_id=to_fact_id,
            relation_type=relation_type,
        )
        if self._pg_conn is not None:
            cursor = self._pg_conn.cursor()
            cursor.execute(
                "INSERT INTO ethan.fact_relations(id, from_fact_id, to_fact_id, relation_type, created_at) VALUES (%s, %s, %s, %s, %s)",
                (rel.id, rel.from_fact_id, rel.to_fact_id, rel.relation_type.value, rel.created_at.isoformat()),
            )
            self._pg_conn.commit()
        else:
            with self._sqlite_conn() as conn:
                conn.execute(
                    "INSERT INTO fact_relations(id, from_fact_id, to_fact_id, relation_type, created_at) VALUES (?, ?, ?, ?, ?)",
                    (rel.id, rel.from_fact_id, rel.to_fact_id, rel.relation_type.value, rel.created_at.isoformat()),
                )
                conn.commit()
        return rel

    def list_relations(self, fact_id: str) -> list[FactRelation]:
        """Liste les relations d'un fait (source ou cible)."""
        if self._pg_conn is not None:
            cursor = self._pg_conn.cursor()
            cursor.execute(
                "SELECT * FROM ethan.fact_relations WHERE from_fact_id=%s OR to_fact_id=%s ORDER BY created_at",
                (fact_id, fact_id),
            )
            return [FactRelation(
                id=r[0], from_fact_id=r[1], to_fact_id=r[2],
                relation_type=FactRelationType(r[3]),
                created_at=datetime.fromisoformat(r[4]),
            ) for r in cursor.fetchall()]
        else:
            with self._sqlite_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM fact_relations WHERE from_fact_id=? OR to_fact_id=? ORDER BY created_at",
                    (fact_id, fact_id),
                ).fetchall()
            return [FactRelation(
                id=r["id"], from_fact_id=r["from_fact_id"], to_fact_id=r["to_fact_id"],
                relation_type=FactRelationType(r["relation_type"]),
                created_at=datetime.fromisoformat(r["created_at"]),
            ) for r in rows]

    # ── Correction humaine ──────────────────────────────────────────

    def apply_correction(
        self,
        fact_id: str,
        new_object: str | None = None,
        new_status: FactStatus | None = None,
        new_confidence: float | None = None,
        correction_text: str = "",
        source: str = "user",
    ) -> tuple[bool, str]:
        """Applique une correction humaine à un fait."""
        fact = self.get(fact_id)
        if fact is None:
            return False, f"Fact {fact_id} not found"

        changes = []
        if new_object is not None:
            old = fact.object
            object.__set__(fact, new_object)
            changes.append(f"object: '{old}' → '{new_object}'")
        if new_status is not None:
            old = fact.status
            object.__set__(fact, new_status)
            changes.append(f"status: {old.value} → {new_status.value}")
        if new_confidence is not None:
            old = fact.confidence
            object.__set__(fact, max(0.0, min(1.0, new_confidence)))
            changes.append(f"confidence: {old} → {fact.confidence}")

        self.update(fact)
        self.record_observation(
            fact_id=fact.id,
            observation_type=ObservationType.CORRECT,
            source=source,
        )

        self._publish("fact.corrected", {
            "fact_id": fact.id,
            "changes": changes,
            "correction": correction_text,
            "source": source,
        })

        return True, "; ".join(changes)

    # ── Helpers ─────────────────────────────────────────────────────

    def _publish(self, event_type: str, data: dict[str, Any]) -> None:
        if self._publish_fn is not None:
            try:
                self._publish_fn({"type": event_type, **data})
            except Exception as e:
                logger.warning("FactStore: publish failed: %s", e)

    @staticmethod
    def _row_to_fact(row: Any) -> Fact | None:
        if row is None:
            return None
        try:
            # Row may be tuple or dict-like
            if hasattr(row, "keys"):
                d = dict(row)
            else:
                columns = [
                    "id", "subject", "predicate", "object", "category", "status",
                    "confidence", "importance", "source", "source_event_id",
                    "created_at", "updated_at", "last_seen_at", "tags", "metadata",
                ]
                d = dict(zip(columns, row))
            return Fact(
                id=d["id"], subject=d["subject"], predicate=d["predicate"],
                object=d["object"], category=FactCategory(d["category"]),
                status=FactStatus(d.get("status", "active")),
                confidence=float(d.get("confidence", 0.5)),
                importance=float(d.get("importance", 0.5)),
                source=d.get("source", "system"),
                source_event_id=d.get("source_event_id", ""),
                created_at=_parse_dt(d["created_at"]),
                updated_at=_parse_dt(d.get("updated_at", d["created_at"])),
                last_seen_at=_parse_dt(d.get("last_seen_at", d["created_at"])),
                tags=d.get("tags", []) if isinstance(d.get("tags"), list) else [],
                metadata=d.get("metadata", {}) if isinstance(d.get("metadata"), dict) else {},
            )
        except Exception as e:
            logger.error("FactStore: row parse error: %s", e)
            return None

    @staticmethod
    def _sqlite_row_to_fact(row: sqlite3.Row | None) -> Fact | None:
        if row is None:
            return None
        try:
            return Fact(
                id=row["id"], subject=row["subject"], predicate=row["predicate"],
                object=row["object"], category=FactCategory(row["category"]),
                status=FactStatus(row["status"] if "status" in row.keys() else "active"),
                confidence=float(row["confidence"]) if "confidence" in row.keys() else 0.5,
                importance=float(row["importance"]) if "importance" in row.keys() else 0.5,
                source=row["source"] if "source" in row.keys() else "system",
                source_event_id=row["source_event_id"] if "source_event_id" in row.keys() else "",
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]) if "updated_at" in row.keys() else datetime.fromisoformat(row["created_at"]),
                last_seen_at=datetime.fromisoformat(row["last_seen_at"]) if "last_seen_at" in row.keys() else datetime.fromisoformat(row["created_at"]),
                tags=json.loads(row["tags"]) if "tags" in row.keys() else [],
                metadata=json.loads(row["metadata"]) if "metadata" in row.keys() else {},
            )
        except Exception as e:
            logger.error("FactStore: sqlite row parse error: %s", e)
            return None


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()