"""Core record store shared by persistent Core domains.

The store deliberately exposes a small document-oriented API.  Domain
managers own validation and their public types; this class only provides the
persistence boundary shared by agents, missions, knowledge and RAG documents.
It uses PostgreSQL as the durable source of truth, Redis as a read cache, and
keeps an in-process fallback for standalone development and tests.
"""

from __future__ import annotations

from copy import deepcopy
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CoreRecordStore:
    """Persist JSON-safe records without leaking storage concerns into domains.

    Args:
        pg_pool: Optional asyncpg-compatible pool.
        redis_client: Optional redis.asyncio-compatible client.
        cache_ttl: Redis record lifetime in seconds.
    """

    def __init__(
        self,
        pg_pool: Any | None = None,
        redis_client: Any | None = None,
        *,
        cache_ttl: int = 300,
    ) -> None:
        self._pg = pg_pool
        self._redis = redis_client
        self._cache_ttl = cache_ttl
        self._memory: dict[tuple[str, str], dict[str, Any]] = {}

    async def save(self, domain: str, record_id: str, record: dict[str, Any]) -> None:
        """Create or replace a record.

        The in-process copy is always updated first so standalone ETHAN keeps
        working when optional infrastructure is unavailable.
        """
        payload = self._clone(record)
        self._memory[(domain, record_id)] = payload

        persisted = False
        if self._pg is not None:
            try:
                await self._pg.execute(
                    """
                    INSERT INTO core_domain_records (domain, record_id, record, updated_at)
                    VALUES ($1, $2, $3::jsonb, NOW())
                    ON CONFLICT (domain, record_id)
                    DO UPDATE SET record = EXCLUDED.record, updated_at = NOW()
                    """,
                    domain,
                    record_id,
                    json.dumps(payload),
                )
                persisted = True
            except Exception as exc:  # infrastructure must not break Core work
                logger.warning("Core record save failed for %s/%s: %s", domain, record_id, exc)

        if self._redis is not None:
            try:
                await self._redis.set(
                    self._cache_key(domain, record_id),
                    json.dumps(payload),
                    ex=self._cache_ttl,
                )
            except Exception as exc:
                logger.warning("Core record cache save failed for %s/%s: %s", domain, record_id, exc)

        if not persisted and self._pg is not None:
            logger.info("Using in-process fallback for Core record %s/%s", domain, record_id)

    async def get(self, domain: str, record_id: str) -> dict[str, Any] | None:
        """Return a record by domain and identifier."""
        cached = self._memory.get((domain, record_id))
        if cached is not None:
            return self._clone(cached)

        if self._redis is not None:
            try:
                raw = await self._redis.get(self._cache_key(domain, record_id))
                if raw:
                    record = self._decode(raw)
                    self._memory[(domain, record_id)] = record
                    return self._clone(record)
            except Exception as exc:
                logger.warning("Core record cache read failed for %s/%s: %s", domain, record_id, exc)

        if self._pg is not None:
            try:
                row = await self._pg.fetchrow(
                    """
                    SELECT record FROM core_domain_records
                    WHERE domain = $1 AND record_id = $2
                    """,
                    domain,
                    record_id,
                )
                if row is not None:
                    record = self._decode(row["record"])
                    self._memory[(domain, record_id)] = record
                    await self._cache(domain, record_id, record)
                    return self._clone(record)
            except Exception as exc:
                logger.warning("Core record read failed for %s/%s: %s", domain, record_id, exc)

        return None

    async def list(self, domain: str) -> list[dict[str, Any]]:
        """Return all records in a domain, ordered by their latest update."""
        if self._pg is not None:
            try:
                rows = await self._pg.fetch(
                    """
                    SELECT record_id, record FROM core_domain_records
                    WHERE domain = $1
                    ORDER BY updated_at DESC, record_id ASC
                    """,
                    domain,
                )
                records: list[dict[str, Any]] = []
                for row in rows:
                    record_id = row["record_id"]
                    record = self._decode(row["record"])
                    self._memory[(domain, record_id)] = record
                    records.append(self._clone(record))
                return records
            except Exception as exc:
                logger.warning("Core record list failed for %s: %s", domain, exc)

        return [
            self._clone(record)
            for (stored_domain, _), record in self._memory.items()
            if stored_domain == domain
        ]

    async def delete(self, domain: str, record_id: str) -> bool:
        """Delete a record and return whether it existed."""
        existed = self._memory.pop((domain, record_id), None) is not None

        if self._pg is not None:
            try:
                result = await self._pg.execute(
                    "DELETE FROM core_domain_records WHERE domain = $1 AND record_id = $2",
                    domain,
                    record_id,
                )
                existed = existed or str(result).endswith("1")
            except Exception as exc:
                logger.warning("Core record delete failed for %s/%s: %s", domain, record_id, exc)

        if self._redis is not None:
            try:
                await self._redis.delete(self._cache_key(domain, record_id))
            except Exception as exc:
                logger.warning("Core record cache delete failed for %s/%s: %s", domain, record_id, exc)

        return existed

    async def _cache(self, domain: str, record_id: str, record: dict[str, Any]) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.set(
                self._cache_key(domain, record_id),
                json.dumps(record),
                ex=self._cache_ttl,
            )
        except Exception as exc:
            logger.debug("Core record cache refresh failed for %s/%s: %s", domain, record_id, exc)

    @staticmethod
    def _cache_key(domain: str, record_id: str) -> str:
        return f"ethan:core-records:{domain}:{record_id}"

    @staticmethod
    def _decode(raw: Any) -> dict[str, Any]:
        if isinstance(raw, str):
            return json.loads(raw)
        return dict(raw)

    @staticmethod
    def _clone(record: dict[str, Any]) -> dict[str, Any]:
        return deepcopy(record)
