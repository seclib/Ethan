"""Backends de persistance — enveloppes agnostiques de driver.

Ces classes ne comportent **aucun import** de ``redis``/``asyncpg`` (ADR-1005,
technology independence).  Le driver est fourni sous forme de *factory*
injectée par la couche interface (``interfaces/api/persistence/backend.py``) :

* Core définit le cycle de vie et la sémantique ;
* l'interface fournit les drivers tierces.

Une factory absente = backend dégradé (``connected`` faux, méthodes en échec
explicite) : ETHAN continue de fonctionner sans Redis/PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

__all__ = ["RedisBackend", "PostgresBackend", "BackendNotConnected"]


class BackendNotConnected(RuntimeError):
    """Le backend n'est pas connecté (driver absent ou connexion échouée)."""


class RedisBackend:
    """Backend « live state » (Redis) — agnostique de driver.

    ``client_factory(url)`` doit retourner un client compatible Redis async
    (``ping``/``get``/``set``/``delete``) — typiquement
    ``redis.asyncio.from_url`` fourni par l'interface.
    """

    def __init__(
        self,
        url: str,
        client_factory: Callable[[str], Any] | None = None,
        *,
        default_ttl: int = 300,
    ) -> None:
        self._url = url
        self._client_factory = client_factory
        self.default_ttl = default_ttl
        self._client: Any = None
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        if self._client_factory is None:
            logger.warning("RedisBackend dégradé : aucune factory de driver injectée")
            self._connected = False
            return False
        try:
            self._client = self._client_factory(self._url)
            await self._client.ping()
            self._connected = True
            logger.info("RedisBackend connecté (%s)", self._url)
            return True
        except Exception as exc:
            logger.warning("RedisBackend inaccessible : %s", exc)
            self._client = None
            self._connected = False
            return False

    async def close(self) -> None:
        client, self._client = self._client, None
        self._connected = False
        if client is not None:
            close = getattr(client, "aclose", None) or getattr(client, "close", None)
            if close is not None:
                result = close()
                if hasattr(result, "__await__"):
                    await result

    def _require(self) -> Any:
        if not self._connected or self._client is None:
            raise BackendNotConnected("RedisBackend non connecté")
        return self._client

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        client = self._require()
        ttl = ttl if ttl is not None else self.default_ttl
        await client.set(key, value, ex=ttl)
        return True

    async def get(self, key: str) -> str | None:
        client = self._require()
        return await client.get(key)

    async def delete(self, key: str) -> bool:
        client = self._require()
        return bool(await client.delete(key))


class PostgresBackend:
    """Backend « source de vérité » (PostgreSQL) — agnostique de driver.

    ``pool_factory(dsn)`` doit retourner (ou awaiter) un pool compatible
    ``asyncpg`` (``fetch``/``execute``) — typiquement
    ``asyncpg.create_pool`` fourni par l'interface.
    """

    def __init__(
        self,
        dsn: str,
        pool_factory: Callable[[str], Awaitable[Any]] | None = None,
    ) -> None:
        self._dsn = dsn
        self._pool_factory = pool_factory
        self._pool: Any = None
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        if self._pool_factory is None:
            logger.warning("PostgresBackend dégradé : aucune factory de driver injectée")
            self._connected = False
            return False
        try:
            pool = self._pool_factory(self._dsn)
            if hasattr(pool, "__await__"):
                pool = await pool
            self._pool = pool
            self._connected = True
            logger.info("PostgresBackend connecté")
            return True
        except Exception as exc:
            logger.warning("PostgresBackend inaccessible : %s", exc)
            self._pool = None
            self._connected = False
            return False

    async def close(self) -> None:
        pool, self._pool = self._pool, None
        self._connected = False
        if pool is not None:
            close = getattr(pool, "close", None)
            if close is not None:
                result = close()
                if hasattr(result, "__await__"):
                    await result

    def _require(self) -> Any:
        if not self._connected or self._pool is None:
            raise BackendNotConnected("PostgresBackend non connecté")
        return self._pool

    async def execute(self, sql: str, *args: Any) -> str:
        return await self._require().execute(sql, *args)

    async def fetch(self, sql: str, *args: Any) -> list[Any]:
        rows = await self._require().fetch(sql, *args)
        return list(rows)
