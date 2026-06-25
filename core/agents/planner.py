"""Planner Agent — Module de planification.

Responsabilités :
- Reçoit des goals (ethan.executive.goal.created)
- Décompose en tâches (DAG)
- Consulte le Capability Registry pour résoudre les capabilities
- Publie le plan (ethan.planner.plan.created)

Communication :
- Reçoit : ethan.executive.goal.created
- Publie : ethan.planner.plan.created, ethan.planner.plan.failed
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.types.event import Event, EventType
from core.types.goal import Goal, GoalPriority
from core.types.plan import Plan, Task, TaskDAG
from core.types.result import Result

logger = logging.getLogger(__name__)


@dataclass
class PlannerConfig(AgentConfig):
    """Configuration du Planner."""
    max_tasks_per_plan: int = 20
    max_depth: int = 5


class PlannerAgent(Agent):
    """Agent planificateur — décompose les goals en tâches."""

    def __init__(self, config: PlannerConfig, bus=None):
        super().__init__(config, bus)
        self._config = config

    async def _on_init(self) -> None:
        logger.info("Planner agent initializing...")

    async def _subscribe_events(self) -> None:
        await self.subscribe("ethan.executive.goal.created", self._handle_goal)

    async def _handle_goal(self, event: Event) -> None:
        """Reçoit un goal et crée un plan."""
        goal_id = event.payload.get("goal_id")
        description = event.payload.get("description", "")
        priority = event.payload.get("priority", "medium")

        logger.info(f"Planner received goal: {goal_id} — {description[:50]}")

        # Créer le plan
        plan = self._decompose(goal_id, description, GoalPriority(priority))

        # Publier le plan
        await self.publish(
            EventType.PLANNER_PLAN_CREATED,
            {
                "plan_id": plan.id,
                "goal_id": goal_id,
                "tasks": [
                    {
                        "id": t.id,
                        "capability": t.capability,
                        "depends_on": t.depends_on,
                        "params": t.params,
                    }
                    for t in plan.tasks
                ],
            },
            correlation_id=event.correlation_id,
        )

        logger.info(f"Plan created: {plan.id} with {len(plan.tasks)} tasks")

    def _decompose(self, goal_id: str | None, description: str, priority: GoalPriority) -> Plan:
        """Décompose un goal en tâches.

        MVP : heuristique simple.
        Production : LLM pour décomposition intelligente.
        """
        tasks = []

        # Heuristique : détecter les actions dans la description
        desc_lower = description.lower()

        if "docker" in desc_lower and "build" in desc_lower:
            tasks.append(Task(id="t1", capability="docker.build", params={"image": "app"}))
            tasks.append(Task(id="t2", capability="docker.push", depends_on=["t1"]))

        elif "deploy" in desc_lower:
            tasks.append(Task(id="t1", capability="deploy.prepare"))
            tasks.append(Task(id="t2", capability="deploy.execute", depends_on=["t1"]))
            tasks.append(Task(id="t3", capability="health.check", depends_on=["t2"]))

        elif "test" in desc_lower:
            tasks.append(Task(id="t1", capability="test.run"))

        else:
            # Goal générique → tâche unique
            tasks.append(Task(id="t1", capability="generic.execute", params={"description": description}))

        # Créer le DAG (un niveau par tâche pour MVP)
        dag = TaskDAG()
        dag.add_level(tasks)

        safe_goal_id = goal_id[:8] if goal_id else "unknown"

        plan = Plan(
            id=f"plan-{safe_goal_id}",
            goal_id=goal_id or "",
            tasks=tasks,
        )

        return plan

    async def run(self, input_data=None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "planning"})