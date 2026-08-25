"""ProviderStore — Persistance de la configuration des providers LLM.

Stocke la configuration (pas les clés API) dans PostgreSQL (table JSONB)
avec un cache Redis. Si PostgreSQL est indisponible, fonctionne en mémoire.

⚠️ Les clés API ne sont JAMAIS persistées ici — elles vivent dans
`core/config/secrets.py` (env / Vault / Docker secrets).
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ProviderStore:
    """Persistance de la configuration des providers.

    Args:
        redis_client: Client Redis optionnel (async).
        pg_pool: Pool PostgreSQL optionnel (asyncpg).
    """

    def __init__(self, redis_client: Any | None = None, pg_pool: Any | None = None):
        self._redis = redis_client
        self._pg = pg_pool
        self._memory: dict[str, dict[str, Any]] = {}
        self._memory_default: str | None = None

    # ── API publique ────────────────────────────────────────────────────

    async def get_all(self) -> dict[str, dict[str, Any]]:
        """Retourne la config de tous les providers.

        Returns:
            Dict {provider_id: config}
        """
        if self._pg:
            try:
                rows = await self._pg.fetch(
                    "SELECT provider_id, config FROM llm_providers"
                )
                configs: dict[str, dict[str, Any]] = {}
                for row in rows:
                    cfg = row["config"]
                    # asyncpg retourne JSONB en str par défaut → désérialiser
                    if isinstance(cfg, str):
                        try:
                            cfg = json.loads(cfg)
                        except (TypeError, ValueError):
                            cfg = {}
                    configs[row["provider_id"]] = cfg if isinstance(cfg, dict) else {}
                return configs
            except Exception as e:
                logger.warning("PostgreSQL provider load failed, falling back: %s", e)

        if self._redis:
            try:
                raw = await self._redis.get("ethan:providers:all")
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.warning("Redis provider load failed, falling back: %s", e)

        return dict(self._memory)

    async def get(self, provider_id: str) -> dict[str, Any] | None:
        """Récupère la config d'un provider.

        Args:
            provider_id: ID du provider

        Returns:
            Config dict ou None si introuvable.
        """
        all_configs = await self.get_all()
        return all_configs.get(provider_id)

    async def save(self, provider_id: str, config: dict[str, Any]) -> None:
        """Sauvegarde la config d'un provider.

        Args:
            provider_id: ID du provider
            config: Config (sans secrets)
        """
        # Toujours mettre à jour le cache mémoire
        self._memory[provider_id] = config

        if self._pg:
            try:
                await self._pg.execute(
                    """
                    INSERT INTO llm_providers (provider_id, config, updated_at)
                    VALUES ($1, $2::jsonb, NOW())
                    ON CONFLICT (provider_id)
                    DO UPDATE SET config = EXCLUDED.config, updated_at = NOW()
                    """,
                    provider_id,
                    json.dumps(config),
                )
                await self._invalidate_cache()
                return
            except Exception as e:
                logger.warning("PostgreSQL provider save failed: %s", e)

        if self._redis:
            try:
                all_configs = await self.get_all()
                all_configs[provider_id] = config
                await self._redis.set(
                    "ethan:providers:all",
                    json.dumps(all_configs),
                    ex=300,  # TTL 5 min
                )
            except Exception as e:
                logger.warning("Redis provider save failed: %s", e)

    async def delete(self, provider_id: str) -> bool:
        """Supprime la config d'un provider.

        Args:
            provider_id: ID du provider

        Returns:
            True si supprimé, False sinon.
        """
        existed = provider_id in self._memory
        self._memory.pop(provider_id, None)

        if self._pg:
            try:
                result = await self._pg.execute(
                    "DELETE FROM llm_providers WHERE provider_id = $1",
                    provider_id,
                )
                existed = existed or "DELETE 1" in str(result)
                await self._invalidate_cache()
                return existed
            except Exception as e:
                logger.warning("PostgreSQL provider delete failed: %s", e)

        if self._redis:
            try:
                all_configs = await self.get_all()
                all_configs.pop(provider_id, None)
                await self._redis.set(
                    "ethan:providers:all",
                    json.dumps(all_configs),
                    ex=300,
                )
            except Exception as e:
                logger.warning("Redis provider delete failed: %s", e)

        return existed

    async def set_default(self, provider_id: str) -> None:
        """Définit le provider par défaut.

        Args:
            provider_id: ID du provider
        """
        self._memory_default = provider_id

        if self._redis:
            try:
                await self._redis.set("ethan:providers:default", provider_id, ex=300)
            except Exception as e:
                logger.warning("Redis default provider save failed: %s", e)

    async def get_default(self) -> str | None:
        """Retourne l'ID du provider par défaut.

        Returns:
            ID du provider ou None.
        """
        if self._memory_default:
            return self._memory_default

        if self._redis:
            try:
                default = await self._redis.get("ethan:providers:default")
                if default:
                    self._memory_default = default
                    return default
            except Exception as e:
                logger.warning("Redis default provider load failed: %s", e)

        # Défaut : premier provider actif
        all_configs = await self.get_all()
        for provider_id, cfg in all_configs.items():
            if cfg.get("enabled", False):
                self._memory_default = provider_id
                return provider_id
        return None

    async def _invalidate_cache(self) -> None:
        """Invalide le cache Redis."""
        if self._redis:
            try:
                await self._redis.delete("ethan:providers:all")
                logger.debug("Provider cache invalidated")
            except Exception as e:
                logger.warning("Redis cache invalidation failed: %s", e)

    async def close(self) -> None:
        """Ferme la connexion Redis éventuelle détenue par le store."""
        if self._redis:
            try:
                await self._redis.close()
                logger.debug("ProviderStore Redis connection closed")
            except Exception as e:
                logger.warning("Error closing Redis for ProviderStore: %s", e)
