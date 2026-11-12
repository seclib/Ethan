"""Durable persistence for MEM-014 application state (Phase 8)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4

SCHEMA_VERSION = 4

MIGRATIONS: list[tuple[int, str]] = [
    (1, """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS permission_requests (
        request_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS permission_grants (
        permission_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS authorization_decisions (
        decision_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        evaluated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS compliance_reports (
        evaluation_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        evaluated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS lifecycle_states (
        scope_key TEXT PRIMARY KEY,
        state TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS observability_events (
        event_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """),
]


MIGRATIONS.append((2, """
CREATE TABLE IF NOT EXISTS capability_definitions (
    capability_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS capability_history (
    history_id TEXT PRIMARY KEY,
    capability_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""))

MIGRATIONS.append((3, """
CREATE TABLE IF NOT EXISTS hrot_approval_requests (
    request_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hrot_consumed_proofs (
    proof_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    consumed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hrot_revoked_keys (
    key_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    revoked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hrot_audit_events (
    event_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""))

MIGRATIONS.append((4, """
CREATE TABLE IF NOT EXISTS application_registry_records (
    registration_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""))

MIGRATIONS.append((5, """
CREATE TABLE IF NOT EXISTS application_manifests (
    manifest_id TEXT PRIMARY KEY,
    app_id TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    payload TEXT NOT NULL,
    manifest_digest TEXT NOT NULL,
    source_type TEXT NOT NULL,
    repository_url TEXT,
    repository_path TEXT,
    git_revision TEXT,
    validation_status TEXT NOT NULL,
    validation_errors TEXT NOT NULL DEFAULT '[]',
    validator_version TEXT NOT NULL,
    validated_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (app_id, instance_id, version)
);
"""))

@dataclass
class ApplicationStateStore:
    """A small synchronous SQLite store for critical MEM-014 state."""

    path: str | Path
    _connection: sqlite3.Connection | None = None

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path), timeout=30)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._apply_migrations()

    def _apply_migrations(self) -> None:
        assert self._connection is not None
        cursor = self._connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        current = cursor.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
        for version, sql in MIGRATIONS:
            if version <= current:
                continue
            cursor.executescript(sql)
            cursor.execute("INSERT OR REPLACE INTO schema_migrations(version, applied_at) VALUES (?, datetime('now'))", (version,))
            self._connection.commit()

    @property
    def schema_version(self) -> int:
        assert self._connection is not None
        return self._connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]

    def close(self) -> None:
        if self._connection is not None:
            self._connection.commit()
            self._connection.close()
            self._connection = None

    def save_record(self, table: str, key: str, payload: Mapping[str, Any]) -> None:
        assert self._connection is not None
        if table == "permission_requests":
            column_key = "request_id"
            timestamp_column = "updated_at"
        elif table == "permission_grants":
            column_key = "permission_id"
            timestamp_column = "updated_at"
        elif table == "authorization_decisions":
            column_key = "decision_id"
            timestamp_column = "evaluated_at"
        elif table == "compliance_reports":
            column_key = "evaluation_id"
            timestamp_column = "evaluated_at"
        elif table == "observability_events":
            column_key = "event_id"
            timestamp_column = "timestamp"
        elif table == "capability_definitions":
            column_key = "capability_id"
            timestamp_column = "updated_at"
        elif table == "capability_history":
            column_key = "history_id"
            timestamp_column = "created_at"
        elif table == "hrot_approval_requests":
            column_key = "request_id"
            timestamp_column = "updated_at"
        elif table == "hrot_consumed_proofs":
            column_key = "proof_id"
            timestamp_column = "consumed_at"
        elif table == "hrot_revoked_keys":
            column_key = "key_id"
            timestamp_column = "revoked_at"
        elif table == "hrot_audit_events":
            column_key = "event_id"
            timestamp_column = "created_at"
        elif table == "application_registry_records":
            column_key = "registration_id"
            timestamp_column = "updated_at"
        elif table == "application_manifests":
            column_key = "manifest_id"
            timestamp_column = "updated_at"
        else:
            raise ValueError(f"unknown storage table: {table}")
        data = json.dumps(payload, sort_keys=True)
        timestamp = (
            payload.get("evaluated_at")
            or payload.get("timestamp")
            or payload.get("updated_at")
            or payload.get("created_at")
            or "now"
        )
        if table == "capability_history":
            self._connection.execute(
                "INSERT OR REPLACE INTO capability_history (history_id, capability_id, payload, created_at) VALUES (?, ?, ?, ?)",
                (key, str(payload.get("capability_id")), data, str(timestamp)),
            )
        elif table == "application_manifests":
            self._connection.execute(
                """
                INSERT OR REPLACE INTO application_manifests
                (manifest_id, app_id, instance_id, version, payload, manifest_digest,
                 source_type, repository_url, repository_path, git_revision,
                 validation_status, validation_errors, validator_version,
                 validated_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    str(payload.get("app_id")),
                    str(payload.get("instance_id")),
                    int(payload.get("record_version", payload.get("version", 1))),
                    data,
                    str(payload.get("manifest_digest", "")),
                    str(payload.get("source_type", "unknown")),
                    payload.get("repository_url"),
                    payload.get("repository_path"),
                    payload.get("git_revision"),
                    str(payload.get("validation_status", "unknown")),
                    json.dumps(payload.get("validation_errors", []), sort_keys=True),
                    str(payload.get("validator_version", "ethan-contract-validator")),
                    str(payload.get("validated_at", payload.get("created_at", ""))),
                    str(payload.get("created_at", timestamp)),
                    str(timestamp),
                ),
            )
        else:
            self._connection.execute(
                f"INSERT OR REPLACE INTO {table} ({column_key}, payload, {timestamp_column}) VALUES (?, ?, ?)",
                (key, data, str(timestamp)),
            )
        self._connection.commit()

    def load_records(self, table: str) -> list[dict[str, Any]]:
        assert self._connection is not None
        rows = self._connection.execute(f"SELECT payload FROM {table}").fetchall()
        return [json.loads(row[0]) for row in rows]

    def delete_record(self, table: str, key: str) -> None:
        assert self._connection is not None
        key_col = {
            "permission_requests": "request_id",
            "permission_grants": "permission_id",
            "authorization_decisions": "decision_id",
            "compliance_reports": "evaluation_id",
            "observability_events": "event_id",
            "application_manifests": "manifest_id",
        }[table]
        self._connection.execute(f"DELETE FROM {table} WHERE {key_col}=?", (key,))
        self._connection.commit()

    def save_lifecycle_state(self, scope_key: str, state: str) -> None:
        assert self._connection is not None
        self._connection.execute(
            "INSERT OR REPLACE INTO lifecycle_states (scope_key, state, updated_at) VALUES (?, ?, datetime('now'))",
            (scope_key, state),
        )
        self._connection.commit()

    def load_lifecycle_states(self) -> dict[str, str]:
        assert self._connection is not None
        return {row[0]: row[1] for row in self._connection.execute("SELECT scope_key, state FROM lifecycle_states").fetchall()}

    def transaction(self):
        assert self._connection is not None
        return self._connection


def open_application_state_store(path: str | Path) -> ApplicationStateStore:
    return ApplicationStateStore(path)


# Aliases
MEM14StateStore = ApplicationStateStore
PersistentStateStore = ApplicationStateStore
SqliteStateStore = ApplicationStateStore


__all__ = [
    "ApplicationStateStore",
    "MEM14StateStore",
    "PersistentStateStore",
    "SCHEMA_VERSION",
    "SqliteStateStore",
    "open_application_state_store",
]
