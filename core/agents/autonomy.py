"""Autonomy Agent — Module d'autonomie.

Responsabilités :
- Détecte les conditions d'initiative autonome
- Crée des goals sans intervention utilisateur
- Priorise les actions autonomes
- Évite les boucles infinies

Communication :
- Reçoit : ethan.system.telemetry, ethan.reflective.insight
- Publie : ethan.autonomy.initiative, ethan.autonomy.suggestion
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.types.event import Event, EventType
from core.types.goal import Goal, GoalPriority, GoalState
from core.types.result import Result

logger = logging.getLogger(__name__)


class AutonomyAgent(Agent):
    """Agent d'autonomie — initiatives auto-gérées."""

    def __init__(self, config: AgentConfig, bus=None):
        super().__init__(config, bus)
        self._max_autonomous_goals = 3
        self._cooldown_seconds = 300  # 5 minutes

    async def _on_init(self) -> None:
        logger.info("Autonomy agent initializing...")

    async def _subscribe_events(self) -> None:
        await self.subscribe("ethan.system.telemetry", self._handle_telemetry)
        await self.subscribe("ethan.reflective.insight", self._handle_insight)

    async def _handle_telemetry(self, event: Event) -> None:
        """Analyse la télémetrie pour détecter des opportunités."""
        metrics = event.payload.get("metrics", {})

        # Exemple : si le système est idle depuis longtemps
        idle_time = metrics.get("idle_time", 0)
        if idle_time > 3600:  # 1 heure
            logger.info("System idle for 1h, suggesting proactive action")
            await self._suggest_initiative("system_idle", "Review recent activities or plan next steps")

    async def _handle_insight(self, event: Event) -> None:
        """Réagit aux insights du ReflectiveAgent."""
        insight_type = event.payload.get("type")
        insight = event.payload.get("insight")

        if insight_type == "task_failure":
            # Proposer une action corrective
            await self._suggest_initiative(
                "fix_failure",
                f"Investigate failure: {insight}",
                priority=GoalPriority.HIGH,
            )

    async def _suggest_initiative(
        self,
        initiative_type: str,
        description: str,
        priority: GoalPriority = GoalPriority.LOW,
    ) -> None:
        """Crée une suggestion d'initiative."""
        await self.publish(
            EventType.AUTONOMY_SUGGESTION,
            {
                "type": initiative_type,
                "description": description,
                "priority": priority.value,
                "auto_execute": False,  # Nécessite validation utilisateur
            },
        )

    async def run(self, input_data=None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "autonomy ready"})