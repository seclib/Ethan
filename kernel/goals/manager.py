"""Goal Manager — Create, track, and complete cognitive goals."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from kernel.bus.interface import EventBus
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class GoalStep:
    """Single step in a goal's cognitive chain."""
    module: str
    status: str = "pending"  # pending | running | completed | failed | skipped
    result: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    retry_count: int = 0


@dataclass
class Goal:
    """A cognitive goal — from user intent to completion."""
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    intent: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    chain: List[GoalStep] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    trace_id: str = ""
    session_id: str = ""


class GoalManager:
    """Manages goal lifecycle: create → track → complete."""

    def __init__(
        self,
        event_bus: EventBus,
        pg: PostgresPersistentState,
        redis: RedisLiveState,
    ):
        self.bus = event_bus
        self.pg = pg
        self.redis = redis

    async def create(
        self, user_id: str, intent: Dict[str, Any],
        session_id: str = "", trace_id: str = "",
    ) -> Goal:
        """Create a new goal and persist it."""
        goal = Goal(
            user_id=user_id,
            intent=intent,
            chain=[
                GoalStep(module="reasoning"),
                GoalStep(module="planning"),
                GoalStep(module="execution"),
                GoalStep(module="memory"),
                GoalStep(module="reflection"),
            ],
            session_id=session_id,
            trace_id=trace_id,
        )

        # Persist to PostgreSQL
        row = await self.pg.create_goal(user_id, intent)
        goal.id = row["id"]

        # Cache in Redis (72h TTL)
        await self.redis.set_goal(goal.id, {
            "status": goal.status,
            "user_id": goal.user_id,
            "chain": [s.__dict__ for s in goal.chain],
        })

        # Emit goal.created event
        await self.bus.publish(EventType.GOAL_CREATED, Event(
            type=EventType.GOAL_CREATED,
            source="goal-manager",
            data={"goal_id": goal.id, "user_id": user_id, "intent": intent},
            metadata={"trace_id": trace_id, "session_id": session_id},
        ))

        logger.info(f"Goal created: {goal.id} for user {user_id}")
        return goal

    async def update_step(
        self, goal_id: str, module: str,
        status: str, result: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Update a step in the goal chain."""
        step = GoalStep(
            module=module,
            status=status,
            result=result,
            duration_ms=duration_ms,
        )

        # Update in PostgreSQL
        await self.pg.insert("goal_steps", {
            "goal_id": goal_id,
            "module": module,
            "status": status,
            "result": result,
            "duration_ms": duration_ms,
        })

        # Update cache in Redis
        goal_data = await self.redis.get_goal(goal_id)
        if goal_data:
            goal_data["chain"].append(step.__dict__)
            await self.redis.set_goal(goal_id, goal_data)

        logger.info(f"Goal {goal_id}: step {module} → {status}")

    async def complete(
        self, goal_id: str, result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mark goal as completed."""
        await self.pg.update_goal_status(goal_id, "completed")

        await self.bus.publish(EventType.GOAL_COMPLETED, Event(
            type=EventType.GOAL_COMPLETED,
            source="goal-manager",
            data={"goal_id": goal_id, "result": result or {}},
        ))

        logger.info(f"Goal completed: {goal_id}")

    async def fail(self, goal_id: str, error: str) -> None:
        """Mark goal as failed."""
        await self.pg.update_goal_status(goal_id, "failed")

        await self.bus.publish(EventType.GOAL_FAILED, Event(
            type=EventType.GOAL_FAILED,
            source="goal-manager",
            data={"goal_id": goal_id, "error": error},
        ))

        logger.warning(f"Goal failed: {goal_id}: {error}")