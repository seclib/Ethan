"""ProviderManager — Gestion centralisée des providers LLM.

Fonctionnalités :
- Enregistrer / supprimer un provider
- Activer / désactiver un provider
- Tester la connexion (healthcheck réel)
- Lister les modèles disponibles
- Sélectionner le modèle actif
- Définir le provider par défaut
- Ordonnancer via LLMSelector / LLMRouter existants
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm.types import ChatMessage, ChatResponse, LLMRequirements, ModelInfo
from core.llm.registry import LLMProviderRegistry
from core.llm.client import LLMClient
from core.llm.selector import LLMSelector
from core.llm.router import LLMRouter
from core.llm.providers.base import LLMProvider
from core.llm.provider_factory import create_provider_from_config
from core.llm.store import ProviderStore

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manager central des providers LLM.

    S'appuie sur le LLMProviderRegistry (existant) et ajoute :
    - la persistance via ProviderStore
    - l'enregistrement dynamique depuis config
    - le healthcheck / test de connexion
    - la gestion de l'activation / du provider par défaut

    Args:
        store: ProviderStore optionnel (persistance). None → mode mémoire.
    """

    def __init__(self, store: ProviderStore | None = None):
        self._store = store or ProviderStore()
        self._registry = LLMProviderRegistry()
        self._selector = LLMSelector()
        self._router = LLMRouter(self._selector)
        self._client = LLMClient(self._registry, self._selector)
        self._providers_config: dict[str, dict[str, Any]] = {}
        self._default_provider: str | None = None

    # ── Initialisation ──────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Charge la config depuis le store et instancie les providers."""
        try:
            self._providers_config = await self._store.get_all()
        except Exception as e:
            logger.warning("Failed to load providers from store: %s", e)
            self._providers_config = {}

        # Charger le provider par défaut
        self._default_provider = await self._store.get_default()

        # Instancier les providers actifs
        for provider_id, config in self._providers_config.items():
            if config.get("enabled", False):
                try:
                    provider = create_provider_from_config({
                        **config,
                        "name": provider_id,
                    })
                    await self._register(provider, provider_id)
                except Exception as e:
                    logger.error("Failed to instantiate provider %s: %s", provider_id, e)

        # Si aucun provider actif, créer les défauts actifs
        if not self._registry.list_providers():
            logger.info("No active providers — creating defaults")
            from core.llm.provider_factory import create_default_providers
            for provider in create_default_providers():
                await self.register_provider(provider, config={"enabled": provider.name == "ollama"})

        await self._client.initialize()
        logger.info("ProviderManager initialized with %d providers", len(self._registry.list_providers()))

    # ── Enregistrement / suppression ────────────────────────────────────

    async def register_provider(
        self,
        provider: LLMProvider | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Enregistre un provider.

        Soit on passe une instance LLMProvider directement, soit une config
        qui sera instanciée via la factory.

        Args:
            provider: Instance LLMProvider (optionnel)
            config: Config dict (optionnel)

        Returns:
            Le provider enregistré sous forme de dict (serializable).

        Raises:
            ValueError: Si ni provider ni config n'est fourni.
        """
        if provider is None:
            if config is None:
                raise ValueError("Either 'provider' or 'config' must be provided")
            provider = create_provider_from_config(config)

        provider_id = config.get("name", provider.name) if config else provider.name

        # Enregistrer dans le registry
        await self._register(provider, provider_id)

        # Persister la config (sans la clé API)
        safe_config = dict(config or {})
        safe_config.pop("api_key", None)
        safe_config["name"] = provider_id
        safe_config["type"] = safe_config.get("type", provider.name)
        safe_config.setdefault("enabled", True)
        safe_config.setdefault("default_model", provider.default_model)
        self._providers_config[provider_id] = safe_config
        await self._store.save(provider_id, safe_config)

        logger.info("Provider registered: %s (type=%s)", provider_id, provider.name)
        return await self.describe_provider(provider_id)

    async def unregister_provider(self, provider_id: str) -> bool:
        """Supprime un provider.

        Args:
            provider_id: ID du provider

        Returns:
            True si supprimé, False sinon.
        """
        existed = provider_id in self._providers_config or bool(
            self._registry.get_provider(provider_id)
        )
        self._registry._providers.pop(provider_id, None)
        self._providers_config.pop(provider_id, None)

        if self._default_provider == provider_id:
            self._default_provider = None

        await self._store.delete(provider_id)
        logger.info("Provider unregistered: %s", provider_id)
        return existed

    # ── Activation / désactivation ──────────────────────────────────────

    async def set_enabled(self, provider_id: str, enabled: bool) -> dict[str, Any]:
        """Active ou désactive un provider.

        Args:
            provider_id: ID du provider
            enabled: True pour activer, False pour désactiver

        Returns:
            Le provider mis à jour.

        Raises:
            ValueError: Si le provider n'existe pas.
        """
        if provider_id not in self._providers_config:
            raise ValueError(f"Provider '{provider_id}' not found")

        self._providers_config[provider_id]["enabled"] = enabled
        await self._store.save(provider_id, self._providers_config[provider_id])

        if enabled:
            # Ré-instancier et ré-enregistrer
            config = self._providers_config[provider_id]
            try:
                provider = create_provider_from_config({**config, "name": provider_id})
                await self._register(provider, provider_id)
                await provider.initialize()
                logger.info("Provider enabled: %s", provider_id)
            except Exception as e:
                logger.error("Failed to enable provider %s: %s", provider_id, e)
                raise ValueError(f"Failed to enable provider {provider_id}: {e}")
        else:
            # Retirer du registry
            self._registry._providers.pop(provider_id, None)
            if self._default_provider == provider_id:
                self._default_provider = None
            logger.info("Provider disabled: %s", provider_id)

        return await self.describe_provider(provider_id)

    # ── Test de connexion ───────────────────────────────────────────────

    async def test_connection(self, provider_id: str) -> dict[str, Any]:
        """Teste la connexion à un provider.

        Args:
            provider_id: ID du provider

        Returns:
            Dict {connected: bool, message: str, status: str}
        """
        provider = self._registry.get_provider(provider_id)
        if provider is None:
            # Essayer de l'instancier depuis la config
            config = self._providers_config.get(provider_id)
            if not config:
                raise ValueError(f"Provider '{provider_id}' not found")
            try:
                provider = create_provider_from_config({**config, "name": provider_id})
                await provider.initialize()
            except Exception as e:
                return {
                    "connected": False,
                    "status": "error",
                    "message": f"Provider instantiation failed: {e}",
                }

        try:
            ok = await provider.test_connection()
            return {
                "connected": ok,
                "status": "connected" if ok else "error",
                "message": "Connection successful" if ok else "Connection failed",
            }
        except Exception as e:
            logger.warning("Connection test failed for %s: %s", provider_id, e)
            return {
                "connected": False,
                "status": "error",
                "message": str(e),
            }

    # ── Modèles ─────────────────────────────────────────────────────────

    async def list_models(self, provider_id: str | None = None) -> list[ModelInfo]:
        """Liste les modèles disponibles.

        Args:
            provider_id: Filtrer par provider (optionnel)

        Returns:
            Liste de ModelInfo.
        """
        if provider_id:
            provider = self._registry.get_provider(provider_id)
            if provider is None:
                # Tenter d'instancier depuis la config
                config = self._providers_config.get(provider_id)
                if config and config.get("enabled", False):
                    provider = create_provider_from_config({**config, "name": provider_id})
                    await provider.initialize()
            if provider is None:
                raise ValueError(f"Provider '{provider_id}' not found or not active")
            try:
                return await provider.list_models()
            except Exception as e:
                logger.warning("Failed to list models for %s: %s", provider_id, e)
                return []

        models: list[ModelInfo] = []
        for pid in self._registry.list_providers():
            provider = self._registry.get_provider(pid)
            if provider is None:
                continue
            try:
                models.extend(await provider.list_models())
            except Exception as e:
                logger.warning("Failed to list models for %s: %s", pid, e)
        return models

    async def get_active_model(self, provider_id: str | None = None) -> str:
        """Retourne le modèle actif d'un provider.

        Args:
            provider_id: ID du provider (None → provider par défaut)

        Returns:
            Nom du modèle actif.
        """
        pid = provider_id or self._default_provider
        config = self._providers_config.get(pid, {})
        if config.get("default_model"):
            return config["default_model"]

        provider = self._registry.get_provider(pid)
        if provider is not None:
            return provider.default_model

        return ""

    # ── Provider par défaut ─────────────────────────────────────────────

    async def set_default_provider(self, provider_id: str) -> dict[str, Any]:
        """Définit le provider par défaut.

        Args:
            provider_id: ID du provider

        Returns:
            Provider défini comme défaut.

        Raises:
            ValueError: Si le provider n'existe pas.
        """
        if provider_id not in self._providers_config and not self._registry.get_provider(provider_id):
            raise ValueError(f"Provider '{provider_id}' not found")

        self._default_provider = provider_id
        await self._store.set_default(provider_id)
        logger.info("Default provider set: %s", provider_id)
        return await self.describe_provider(provider_id)

    async def get_default_provider(self) -> dict[str, Any] | None:
        """Retourne le provider par défaut.

        Returns:
            Provider par défaut ou None.
        """
        if self._default_provider is None:
            self._default_provider = await self._store.get_default()
        if self._default_provider is None:
            return None
        try:
            return await self.describe_provider(self._default_provider)
        except ValueError:
            return None

    # ── Description (pour l'API) ────────────────────────────────────────

    async def describe_provider(self, provider_id: str) -> dict[str, Any]:
        """Retourne une description sérialisable d'un provider.

        Args:
            provider_id: ID du provider

        Returns:
            Dict de description.

        Raises:
            ValueError: Si le provider n'existe pas.
        """
        config = self._providers_config.get(provider_id)
        if config is None:
            # Utiliser la config du registry
            provider = self._registry.get_provider(provider_id)
            if provider is None:
                raise ValueError(f"Provider '{provider_id}' not found")
            config = {
                "name": provider_id,
                "type": provider.name,
                "enabled": True,
                "default_model": provider.default_model,
            }

        # Tester la connexion si activé
        connection_status = "unknown"
        if config.get("enabled", False):
            try:
                result = await self.test_connection(provider_id)
                connection_status = result["status"]
            except Exception:
                connection_status = "error"

        return {
            "id": provider_id,
            "name": config.get("display_name", config.get("name", provider_id)),
            "type": config.get("type", provider_id),
            "enabled": config.get("enabled", False),
            "status": connection_status,
            "default_model": config.get("default_model", ""),
            "is_default": provider_id == self._default_provider,
            "base_url": config.get("base_url", ""),
            "models": [m.id for m in await self.list_models(provider_id)],
        }

    async def list_providers(self) -> list[dict[str, Any]]:
        """Liste tous les providers avec leur état.

        Returns:
            Liste de descriptions.
        """
        provider_ids = set(self._providers_config.keys()) | set(self._registry.list_providers())
        providers = []
        for pid in provider_ids:
            try:
                providers.append(await self.describe_provider(pid))
            except Exception as e:
                logger.warning("Failed to describe provider %s: %s", pid, e)
        return providers

    # ── Chat / utilisation (via LLMClient) ──────────────────────────────

    async def chat(
        self,
        messages: list[ChatMessage],
        requirements: LLMRequirements | None = None,
    ) -> ChatResponse:
        """Chat completion via le LLMClient (avec sélection + circuit breaker).

        Args:
            messages: Messages de conversation
            requirements: Requirements pour la sélection

        Returns:
            Réponse du LLM.
        """
        return await self._client.chat(messages, requirements)

    # ── Helpers privés ──────────────────────────────────────────────────

    async def _register(self, provider: LLMProvider, provider_id: str) -> None:
        """Enregistre un provider dans le registry et l'initialise."""
        self._registry._providers[provider_id] = provider
        try:
            await provider.initialize()
            models = provider.list_models() if hasattr(provider.list_models, "__call__") else []
            # Le registry n'a pas accès async — on met à jour la liste _models
            if models:
                try:
                    model_list = await models if hasattr(models, "__await__") else models
                    for m in model_list:
                        self._registry._models[m.id] = m
                except Exception:
                    pass
        except Exception as e:
            logger.warning("Failed to initialize provider %s: %s", provider_id, e)