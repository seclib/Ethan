"""Module & Agent — Classes de base pour tous les composants ETHAN.

Un Module est un composant réactif qui répond aux événements.
Un Agent est un Module capable d'initiative autonome.

Tous les Agents sont des Modules.
Tous les Modules ne sont pas des Agents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.bus.interface import EventBus
from core.types.event import Event


class ModuleState(str, Enum):
    """États possibles d'un module."""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"
    CRASHED = "crashed"


@dataclass
class ModuleContext:
    """Contexte d'exécution fourni à chaque module au démarrage."""
    name: str
    bus: EventBus
    config: dict[str, Any] = field(default_factory=dict)
    state: ModuleState = ModuleState.CREATED


class Module(ABC):
    """Module de base — composant réactif.

    Un Module répond aux événements qui lui sont adressés.
    Il ne prend pas d'initiative autonome.

    Cycle de vie :
        1. initialize(context) → prépare le module
        2. handle_event(event) → traite les événements
        3. shutdown() → arrêt propre
    """

    def __init__(self, name: str):
        self.name = name
        self.context: ModuleContext | None = None
        self._state = ModuleState.CREATED

    @property
    def state(self) -> ModuleState:
        return self._state

    async def initialize(self, context: ModuleContext) -> None:
        """Initialisation du module.

        Args:
            context: Contexte d'exécution (bus, config, etc.)
        """
        self.context = context
        self._state = ModuleState.INITIALIZING
        await self._on_initialize()
        self._state = ModuleState.READY

    async def _on_initialize(self) -> None:
        """Hook d'initialisation — à surcharger si nécessaire."""
        pass

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Traite un événement.

        Args:
            event: L'événement à traiter
        """
        ...

    async def shutdown(self) -> None:
        """Arrêt propre du module."""
        self._state = ModuleState.STOPPED
        await self._on_shutdown()

    async def _on_shutdown(self) -> None:
        """Hook d'arrêt — à surcharger si nécessaire."""
        pass

    async def publish(self, subject: str, event: Event) -> None:
        """Publie un événement sur le bus.

        Args:
            subject: Sujet NATS
            event: Événement à publier
        """
        if self.context is None:
            raise RuntimeError(f"Module {self.name} not initialized")
        await self.context.bus.publish(subject, event)

    async def subscribe(
        self,
        pattern: str,
        handler,
        queue: str | None = None,
    ):
        """Souscrit à un pattern d'événements.

        Args:
            pattern: Pattern NATS
            handler: Fonction de traitement
            queue: Queue group optionnel
        """
        if self.context is None:
            raise RuntimeError(f"Module {self.name} not initialized")
        return await self.context.bus.subscribe(pattern, handler, queue)


class Agent(Module):
    """Agent — module capable d'initiative autonome.

    Un Agent peut :
    - Démarrer une boucle d'exécution autonome (run)
    - Émettre des événements sans sollicitation externe
    - Maintenir un état interne persistant

    Cycle de vie :
        1. initialize(context) → prépare l'agent
        2. run() → boucle principale autonome
        3. shutdown() → arrêt propre
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def run(self) -> None:
        """Boucle principale autonome.

        À surcharger dans les sous-classes.
        Par défaut, ne fait rien (agent passif).
        """
        self._running = True
        self._state = ModuleState.RUNNING
        try:
            await self._on_run()
        finally:
            self._running = False
            self._state = ModuleState.READY

    async def _on_run(self) -> None:
        """Hook de la boucle principale — à surcharger."""
        pass

    async def shutdown(self) -> None:
        """Arrêt propre de l'agent."""
        self._running = False
        self._state = ModuleState.STOPPED
        await self._on_shutdown()