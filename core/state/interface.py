"""StateBackend — Abstract interface for persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StateBackend(ABC):
    """Interface abstraite pour la persistance d'état."""

    @abstractmethod
    async def get(self, key: str, namespace: str = "") -> bytes | None:
        """Lit une valeur."""
        pass

    @abstractmethod
    async def set(
        self, key: str, value: bytes, ttl: int | None = None, namespace: str = ""
    ) -> None:
        """Écrit une valeur."""
        pass

    @abstractmethod
    async def delete(self, key: str, namespace: str = "") -> None:
        """Supprime une valeur."""
        pass

    @abstractmethod
    async def persist(self, event: Any) -> None:
        """Persiste un événement."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Ferme les connexions."""
        pass


class LiveState(StateBackend):
    """Alias pour StateBackend — compatibilité avec les imports existants."""

    @abstractmethod
    async def get(self, key: str, namespace: str = "") -> bytes | None:
        pass

    @abstractmethod
    async def set(
        self, key: str, value: bytes, ttl: int | None = None, namespace: str = ""
    ) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str, namespace: str = "") -> None:
        pass

    @abstractmethod
    async def persist(self, event: Any) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass