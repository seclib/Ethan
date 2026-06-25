"""Executive Module — Module exécutif principal.

Responsabilités :
- Créer des goals
- Déléguer au Planner
- Coordonner l'exécution
- Suivre les progrès
- Gérer les priorités
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.executive.goal_manager import ExecutiveGoalManager
from core.executive.types import Goal, GoalPriority
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class ExecutiveModule(Agent):
    """Module Executive — gère les goals et coordonne l'exécution."""

    def __init__(self, config: AgentConfig, bus=None):
        super().__init__(config, bus)
        self._config = config
        self.goal_manager = ExecutiveGoalManager(bus)

    async def _on_init(self) -> None:
        """Initialise le module."""
        logger.info("Executive module initializing...")

    async def _subscribe_events(self) -> None:
        """S'abonne aux événements."""
        await self.subscribe("ethan.interface.message", self._handle_user_input)
        await self.subscribe("ethan.planner.plan.created", self._handle_plan_created)
        await self.subscribe("ethan.executor.plan.done", self._handle_plan_done)

    async def _handle_user_input(self, event: Event) -> None:
        """Reçoit une entrée utilisateur et crée un goal."""
        query = event.payload.get("query", "")
        if not query:
            return

        logger.info(f"Executive received query: {query[:50]}")

        # Créer un goal depuis la requête
        goal = await self.goal_manager.create_goal(
            description=query,
            priority=GoalPriority.MEDIUM,
        )

        logger.info(f"Goal created from query: {goal.id}")

    async def _handle_plan_created(self, event: Event) -> None:
        """Reçoit un plan créé par le Planner."""
        plan_id = event.payload.get("plan_id")
        goal_id = event.payload.get("goal_id")

        logger.info(f"Executive received plan: {plan_id} for goal {goal_id}")

        # Mettre à jour l'état du goal
        await self.goal_manager.update_goal_state(goal_id, GoalState.PLANNED)

    async def _handle_plan_done(self, event: Event) -> None:
        """Reçoit la fin d'exécution d'un plan."""
        plan_id = event.payload.get("plan_id")
        success = event.payload.get("success", False)

        # Récupérer le goal associé
        # TODO: Mapping plan_id -> goal_id
        logger.info(f"Plan {plan_id} done: success={success}")

    async def create_goal(
        self,
        description: str,
        priority: GoalPriority = GoalPriority.MEDIUM,
        required_capabilities: list[str] | None = None,
    ) -> Goal:
        """Crée un goal (API publique).

        Args:
            description: Description
            priority: Priorité
            required_capabilities: Capabilities requises

        Returns:
            Goal créé
        """
        return await self.goal_manager.create_goal(
            description=description,
            priority=priority,
            required_capabilities=required_capabilities,
        )

    async def cancel_goal(self, goal_id: str, reason: str = "") -> None:
        """Annule un goal.

        Args:
            goal_id: ID du goal
            reason: Raison
        """
        await self.goal_manager.cancel_goal(goal_id, reason)

    def get_active_goals(self) -> list[Goal]:
        """Récupère les goals actifs.

        Returns:
            Liste de goals actifs
        """
        return self.goal_manager.get_active_goals()

    async def run(self, input_data: dict[str, Any] | None = None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "executive ready"})