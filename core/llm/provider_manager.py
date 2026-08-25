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
import os
from typing import Any, AsyncIterator

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
        """Charge la config depuis le store et instancie les providers.

        - Charge les configs persistées (sans clés API).
        - Si le store est vide/absent, seed les providers par défaut.
        - Injecte les clés API depuis les secrets/env (mémoire, jamais persistées).
        - Instancie et enregistre les providers activés.
        """
        try:
            self._providers_config = await self._store.get_all()
        except Exception as e:
            logger.warning("Failed to load providers from store: %s", e)
            self._providers_config = {}

        # Seed les configs par défaut si le store est vide
        if not self._providers_config:
            logger.info("No provider configs found - seeding defaults")
            self._providers_config = self._default_provider_configs()
            for pid, cfg in self._providers_config.items():
                try:
                    await self._store.save(pid, cfg)
                except Exception as exc:
                    logger.debug("Could not persist default provider %s: %s", pid, exc)

        # Injecter les clés API (secrets/env) en mémoire — jamais persistées
        await self._inject_secrets()

        # Charger le provider par défaut
        self._default_provider = await self._store.get_default()
        if self._default_provider is None:
            for pid, cfg in self._providers_config.items():
                if cfg.get("enabled", False):
                    self._default_provider = pid
                    break

        # Instancier les providers activés
        for provider_id, config in self._providers_config.items():
            if config.get("enabled", False):
                try:
                    provider = create_provider_from_config({**config, "name": provider_id})
                    await self._register(provider, provider_id)
                except Exception as e:
                    logger.error("Failed to instantiate provider %s: %s", provider_id, e)

        await self._client.initialize()
        logger.info(
            "ProviderManager initialized with %d providers (default=%s)",
            len(self._registry.list_providers()),
            self._default_provider,
        )

    def _default_provider_configs(self) -> dict[str, dict[str, Any]]:
        """Retourne les configs de providers par défaut (sans clés API)."""
        return {
            "ollama": {
                "name": "ollama",
                "type": "ollama",
                "enabled": True,
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
                "default_model": os.getenv("OLLAMA_DEFAULT_MODEL", ""),
                "display_name": "Ollama (local)",
            },
            "openai": {
                "name": "openai",
                "type": "openai",
                "enabled": False,
                "base_url": "",
                "default_model": "gpt-4o-mini",
                "display_name": "OpenAI",
            },
            "azure": {
                "name": "azure",
                "type": "azure",
                "enabled": False,
                "base_url": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "default_model": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
                "display_name": "Azure OpenAI",
            },
            "anthropic": {
                "name": "anthropic",
                "type": "anthropic",
                "enabled": False,
                "base_url": "",
                "default_model": "claude-3-5-sonnet-20241022",
                "display_name": "Anthropic Claude",
            },
            "vllm": {
                "name": "vllm",
                "type": "vllm",
                "enabled": False,
                "base_url": os.getenv("VLLM_BASE_URL", "http://vllm:8000"),
                "default_model": "",
                "display_name": "vLLM (local)",
            },
            "openrouter": {
                "name": "openrouter",
                "type": "openrouter",
                "enabled": False,
                "base_url": "https://openrouter.ai/api/v1",
                "default_model": os.getenv("OPENROUTER_DEFAULT_MODEL", "openrouter/auto"),
                "display_name": "OpenRouter",
                "options": {"routing": {"allow_fallbacks": True}},
            },
            "custom": {
                "name": "custom",
                "type": "openai-compatible",
                "enabled": False,
                "base_url": os.getenv("CUSTOM_OPENAI_BASE_URL", "http://localhost:8000/v1"),
                "default_model": "gpt-4",
                "display_name": "Custom OpenAI-Compatible",
            },
        }

    async def _inject_secrets(self) -> None:
        """Injecte les clés API des providers cloud depuis les secrets/env.

        Mémoire uniquement — aucune clé n'est écrite dans le store.
        Un provider cloud disposant d'une clé est automatiquement activé.
        """
        keys: dict[str, str | None] = {}
        try:
            from core.config.secrets import get_secrets
            secrets = get_secrets()
            keys["openai"] = getattr(secrets, "openai_api_key", None)
            keys["anthropic"] = getattr(secrets, "anthropic_api_key", None)
            keys["gemini"] = getattr(secrets, "gemini_api_key", None)
            keys["azure"] = getattr(secrets, "azure_openai_api_key", None)
            keys["openrouter"] = getattr(secrets, "openrouter_api_key", None)
        except Exception as exc:
            logger.debug("get_secrets() unavailable, falling back to env: %s", exc)
        keys.setdefault("openai", os.getenv("OPENAI_API_KEY"))
        keys.setdefault("anthropic", os.getenv("ANTHROPIC_API_KEY"))
        keys.setdefault("gemini", os.getenv("GEMINI_API_KEY"))
        keys.setdefault("azure", os.getenv("AZURE_OPENAI_API_KEY"))
        keys.setdefault("openrouter", os.getenv("OPENROUTER_API_KEY"))

        for provider_id, config in self._providers_config.items():
            ptype = config.get("type", "")
            key = keys.get(ptype)
            if ptype in keys and key:
                config["api_key"] = key
                config["enabled"] = True
                logger.info("Auto-enabled provider %s (%s) from secret/env", provider_id, ptype)

    async def close(self) -> None:
        """Libère les ressources des providers et du store."""
        for provider in self._registry._providers.values():
            close_fn = getattr(provider, "close", None)
            if close_fn is not None:
                try:
                    await close_fn()
                except Exception as exc:
                    logger.debug("Error closing provider %s: %s", getattr(provider, "name", "?"), exc)
        if self._store is not None:
            try:
                await self._store.close()
            except Exception as exc:
                logger.debug("Error closing provider store: %s", exc)
        logger.info("ProviderManager closed")

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

        # Enregistrer dans le registry uniquement si activé
        enabled = bool(config.get("enabled", True)) if config else True
        if enabled:
            await self._register(provider, provider_id)
        else:
            # Provider désactivé : on valide la config sans l'instancier
            try:
                await provider.initialize()
            except Exception as exc:
                logger.debug(
                    "Provider %s désactivé — skip initialization: %s",
                    provider_id,
                    exc,
                )

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
        if pid is None:
            return ""
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

        # Tester la connexion si activé — avec un délai borné : un healthcheck
        # ne doit jamais bloquer list_providers() pendant plusieurs minutes
        # (ex: provider injoignable + client HTTP longue durée).
        connection_status = "unknown"
        if config.get("enabled", False):
            try:
                import asyncio
                result = await asyncio.wait_for(self.test_connection(provider_id), timeout=12.0)
                connection_status = result["status"]
            except asyncio.TimeoutError:
                connection_status = "error"
            except Exception:
                connection_status = "error"

        # Les modèles d'un provider désactivé/ne-initialisé pas sont inaccessibles.
        # describe_provider() est appelé par list_providers() et set_enabled() et
        # ne doit jamais planter à cause d'un provider injoignable.
        try:
            models = [m.id for m in await self.list_models(provider_id)]
        except Exception:
            models = []

        return {
            "id": provider_id,
            "name": config.get("display_name", config.get("name", provider_id)),
            "type": config.get("type", provider_id),
            "enabled": config.get("enabled", False),
            "status": connection_status,
            "default_model": config.get("default_model", ""),
            "is_default": provider_id == self._default_provider,
            "base_url": config.get("base_url", ""),
            "models": models,
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

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        requirements: LLMRequirements | None = None,
    ) -> AsyncIterator[str]:
        """Chat completion streaming via le LLMClient.

        Args:
            messages: Messages de conversation
            requirements: Requirements pour la sélection

        Yields:
            Chunks de texte (tokens) un par un.
        """
        async for chunk in self._client.chat_stream(messages, requirements):
            yield chunk

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
