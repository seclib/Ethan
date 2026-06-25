"""Autonomy Loop Controller — Orchestrates continuous cognitive cycles."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.state.redis_state import RedisLiveState
from sdk.autonomy import CycleState
from sdk.event import Event, EventType

logger = logging.getLogger(__name__)


class AutonomyLoopController:
    """Continuous autonomy loop: THINK → ACT → LEARN → REFLECT → REPLAN."""

    MAX_CYCLES_PER_MIN = 10
    CYCLE_TIMEOUT = 30  # seconds

    def __init__(self, bus: EventBus, redis: RedisLiveState):
        self.bus = bus
        self.redis = redis
        self.state = CycleState()
        self._running = False
        self._cycle_times: List[float] = []

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        await self.bus.subscribe("goal.>", self._on_goal_event, queue="autonomy-loop")
        await self.bus.subscribe("task.>", self._on_task_event, queue="autonomy-loop")
        await self.bus.subscribe("system.>", self._on_system_event, queue="autonomy-loop")
        await self.bus.subscribe("idle.>", self._on_idle_event, queue="autonomy-loop")
        logger.info("Autonomy Loop Controller started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Autonomy Loop Controller stopped")

    async def _on_goal_event(self, event: Event) -> None:
        if not self._running:
            return
        try:
            await self._run_cycle(event)
        except Exception as e:
            logger.error(f"Autonomy cycle failed: {e}")

    async def _on_task_event(self, event: Event) -> None:
        if not self._running:
            return
        try:
            await self._run_cycle(event)
        except Exception as e:
            logger.error(f"Autonomy cycle failed: {e}")

    async def _on_system_event(self, event: Event) -> None:
        if not self._running:
            return
        try:
            await self._run_cycle(event)
        except Exception as e:
            logger.error(f"Autonomy cycle failed: {e}")

    async def _on_idle_event(self, event: Event) -> None:
        if not self._running:
            return
        try:
            await self._run_cycle(event)
        except Exception as e:
            logger.error(f"Autonomy cycle failed: {e}")

    async def _run_cycle(self, trigger_event: Event) -> None:
        """Orchestrate one THINK → ACT → LEARN → REFLECT → REPLAN."""
        start = time.monotonic()

        # Rate limit
        if self._cycle_times:
            last = self._cycle_times[-1]
            if (start - last) < (60.0 / self.MAX_CYCLES_PER_MIN):
                logger.debug("Cycle rate limited")
                return

        self.state.state = "running"
        self.state.cycle_count += 1
        self.state.last_cycle_start = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()

        await self.bus.publish(EventType.AUTONOMY_CYCLE_STARTED, Event(
            type=EventType.AUTONOMY_CYCLE_STARTED,
            source="autonomy-loop",
            data={"cycle": self.state.cycle_count},
        ))

        try:
            asyncio.create_task(self._cycle_with_timeout(trigger_event))
        except asyncio.TimeoutError:
            logger.warning("Autonomy cycle timeout")
        finally:
            self.state.last_cycle_end = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
            self._cycle_times.append(start)
            if len(self._cycle_times) > 100:
                self._cycle_times.pop(0)
            self.state.state = "idle"

    async def _cycle_with_timeout(self, trigger_event: Event) -> None:
        """Execute cycle with timeout."""
        try:
            await asyncio.wait_for(self._execute_cycle(trigger_event), timeout=self.CYCLE_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Cycle execution timeout")

    async def _execute_cycle(self, trigger_event: Event) -> None:
        """THINK → ACT → LEARN → REFLECT → REPLAN."""
        # 1. THINK — sélectionner un goal
        goal_id = await self._select_goal(trigger_event)
        if not goal_id:
            logger.debug("No goal selected, cycle skipped")
            return

        self.state.current_goal = goal_id

        # 2. ACT — exécuter (via kernel dispatch)
        await self._execute_goal(goal_id)

        # 3. LEARN — laisser le LearningEngine traiter les résultats
        await self.bus.publish(EventType.TASK_EXECUTED, Event(
            type=EventType.TASK_EXECUTED,
            source="autonomy-loop",
            data={"goal_id": goal_id},
        ))

        # 4. REFLECT — attendre reflection
        # (géré par module-reflective)

        # 5. REPLAN — générer ou mettre à jour goals
        await self.bus.publish(EventType.NEW_GOAL_CREATED, Event(
            type=EventType.NEW_GOAL_CREATED,
            source="autonomy-loop",
            data={"cycle": self.state.cycle_count},
        ))

        await self.bus.publish(EventType.AUTONOMY_CYCLE_COMPLETED, Event(
            type=EventType.AUTONOMY_CYCLE_COMPLETED,
            source="autonomy-loop",
            data={"cycle": self.state.cycle_count, "goal_id": goal_id},
        ))

        logger.info(f"Autonomy cycle {self.state.cycle_count} completed")

    async def _select_goal(self, trigger_event: Event) -> Optional[str]:
        """Select next goal from goal.proposed events."""
        # In production: use priority queue, self-model, context
        # Simplified: return trigger goal if present
        data = trigger_event.data or {}
        return data.get("goal_id")

    async def _execute_goal(self, goal_id: str) -> None:
        """Request goal execution via Kernel."""
        await self.bus.publish("intent.user", Event(
            type="intent.user",
            source="autonomy-loop",
            data={"goal_id": goal_id, "autonomous": True},
        ))