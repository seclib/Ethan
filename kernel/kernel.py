"""Cognitive Kernel — Production-grade event orchestrator."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from kernel.autonomy.engine import AutonomyEngine
from kernel.bus.interface import EventBus
from kernel.goals.manager import GoalManager
from kernel.learning.engine import LearningEngine
from kernel.metacognition.engine import MetaCognitionEngine
from kernel.registry.module_registry import ModuleRegistry, ModuleManifest
from kernel.scheduler.scheduler import Scheduler
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event, EventType

logger = logging.getLogger(__name__)


class CognitiveKernel:
    """Event orchestrator — no business logic, only routing."""

    def __init__(
        self,
        bus: EventBus,
        redis: RedisLiveState,
        pg: PostgresPersistentState,
        registry: ModuleRegistry,
        goals: GoalManager,
        scheduler: Scheduler,
        learning: Optional[LearningEngine] = None,
        metacognition: Optional[MetaCognitionEngine] = None,
        autonomy: Optional[AutonomyEngine] = None,
    ):
        self.bus = bus
        self.redis = redis
        self.pg = pg
        self.registry = registry
        self.goals = goals
        self.scheduler = scheduler
        self.learning = learning
        self.metacognition = metacognition
        self.autonomy = autonomy
        self._running = False

    async def start(self) -> None:
        if self._running:
            logger.warning("Kernel already running")
            return

        self._running = True
        logger.info("Cognitive Kernel starting")

        await self.bus.subscribe("kernel.>", self._on_system_event, queue="kernel-system")
        await self.bus.subscribe("goal.>", self._on_goal_event, queue="kernel-goals")
        await self.bus.subscribe("module.>", self._on_module_event, queue="kernel-dispatch")
        await self.bus.subscribe("intent.>", self._on_intent_event, queue="kernel-intents")
        await self._register_builtin_modules()
        await self.scheduler.start()

        if self.learning:
            await self.learning.start()
            logger.info("Learning Engine started")

        if self.metacognition:
            await self.metacognition.start()
            logger.info("Meta-Cognition Engine started")

        if self.autonomy:
            await self.autonomy.start()
            logger.info("Autonomy Engine started")

        await self.bus.publish("system.kernel.started", Event(
            type=EventType.SYSTEM_KERNEL_STARTED,
            source="kernel",
            data={"version": "0.6.0", "phase": "6.0"},
        ))
        logger.info("Cognitive Kernel started")

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        logger.info("Cognitive Kernel stopping")

        if self.learning:
            await self.learning.stop()

        if self.metacognition:
            await self.metacognition.stop()

        if self.autonomy:
            await self.autonomy.stop()

        await self.bus.publish("system.kernel.stopping", Event(
            type="system.kernel.stopping",
            source="kernel",
        ))
        await self.scheduler.stop()
        await self.bus.close()
        await self.redis.close()
        await self.pg.close()
        logger.info("Cognitive Kernel stopped")

    async def register_module(self, module_id: str, capabilities: List[str]) -> None:
        manifest = ModuleManifest(
            id=module_id,
            name=module_id,
            version="1.0.0",
            capabilities=capabilities,
            topics_subscribed=[],
            topics_published=[],
        )
        await self.registry.register(manifest)
        logger.info(f"Module registered: {module_id} capabilities={capabilities}")

    async def dispatch_event(self, event: Event) -> None:
        if not self._running:
            logger.warning("Kernel not running, cannot dispatch")
            return

        start = time.monotonic()
        try:
            capability = f"handle.{event.type.split('.')[-1]}"
            modules = self.registry.find_by_capability(capability)

            if not modules:
                logger.debug("No module for capability=%s event=%s", capability, event.id)
                return

            targets = [m.id for m in modules]
            logger.info("Dispatching %s to %s", event.type, targets)
            await self.bus.publish(f"module.dispatch.{event.type}", event)
            await self._sync_state(event)

            duration = (time.monotonic() - start) * 1000
            logger.info("Dispatched %s in %.1fms", event.type, duration)
        except Exception as e:
            logger.error("Dispatch failed for %s: %s", event.id, e, exc_info=True)
            await self.bus.publish("system.error", Event(
                type="system.error",
                source="kernel",
                data={"event_id": event.id, "error": str(e)},
            ))

    async def handle_event(self, event: Event) -> None:
        await self.dispatch_event(event)

    async def _register_builtin_modules(self) -> None:
        builtins = [
            ("module-executive", ["handle.intent"]),
            ("module-planner", ["handle.task"]),
            ("module-memory", ["store.event"]),
            ("module-reflective", ["handle.completion"]),
        ]
        for module_id, caps in builtins:
            try:
                await self.register_module(module_id, caps)
            except Exception:
                pass

    async def _on_system_event(self, event: Event) -> None:
        logger.debug("System event: %s", event.type)

    async def _on_goal_event(self, event: Event) -> None:
        try:
            event_type = event.type
            goal_id = event.data.get("goal_id")
            if event_type == "goal.created":
                await self.goals.create(
                    user_id=event.metadata.get("user_id", "anonymous"),
                    intent=event.data.get("intent", {}),
                    session_id=event.metadata.get("session_id", ""),
                    trace_id=event.metadata.get("trace_id", ""),
                )
            elif event_type == "goal.completed" and goal_id:
                await self.goals.complete(goal_id)
            elif event_type == "goal.failed" and goal_id:
                await self.goals.fail(goal_id, event.data.get("error", ""))
        except Exception as e:
            logger.error("Goal handling failed: %s", e)

    async def _on_module_event(self, event: Event) -> None:
        logger.debug("Module event: %s from %s", event.type, event.source)

    async def _on_intent_event(self, event: Event) -> None:
        try:
            goal = await self.goals.create(
                user_id=event.metadata.get("user_id", "anonymous"),
                intent=event.data.get("intent", {}),
                session_id=event.metadata.get("session_id", ""),
                trace_id=event.metadata.get("trace_id", ""),
            )
            event.data["goal_id"] = goal.id
            await self.dispatch_event(event)
        except Exception as e:
            logger.error("Intent handling failed: %s", e, exc_info=True)

    async def _sync_state(self, event: Event) -> None:
        try:
            payload = event.dict()
            await self.redis.set(f"event:{event.id}", payload, ttl=3600)
            await self.pg.insert("events", {
                "id": event.id,
                "type": event.type,
                "source": event.source,
                "timestamp": event.timestamp,
                "data": event.data,
                "metadata": event.metadata,
            })
        except Exception as e:
            logger.warning("State sync failed: %s", e)