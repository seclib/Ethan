"""Cognitive Kernel — Event orchestrator for Ethan Cognitive OS."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.goals.manager import GoalManager, Goal
from kernel.registry.module_registry import ModuleRegistry
from kernel.scheduler.scheduler import Scheduler
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event, EventType

logger = logging.getLogger(__name__)


class CognitiveKernel:
    """Orchestrates cognitive modules via NATS.
    
    Does NOT contain cognitive logic — only routes events between modules.
    Phase 0.3 chain: intent.user → task.created → task.plan → memory → task.completed → reflection
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

    async def start(self) -> None:
        """Boot sequence: subscribe to pipeline topics."""
        logger.info("═══ Cognitive Kernel starting ═══")

        subscriptions = [
            EventType.INTENT_USER,
            EventType.TASK_PLANNED,
            EventType.TASK_COMPLETED,
        ]

        for topic in subscriptions:
            await self.bus.subscribe(topic, self._handle, queue="kernel-pipeline")
            logger.info(f"Subscribed to {topic}")

        # Discover modules and register known modules
        await self._register_builtin_modules()

        # Start scheduler
        await self.scheduler.start()

        # Emit startup
        await self.bus.publish(EventType.SYSTEM_KERNEL_STARTED, Event(
            type=EventType.SYSTEM_KERNEL_STARTED,
            source="kernel",
            data={"version": "0.3.0", "phase": "0.3"},
        ))
        logger.info("═══ Cognitive Kernel started ═══")

    async def _register_builtin_modules(self) -> None:
        """Register known built-in modules in PostgreSQL (idempotent)."""
        modules = [
            {"id": "executive-v1", "name": "Executive Module", "version": "1.0.0",
             "capabilities": ["module.executive"], "topics_subscribed": ["ethan.intent.user"], "topics_published": ["ethan.task.created"]},
            {"id": "planner-v1", "name": "Planner Module", "version": "1.0.0",
             "capabilities": ["module.planner"], "topics_subscribed": ["ethan.task.created"], "topics_published": ["ethan.task.plan"]},
            {"id": "memory-v1", "name": "Memory Module", "version": "1.0.0",
             "capabilities": ["module.memory"], "topics_subscribed": ["ethan.task.created", "ethan.task.plan", "ethan.task.completed"], "topics_published": ["ethan.memory.stored"]},
            {"id": "reflective-v1", "name": "Reflective Module", "version": "1.0.0",
             "capabilities": ["module.reflective"], "topics_subscribed": ["ethan.task.completed"], "topics_published": ["ethan.reflection.done"]},
        ]
        for m in modules:
            try:
                await self.pg.insert("modules", dict(status="active", **m))
                logger.info(f"Registered module: {m['id']}")
            except Exception:
                # Already exists — safe to ignore
                pass

    async def _handle(self, event: Event) -> None:
        """Handle incoming event and continue pipeline."""
        if event.type == EventType.INTENT_USER:
            # Bridge to module-native topic
            await self.bus.publish("ethan.intent.user", event)
            # Mark goal step executive if goal_id present
            goal_id = event.data.get("goal_id")
            if goal_id:
                await self.goals.update_step(goal_id, "executive", "running")

        elif event.type in (EventType.TASK_PLANNED, EventType.TASK_COMPLETED, EventType.MEMORY_STORED):
            # Propagate down the chain — listener modules will react
            # Also emit to user response channel
            response = Event(
                type=EventType.INTENT_RESPONSE,
                source="kernel",
                data={"last_event": event.type, "payload": event.data},
                metadata={"trace_id": event.metadata.get("trace_id", "")},
            )
            await self.bus.publish("ethan.intent.response", response)

        logger.info(f"Kernel handled: {event.type}")

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down Cognitive Kernel...")
        await self.bus.publish(EventType.SYSTEM_KERNEL_SHUTDOWN, Event(
            type=EventType.SYSTEM_KERNEL_SHUTDOWN,
            source="kernel",
        ))
        await self.scheduler.stop()
        await self.bus.close()
        await self.redis.close()
        await self.pg.close()
        logger.info("Cognitive Kernel shut down")