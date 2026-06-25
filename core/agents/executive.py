"""Executive Agent — Module exécutif.

Responsabilités :
- Reçoit les intents utilisateur (messages, commandes)
- Crée des goals à partir des intents
- Gère la priorité des goals
- Coordonne les autres modules (Planner, Memory, etc.)
- Produit des réponses finales

Communication :
- Reçoit : ethan.interface.message, ethan.interface.command
- Publie : ethan.executive.goal.created, ethan.executive.response
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from core.agents.base import Agent, AgentConfig, AgentStatus
from core.bus.interface import EventBus
from core.types.event import Event, EventType
from core.types.goal import Goal, GoalPriority, GoalState
from core.types.result import Result

logger = logging.getLogger(__name__)


@dataclass
class ExecutiveConfig(AgentConfig):
    """Configuration spécifique de l'Executive."""
    max_goals: int = 10
    goal_ttl: int = 3600  # 1 heure
    auto_prioritize: bool = True


class ExecutiveAgent(Agent):
    """Agent exécutif — point d'entrée principal du système.

    Reçoit tous les messages/commandes des interfaces.
    Crée des goals et délègue au Planner.
    """

    def __init__(
        self,
        config: ExecutiveConfig,
        bus: EventBus | None = None,
    ):
        super().__init__(config, bus)
        self._config = config  # type hint
        self._active_goals: dict[str, Goal] = {}
        self._sessions: dict[str, dict[str, Any]] = {}

    async def _on_init(self) -> None:
        """Initialise l'Executive."""
        logger.info("Executive agent initializing...")

    async def _subscribe_events(self) -> None:
        """S'abonne aux événements."""
        await self.subscribe("ethan.interface.message", self._handle_message)
        await self.subscribe("ethan.interface.command", self._handle_command)
        await self.subscribe("ethan.planner.plan.created", self._handle_plan_created)
        await self.subscribe("ethan.executor.plan.done", self._handle_plan_done)

    async def _on_event(self, event: Event) -> None:
        """Route les événements vers les handlers spécifiques."""
        # Les handlers sont déjà enregistrés via subscribe()
        pass

    async def _handle_message(self, event: Event) -> None:
        """Traite un message utilisateur."""
        logger.info(f"Executive received message: {event.payload}")

        text = event.payload.get("text", "")
        session_id = event.payload.get("session_id", "default")
        user_id = event.payload.get("user_id", "anonymous")

        # Créer ou récupérer la session
        session = self._get_or_create_session(session_id, user_id)

        # Créer un goal à partir du message
        goal = Goal(
            title=text[:100],  # Tronquer pour le titre
            description=text,
            state=GoalState.ACTIVE,
            priority=GoalPriority.MEDIUM,
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "source": "interface.message",
            },
        )

        # Stocker le goal
        self._active_goals[goal.id] = goal

        # Publier l'événement de création de goal
        await self.publish(
            EventType.EXECUTIVE_GOAL_CREATED,
            {
                "goal_id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "priority": goal.priority.value,
                "session_id": session_id,
            },
            correlation_id=event.correlation_id,
        )

        logger.info(f"Goal created: {goal.id} — {goal.title}")

    async def _handle_command(self, event: Event) -> None:
        """Traite une commande structurée."""
        command = event.payload.get("command", "")
        args = event.payload.get("args", [])
        meta = event.payload.get("meta", {})

        logger.info(f"Executive received command: {command} {args}")

        # TODO: Router vers le bon handler de commande
        # Pour l'instant, on crée un goal
        goal = Goal(
            title=f"Command: {command}",
            description=f"Execute command: {command} with args {args}",
            state=GoalState.ACTIVE,
            priority=GoalPriority.HIGH,
            metadata={
                "command": command,
                "args": args,
                "meta": meta,
            },
        )

        self._active_goals[goal.id] = goal

        await self.publish(
            EventType.EXECUTIVE_GOAL_CREATED,
            {
                "goal_id": goal.id,
                "command": command,
                "args": args,
            },
            correlation_id=event.correlation_id,
        )

    async def _handle_plan_created(self, event: Event) -> None:
        """Reçoit un plan du Planner."""
        plan_id = event.payload.get("plan_id")
        goal_id = event.payload.get("goal_id")
        tasks = event.payload.get("tasks", [])

        logger.info(f"Plan received: {plan_id} for goal {goal_id} ({len(tasks)} tasks)")

        # Mettre à jour le goal
        if goal_id in self._active_goals:
            goal = self._active_goals[goal_id]
            goal.state = GoalState.ACTIVE
            goal.metadata["plan_id"] = plan_id

    async def _handle_plan_done(self, event: Event) -> None:
        """Reçoit le résultat d'un plan."""
        plan_id = event.payload.get("plan_id")
        results = event.payload.get("results", [])
        goal_id = event.payload.get("goal_id")

        logger.info(f"Plan completed: {plan_id}")

        # Évaluer le résultat
        success = all(r.get("status") == "completed" for r in results)

        # Mettre à jour le goal
        if goal_id and goal_id in self._active_goals:
            goal = self._active_goals[goal_id]
            if success:
                goal.state = GoalState.COMPLETED
            else:
                goal.state = GoalState.FAILED

        # Publier la réponse finale
        response_text = self._format_response(goal_id, results, success)

        await self.publish(
            EventType.EXECUTIVE_RESPONSE,
            {
                "goal_id": goal_id,
                "success": success,
                "response": response_text,
                "results": results,
            },
            correlation_id=event.correlation_id,
        )

    def _get_or_create_session(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Récupère ou crée une session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "id": session_id,
                "user_id": user_id,
                "created_at": "now",
                "message_count": 0,
            }
        self._sessions[session_id]["message_count"] += 1
        return self._sessions[session_id]

    def _format_response(self, goal_id: str | None, results: list[dict], success: bool) -> str:
        """Formate la réponse finale pour l'utilisateur."""
        if not results:
            return "Done."

        if success:
            return f"✅ Completed {len(results)} tasks successfully."
        else:
            failed = [r for r in results if r.get("status") != "completed"]
            return f"⚠️ Completed with {len(failed)} failures."

    async def run(self, input_data: dict[str, Any] | None = None) -> Result:
        """Point d'entrée principal (pour mode standalone)."""
        if input_data and "text" in input_data:
            # Simuler un événement
            event = Event(
                type=EventType.INTERFACE_MESSAGE,
                source="standalone",
                payload={"text": input_data["text"]},
            )
            await self._handle_message(event)
            return Result.ok(data={"status": "processed"})

        return Result.ok(data={"status": "running"})