"""Reflective Agent — Module d'auto-évaluation.

Responsabilités :
- Évalue les résultats des plans
- Produit des insights et leçons apprises
- Identifie les échecs et les succès
- Propose des améliorations

Communication :
- Reçoit : ethan.executor.plan.done, ethan.executor.task.failed
- Publie : ethan.reflective.evaluation, ethan.reflective.insight
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class ReflectiveAgent(Agent):
    """Agent réflexif — évalue les résultats et produit des insights."""

    def __init__(self, config: AgentConfig, bus=None):
        super().__init__(config, bus)

    async def _on_init(self) -> None:
        logger.info("Reflective agent initializing...")

    async def _subscribe_events(self) -> None:
        await self.subscribe("ethan.executor.plan.done", self._handle_plan_done)
        await self.subscribe("ethan.executor.task.failed", self._handle_task_failed)

    async def _handle_plan_done(self, event: Event) -> None:
        """Évalue un plan terminé."""
        plan_id = event.payload.get("plan_id")
        goal_id = event.payload.get("goal_id")
        results = event.payload.get("results", [])
        success = event.payload.get("success", False)

        logger.info(f"Reflective evaluating plan: {plan_id} (success={success})")

        # Calculer les métriques
        total_tasks = len(results)
        failed_tasks = [r for r in results if r.get("status") != "completed"]
        success_rate = (total_tasks - len(failed_tasks)) / total_tasks if total_tasks > 0 else 0

        # Produire l'évaluation
        evaluation = {
            "plan_id": plan_id,
            "goal_id": goal_id,
            "success": success,
            "total_tasks": total_tasks,
            "failed_tasks": len(failed_tasks),
            "success_rate": success_rate,
            "insights": [],
        }

        # Générer des insights
        if success_rate == 1.0:
            evaluation["insights"].append("All tasks completed successfully")
        elif success_rate >= 0.8:
            evaluation["insights"].append(f"Mostly successful ({success_rate:.0%}), minor issues")
        else:
            evaluation["insights"].append(f"Significant failures ({success_rate:.0%}), needs investigation")
            if failed_tasks:
                failed_capabilities = [r.get("capability") for r in failed_tasks]
                evaluation["insights"].append(f"Failed capabilities: {', '.join(failed_capabilities)}")

        # Publier l'évaluation
        await self.publish(
            EventType.REFLECTIVE_EVALUATION,
            evaluation,
            correlation_id=event.correlation_id,
        )

        # Si insight intéressant, le publier séparément
        if evaluation["insights"]:
            await self.publish(
                EventType.REFLECTIVE_INSIGHT,
                {
                    "plan_id": plan_id,
                    "insight": evaluation["insights"][0],
                    "details": evaluation,
                },
            )

        logger.info(f"Evaluation complete: {success_rate:.0%} success rate")

    async def _handle_task_failed(self, event: Event) -> None:
        """Traite un échec de tâche."""
        task_id = event.payload.get("task_id")
        capability = event.payload.get("capability")
        error = event.payload.get("error")

        logger.warning(f"Reflective analyzing failure: {task_id} ({capability})")

        # Publier un insight sur l'échec
        await self.publish(
            EventType.REFLECTIVE_INSIGHT,
            {
                "type": "task_failure",
                "task_id": task_id,
                "capability": capability,
                "error": error,
                "suggestion": f"Check {capability} implementation or retry with different params",
            },
        )

    async def run(self, input_data=None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "reflective ready"})