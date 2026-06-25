"""Goal Manager — Gère les goals du module Executive.

Responsabilités :
- Créer, suivre, mettre à jour les goals
- Gérer le cycle de vie des goals
- Coordonner avec le Planner
- Suivre les progrès
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from core.executive.types import Goal, GoalState, GoalProgress, GoalPriority
from core.types.event import Event, EventType

logger = logging.getLogger(__name__)


class ExecutiveGoalManager:
    """Gestionnaire de goals pour le module Executive."""

    def __init__(self, bus=None):
        self._bus = bus
        self._goals: dict[str, Goal] = {}
        self._progress: dict[str, GoalProgress] = {}

    async def create_goal(
        self,
        description: str,
        priority: GoalPriority = GoalPriority.MEDIUM,
        required_capabilities: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
        deadline: datetime | None = None,
    ) -> Goal:
        """Crée un nouveau goal.

        Args:
            description: Description du goal
            priority: Priorité
            required_capabilities: Capabilities requises
            constraints: Contraintes
            deadline: Date limite

        Returns:
            Goal créé
        """
        goal_id = f"goal-{datetime.utcnow().timestamp()}"

        goal = Goal(
            id=goal_id,
            description=description,
            priority=priority,
            required_capabilities=required_capabilities or [],
            constraints=constraints or {},
            deadline=deadline,
        )

        self._goals[goal_id] = goal
        self._progress[goal_id] = GoalProgress(goal_id=goal_id)

        # Publier l'événement
        if self._bus:
            await self._bus.publish(
                EventType.EXECUTIVE_GOAL_CREATED,
                {
                    "goal_id": goal_id,
                    "description": description,
                    "priority": priority.value,
                    "required_capabilities": required_capabilities or [],
                },
            )

        logger.info(f"Goal created: {goal_id} — {description[:50]}")
        return goal

    async def update_goal_state(self, goal_id: str, state: GoalState) -> None:
        """Met à jour l'état d'un goal.

        Args:
            goal_id: ID du goal
            state: Nouvel état
        """
        goal = self._goals.get(goal_id)
        if not goal:
            logger.warning(f"Goal not found: {goal_id}")
            return

        old_state = goal.state
        goal.state = state

        # Mettre à jour les timestamps
        if state == GoalState.EXECUTING and not goal.started_at:
            goal.started_at = datetime.utcnow()
        elif state in [GoalState.COMPLETED, GoalState.FAILED, GoalState.CANCELLED]:
            goal.completed_at = datetime.utcnow()

        # Publier l'événement
        if self._bus:
            await self._bus.publish(
                EventType.EXECUTIVE_GOAL_UPDATED,
                {
                    "goal_id": goal_id,
                    "old_state": old_state.value,
                    "new_state": state.value,
                },
            )

        logger.info(f"Goal {goal_id} state: {old_state} → {state}")

    async def update_progress(
        self,
        goal_id: str,
        completed_tasks: int,
        total_tasks: int,
        current_task: str | None = None,
    ) -> None:
        """Met à jour le progrès d'un goal.

        Args:
            goal_id: ID du goal
            completed_tasks: Tâches complétées
            total_tasks: Total de tâches
            current_task: Tâche en cours
        """
        progress = self._progress.get(goal_id)
        if not progress:
            return

        progress.completed_tasks = completed_tasks
        progress.total_tasks = total_tasks
        progress.current_task = current_task
        progress.progress_percent = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

    async def cancel_goal(self, goal_id: str, reason: str = "") -> None:
        """Annule un goal.

        Args:
            goal_id: ID du goal
            reason: Raison de l'annulation
        """
        goal = self._goals.get(goal_id)
        if not goal:
            return

        await self.update_goal_state(goal_id, GoalState.CANCELLED)

        if self._bus:
            await self._bus.publish(
                EventType.EXECUTIVE_GOAL_CANCELLED,
                {
                    "goal_id": goal_id,
                    "reason": reason,
                },
            )

        logger.info(f"Goal cancelled: {goal_id}")

    async def fail_goal(self, goal_id: str, error: str) -> None:
        """Marque un goal comme échoué.

        Args:
            goal_id: ID du goal
            error: Message d'erreur
        """
        goal = self._goals.get(goal_id)
        if not goal:
            return

        await self.update_goal_state(goal_id, GoalState.FAILED)

        if self._bus:
            await self._bus.publish(
                EventType.EXECUTIVE_GOAL_FAILED,
                {
                    "goal_id": goal_id,
                    "error": error,
                },
            )

        logger.error(f"Goal failed: {goal_id} — {error}")

    def get_goal(self, goal_id: str) -> Goal | None:
        """Récupère un goal.

        Args:
            goal_id: ID du goal

        Returns:
            Goal ou None
        """
        return self._goals.get(goal_id)

    def get_progress(self, goal_id: str) -> GoalProgress | None:
        """Récupère le progrès d'un goal.

        Args:
            goal_id: ID du goal

        Returns:
            GoalProgress ou None
        """
        return self._progress.get(goal_id)

    def list_goals(self, state: GoalState | None = None) -> list[Goal]:
        """Liste les goals.

        Args:
            state: Filtrer par état (optionnel)

        Returns:
            Liste de goals
        """
        goals = list(self._goals.values())
        if state:
            goals = [g for g in goals if g.state == state]
        return goals

    def get_active_goals(self) -> list[Goal]:
        """Récupère les goals actifs.

        Returns:
            Liste de goals actifs
        """
        return [
            g for g in self._goals.values()
            if g.state in [GoalState.PENDING, GoalState.PLANNING, GoalState.EXECUTING]
        ]