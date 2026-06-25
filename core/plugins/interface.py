"""Plugin Interface — Contrat pour tous les plugins Python ETHAN."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from core.bus.interface import EventBus
from core.types.capability import Capability


@dataclass
class PluginManifest:
    """Manifeste d'un plugin.

    Doit être défini dans le module __init__ du plugin.
    """
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    api_version: str = "1"
    capabilities: list[Capability] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class EthanPlugin(ABC):
    """Interface abstraite pour tous les plugins Python.

    Cycle de vie :
        load() → init(bus, config) → [use] → close()
    """

    manifest: PluginManifest

    @abstractmethod
    async def init(self, bus: EventBus, config: dict[str, Any]) -> None:
        """Initialise le plugin avec le bus et sa configuration.

        Args:
            bus: Bus d'événements pour la communication
            config: Configuration spécifique au plugin
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Nettoie les ressources du plugin."""
        ...

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def version(self) -> str:
        return self.manifest.version