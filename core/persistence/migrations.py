"""Migrations de la couche de persistance."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MigrationManager:
    """Gestionnaire de migrations (PostgreSQL uniquement pour l'audit et les domaines)."""

    def __init__(self) -> None:
        self.applied: list[str] = []

    async def run(self, pg: Any) -> list[str]:
        """Applique les migrations idempotentes (CREATE TABLE IF NOT EXISTS).

        Backend dégradé (non connecté) : aucune migration appliquée, liste
        vide retournée — le boot continue, la persistance reste dégradée.
        """
        from core.persistence.backends import BackendNotConnected

        if pg is None or not getattr(pg, "connected", False):
            logger.warning("Migrations ignorées : PostgresBackend non connecté")
            return []
        migrations = self._available_migrations()
        for name in migrations:
            if name not in self.applied:
                logger.info("Migration %s en cours...", name)
                try:
                    await self._apply(pg, name)
                except BackendNotConnected:
                    logger.warning("Migration %s ignorée : backend non connecté", name)
                    break
                self.applied.append(name)
        return list(self.applied)

    def _available_migrations(self) -> list[str]:
        return [
            "0001_create_audit_log_table",
            "0002_create_core_domain_records",
            "0003_create_resource_log",
            "0004_create_event_store",
        ]

    async def _apply(self, pg: Any, name: str) -> None:
        if name == "0001_create_audit_log_table":
            await pg.execute(
                """CREATE TABLE IF NOT EXISTS audit_log (
                    id VARCHAR PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    category VARCHAR NOT NULL,
                    decision VARCHAR NOT NULL,
                    action TEXT NOT NULL,
                    actor VARCHAR NOT NULL,
                    source VARCHAR NOT NULL,
                    details JSONB NOT NULL DEFAULT '{}',
                    correlation_id VARCHAR,
                    tags TEXT[] NOT NULL DEFAULT '{}'
                );"""
            )
        elif name == "0002_create_core_domain_records":
            await pg.execute(
                """CREATE TABLE IF NOT EXISTS core_domain_records (
                    domain VARCHAR NOT NULL,
                    record_id VARCHAR NOT NULL,
                    record JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (domain, record_id)
                );"""
            )
