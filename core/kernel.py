"""Cognitive Kernel — Production-grade event orchestrator."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from core.autonomy.controller import AutonomyLoopController
from core.bus.interface import EventBus, Subscription
from core.goals.manager import GoalManager
from core.learning.engine import LearningEngine
from core.metacognition.engine import MetaCognitionEngine
from core.registry.module import ModuleRegistry
from core.scheduler.scheduler import Scheduler
from core.state.interface import StateBackend
from core.ethan_types.event import Event, EventType

logger = logging.getLogger(__name__)


class CognitiveKernel:
    """Event orchestrator — no business logic, only routing."""

    def __init__(
        self,
        bus: EventBus,
        state: StateBackend,  # Unified state backend (RedisLiveState + PostgresPersistentState wrapper)
        registry: ModuleRegistry,
        goals: GoalManager,
        scheduler: Scheduler,
        learning: Optional[LearningEngine] = None,
        metacognition: Optional[MetaCognitionEngine] = None,
        autonomy: Optional[AutonomyLoopController] = None,
    ):
        self.bus = bus
        self.state = state
        self.registry = registry
        self.goals = goals
        self.scheduler = scheduler
        self.learning = learning
        self.metacognition = metacognition
        self.autonomy = autonomy
        self._running = False
        self._subscriptions: list[Subscription] = []
        self._started_components: set[str] = set()
        self._builtin_module_ids: set[str] = set()

    async def start(self) -> None:
        if self._running:
            logger.warning("Kernel already running")
            return

        self._running = True
        self._started_components.clear()
        self._subscriptions.clear()
        logger.info("Cognitive Kernel starting")

        try:
            for pattern, handler, queue in (
                ("kernel.>", self._on_system_event, "kernel-system"),
                ("goal.>", self._on_goal_event, "kernel-goals"),
                ("module.>", self._on_module_event, "kernel-dispatch"),
                ("intent.>", self._on_intent_event, "kernel-intents"),
            ):
                subscription = await asyncio.wait_for(
                    self.bus.subscribe(pattern, handler, queue=queue), timeout=10
                )
                if subscription is not None:
                    self._subscriptions.append(subscription)

            await self._register_builtin_modules()
            self._started_components.add("scheduler")
            await asyncio.wait_for(self.scheduler.start(), timeout=10)

            if self.learning:
                self._started_components.add("learning")
                await asyncio.wait_for(self.learning.start(), timeout=10)
                logger.info("Learning Engine started")

            if self.metacognition:
                self._started_components.add("metacognition")
                await asyncio.wait_for(self.metacognition.start(), timeout=10)
                logger.info("Meta-Cognition Engine started")

            if self.autonomy:
                self._started_components.add("autonomy")
                await asyncio.wait_for(self.autonomy.start(), timeout=10)
                logger.info("Autonomy Engine started")

            await asyncio.wait_for(
                self.bus.publish("system.kernel.started", Event(
                    type=EventType.SYSTEM_BOOT,
                    source="kernel",
                    payload={"version": "0.7.0", "phase": "7.0"},
                )),
                timeout=10,
            )
            logger.info("Cognitive Kernel started")
        except BaseException:
            await self._rollback_startup()
            raise

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        logger.info("Cognitive Kernel stopping")
        first_error: BaseException | None = None

        async def shutdown_step(name: str, operation, timeout: float = 10) -> None:
            nonlocal first_error
            try:
                await asyncio.wait_for(operation(), timeout=timeout)
            except BaseException as exc:
                if first_error is None:
                    first_error = exc
                logger.error("Kernel shutdown step failed: %s", name, exc_info=True)

        await shutdown_step("learning", self.learning.stop if self.learning and "learning" in self._started_components else _noop)
        await shutdown_step("metacognition", self.metacognition.stop if self.metacognition and "metacognition" in self._started_components else _noop)
        await shutdown_step("autonomy", self.autonomy.stop if self.autonomy and "autonomy" in self._started_components else _noop)
        await shutdown_step(
            "kernel stopping event",
            lambda: self.bus.publish("system.kernel.stopping", Event(
                type=EventType.SYSTEM_SHUTDOWN,
                source="kernel",
            )),
        )
        await shutdown_step("scheduler", self.scheduler.stop if "scheduler" in self._started_components else _noop)
        for subscription in reversed(self._subscriptions):
            await shutdown_step("subscription", subscription.unsubscribe, timeout=5)
        await shutdown_step("bus", self.bus.close)
        await shutdown_step("state", self.state.close)
        for module_id in reversed(tuple(self._builtin_module_ids)):
            try:
                self.registry.unregister(module_id)
            except Exception:
                logger.exception("Failed to unregister builtin module: %s", module_id)
        self._builtin_module_ids.clear()
        self._subscriptions.clear()
        self._started_components.clear()
        logger.info("Cognitive Kernel stopped")
        if first_error is not None:
            raise first_error

    async def _rollback_startup(self) -> None:
        """Best-effort cleanup after a failed startup, preserving the cause."""
        try:
            await self.stop()
        except Exception:
            logger.exception("Kernel rollback cleanup failed")

    async def register_module(self, module_id: str, capabilities: list[str]) -> None:
        from core.modules.base import Module, ModuleContext

        class _SimpleModule(Module):
            def __init__(self, name: str = module_id):
                super().__init__(name)
            
            async def initialize(self, context: ModuleContext) -> None:
                logger.info("Module %s initialized with caps=%s", module_id, capabilities)
            async def handle_event(self, event: Event) -> None:
                logger.debug("Module %s received event: %s", module_id, event.type)
            async def shutdown(self) -> None:
                pass

        module = _SimpleModule()
        self.registry.register(module)
        logger.info("Module registered: %s capabilities=%s", module_id, capabilities)

    async def dispatch_event(self, event: Event) -> None:
        if not self._running:
            logger.warning("Kernel not running, cannot dispatch")
            return

        start = time.monotonic()
        try:
            capability = f"handle.{event.type.value.split('.')[-1]}"
            modules = self.registry.get_by_capability(capability)

            if not modules:
                logger.debug("No module for capability=%s event=%s", capability, event.id)
                return

            targets = [m.name for m in modules]
            logger.info("Dispatching %s to %s", event.type, targets)
            await self.bus.publish(f"module.dispatch.{event.type.value}", event)
            await self._sync_state(event)

            duration = (time.monotonic() - start) * 1000
            logger.info("Dispatched %s in %.1fms", event.type, duration)
        except Exception as e:
            logger.error("Dispatch failed for %s: %s", event.id, e, exc_info=True)
            await self.bus.publish("system.error", Event(
                type=EventType.SYSTEM_ERROR,
                source="kernel",
                payload={"event_id": event.id, "error": str(e)},
            ))

    async def handle_event(self, event: Event) -> None:
        await self.dispatch_event(event)

    async def _register_builtin_modules(self) -> None:
        # These registry entries are lightweight kernel routing contracts. The
        # executable cognitive implementations are loaded by the dedicated
        # ``core.modules`` service (see core/modules/__main__.py); registering
        # them here must not be mistaken for constructing a second NATS client.
        builtins = [
            ("module-executive", ["handle.intent"]),
            ("module-planner", ["handle.task"]),
            ("module-memory", ["store.event"]),
            ("module-reflective", ["handle.completion"]),
        ]
        for module_id, caps in builtins:
            try:
                await asyncio.wait_for(self.register_module(module_id, caps), timeout=5)
                self._builtin_module_ids.add(module_id)
            except asyncio.TimeoutError as exc:
                logger.error("Builtin module %s registration timed out", module_id)
                raise RuntimeError(f"Module {module_id} registration timed out") from exc
            except Exception as exc:
                logger.error("Builtin module %s registration failed: %s", module_id, exc)
                raise RuntimeError(f"Module {module_id} registration failed: {exc}") from exc

    async def _on_system_event(self, event: Event) -> None:
        logger.debug("System event: %s", event.type)

    async def _on_goal_event(self, event: Event) -> None:
        try:
            goal_id = event.payload.get("goal_id")
            type_str = event.type.value
            if "goal.created" in type_str:
                await self.goals.create(
                    user_id=event.metadata.get("user_id", "anonymous"),
                    intent=event.payload.get("intent", {}),
                    session_id=event.metadata.get("session_id", ""),
                    trace_id=event.metadata.get("trace_id", ""),
                )
            elif "goal.completed" in type_str and goal_id:
                await self.goals.complete(goal_id)
            elif "goal.failed" in type_str and goal_id:
                await self.goals.fail(goal_id, event.payload.get("error", ""))
        except Exception as e:
            logger.error("Goal handling failed: %s", e)

    async def _on_module_event(self, event: Event) -> None:
        logger.debug("Module event: %s from %s", event.type, event.source)

    async def _on_intent_event(self, event: Event) -> None:
        try:
            goal = await self.goals.create(
                user_id=event.metadata.get("user_id", "anonymous"),
                intent=event.payload.get("intent", {}),
                session_id=event.metadata.get("session_id", ""),
                trace_id=event.metadata.get("trace_id", ""),
            )
            event.payload["goal_id"] = goal.id
            await self.dispatch_event(event)
        except Exception as e:
            logger.error("Intent handling failed: %s", e, exc_info=True)

    async def _sync_state(self, event: Event) -> None:
        try:
            payload = {
                "id": event.id,
                "type": event.type.value,
                "source": event.source,
                "timestamp": event.timestamp.isoformat(),
                "payload": event.payload,
                "metadata": event.metadata,
            }
            await self.state.sync_event(event.id, payload)
        except Exception as e:
            logger.warning("State sync failed: %s", e)


async def _noop() -> None:
    """No-op used to keep shutdown cleanup uniform."""
