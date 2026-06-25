"""Pipeline — Définition des étapes de traitement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine


@dataclass
class PipelineStep:
    """Étape d'un pipeline."""
    name: str
    handler: Callable[[Any], Coroutine[Any, Any, Any]]
    enabled: bool = True
    retry_on_failure: bool = False
    timeout_seconds: float = 30.0


class Pipeline:
    """Pipeline de traitement.
    
    Responsabilités :
    - Définir les étapes
    - Exécuter séquentiellement
    - Gérer les erreurs
    """

    def __init__(self, name: str):
        self.name = name
        self._steps: list[PipelineStep] = []

    def add_step(self, step: PipelineStep) -> None:
        """Ajoute une étape.

        Args:
            step: Étape
        """
        self._steps.append(step)

    async def execute(self, context: Any) -> Any:
        """Exécute le pipeline.

        Args:
            context: Contexte

        Returns:
            Résultat
        """
        result = context
        for step in self._steps:
            if not step.enabled:
                continue

            # TODO: Implémenter timeout et retry
            result = await step.handler(result)

        return result