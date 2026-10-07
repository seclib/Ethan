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


class ProviderDefaultError(RuntimeError):
    """Le provider par défaut n'a pas pu être rendu durable (fail-closed).

    Distingué du `RuntimeError` d'infrastructure pour ne pas être confondu
    avec l'erreur Postgres sous-jacente : l'appelant veut savoir que le
    réglage n'est *pas* garanti, pas analyser la panne SQL.
    """


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
                rows = await self._pg.fetch("SELECT provider_id, config FROM llm_providers")
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
        """Définit le provider par défaut — PostgreSQL fait foi.

        La colonne ``llm_providers.is_default`` (migration 004) existe
        précisément pour cela. Ni la mémoire du processus ni le cache Redis ne
        sont une source de vérité : le défaut doit survivre à un refresh de la
        WebUI, à un restart/recreate de l'API et à une expiration Redis.

        Fail-closed : si PostgreSQL est configuré mais que l'écriture échoue,
        l'erreur est remontée (jamais un « succès » qui ne survivrait à rien).

        Args:
            provider_id: ID du provider

        Raises:
            RuntimeError: l'écriture PostgreSQL a échoué (défaut non durable).
        """
        self._memory_default = provider_id

        if self._pg:
            try:
                affected = await self._write_default(provider_id)
                if affected == 0:
                    # Le provider n'a jamais été persisté (ligne absente) : on
                    # écrit d'abord sa configuration connue, puis le marquage.
                    config = self._memory.get(provider_id)
                    if not config:
                        config = await self.get(provider_id)
                    if config:
                        await self.save(provider_id, config)
                        affected = await self._write_default(provider_id)
                if affected == 0:
                    raise ProviderDefaultError(
                        f"provider par défaut {provider_id!r} introuvable dans "
                        "llm_providers — défaut non persisté"
                    )
                await self._invalidate_cache()
            except ProviderDefaultError:
                raise
            except Exception as e:
                logger.error("PostgreSQL default provider save failed: %s", e)
                raise ProviderDefaultError(
                    f"impossible de persister le provider par défaut {provider_id!r}"
                ) from e
            return

        # Mode mémoire seule (sans PostgreSQL) : le défaut est explicitement
        # NON durable — avertissement, jamais un silence trompeur.
        logger.warning(
            "Provider par défaut %r en mémoire seule : non durable (PostgreSQL absent)",
            provider_id,
        )
        if self._redis:
            try:
                await self._redis.set("ethan:providers:default", provider_id, ex=300)
            except Exception as e:
                logger.warning("Redis default provider save failed: %s", e)

    async def _write_default(self, provider_id: str) -> int:
        """Marque `provider_id` comme unique défaut. Retourne les lignes touchées."""
        result = await self._pg.execute(
            """
            UPDATE llm_providers
               SET is_default = (provider_id = $1),
                   updated_at = NOW()
             WHERE is_default OR provider_id = $1
            """,
            provider_id,
        )
        # asyncpg renvoie « UPDATE n » ; autrement on compte au plus juste.
        text = str(result)
        if text.startswith("UPDATE "):
            try:
                return int(text.split()[1])
            except (IndexError, ValueError):  # pragma: no cover — format inconnu
                return 1
        return 1

    async def get_default(self) -> str | None:
        """Retourne l'ID du provider par défaut.

        PostgreSQL d'abord (colonne ``is_default``) ; la mémoire et Redis ne
        servent que de replis quand la base est indisponible ou vide.

        Returns:
            ID du provider ou None.
        """
        if self._pg:
            try:
                row = await self._pg.fetchrow(
                    """
                    SELECT provider_id FROM llm_providers
                     WHERE is_default
                     ORDER BY updated_at DESC
                     LIMIT 1
                    """
                )
            except Exception as e:
                logger.warning("PostgreSQL default provider load failed: %s", e)
            else:
                if row is not None:
                    provider_id = row["provider_id"]
                    self._memory_default = provider_id
                    return provider_id

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
        """Invalide les caches Redis (liste + provider par défaut)."""
        if self._redis:
            try:
                await self._redis.delete("ethan:providers:all")
                await self._redis.delete("ethan:providers:default")
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
