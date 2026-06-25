"""Learning Agent — Module d'apprentissage.

Responsabilités :
- Analyse les patterns de succès/échec
- Extrait des leçons apprises
- Met à jour les heuristiques
- Propose des améliorations au système

Communication :
- Reçoit : ethan.reflective.evaluation, ethan.executor.task.completed
- Publie : ethan.learning.outcome, ethan.learning.pattern
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class LearningAgent(Agent):
    """Agent d'apprentissage — extrait des patterns et améliore le système."""

    def __init__(self, config: AgentConfig, bus=None):
        super().__init__(config, bus)
        self._patterns: dict[str, dict[str, Any]] = {}

    async def _on_init(self) -> None:
        logger.info("Learning agent initializing...")

    async def _subscribe_events(self) -> None:
        await self.subscribe("ethan.reflective.evaluation", self._handle_evaluation)
        await self.subscribe("ethan.executor.task.completed", self._handle_task_completed)

    async def _handle_evaluation(self, event: Event) -> None:
        """Traite une évaluation du ReflectiveAgent."""
        evaluation = event.payload

        plan_id = evaluation.get("plan_id")
        success_rate = evaluation.get("success_rate", 0)
        insights = evaluation.get("insights", [])

        logger.info(f"Learning from evaluation: {plan_id} (success_rate={success_rate:.0%})")

        # Extraire des patterns
        if success_rate >= 0.9:
            pattern_key = "high_success_patterns"
            if pattern_key not in self._patterns:
                self._patterns[pattern_key] = {"count": 0, "examples": []}
            self._patterns[pattern_key]["count"] += 1
            self._patterns[pattern_key]["examples"].append({
                "plan_id": plan_id,
                "insights": insights,
            })

        # Publier un outcome d'apprentissage
        await self.publish(
            EventType.LEARNING_OUTCOME,
            {
                "type": "evaluation_learned",
                "plan_id": plan_id,
                "success_rate": success_rate,
                "pattern": "high_success" if success_rate >= 0.9 else "needs_improvement",
            },
            correlation_id=event.correlation_id,
        )

    async def _handle_task_completed(self, event: Event) -> None:
        """Traite une tâche complétée pour apprendre des succès."""
        task_id = event.payload.get("task_id")
        capability = event.payload.get("capability")
        duration_ms = event.payload.get("duration_ms", 0)

        # Enregistrer le pattern de succès
        pattern_key = f"capability_success:{capability}"
        if pattern_key not in self._patterns:
            self._patterns[pattern_key] = {
                "count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
            }

        pattern = self._patterns[pattern_key]
        pattern["count"] += 1
        pattern["total_duration_ms"] += duration_ms
        pattern["avg_duration_ms"] = pattern["total_duration_ms"] / pattern["count"]

        logger.debug(f"Learned from {capability}: avg {pattern['avg_duration_ms']:.0f}ms")

    async def run(self, input_data=None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "learning ready", "patterns": len(self._patterns)})