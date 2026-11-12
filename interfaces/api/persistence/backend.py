"""Backend de persistance — drivers tierces (couche interface).

Ce module est le **seul** endroit autorisé à importer les drivers
``redis``/``asyncpg`` pour la persistance unifiée : il fournit les *factories*
injectées dans ``core.persistence`` (ADR-1005 — technology independence).

Usage typique (lifespan de l'API) :

    from interfaces.api.persistence.backend import build_persistence
    persistence = build_persistence()          # lit REDIS_URL / DATABASE_URL
    await persistence.connect()                # dégradation gracieuse
"""

from __future__ import annotations

import os

from core.persistence import Persistence, PersistenceConfig

__all__ = [
    "redis_client_factory",
    "pg_pool_factory",
    "build_persistence",
]


def redis_client_factory(url: str):
    """Crée un client Redis async (protocol=2 requis par les cluster modernes)."""
    import redis.asyncio as aioredis

    return aioredis.from_url(url, decode_responses=True, protocol=2)


async def pg_pool_factory(dsn: str):
    """Crée un pool asyncpg (limité : la persistance n'est pas un pool web)."""
    import asyncpg

    return await asyncpg.create_pool(dsn, min_size=1, max_size=5)


def build_persistence(config: PersistenceConfig | None = None) -> Persistence:
    """Construit une ``Persistence`` câblée avec les drivers réels.

    Les URL viennent de ``REDIS_URL`` / ``DATABASE_URL`` sauf si ``config``
    les fournit explicitement.  ``connect()`` reste à appeler (async) — un
    driver indisponible laisse le backend dégradé sans faire échouer le boot.
    """
    if config is None:
        config = PersistenceConfig(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            database_url=os.getenv(
                "DATABASE_URL", "postgresql://ethan:ethan@postgres:5432/ethan"
            ),
            cache_ttl=int(os.getenv("PERSISTENCE_CACHE_TTL", "300")),
        )
    return Persistence(
        config,
        redis_client_factory=redis_client_factory,
        pg_pool_factory=pg_pool_factory,
    )
