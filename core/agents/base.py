"""ETHAN Core — Agent Base Class.

Classe de base pour tous les agents du système.
Chaque agent est un processus indépendant qui communique via l'Event Bus.

Cycle de vie :
    init() → start() → [handle_event() | run()] → stop()

Modes :
    - STANDALONE : InMemoryBus (développement, tests)
    - DISTRIBUTED : NATSBus (production, Kernel Go)
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.bus.interface import EventBus, Subscription
from core.bus.memory import InMemoryBus
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Statuts possibles d'un agent."""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentConfig:
    """Configuration d'un agent."""
    name: str
    description: str = ""
    model: str | None = None
    provider: str | None = None
    temperature: float = 0.7
    max_iterations: int = 10
    timeout: int = 300  # seconds
    enabled: bool = True
    auto_start: bool = True
    subscription_patterns: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """Classe de base abstraite pour tous les agents.

    Principes :
    - Communication UNIQUEMENT via EventBus
    - Pas d'appels directs à d'autres agents ou modules
    - Chaque événement contient correlation_id pour le tracing
    - L'implémentation du bus est interchangeable
    
    Utilisation :
        class MyAgent(Agent):
            async def _subscribe_events(self):
                await self.subscribe("ethan.interface.message", self.handle_message)
            
            async def _on_init(self):
                # Setup spécifique
                pass
    """

    def __init__(
        self,
        config: AgentConfig,
        bus: EventBus | None = None,
    ):
        self.config = config
        self._bus = bus or InMemoryBus()
        self._status = AgentStatus.CREATED
        self._tasks: list[asyncio.Task] = []
        self._subscriptions: list[Subscription] = []
        self._metrics: dict[str, Any] = {
            "events_processed": 0,
            "errors": 0,
            "start_time": 0.0,
        }

    # ─── Properties ────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def is_running(self) -> bool:
        return self._status == AgentStatus.RUNNING

    # ─── Lifecycle ─────────────────────────────────────────────────

    async def init(self) -> None:
        """Initialise l'agent. Configure les souscriptions et ressources."""
        if self._status != AgentStatus.CREATED:
            return

        self._status = AgentStatus.INITIALIZING
        logger.info(f"Agent '{self.name}' initializing...")

        # Connexion au bus si nécessaire
        if not await self._bus.is_connected():
            await self._bus.connect("inmemory://local")

        # Hook d'initialisation spécifique
        await self._on_init()

        self._status = AgentStatus.READY
        logger.info(f"Agent '{self.name}' ready")

    async def _on_init(self) -> None:
        """Hook d'initialisation. Surcharger pour ajouter des setups."""
        pass

    async def start(self) -> None:
        """Démarre l'agent : s'abonne aux événements et lance la boucle."""
        if self._status != AgentStatus.READY:
            await self.init()

        self._status = AgentStatus.RUNNING
        self._metrics["start_time"] = time.time()

        # S'abonner aux événements
        await self._subscribe_events()

        logger.info(f"Agent '{self.name}' started")

        # Lancer la boucle principale
        task = asyncio.create_task(self._run_loop())
        self._tasks.append(task)

    async def stop(self) -> None:
        """Arrête proprement l'agent."""
        self._status = AgentStatus.STOPPED

        # Se désabonner
        for sub in self._subscriptions:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
        self._subscriptions.clear()

        # Cancel les tâches en cours
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # Hook d'arrêt
        await self._on_stop()

        logger.info(f"Agent '{self.name}' stopped")

    async def _on_stop(self) -> None:
        """Hook d'arrêt. Surcharger pour cleanup."""
        pass

    async def pause(self) -> None:
        """Met l'agent en pause (continue d'écouter, ne répond pas)."""
        self._status = AgentStatus.PAUSED
        logger.info(f"Agent '{self.name}' paused")

    async def resume(self) -> None:
        """Reprend l'agent après une pause."""
        self._status = AgentStatus.RUNNING
        logger.info(f"Agent '{self.name}' resumed")

    # ─── Event Bus ─────────────────────────────────────────────────

    async def _subscribe_events(self) -> None:
        """S'abonne aux événements de la configuration."""
        for pattern in self.config.subscription_patterns:
            await self.subscribe(pattern, self._on_event)

    async def subscribe(
        self,
        pattern: str,
        handler: Any = None,
    ) -> Subscription:
        """Souscrit à un pattern d'événements.

        Args:
            pattern: Pattern NATS (e.g., "ethan.interface.*")
            handler: Fonction de callback. Si None, utilise _on_event.

        Returns:
            Subscription pour se désabonner
        """
        handler = handler or self._on_event
        sub = await self._bus.subscribe(pattern, handler)
        self._subscriptions.append(sub)
        logger.debug(f"Agent '{self.name}' subscribed to {pattern}")
        return sub

    async def publish(
        self,
        event_type: EventType | str,
        payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Publie un événement sur le bus.

        Args:
            event_type: Type d'événement (EventType enum ou string)
            payload: Données de l'événement
            correlation_id: ID de corrélation pour le tracing
        """
        if isinstance(event_type, str):
            event_type = self._resolve_event_type(event_type)

        event = Event(
            type=event_type,
            source=self.name,
            payload=payload or {},
        )
        if correlation_id:
            event.correlation_id = correlation_id

        await self._bus.publish(event_type.value, event)
        self._metrics["events_processed"] += 1

    async def request(
        self,
        subject: str,
        payload: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Event | None:
        """Envoie une requête et attend une réponse synchrone.

        Args:
            subject: Sujet de la requête
            payload: Données de la requête
            timeout: Timeout en secondes

        Returns:
            Événement de réponse ou None si timeout
        """
        event = Event(
            type=self._resolve_event_type(subject),
            source=self.name,
            payload=payload or {},
        )
        return await self._bus.request(subject, event, timeout=timeout)

    async def _on_event(self, event: Event) -> None:
        """Handler par défaut pour les événements reçus.

        Surcharger pour traiter les événements.
        """
        logger.debug(f"Agent '{self.name}' received {event.type}")

    # ─── Main Loop ─────────────────────────────────────────────────

    async def _run_loop(self) -> None:
        """Boucle principale. Surcharger pour un comportement personnalisé."""
        try:
            while self._status == AgentStatus.RUNNING:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    # ─── Actions ───────────────────────────────────────────────────

    @abstractmethod
    async def run(self, input_data: dict[str, Any] | None = None) -> Result:
        """Point d'entrée principal pour exécuter l'agent.

        Args:
            input_data: Données d'entrée optionnelles

        Returns:
            Result encapsulant le succès ou l'échec
        """
        ...

    # ─── Métriques ─────────────────────────────────────────────────

    def get_metrics(self) -> dict[str, Any]:
        """Retourne les métriques de l'agent."""
        uptime = time.time() - self._metrics["start_time"] if self._metrics["start_time"] else 0
        return {
            "name": self.name,
            "status": self._status.value,
            "uptime": uptime,
            "events_processed": self._metrics["events_processed"],
            "errors": self._metrics["errors"],
            "subscriptions": len(self._subscriptions),
        }

    # ─── Utilitaires ───────────────────────────────────────────────

    def _resolve_event_type(self, name: str) -> EventType:
        """Résout un nom d'événement en EventType.

        Essaye de matcher avec un EventType existant.
        Si aucun match, crée un événement générique.
        """
        try:
            return EventType(name)
        except ValueError:
            # Pour les événements personnalisés, on utilise un mapping
            logger.warning(f"Unknown EventType: {name}")
            return EventType(name)  # Les str enums acceptent n'importe quoi


class AgentRegistry:
    """Registry des agents.

    Gère le cycle de vie et la découverte des agents.
    Compatible avec l'ancienne API.
    """

    def __init__(self):
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Enregistre un agent dans le registry."""
        self._agents[agent.name] = agent
        logger.info(f"Agent '{agent.name}' registered")

    def unregister(self, name: str) -> None:
        """Désenregistre un agent."""
        if name in self._agents:
            del self._agents[name]
            logger.info(f"Agent '{name}' unregistered")

    def get(self, name: str) -> Agent | None:
        """Récupère un agent par son nom."""
        return self._agents.get(name)

    def list(self) -> list[Agent]:
        """Liste tous les agents enregistrés."""
        return list(self._agents.values())

    def list_by_status(self, status: AgentStatus) -> list[Agent]:
        """Liste les agents par statut."""
        return [a for a in self._agents.values() if a.status == status]

    async def start_all(self) -> None:
        """Démarre tous les agents."""
        for agent in self._agents.values():
            await agent.start()

    async def stop_all(self) -> None:
        """Arrête tous les agents."""
        for agent in self._agents.values():
            await agent.stop()

    async def init_all(self) -> None:
        """Initialise tous les agents."""
        for agent in self._agents.values():
            await agent.init()


# Instance globale du registry
registry = AgentRegistry()
