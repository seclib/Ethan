"""LLM Provider Registry — Catalogue des providers LLM."""

from __future__ import annotations

import logging
from typing import Any

from core.llm.types import ModelInfo

logger = logging.getLogger(__name__)


class LLMProviderRegistry:
    """Catalogue des providers LLM."""

    def __init__(self):
        self._providers: dict[str, Any] = {}  # LLMProvider instances
        self._models: dict[str, ModelInfo] = {}

    def register_provider(self, provider: Any) -> None:
        """Enregistre un provider.

        Args:
            provider: Instance de LLMProvider
        """
        self._providers[provider.name] = provider

        # Enregistrer les modèles
        try:
            models = provider.list_models()
            for model in models:
                self._models[model.id] = model
            logger.info(f"Provider registered: {provider.name} ({len(models)} models)")
        except Exception as e:
            logger.warning(f"Failed to list models for {provider.name}: {e}")

    def get_provider(self, name: str) -> Any:
        """Récupère un provider.

        Args:
            name: Nom du provider

        Returns:
            Provider ou None
        """
        return self._providers.get(name)

    def get_model(self, model_id: str) -> ModelInfo | None:
        """Récupère les infos d'un modèle.

        Args:
            model_id: ID du modèle

        Returns:
            ModelInfo ou None
        """
        return self._models.get(model_id)

    def list_providers(self) -> list[str]:
        """Liste les providers disponibles.

        Returns:
            Liste de noms
        """
        return list(self._providers.keys())

    def list_models(self, provider: str | None = None) -> list[ModelInfo]:
        """Liste les modèles.

        Args:
            provider: Filtrer par provider (optionnel)

        Returns:
            Liste de ModelInfo
        """
        if provider:
            return [m for m in self._models.values() if m.provider == provider]
        return list(self._models.values())

    async def health_check(self) -> dict[str, bool]:
        """Vérifie la disponibilité de chaque provider.

        Returns:
            Dict {provider_name: is_available}
        """
        results = {}
        for name, provider in self._providers.items():
            try:
                await provider.list_models()
                results[name] = True
            except Exception as e:
                logger.warning(f"Health check failed for {name}: {e}")
                results[name] = False
        return results

    def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques
        """
        return {
            "total_providers": len(self._providers),
            "total_models": len(self._models),
            "available_models": sum(1 for m in self._models.values() if m.is_available),
        }