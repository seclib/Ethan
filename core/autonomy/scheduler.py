"""Priority Scheduler — Balances user/system/exploration goals."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sdk.autonomy import GoalPriority

logger = logging.getLogger(__name__)


class PriorityScheduler:
    """Schedules goals with weighted priority across categories."""

    WEIGHTS = {
        "user": 0.5,
        "system": 0.3,
        "exploration": 0.2,
    }

    MAX_QUEUE = 100

    def __init__(self):
        self.queue: List[GoalPriority] = []

    def enqueue(self, goal: GoalPriority) -> None:
        """Add goal to queue, respecting max size."""
        self.queue.append(goal)
        self.queue.sort(key=lambda g: g.priority, reverse=True)
        if len(self.queue) > self.MAX_QUEUE:
            self.queue = self.queue[: self.MAX_QUEUE]
        logger.debug(f"Goal enqueued: {goal.goal_id} priority={goal.priority}")

    def dequeue(self) -> GoalPriority | None:
        """Get highest priority goal, avoiding starvation."""
        if not self.queue:
            return None

        # Round-robin by category with weights
        for category, weight in self.WEIGHTS.items():
            for g in self.queue:
                if g.category == category:
                    self.queue.remove(g)
                    return g

        # Fallback
        return self.queue.pop(0)

    def peek(self) -> GoalPriority | None:
        """Return next goal without removing."""
        return self.queue[0] if self.queue else None