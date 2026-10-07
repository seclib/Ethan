"""Configuration Service — Source de vérité unique pour toute configuration ETHAN.

Toutes les interfaces (Runtime, Core, CLI, WebUI, Desktop) utilisent ce service.
WebUI et CLI ne stockent plus de configuration métier.

Domaines gérés :
- providers
- models
- rag
- memory
- agents
- planner
- plugins
- authentication
- runtime
- preferences
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from core.config.loader import ConfigLoader
from core.config.schema import ConfigSchema
from core.config.store import ConfigPersistenceError, ConfigStore

__all__ = ["ConfigPersistenceError", "ConfigurationService", "DOMAINS"]

logger = logging.getLogger(__name__)

# Domaines métier gérés par le service
DOMAINS = (
    "providers",
    "models",
    "rag",
    "memory",
    "agents",
    "planner",
    "plugins",
    "authentication",
    "runtime",
    "preferences",
)


class ConfigurationService:
    """Service de configuration centralisé.

    Fournit un accès unifié à toute la configuration ETHAN.
    Les interfaces (WebUI, CLI, Desktop) utilisent ce service
    au lieu de stocker leur propre configuration.

    Args:
        loader: Chargeur de configuration (optionnel — utilise ConfigLoader par défaut)
        store: Persistance (optionnel — utilise ConfigStore par défaut)
    """

    def __init__(
        self,
        loader: ConfigLoader | None = None,
        store: ConfigStore | None = None,
    ):
        self._loader = loader or ConfigLoader()
        self._store = store or ConfigStore()
        self._schema: ConfigSchema | None = None
        self._persisted: dict[str, dict[str, Any]] = {}
        self._loaded = False

    # ── Chargement ──────────────────────────────────────────────────────

    async def load(self) -> None:
        """Charge la configuration depuis les sources (loader + store)."""
        try:
            self._schema = self._loader.load()
            self._loaded = True
            logger.info("Configuration loaded from loader")
        except Exception as e:
            logger.warning("ConfigLoader failed, using defaults: %s", e)
            self._schema = ConfigSchema()
            self._loaded = True

        # Charger les overrides persistés (store)
        try:
            self._persisted = await self._store.get_all()
            if self._persisted:
                logger.info("Configuration loaded %d persisted domains", len(self._persisted))
        except Exception as e:
            logger.warning("ConfigStore load failed: %s", e)
            self._persisted = {}

    def _ensure_loaded(self) -> None:
        """S'assure que la configuration est chargée (sync)."""
        if not self._loaded:
            self._schema = self._loader.load()
            self._loaded = True

    # ── Lecture ─────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration.

        Args:
            key: Clé de configuration (dot-notation supportée, ex: "rag.enabled")
            default: Valeur par défaut si la clé n'existe pas

        Returns:
            Valeur de configuration
        """
        self._ensure_loaded()

        # Fusionner le schéma de base avec les overrides persistés
        config = self._merged_config()

        # Support dot-notation
        keys = key.split(".")
        value: Any = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_domain(self, domain: str) -> dict[str, Any]:
        """Récupère une section de configuration.

        Args:
            domain: Nom du domaine (providers, models, rag, memory, agents,
                     planner, plugins, authentication, runtime)

        Returns:
            Dict de configuration pour le domaine
        """
        return self.get(domain, {})

    def get_all(self) -> dict[str, Any]:
        """Récupère toute la configuration (fusionnée).

        Returns:
            Dict complet de configuration
        """
        self._ensure_loaded()
        return self._merged_config()

    def _merged_config(self) -> dict[str, Any]:
        """Fusionne le schéma de base avec les overrides persistés."""
        base = self._schema.to_dict() if self._schema else ConfigSchema().to_dict()
        for domain, overrides in self._persisted.items():
            if domain in base and isinstance(base[domain], dict) and isinstance(overrides, dict):
                base[domain] = _deep_merge(base[domain], overrides)
            else:
                base[domain] = copy.deepcopy(overrides)
        return base

    # ── Écriture ────────────────────────────────────────────────────────
    #
    # Toutes les écritures sont fail-closed :
    #   1. on construit une copie candidate de l'état ;
    #   2. on persiste en premier ;
    #   3. seulement si la persistance réussit on engage `self._persisted` ;
    #   4. sinon on lève ConfigPersistenceError.
    # L'état en mémoire ne peut donc jamais annoncer une valeur que la base
    # ne contient pas (cf. docs/security/10-secret-hygiene.md et ADR-3007).

    async def set(self, key: str, value: Any) -> dict[str, Any]:
        """Définit une valeur de configuration et la persiste.

        Args:
            key: Clé de configuration (dot-notation supportée)
            value: Nouvelle valeur

        Returns:
            L'état du domaine réellement persisté.

        Raises:
            ConfigPersistenceError: la persistance a échoué — la valeur n'a
                pas été acceptée.
        """
        self._ensure_loaded()

        # Déterminer le domaine racine
        domain = key.split(".")[0]

        # Construire le candidat SANS muter l'état engagé.
        persisted = copy.deepcopy(self._persisted.get(domain, {}))
        keys = key.split(".")[1:]  # Exclure le domaine
        current = persisted
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

        await self._commit(domain, persisted)
        logger.info("Configuration set: %s = %s", key, value)
        return self._persisted.get(domain, {})

    async def set_domain(self, domain: str, data: dict[str, Any]) -> dict[str, Any]:
        """Remplace complètement la configuration d'un domaine.

        Args:
            domain: Nom du domaine
            data: Nouvelle configuration du domaine

        Returns:
            L'état du domaine réellement persisté (relu depuis le store).

        Raises:
            ConfigPersistenceError: la persistance a échoué — la valeur n'a
                pas été acceptée et l'état en mémoire est inchangé.
        """
        self._ensure_loaded()
        await self._commit(domain, copy.deepcopy(data))
        logger.info("Configuration domain set: %s", domain)
        return self._persisted.get(domain, {})

    async def _commit(self, domain: str, payload: dict[str, Any]) -> None:
        """Persiste ``payload`` puis engage l'état en mémoire.

        Le read-back sur le store garantit que la valeur retournée (et donc
        exposée par l'API) correspond à ce qui est durablement stocké.
        """
        try:
            await self._store.save(domain, payload)
        except Exception as e:
            logger.error("Failed to persist domain %s: %s", domain, e)
            # `_persisted` n'est PAS modifié : l'état reste celui de la base.
            raise ConfigPersistenceError(
                f"Configuration domain '{domain}' could not be persisted: {e}"
            ) from e

        if not self._store.durable:
            logger.warning(
                "Configuration domain %s written to NON-DURABLE backend '%s': "
                "it will be lost on restart",
                domain,
                self._store.backend,
            )

        # Read-back : vérifier ce que la base contient réellement.
        try:
            stored = await self._store.get(domain)
        except Exception as e:
            logger.error("Read-back verification failed for domain %s: %s", domain, e)
            raise ConfigPersistenceError(
                f"Configuration domain '{domain}' was written but could not be "
                f"read back for verification: {e}"
            ) from e

        if stored is None:
            raise ConfigPersistenceError(
                f"Configuration domain '{domain}' write reported success but the "
                "value is missing from the store"
            )

        self._persisted[domain] = copy.deepcopy(stored)

    @property
    def durable(self) -> bool:
        """True si la configuration est réellement stockée dans un backend durable."""
        return self._store.durable

    @property
    def backend(self) -> str:
        """Nom du backend de persistance du store sous-jacent."""
        return self._store.backend

    async def status(self) -> dict[str, Any]:
        """État de la persistance de la configuration (pour ``GET /config/status``).

        Permet à une interface d'afficher « réglages non persistés » plutôt que
        de laisser l'utilisateur croire que son choix survivra à un
        redémarrage.
        """
        return {
            "durable": self.durable,
            "backend": self.backend,
            "loaded_domains": sorted(self._persisted),
            "warning": (
                None
                if self.durable
                else (
                    "No durable backend (PostgreSQL) is attached: configuration "
                    "changes live in process memory only and WILL be lost on "
                    "restart."
                )
            ),
        }

    async def delete(self, key: str) -> bool:
        """Supprime une clé de configuration.

        Args:
            key: Clé de configuration (dot-notation)

        Returns:
            True si supprimé, False sinon

        Raises:
            ConfigPersistenceError: la persistance de la suppression a échoué.
        """
        self._ensure_loaded()
        domain = key.split(".")[0]
        persisted = self._persisted.get(domain, {})

        keys = key.split(".")[1:]  # Exclure le domaine
        candidate = copy.deepcopy(persisted)
        current = candidate
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False

        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            await self._commit(domain, candidate)
            return True

        return False

    # ── Validation ──────────────────────────────────────────────────────

    def validate(self, key: str | None = None) -> dict[str, Any]:
        """Valide la configuration.

        Args:
            key: Clé à valider (optionnel — valide tout si None)

        Returns:
            Dict {valid: bool, errors: list[str]}
        """
        self._ensure_loaded()
        errors: list[str] = []

        if key:
            value = self.get(key)
            if value is None:
                errors.append(f"Key '{key}' is not configured")
        else:
            for domain in DOMAINS:
                value = self.get(domain)
                if value is None:
                    errors.append(f"Domain '{domain}' is not configured")

        return {"valid": len(errors) == 0, "errors": errors}

    # ── Export / Import ─────────────────────────────────────────────────

    def export(self) -> dict[str, Any]:
        """Exporte la configuration complète.

        Returns:
            Dict de configuration exportable
        """
        return self.get_all()

    async def import_(self, data: dict[str, Any]) -> dict[str, Any]:
        """Importe une configuration (remplace les domaines fournis).

        Args:
            data: Configuration à importer

        Returns:
            Rapport {imported: list[str], errors: list[str]}
        """
        self._ensure_loaded()
        imported: list[str] = []
        errors: list[str] = []

        for domain, value in data.items():
            if domain not in DOMAINS:
                errors.append(f"Unknown domain '{domain}'")
                continue
            if not isinstance(value, dict):
                errors.append(f"Domain '{domain}' must be a dict")
                continue
            try:
                await self.set_domain(domain, value)
            except ConfigPersistenceError as e:
                # Un domaine non persisté n'est PAS déclaré importé : l'état
                # de l'import doit refléter la base, pas l'intention.
                logger.error("Import failed for domain %s: %s", domain, e)
                errors.append(str(e))
                continue
            imported.append(domain)

        logger.info("Configuration imported (%d domains)", len(imported))
        return {"imported": imported, "errors": errors}

    # ── Helpers ─────────────────────────────────────────────────────────

    def get_schema(self) -> ConfigSchema:
        """Retourne le schéma ConfigSchema complet."""
        self._ensure_loaded()
        assert self._schema is not None, "Schema not loaded"
        return self._schema

    async def close(self) -> None:
        """Ferme le store."""
        if self._store:
            try:
                await self._store.close()
            except Exception as e:
                logger.warning("Error closing ConfigStore: %s", e)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Fusionne récursivement override dans base."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
