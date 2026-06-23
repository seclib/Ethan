"""Meta-Cognition Engine — Controls how ETHAN thinks."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.metacognition.load import CognitiveLoadManager
from kernel.metacognition.prioritizer import ModulePrioritizer
from kernel.metacognition.strategy import DecisionStrategySelector
from kernel.metacognition.trace import ThoughtTraceAnalyzer
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event
from sdk.metacognition import CognitiveMode, DecisionStrategy, ModulePriority, ThoughtTrace
from sdk.learning import SelfModel

logger = logging.getLogger(__name__)


class MetaCognitionEngine:
    """Closed-loop meta-cognitive controller."""

    INPUT_TOPICS = [
        "task.>",
        "failure.>",
        "tool.>",
        "learning.>",
    ]

    def __init__(
        self,
        bus: EventBus,
        redis: RedisLiveState,
        strategy: DecisionStrategySelector,
        load_manager: CognitiveLoadManager,
        prioritizer: ModulePrioritizer,
        trace_analyzer: ThoughtTraceAnalyzer,
    ):
        self.bus = bus
        self.redis = redis
        self.strategy = strategy
        self.load_manager = load_manager
        self.prioritizer = prioritizer
        self.trace_analyzer = trace_analyzer
        self._running = False
        self.current_mode = CognitiveMode()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True

        for topic in self.INPUT_TOPICS:
            await self.bus.subscribe(topic, self._on_event, queue="metacognition")
        logger.info("Meta-Cognition Engine started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Meta-Cognition Engine stopped")

    async def _on_event(self, event: Event) -> None:
        if not self._running:
            return
        try:
            await self._process(event)
        except Exception as e:
            logger.error(f"Meta-cognition handler failed: {e}")

    async def _process(self, event: Event) -> None:
        data = event.data or {}
        task_type = data.get("type", "general")

        # Load self-model from Redis
        model_data = await self.redis.get("system:self_model")
        self_model = SelfModel()
        if model_data:
            self_model = SelfModel(
                skills=model_data.get("skills", {}),
                reliability=model_data.get("reliability", 0.0),
                error_rate=model_data.get("error_rate", 0.0),
            )

        # Assess load
        load = await self.load_manager.assess()
        depth = await self.load_manager.adjust_depth(load)

        # Select strategy
        strategy = await self.strategy.select(task_type, data, self_model)
        strategy.depth = depth

        # Update priorities
        modules = [{"id": "module-executive", "capabilities": ["handle.intent"]}]
        priority = await self.prioritizer.rank(modules, task_type, self_model, strategy.mode)

        # Publish outputs using string literals to avoid Pylance issues
        await self.bus.publish("meta.strategy_selected", Event(
            type="meta.strategy_selected",
            source="metacognition",
            data={"strategy": strategy.dict(), "task_type": task_type},
            metadata=event.metadata or {},
        ))

        mode_changed = strategy.mode != self.current_mode.mode
        if mode_changed:
            self.current_mode = CognitiveMode(
                mode=strategy.mode,
                depth=depth,
                reasoning=strategy.reasoning,
            )
            await self.bus.publish("meta.mode_changed", Event(
                type="meta.mode_changed",
                source="metacognition",
                data={"mode": self.current_mode.dict()},
                metadata=event.metadata or {},
            ))

        await self.bus.publish("meta.priority_updated", Event(
            type="meta.priority_updated",
            source="metacognition",
            data={"priority": priority.dict()},
            metadata=event.metadata or {},
        ))

        await self.bus.publish("meta.depth_adjusted", Event(
            type="meta.depth_adjusted",
            source="metacognition",
            data={"depth": depth, "load": load},
            metadata=event.metadata or {},
        ))