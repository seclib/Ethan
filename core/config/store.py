"""ConfigStore — Persistance de la configuration centralisee.

Stocke la configuration ETHAN dans PostgreSQL (JSONB, table ``ethan_config``)
avec cache Redis.  PostgreSQL indisponible → bascule en memoire.

Les cles API / secrets ne sont JAMAIS persistees ici — elles vivent dans
``core/config/secrets.py`` (env / Vault / Docker secrets).

Sémantique de persistance
-------------------------
``save()`` ne ment jamais sur la durabilité :

* PostgreSQL configuré et écriture réussie  → retourne ``True`` (durable) ;
* PostgreSQL configuré mais écriture en échec → lève ``ConfigPersistenceError``
  (l'appelant peut alors refuser de retourner un état non persisté) ;
* pas de PostgreSQL (développement / tests) → ``False`` : la valeur vit en
  mémoire + cache Redis, ce qui est explicitement non durable.

Le cache Redis seul n'est jamais considéré comme une persistance durable : il
n'est qu'une accélération de lecture et expire (TTL).
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_CACHE_KEY = "ethan:config:all"
_CACHE_TTL = 300


class ConfigPersistenceError(RuntimeError):
    """Le backend durable (PostgreSQL) n'a pas pu enregistrer la configuration.

    Levée uniquement lorsque PostgreSQL est configuré : l'appelant doit
    répondre en erreur plutôt que de présenter une valeur non persistée.
    """


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

    @property
    def durable(self) -> bool:
        """True si les écritures sont réellement durablement stockées.

        ``False`` lorsque PostgreSQL n'a pas pu être branché (asyncpg absent,
        connexion refusée…) : les valeurs ne survivent alors pas à un
        redémarrage de conteneur.  Exposé via ``GET /config/status`` pour que
        l'interface puisse signaler le mode dégradé au lieu de laisser croire
        que l'enregistrement a eu lieu.
        """
        return self._pg is not None

    @property
    def backend(self) -> str:
        """Nom du backend de persistance : ``postgresql`` ou ``memory``."""
        return "postgresql" if self._pg is not None else "memory"

    async def get_all(self) -> dict[str, dict[str, Any]]:
        """Retourne la config de tous les domaines.

        PostgreSQL est la source de verite des qu'il est configure.  En cas
        d'echec de lecture, le cache Redis puis la memoire process servent de
        repli degrade (journalise).
        """
        if self._pg:
            try:
                rows = await self._pg.fetch("SELECT domain_name, config FROM ethan_config")
                # PostgreSQL répond : c'est la vérité, même vide.  On rafraîchit
                # le cache et la copie mémoire à partir de cette réponse.
                result = {row["domain_name"]: self._decode(row["config"]) for row in rows}
                self._memory = {k: dict(v) for k, v in result.items()}
                await self._write_cache(result)
                return result
            except Exception as e:
                logger.warning("PostgreSQL config load failed, falling back: %s", e)

        if self._redis:
            try:
                raw = await self._redis.get(_CACHE_KEY)
                if raw:
                    decoded = json.loads(raw)
                    if isinstance(decoded, dict):
                        return decoded
            except Exception as e:
                logger.warning("Redis config load failed, falling back: %s", e)

        return {k: dict(v) for k, v in self._memory.items()}

    async def get(self, domain: str) -> dict[str, Any] | None:
        """Recupere la config d'un domaine."""
        all_configs = await self.get_all()
        return all_configs.get(domain)

    async def save(self, domain: str, config: dict[str, Any]) -> bool:
        """Sauvegarde la config d'un domaine.

        Returns:
            ``True`` si la valeur est durablement persistée (PostgreSQL),
            ``False`` si seul un support non durable (mémoire/Redis) a été
            utilisé.

        Raises:
            ConfigPersistenceError: PostgreSQL est configuré mais l'écriture a
                échoué.  La valeur n'est alors pas considérée comme sauvegardée.
        """
        if self._pg:
            try:
                payload = json.loads(json.dumps(config))  # copie JSON-safe
            except (TypeError, ValueError) as e:
                # Une valeur non sérialisable ne peut pas atteindre JSONB : on
                # échoue explicitement plutôt que de prétendre avoir persisté.
                logger.error("Configuration value for %s is not JSON-serializable: %s", domain, e)
                raise ConfigPersistenceError(
                    f"Configuration '{domain}' is not JSON-serializable: {e}"
                ) from e
            try:
                await self._pg.execute(
                    """
                    INSERT INTO ethan_config (domain_name, config, updated_at)
                    VALUES ($1, $2::jsonb, NOW())
                    ON CONFLICT (domain_name)
                    DO UPDATE SET config = EXCLUDED.config, updated_at = NOW()
                    """,
                    domain,
                    json.dumps(payload),
                )
            except Exception as e:
                logger.error("PostgreSQL config save failed for %s: %s", domain, e)
                raise ConfigPersistenceError(
                    f"Configuration '{domain}' could not be persisted to PostgreSQL: {e}"
                ) from e
            # Succès durable : mémoire + invalidation du cache de lecture.
            self._memory[domain] = payload
            await self._invalidate_cache()
            return True

        # Aucun backend durable : mémoire (+ cache Redis best-effort).
        self._memory[domain] = config
        if self._redis:
            try:
                all_configs = {k: dict(v) for k, v in self._memory.items()}
                await self._redis.set(_CACHE_KEY, json.dumps(all_configs), ex=_CACHE_TTL)
            except Exception as e:
                logger.warning("Redis config save failed: %s", e)
        return False

    async def delete(self, domain: str) -> bool:
        """Supprime la config d'un domaine.

        Raises:
            ConfigPersistenceError: PostgreSQL est configuré mais la suppression
                a échoué — la suppression ne doit pas être annoncée comme faite.
        """
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
            except Exception as e:
                logger.error("PostgreSQL config delete failed for %s: %s", domain, e)
                raise ConfigPersistenceError(
                    f"Configuration '{domain}' could not be deleted from PostgreSQL: {e}"
                ) from e
            return existed

        if self._redis:
            try:
                all_configs = {k: dict(v) for k, v in self._memory.items()}
                await self._redis.set(_CACHE_KEY, json.dumps(all_configs), ex=_CACHE_TTL)
            except Exception as e:
                logger.warning("Redis config delete failed: %s", e)

        return existed

    async def _write_cache(self, all_configs: dict[str, dict[str, Any]]) -> None:
        """Rafraîchit le cache Redis de lecture (best-effort)."""
        if not self._redis:
            return
        try:
            await self._redis.set(_CACHE_KEY, json.dumps(all_configs), ex=_CACHE_TTL)
        except Exception as e:
            logger.debug("Redis config cache write failed: %s", e)

    async def _invalidate_cache(self) -> None:
        """Invalide le cache Redis."""
        if self._redis:
            try:
                await self._redis.delete(_CACHE_KEY)
                logger.debug("Config cache invalidated")
            except Exception as e:
                logger.warning("Redis cache invalidation failed: %s", e)

    @staticmethod
    def _decode(raw: Any) -> dict[str, Any]:
        """Décode une valeur JSONB asyncpg (str, dict ou None)."""
        if raw is None:
            return {}
        if isinstance(raw, str):
            decoded = json.loads(raw)
            return decoded if isinstance(decoded, dict) else {}
        if isinstance(raw, dict):
            return dict(raw)
        return {}

    async def close(self) -> None:
        """Ferme la connexion Redis."""
        if self._redis:
            try:
                await self._redis.close()
                logger.debug("ConfigStore Redis connection closed")
            except Exception as e:
                logger.warning("Error closing Redis for ConfigStore: %s", e)
