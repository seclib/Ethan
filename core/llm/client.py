"""LLM Client — Interface unifiée pour tous les providers."""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from core.llm.registry import LLMProviderRegistry
from core.llm.selector import LLMSelector
from core.llm.types import ChatMessage, ChatResponse, LLMRequirements, ModelInfo

logger = logging.getLogger(__name__)


class LLMClient:
    """Client LLM unifié."""

    def __init__(self, registry: LLMProviderRegistry, selector: LLMSelector):
        self.registry = registry
        self.selector = selector
        self._cost_tracker = None  # Initialisé dans initialize()

    async def initialize(self) -> None:
        """Initialise le client."""
        from core.llm.tracker import CostTracker
        self._cost_tracker = CostTracker()
        logger.info("LLM Client initialized")

    async def chat(
        self,
        messages: list[ChatMessage],
        requirements: LLMRequirements | None = None,
    ) -> ChatResponse:
        """Chat completion avec sélection automatique.

        Args:
            messages: Messages de conversation
            requirements: Requirements pour la sélection

        Returns:
            Réponse du LLM
        """
        # 1. Sélectionner le modèle
        model, provider = self._select_model(requirements)

        # 2. Appeler le provider
        response = await provider.chat(
            messages=messages,
            model=model.id if model else None,
        )

        # 3. Tracker le coût
        if self._cost_tracker and response.usage:
            self._cost_tracker.track(model.provider, model.id, response.usage)

        return response

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        requirements: LLMRequirements | None = None,
    ) -> AsyncIterator[str]:
        """Chat completion avec streaming.

        Args:
            messages: Messages
            requirements: Requirements

        Yields:
            Tokens générés
        """
        # 1. Sélectionner le modèle
        model, provider = self._select_model(requirements)

        # 2. Streamer
        async for chunk in provider.chat_stream(
            messages=messages,
            model=model.id if model else None,
        ):
            yield chunk

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
        provider_name: str | None = None,
    ) -> list[list[float]]:
        """Génère des embeddings.

        Args:
            texts: Textes à encoder
            model: ID du modèle (optionnel)
            provider_name: Nom du provider (optionnel)

        Returns:
            Embeddings
        """
        # Sélectionner un provider
        if provider_name:
            provider = self.registry.get_provider(provider_name)
        else:
            # Utiliser le premier provider disponible
            providers = self.registry.list_providers()
            if not providers:
                raise ValueError("No LLM providers registered")
            provider = self.registry.get_provider(providers[0])

        return await provider.embed(texts, model=model)

    def _select_model(self, requirements: LLMRequirements | None) -> tuple[ModelInfo | None, Any]:
        """Sélectionne un modèle.

        Args:
            requirements: Requirements

        Returns:
            (ModelInfo, Provider)
        """
        # Si pas de requirements, utiliser le défaut
        if not requirements:
            provider_name = self.registry.list_providers()[0]
            provider = self.registry.get_provider(provider_name)
            default_model_id = provider.default_model
            model = self.registry.get_model(default_model_id)
            return model, provider

        # Récupérer tous les modèles disponibles
        all_models = self.registry.list_models()

        # Sélectionner le meilleur
        scored = self.selector.select(requirements, all_models)

        if not scored:
            # Fallback: utiliser le provider par défaut
            logger.warning("No model matched requirements, using default")
            provider_name = self.registry.list_providers()[0]
            provider = self.registry.get_provider(provider_name)
            default_model_id = provider.default_model
            model = self.registry.get_model(default_model_id)
            return model, provider

        best = scored[0]
        logger.info(f"Selected model: {best.model.name} (score: {best.score:.3f})")
        logger.info(f"Reasoning: {best.reasoning}")

        provider = self.registry.get_provider(best.model.provider)
        return best.model, provider