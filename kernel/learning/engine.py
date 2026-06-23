"""Learning Engine — Async event consumer and orchestrator."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.learning.detector import PatternDetector
from kernel.learning.generator import RuleGenerator
from kernel.learning.modeler import SelfModelUpdater
from kernel.learning.store import ExperienceStore
from sdk.event import Event, EventType
from sdk.learning import Experience, Pattern

logger = logging.getLogger(__name__)


class LearningEngine:
    """Closed-loop learning system — observes, detects, proposes, updates."""

    LEARNING_EVENTS = {
        EventType.TASK_COMPLETED,
        EventType.TASK_FAILED,
        EventType.TASK_PLANNED,
        EventType.MEMORY_STORED,
        EventType.REFLECTION_DONE,
    }

    def __init__(
        self,
        bus: EventBus,
        store: ExperienceStore,
        detector: PatternDetector,
        generator: RuleGenerator,
        modeler: SelfModelUpdater,
    ):
        self.bus = bus
        self.store = store
        self.detector = detector
        self.generator = generator
        self.modeler = modeler
        self._running = False

    async def start(self) -> None:
        """Subscribe to relevant system events."""
        if self._running:
            return
        self._running = True
        await self.bus.subscribe("task.>", self._on_task_event, queue="learning-tasks")
        await self.bus.subscribe("memory.>", self._on_memory_event, queue="learning-memory")
        await self.bus.subscribe("reflection.>", self._on_reflection_event, queue="learning-reflection")
        logger.info("Learning Engine started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Learning Engine stopped")

    async def _on_task_event(self, event: Event) -> None:
        """Consume task events and extract experience."""
        if not self._running:
            return
        try:
            experience = self._extract(event)
            await self.store.save(experience)
            await self.modeler.update_skill(experience.skill_invoked, experience.outcome)
            await self._analyze()
        except Exception as e:
            logger.error(f"Learning task handler failed: {e}")

    async def _on_memory_event(self, event: Event) -> None:
        """Track memory events for pattern analysis."""
        if not self._running:
            return
        try:
            experience = self._extract(event)
            experience.outcome = "success"
            await self.store.save(experience)
        except Exception as e:
            logger.error(f"Learning memory handler failed: {e}")

    async def _on_reflection_event(self, event: Event) -> None:
        """Consume reflection outcomes."""
        if not self._running:
            return
        try:
            experience = self._extract(event)
            experience.outcome = "success"
            await self.store.save(experience)
            await self.modeler.update_skill(experience.skill_invoked, "success")
        except Exception as e:
            logger.error(f"Learning reflection handler failed: {e}")

    async def _analyze(self) -> None:
        """Run pattern detection and rule generation."""
        try:
            experiences = await self.store.get_recent(limit=1000)
            if not experiences:
                return

            patterns = await self.detector.detect(experiences)

            for pattern in patterns:
                rule = await self.generator.propose(pattern)

                await self.bus.publish(EventType.RULE_PROPOSAL, Event(
                    type=EventType.RULE_PROPOSAL,
                    source="learning-engine",
                    data=rule.dict(),
                ))

                await self.bus.publish(EventType.LEARNING_INSIGHT, Event(
                    type=EventType.LEARNING_INSIGHT,
                    source="learning-engine",
                    data={
                        "pattern": pattern.dict(),
                        "rule": rule.dict(),
                    },
                ))

            self_model = await self.modeler.get_model()
            await self.bus.publish(EventType.SELF_MODEL_UPDATED, Event(
                type=EventType.SELF_MODEL_UPDATED,
                source="learning-engine",
                data={"self_model": self_model},
            ))

        except Exception as e:
            logger.error(f"Learning analysis failed: {e}")

    def _extract(self, event: Event) -> Experience:
        """Extract structured experience from event."""
        data = event.data or {}
        experience = Experience(
            event_type=event.type,
            event_id=event.id,
            user_id=event.metadata.get("user_id", "anonymous") if event.metadata else "anonymous",
            goal_id=data.get("goal_id", ""),
            outcome=self._infer_outcome(event.type),
            duration_ms=data.get("duration_ms", 0.0),
            module_used=event.source,
            skill_invoked=data.get("type", "general"),
            context=data.get("intent", data.get("task", data.get("plan", {}))),
            metadata=event.metadata or {},
        )
        return experience

    def _infer_outcome(self, event_type: str) -> str:
        """Infer success/failure from event type."""
        if "failed" in event_type or "error" in event_type:
            return "failure"
        if "completed" in event_type or "success" in event_type:
            return "success"
        return "unknown"