"""Manager de persistance — injection et configuration."""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from core.persistence import Persistence, PersistenceConfig

logger = logging.getLogger(__name__)

_persistence: Persistence | None = None


def set_persistence_service(persistence: Persistence) -> None:
    global _persistence
    _persistence = persistence


async def get_persistence() -> Persistence:
    if _persistence is None:
        raise RuntimeError("Persistence service not initialized")
    return _persistence


async def init_persistence(
    config: PersistenceConfig | None = None,
    *,
    redis_client_factory: Callable[[str], Any] | None = None,
    pg_pool_factory: Callable[[str], Awaitable[Any]] | None = None,
) -> Persistence:
    """Initialise le service de persistance et l'expose au singleton.

    Les *factories* de driver proviennent de la couche interface
    (``interfaces/api/persistence/backend.py``) ; sans elles, les backends
    démarrent dégradés (absence de Redis/PostgreSQL tolérée).
    """
    global _persistence
    config = config or PersistenceConfig()
    _persistence = Persistence(
        config,
        redis_client_factory=redis_client_factory,
        pg_pool_factory=pg_pool_factory,
    )
    await _persistence.connect()
    logger.info(
        "Persistence initialized: Redis=%s PG=%s",
        _persistence.redis.connected,
        _persistence.postgres.connected,
    )
    return _persistence

