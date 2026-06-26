"""Plugin Base — classe abstraite pour tous les plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PluginBase(ABC):
    """Classe de base pour tous les plugins ETHAN."""

    def __init__(self, manifest: dict):
        self.manifest = manifest
        self.name = manifest.get("name", "unknown")
        self.version = manifest.get("version", "0.0.0")
        self._running = False

    @abstractmethod
    async def on_load(self) -> None:
        """Appelé quand le plugin est chargé."""
        pass

    @abstractmethod
    async def on_start(self) -> None:
        """Appelé quand le plugin démarre."""
        pass

    @abstractmethod
    async def on_stop(self) -> None:
        """Appelé quand le plugin s'arrête."""
        pass

    @abstractmethod
    async def on_unload(self) -> None:
        """Appelé quand le plugin est déchargé."""
        pass

    async def health(self) -> dict:
        """Health check."""
        return {"status": "healthy", "name": self.name, "version": self.version}