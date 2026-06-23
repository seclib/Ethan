"""Cognitive Kernel — Production-grade event orchestrator."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.goals.manager import GoalManager
from kernel.registry.module_registry import ModuleRegistry, ModuleManifest
from kernel.scheduler.scheduler import Scheduler
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event, EventType

logger = logging.getLogger(__name__)


class CognitiveKernel:
    """Event orchestrator — no business logic, only routing.

    Lifecycle:
        start() → running → stop()

    Core responsibilities:
        - subscribe wildcard events
        - dispatch to registry modules
        - sync state (Redis + PostgreSQL)
        - forward goal events to GoalManager
    """

    def __init__(
        self,
        bus: EventBus,
        redis: RedisLiveState,
        pg: PostgresPersistentState,
        registry: ModuleRegistry,
        goals: GoalManager,
        scheduler: Scheduler,
    ):
        self.bus = bus
        self.redis = redis
        self.pg = pg
        self.registry = registry
        self.goals = goals
        self.scheduler = scheduler
        self._running = False

    async def start(self) -> None:
        """Boot kernel: connect bus, register modules, subscribe events."""
        if self._running:
            logger.warning("Kernel already running")
            return

        self._running = True
        logger.info("Cognitive Kernel starting")

        await self.bus.subscribe("kernel.>", self._on_system_event, queue="kernel-system")
        logger.info("Subscribed to kernel.>")

        await self.bus.subscribe("goal.>", self._on_goal_event, queue="kernel-goals")
        logger.info("Subscribed to goal.>")

        await self.bus.subscribe("module.>", self._on_module_event, queue="kernel-dispatch")
        logger.info("Subscribed to module.>")

        await self.bus.subscribe("intent.>", self._on_intent_event, queue="kernel-intents")
        logger.info("Subscribed to intent.>")

        await self._register_builtin_modules()
        await self.scheduler.start()

        await self.bus.publish("system.kernel.started", Event(
            type=EventType.SYSTEM_KERNEL_STARTED,
            source="kernel",
            data={"version": "0.3.0"},
        ))
        logger.info("Cognitive Kernel started")

    async def stop(self) -> None:
        """Graceful shutdown."""
        if not self._running:
            return

        self._running = False
        logger.info("Cognitive Kernel stopping")

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
        """Register module in registry and PostgreSQL."""
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
        """Dispatch event to matching modules via registry."""
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
        """Public entry — route through dispatch."""
        await self.dispatch_event(event)

    async def _register_builtin_modules(self) -> None:
        """Register built-in modules idempotently."""
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
        """Handle system events."""
        logger.debug("System event: %s", event.type)

    async def _on_goal_event(self, event: Event) -> None:
        """Forward goal lifecycle events to GoalManager."""
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
        """Handle module responses."""
        logger.debug("Module event: %s from %s", event.type, event.source)

    async def _on_intent_event(self, event: Event) -> None:
        """Handle intent events — create goal and dispatch."""
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
        """Sync event to Redis + PostgreSQL."""
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