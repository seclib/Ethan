"""LLM Router — Routeur simple de modèles.

Retourne le meilleur modèle pour une tâche donnée.
Catégories : reasoning, code, fast, local
"""

from __future__ import annotations

from core.llm.selector import LLMSelector
from core.llm.types import LLMRequirements, ModelInfo, ScoredModel


# Catégories de tâches avec leurs requirements
TASK_CATEGORIES = {
    "reasoning": LLMRequirements(
        min_quality=0.8,
        context_length=32000,
        preferred_providers=["openai", "anthropic"],
    ),
    "code": LLMRequirements(
        min_quality=0.7,
        context_length=16000,
        preferred_providers=["anthropic", "openai"],
    ),
    "fast": LLMRequirements(
        max_latency_ms=2000,
        min_quality=0.4,
    ),
    "local": LLMRequirements(
        require_local=True,
        require_private=True,
        min_quality=0.3,
    ),
}


class LLMRouter:
    """Routeur LLM — choisit le meilleur modèle pour une tâche."""

    def __init__(self, selector: LLMSelector | None = None):
        self._selector = selector or LLMSelector()

    def route(
        self,
        task: str,
        available_models: list[ModelInfo],
    ) -> str:
        """Retourne le meilleur modèle pour la tâche.

        Args:
            task: Catégorie de tâche ("reasoning", "code", "fast", "local")
            available_models: Modèles disponibles

        Returns:
            Nom du meilleur modèle, ou "unknown" si aucun trouvé
        """
        requirements = TASK_CATEGORIES.get(task)
        if requirements is None:
            return "unknown"

        scored = self._selector.select(requirements, available_models)
        if not scored:
            return "unknown"

        return scored[0].model.name

    def route_with_fallback(
        self,
        task: str,
        available_models: list[ModelInfo],
    ) -> str:
        """Retourne le meilleur modèle, avec fallback vers 'fast'.

        Args:
            task: Catégorie de tâche
            available_models: Modèles disponibles

        Returns:
            Nom du meilleur modèle trouvé
        """
        result = self.route(task, available_models)
        if result != "unknown":
            return result

        # Fallback vers fast
        if task != "fast":
            return self.route("fast", available_models)

        return "unknown"

    def list_categories(self) -> list[str]:
        """Liste les catégories disponibles.

        Returns:
            ["reasoning", "code", "fast", "local"]
        """
        return list(TASK_CATEGORIES.keys())