"""Core persistence layer — interface minimale.

Ce module expose l'interface de persistance sans dépendre de librairies
tierce. Les implémentations concrètes (Redis, PostgreSQL) résident dans
``interfaces/api/persistence/`` où les drivers tierces sont autorisés.

``Persistence`` compose deux ``RedisBackend``/``PostgresBackend``
(voir ``core/persistence/backends.py``) dont les *factories* de driver sont
injectées depuis l'interface — jamais importées ici (ADR-1005).
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from core.persistence.backends import BackendNotConnected, PostgresBackend, RedisBackend

logger = logging.getLogger(__name__)

__all__ = ["Persistence", "PersistenceConfig"]


class PersistenceConfig:
    """Configuration de la couche de persistance."""

    def __init__(
        self,
        redis_url: str | None = None,
        database_url: str | None = None,
        cache_ttl: int = 300,
    ) -> None:
        self.redis_url = redis_url
        self.database_url = database_url
        self.cache_ttl = cache_ttl


class Persistence:
    """Persistance unifiée — Redis + PostgreSQL (sans imports de drivers).

    Les factories de driver (``redis.asyncio``, ``asyncpg``) sont injectées
    depuis ``interfaces/api/persistence/backend.py``.  Sans injection, chaque
    backend reste dégradé (``connected`` faux) : ETHAN fonctionne sans
    Redis/PostgreSQL mais les écritures levées par ``BackendNotConnected``
    restent explicites pour l'appelant.
    """

    def __init__(
        self,
        config: PersistenceConfig | None = None,
        *,
        redis_client_factory: Callable[[str], Any] | None = None,
        pg_pool_factory: Callable[[str], Awaitable[Any]] | None = None,
        redis_backend: RedisBackend | None = None,
        pg_backend: PostgresBackend | None = None,
    ) -> None:
        self._config = config or PersistenceConfig()
        self._redis = redis_backend or RedisBackend(
            self._config.redis_url or "redis://localhost:6379/0",
            redis_client_factory,
            default_ttl=self._config.cache_ttl,
        )
        self._pg = pg_backend or PostgresBackend(
            self._config.database_url or "",
            pg_pool_factory,
        )

    async def connect(self) -> None:
        """Connecte les deux backends ; dégradation gracieuse si absent."""
        await self._redis.connect()
        await self._pg.connect()
        logger.info(
            "Persistence initialisée : Redis=%s PG=%s",
            self._redis.connected,
            self._pg.connected,
        )

    async def close(self) -> None:
        await self._redis.close()
        await self._pg.close()

    @property
    def redis(self) -> RedisBackend:
        return self._redis

    @property
    def postgres(self) -> PostgresBackend:
        return self._pg

    async def set_live(self, key: str, value: Any, ttl: int | None = None) -> bool:
        return await self._redis.set(key, value, ttl)

    async def get_live(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def persist(self, table: str, payload: dict[str, Any], *params: Any) -> int:
        """Insère ``payload`` dans ``table`` (colonnes = clés du dict)."""
        if not table.replace("_", "").isalnum():
            raise ValueError(f"Nom de table invalide : {table!r}")
        columns = list(payload.keys())
        for column in columns:
            if not column.replace("_", "").isalnum():
                raise ValueError(f"Nom de colonne invalide : {column!r}")
        placeholders = ", ".join(f"${i}" for i in range(1, len(columns) + 1))
        sql = (
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT DO NOTHING"
        )
        await self._pg.execute(sql, *(payload[c] for c in columns), *params)
        return 1

    async def query(self, table: str, *params: Any) -> list[dict[str, Any]]:
        """Lit les lignes de ``table`` (lecture seule, sans filtre)."""
        if not table.replace("_", "").isalnum():
            raise ValueError(f"Nom de table invalide : {table!r}")
        rows = await self._pg.fetch(f"SELECT * FROM {table}", *params)
        return [dict(row) for row in rows]

