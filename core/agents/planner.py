"""Planner Agent — Planification de tâches complexes"""

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.events import Event

logger = logging.getLogger(__name__)


class PlannerAgent(Agent):
    """Agent spécialisé dans la planification de tâches complexes.

    Reçoit des objectifs et produit des plans d'exécution.
    Délègue les sous-tâches aux agents spécialisés.
    """

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="planner",
            description="Planification et orchestration de tâches complexes",
            **kwargs
        )
        super().__init__(config)
        self._active_plans: dict[str, dict] = {}

    async def _subscribe_events(self) -> None:
        self.bus.subscribe("task:plan", self._handle_plan_request)
        self.bus.subscribe("task:status", self._handle_status_update)

    async def _handle_plan_request(self, event: Event) -> None:
        """Reçoit une demande de planification."""
        logger.info(f"Planning request: {event.data}")
        plan = await self.run(event.data)
        await self.publish("plan:ready", plan)

    async def _handle_status_update(self, event: Event) -> None:
        """Met à jour le statut d'une tâche planifiée."""
        task_id = event.data.get("task_id")
        status = event.data.get("status")
        if task_id and task_id in self._active_plans:
            self._active_plans[task_id]["status"] = status

    async def run(self, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyse un objectif et produit un plan."""
        objective = (input_data or {}).get("objective", "")
        context = (input_data or {}).get("context", {})

        prompt = f"""You are a planning agent. Analyze this objective and create a step-by-step plan.

Objective: {objective}
Context: {context}

Output a JSON plan with:
- goal: the main objective
- steps: array of steps (each with: id, agent, action, expected_output)
- dependencies: step dependencies
- estimated_duration: total estimated time"""

        plan_text = await self.think(prompt)

        plan = {
            "objective": objective,
            "plan": plan_text,
            "steps": [],
            "status": "created",
            "timestamp": __import__("time").time(),
        }

        plan_id = f"plan_{hash(objective) % 10000}"
        self._active_plans[plan_id] = plan

        return plan