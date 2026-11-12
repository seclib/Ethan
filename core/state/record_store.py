"""Core record store shared by persistent Core domains.

The store deliberately exposes a small document-oriented API.  Domain
managers own validation and their public types; this class only provides the
persistence boundary shared by agents, missions, knowledge and RAG documents.
It uses PostgreSQL as the durable source of truth, Redis as a read cache, and
keeps an in-process fallback for standalone development and tests.
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from copy import deepcopy
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


class RecordStoreUnavailable(RuntimeError):
    """Le store de records est indisponible ou a échoué.

    Les méthodes « tolérantes » (`get`, `list`, `save`, `delete`) avalent les
    pannes d'infrastructure : le domaine continue de fonctionner, mais
    l'appelant ne peut pas distinguer « absent » de « inconnu ». Les
    méthodes « strictes » (`get_strict`, `list_strict`, `save_strict`) lèvent
    cette exception : un domaine qui doit garantir une invariant (exclusivité
    d'un rattachement) ne peut pas dégrader une panne en absence de donnée.
    """


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
        # Sérialisation locale par clé de garde : le repli en mémoire
        # (développement autonome, tests) doit garantir la même exclusion
        # mutuelle que la transaction PostgreSQL.
        self._guards: dict[str, asyncio.Lock] = {}

    # -- Lecture / écriture strictes -----------------------------------

    async def get_strict(self, domain: str, record_id: str) -> dict[str, Any] | None:
        """Lecture qui **ne masque pas** une panne d'infrastructure.

        Contrairement à `get`, une indisponibilité de PostgreSQL ou de Redis
        lève `RecordStoreUnavailable` au lieu de se déguiser en « absent ».
        Un domaine qui doit garantir une invariant ne peut pas confondre
        l'absence d'une donnée et l'incapacité de la lire.

        Args:
            domain: Domaine de persistance.
            record_id: Identifiant du record.

        Returns:
            Le record, ou None s'il n'existe pas.

        Raises:
            RecordStoreUnavailable: Si la source durable est inaccessible.
        """
        cached = self._memory.get((domain, record_id))
        if cached is not None:
            return self._clone(cached)

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
            except Exception as exc:
                raise RecordStoreUnavailable(
                    f"read failed for {domain}/{record_id}: {exc}"
                ) from exc
            if row is not None:
                record = self._decode(row["record"])
                self._memory[(domain, record_id)] = record
                await self._cache(domain, record_id, record)
                return self._clone(record)

        if self._redis is not None:
            try:
                raw = await self._redis.get(self._cache_key(domain, record_id))
            except Exception as exc:
                raise RecordStoreUnavailable(
                    f"cache read failed for {domain}/{record_id}: {exc}"
                ) from exc
            if raw:
                record = self._decode(raw)
                self._memory[(domain, record_id)] = record
                return self._clone(record)

        return None

    async def list_strict(self, domain: str) -> list[dict[str, Any]]:
        """Liste qui **ne masque pas** une panne d'infrastructure.

        Args:
            domain: Domaine de persistance.

        Returns:
            Les records du domaine.

        Raises:
            RecordStoreUnavailable: Si la source durable est inaccessible.
        """
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
            except Exception as exc:
                raise RecordStoreUnavailable(f"list failed for {domain}: {exc}") from exc
            records: list[dict[str, Any]] = []
            for row in rows:
                record = self._decode(row["record"])
                self._memory[(domain, row["record_id"])] = record
                records.append(self._clone(record))
            return records

        return [
            self._clone(record)
            for (stored_domain, _), record in self._memory.items()
            if stored_domain == domain
        ]

    async def save_strict(
        self, domain: str, record_id: str, record: dict[str, Any]
    ) -> None:
        """Écriture qui **ne masque pas** une panne d'infrastructure.

        `save` journalise l'échec et continue : l'appelant croit avoir
        écrit. `save_strict` lève, ce qui permet à un domaine de ne pas
        annoncer un état qui n'a pas été persisté.

        Args:
            domain: Domaine de persistance.
            record_id: Identifiant du record.
            record: Contenu du record.

        Raises:
            RecordStoreUnavailable: Si l'écriture durable a échoué.
        """
        payload = self._clone(record)
        self._memory[(domain, record_id)] = payload

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
            except Exception as exc:
                raise RecordStoreUnavailable(
                    f"save failed for {domain}/{record_id}: {exc}"
                ) from exc

        if self._redis is not None:
            try:
                await self._redis.set(
                    self._cache_key(domain, record_id),
                    json.dumps(payload),
                    ex=self._cache_ttl,
                )
            except Exception as exc:
                logger.warning(
                    "Core record cache save failed for %s/%s: %s", domain, record_id, exc
                )

    # -- Section critique ------------------------------------------------

    @asynccontextmanager
    async def atomic(self, guard: str) -> AsyncIterator[None]:
        """Section critique sérialisée par clé de garde.

        Le store ne fournit **pas** de contrôle de concurrence : `save()`
        est un upsert simple, sans transaction ni verrou. Un domaine qui doit
        garantir une invariant sur plusieurs enregistrements (par exemple
        « une ancre exclusive n'appartient qu'à un seul projet ») ne peut pas
        se contenter d'un contrôle suivi d'une écriture : deux opérations
        concurrentes peuvent passer le contrôle avant de s'écrire.

        Cette primitive apporte la garantie manquante **sans nouvelle base,
        sans nouveau daemon et sans migration** :

        * avec PostgreSQL, une transaction réelle est ouverte et un verrou
          consultatif `pg_advisory_xact_lock` est pris sur la clé de garde ;
          toute autre transaction prenant la même clé attend la fin de
          celle-ci ;
        * sans PostgreSQL (développement autonome, tests), un verrou
          `asyncio.Lock` par clé est utilisé : l'exclusion mutuelle est
          garantie dans le processus.

        Args:
            guard: Clé de garde (ex. le triplet type/cible d'un rattachement).

        Yields:
            None, à l'intérieur de la section critique.
        """
        if self._pg is not None:
            acquire = self._pg.acquire()
            try:
                connection = await acquire.__aenter__()
            except Exception as exc:
                raise RecordStoreUnavailable(f"atomic section unavailable: {exc}") from exc
            try:
                async with connection.transaction():
                    try:
                        await connection.execute(
                            "SELECT pg_advisory_xact_lock(hashtext($1))", guard
                        )
                    except Exception as exc:
                        raise RecordStoreUnavailable(
                            f"advisory lock unavailable: {exc}"
                        ) from exc
                    # Le corps de la section peut lever : l'exception est
                    # propagée telle quelle, la transaction est annulée.
                    yield
            finally:
                await acquire.__aexit__(None, None, None)
            return

        lock = self._guards.get(guard)
        if lock is None:
            lock = asyncio.Lock()
            self._guards[guard] = lock
        async with lock:
            yield

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
                logger.warning(
                    "Core record cache save failed for %s/%s: %s", domain, record_id, exc
                )

        if not persisted and self._pg is not None:
            logger.info("Using in-process fallback for Core record %s/%s", domain, record_id)

    async def get(self, domain: str, record_id: str) -> dict[str, Any] | None:
        """Return a record by domain and identifier.

        Source de vérité : PostgreSQL. La mémoire du process est le cache
        chaud ; Redis n'est relu qu'en dernier recours. Lire Redis AVANT
        PostgreSQL rendait l'état durable invisible tant que le cache vivait
        (TTL 300 s) : après un redémarrage de l'API, une capability resterait
        bloquée sur un état périmé (INSTALLING fantôme) alors que la base
        disait autre chose.
        """
        cached = self._memory.get((domain, record_id))
        if cached is not None:
            return self._clone(cached)

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

        if self._redis is not None:
            try:
                raw = await self._redis.get(self._cache_key(domain, record_id))
                if raw:
                    record = self._decode(raw)
                    self._memory[(domain, record_id)] = record
                    return self._clone(record)
            except Exception as exc:
                logger.warning(
                    "Core record cache read failed for %s/%s: %s", domain, record_id, exc
                )

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
                logger.warning(
                    "Core record cache delete failed for %s/%s: %s", domain, record_id, exc
                )

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
