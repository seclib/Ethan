"""Autonomy schemas — CycleState, Priority, HealthStatus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class CycleState:
    """Current autonomy loop state."""
    state: str = "idle"  # idle | running | paused | stopped
    cycle_count: int = 0
    last_cycle_start: str = ""
    last_cycle_end: str = ""
    current_goal: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "cycle_count": self.cycle_count,
            "last_cycle_start": self.last_cycle_start,
            "last_cycle_end": self.last_cycle_end,
            "current_goal": self.current_goal,
            "started_at": self.started_at,
        }


@dataclass
class GoalPriority:
    """Priority score for goal selection."""
    goal_id: str = ""
    priority: float = 0.0  # 0.0-1.0
    category: str = "user"  # user | system | exploration
    urgency: int = 0  # 1-5
    estimated_effort: str = "medium"
    reasoning: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "priority": self.priority,
            "category": self.category,
            "urgency": self.urgency,
            "estimated_effort": self.estimated_effort,
            "reasoning": self.reasoning,
            "updated_at": self.updated_at,
        }


@dataclass
class HealthStatus:
    """Module health snapshot."""
    module_id: str = ""
    healthy: bool = True
    consecutive_failures: int = 0
    last_success: str = ""
    last_failure: str = ""
    isolation_reason: str = ""
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "healthy": self.healthy,
            "consecutive_failures": self.consecutive_failures,
            "last_success": self.last_success,
            "last_failure": self.last_failure,
            "isolation_reason": self.isolation_reason,
            "checked_at": self.checked_at,
        }