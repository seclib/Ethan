"""Provider Model — Ethan OS

Les modèles IA sont interchangeables.
Le Core ne connaît que l'abstraction, jamais les implémentations.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional


class ReasoningProvider(ABC):
    """Interface abstraite pour tous les providers de raisonnement."""

    @abstractmethod
    async def reason(self, prompt: str, context: Any) -> str:
        """Capacité de raisonnement. Retourne une réponse texte."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Capacité d'embedding. Retourne un vecteur."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Vérifie que le provider est disponible."""
        pass


class ProviderRegistry:
    """Registry des providers disponibles."""

    def __init__(self):
        self._providers = {}

    def register(self, name: str, provider: ReasoningProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> Optional[ReasoningProvider]:
        return self._providers.get(name)

    def list_all(self):
        return list(self._providers.keys())