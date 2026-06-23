"""Autonomous Goal Generation Engine — Analyzes and proposes new goals."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.autonomy.curiosity import CuriosityEngine
from kernel.autonomy.environment import EnvironmentAnalyzer
from kernel.autonomy.weakness import WeaknessDetector
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event
from sdk.goals import GoalProposal, GoalScore

logger = logging.getLogger(__name__)


class AutonomyEngine:
    """Closed-loop autonomous goal generation."""

    INPUT_TOPICS = [
        "task.>",
        "failure.>",
        "learning.>",
        "system.>",
        "idle.>",
    ]

    def __init__(
        self,
        bus: EventBus,
        redis: RedisLiveState,
        curiosity: CuriosityEngine,
        weakness: WeaknessDetector,
        environment: EnvironmentAnalyzer,
    ):
        self.bus = bus
        self.redis = redis
        self.curiosity = curiosity
        self.weakness = weakness
        self.environment = environment
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for topic in self.INPUT_TOPICS:
            await self.bus.subscribe(topic, self._on_signal, queue="autonomy")
        logger.info("Autonomy Engine started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Autonomy Engine stopped")

    async def _on_signal(self, event: Event) -> None:
        if not self._running:
            return
        try:
            await self._analyze(event)
        except Exception as e:
            logger.error(f"Autonomy handler failed: {e}")

    async def _analyze(self, event: Event) -> None:
        # Load current self-model
        self_model = await self.redis.get("system:self_model") or {}

        # Trigger detectors
        curiosity_proposals = await self.curiosity.detect_gaps({
            "all_skills": list(self_model.get("skills", {}).keys()),
            "skills_tested": ["linux", "docker", "reasoning"],
            "all_tools": ["shell", "filesystem", "web"],
            "tools_used": ["shell"],
        })

        weakness_proposals = await self.weakness.detect(self_model)

        env_proposals = await self.environment.analyze({
            "system_load": 0.7,
            "recent_tool_failures": 0,
        })

        all_proposals = curiosity_proposals + weakness_proposals + env_proposals
        if not all_proposals:
            return

        scored = await self._score(all_proposals)
        await self._publish(scored)

    async def _score(self, proposals: List[GoalProposal]) -> List[GoalScore]:
        scores = []
        for i, p in enumerate(proposals):
            score = GoalScore(
                proposal_id=p.proposal_id,
                score=p.priority,
                priority_rank=i + 1,
                reasoning=f"Auto-scored for {p.goal_type}",
                factors={"priority": p.priority},
            )
            scores.append(score)
        scores.sort(key=lambda s: s.score, reverse=True)
        for i, s in enumerate(scores):
            s.priority_rank = i + 1
        return scores

    async def _publish(self, scores: List[GoalScore]) -> None:
        for score in scores:
            await self.bus.publish("goal.proposed", Event(
                type="goal.proposed",
                source="autonomy",
                data={"score": score.dict()},
            ))