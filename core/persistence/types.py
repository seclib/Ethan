"""Types de configuration de la persistance."""
from __future__ import annotations


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
