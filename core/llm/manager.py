"""LLM Manager — Module principal du moteur LLM multi-provider.

Orchestre :
- LLMProviderRegistry (catalogue)
- LLMSelector (sélection)
- LLMClient (interface unifiée)
- CostTracker (suivi des coûts)
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm.registry import LLMProviderRegistry
from core.llm.selector import LLMSelector
from core.llm.client import LLMClient
from core.llm.tracker import CostTracker
from core.llm.types import ChatMessage, ChatResponse, LLMRequirements, ModelInfo

logger = logging.getLogger(__name__)


class LLMManager:
    """Module LLM Manager — gère les providers et modèles LLM."""

    def __init__(self):
        self.registry = LLMProviderRegistry()
        self.selector = LLMSelector()
        self.client = LLMClient(self.registry, self.selector)
        self.tracker = CostTracker()

    async def initialize(self) -> None:
        """Initialise le manager."""
        await self.client.initialize()
        logger.info("LLM Manager initialized")

    def register_provider(self, provider: Any) -> None:
        """Enregistre un provider.

        Args:
            provider: Instance de LLMProvider
        """
        self.registry.register_provider(provider)

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
        return await self.client.chat(messages, requirements)

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        requirements: LLMRequirements | None = None,
    ):
        """Chat completion avec streaming.

        Args:
            messages: Messages
            requirements: Requirements

        Yields:
            Tokens générés
        """
        async for chunk in self.client.chat_stream(messages, requirements):
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
        return await self.client.embed(texts, model, provider_name)

    def get_available_providers(self) -> list[str]:
        """Liste les providers disponibles.

        Returns:
            Liste de noms
        """
        return self.registry.list_providers()

    def get_available_models(self, provider: str | None = None) -> list[ModelInfo]:
        """Liste les modèles disponibles.

        Args:
            provider: Filtrer par provider (optionnel)

        Returns:
            Liste de ModelInfo
        """
        return self.registry.list_models(provider)

    def select_best_model(self, requirements: LLMRequirements) -> list[ModelInfo]:
        """Sélectionne le meilleur modèle.

        Args:
            requirements: Requirements

        Returns:
            Top 3 modèles
        """
        models = self.registry.list_models()
        scored = self.selector.select(requirements, models)
        return [sm.model for sm in scored]

    def get_usage_stats(self) -> dict[str, Any]:
        """Récupère les statistiques d'utilisation.

        Returns:
            Statistiques
        """
        return self.tracker.get_usage()

    def get_total_cost(self) -> float:
        """Coût total.

        Returns:
            Coût total en USD
        """
        return self.tracker.get_total_cost()

    def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques globales.

        Returns:
            Statistiques
        """
        registry_stats = self.registry.get_stats()
        usage = self.tracker.get_usage()

        return {
            "registry": registry_stats,
            "total_cost": self.tracker.get_total_cost(),
            "total_calls": sum(v.get("calls", 0) for v in usage.values()),
            "total_tokens": sum(v.get("tokens", 0) for v in usage.values()),
        }