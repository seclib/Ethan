"""ConfigStore — Persistance de la configuration centralisee.

Stocke la configuration ETHAN dans PostgreSQL (JSONB) avec cache Redis.
PostgreSQL indisponible → bascule en memoire.

Les cles API / secrets ne sont JAMAIS persistees ici — elles vivent dans
``core/config/secrets.py`` (env / Vault / Docker secrets).
"""

from __future__ import annotations
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConfigStore:
    """Persistance de la configuration globale.

    Args:
        redis_client: Client Redis optionnel (async).
        pg_pool: Pool PostgreSQL optionnel (asyncpg).
    """

    def __init__(self, redis_client: Any | None = None, pg_pool: Any | None = None):
        self._redis = redis_client
        self._pg = pg_pool
        self._memory: dict[str, dict[str, Any]] = {}

    async def get_all(self) -> dict[str, dict[str, Any]]:
        """Retourne la config de tous les domaines."""
        if self._pg:
            try:
                rows = await self._pg.fetch(
                    "SELECT domain_name, config FROM ethan_config"
                )
                return {row["domain_name"]: row["config"] for row in rows}
            except Exception as e:
                logger.warning("PostgreSQL config load failed, falling back: %s", e)

        if self._redis:
            try:
                raw = await self._redis.get("ethan:config:all")
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.warning("Redis config load failed, falling back: %s", e)

        return dict(self._memory)

    async def get(self, domain: str) -> dict[str, Any] | None:
        """Recupere la config d'un domaine."""
        all_configs = await self.get_all()
        return all_configs.get(domain)

    async def save(self, domain: str, config: dict[str, Any]) -> None:
        """Sauvegarde la config d'un domaine."""
        self._memory[domain] = config

        if self._pg:
            try:
                await self._pg.execute(
                    """
                    INSERT INTO ethan_config (domain_name, config, updated_at)
                    VALUES ($1, $2::jsonb, NOW())
                    ON CONFLICT (domain_name)
                    DO UPDATE SET config = EXCLUDED.config, updated_at = NOW()
                    """,
                    domain,
                    json.dumps(config),
                )
                await self._invalidate_cache()
                return
            except Exception as e:
                logger.warning("PostgreSQL config save failed: %s", e)

        if self._redis:
            try:
                all_configs = await self.get_all()
                all_configs[domain] = config
                await self._redis.set(
                    "ethan:config:all",
                    json.dumps(all_configs),
                    ex=300,
                )
            except Exception as e:
                logger.warning("Redis config save failed: %s", e)

    async def delete(self, domain: str) -> bool:
        """Supprime la config d'un domaine."""
        existed = domain in self._memory
        self._memory.pop(domain, None)

        if self._pg:
            try:
                result = await self._pg.execute(
                    "DELETE FROM ethan_config WHERE domain_name = $1",
                    domain,
                )
                existed = existed or "DELETE 1" in str(result)
                await self._invalidate_cache()
                return existed
            except Exception as e:
                logger.warning("PostgreSQL config delete failed: %s", e)

        if self._redis:
            try:
                all_configs = await self.get_all()
                all_configs.pop(domain, None)
                await self._redis.set(
                    "ethan:config:all",
                    json.dumps(all_configs),
                    ex=300,
                )
            except Exception as e:
                logger.warning("Redis config delete failed: %s", e)

        return existed

    async def _invalidate_cache(self) -> None:
        """Invalide le cache Redis."""
        if self._redis:
            try:
                await self._redis.delete("ethan:config:all")
                logger.debug("Config cache invalidated")
            except Exception as e:
                logger.warning("Redis cache invalidation failed: %s", e)

    async def close(self) -> None:
        """Ferme la connexion Redis."""
        if self._redis:
            try:
                await self._redis.close()
                logger.debug("ConfigStore Redis connection closed")
            except Exception as e:
                logger.warning("Error closing Redis for ConfigStore: %s", e)