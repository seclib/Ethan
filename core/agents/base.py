"""Jarvis OS — Agent Base Class

Classe de base pour tous les agents du système.
Chaque agent est indépendant et communique via l'Event Bus.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.events import Event, EventBus, bus as default_bus
from core.llm import LLMProvider, get_provider

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
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
    metadata: dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """Classe de base abstraite pour tous les agents.

    Cycle de vie:
        init() → start() → run() / handle_event() → stop()

    Communication:
        - Publie des événements via self.bus.publish()
        - Répond aux événements via self.bus.subscribe()
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_provider: LLMProvider | None = None,
        bus: EventBus | None = None,
    ):
        self.config = config
        self._llm = llm_provider or get_provider(config.provider)
        self._bus = bus or default_bus
        self._status = AgentStatus.CREATED
        self._tasks: list[asyncio.Task] = []
        self._metrics = {"events_processed": 0, "errors": 0, "start_time": 0.0}

    # ─── Properties ─────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def llm(self) -> LLMProvider:
        return self._llm

    @property
    def bus(self) -> EventBus:
        return self._bus

    # ─── Lifecycle ───────────────────────────────────────────────────

    async def init(self) -> None:
        """Initialise l'agent. À surcharger si nécessaire."""
        self._status = AgentStatus.INITIALIZING
        logger.info(f"Agent '{self.name}' initializing...")
        await self._on_init()
        self._status = AgentStatus.READY
        logger.info(f"Agent '{self.name}' ready")

    async def _on_init(self) -> None:
        """Hook d'initialisation. Surcharger pour ajouter des setups."""
        pass

    async def start(self) -> None:
        """Démarre l'agent et s'abonne aux événements."""
        if self._status != AgentStatus.READY:
            await self.init()

        self._status = AgentStatus.RUNNING
        self._metrics["start_time"] = time.time()

        # Subscribe aux événements
        await self._subscribe_events()

        logger.info(f"Agent '{self.name}' started")

        # Lancer la boucle principale
        task = asyncio.create_task(self._run_loop())
        self._tasks.append(task)

    async def stop(self) -> None:
        """Arrête proprement l'agent."""
        self._status = AgentStatus.STOPPED

        # Cancel running tasks
        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        await self._on_stop()
        logger.info(f"Agent '{self.name}' stopped")

    async def _on_stop(self) -> None:
        """Hook d'arrêt. Surcharger pour cleanup."""
        pass

    # ─── Events ──────────────────────────────────────────────────────

    async def _subscribe_events(self) -> None:
        """S'abonne aux événements. Surcharger pour écouter des événements."""
        pass

    async def publish(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Publie un événement sur le bus."""
        event = Event(
            type=event_type,
            data=data or {},
            source=self.name,
            timestamp=time.time(),
        )
        await self._bus.publish(event)

    # ─── Main Loop ───────────────────────────────────────────────────

    async def _run_loop(self) -> None:
        """Boucle principale. Surcharger pour un comportement personnalisé."""
        try:
            while self._status == AgentStatus.RUNNING:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    # ─── Actions ─────────────────────────────────────────────────────

    @abstractmethod
    async def run(self, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Point d'entrée principal pour exécuter l'agent."""
        ...

    async def think(self, prompt: str, **kwargs) -> str:
        """Utilise le LLM pour réfléchir/générer une réponse."""
        from core.llm import ChatMessage

        messages = [ChatMessage(role="user", content=prompt)]
        response = await self._llm.chat(
            messages=messages,
            model=self.config.model,
            temperature=self.config.temperature,
            **kwargs,
        )
        return response.content

    # ─── Metrics ─────────────────────────────────────────────────────

    def get_metrics(self) -> dict[str, Any]:
        """Retourne les métriques de l'agent."""
        uptime = time.time() - self._metrics["start_time"] if self._metrics["start_time"] else 0
        return {
            "name": self.name,
            "status": self._status.value,
            "uptime": uptime,
            "events_processed": self._metrics["events_processed"],
            "errors": self._metrics["errors"],
        }


class AgentRegistry:
    """Registry des agents.

    Gère le cycle de vie et la découverte des agents.
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