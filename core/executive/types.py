"""Executive Types — Types de données pour le module Executive."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class GoalState(str, Enum):
    """États d'un goal."""
    PENDING = "pending"
    PLANNING = "planning"
    PLANNED = "planned"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GoalPriority(str, Enum):
    """Niveaux de priorité."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


@dataclass
class Goal:
    """Objectif à accomplir."""
    id: str
    description: str
    priority: GoalPriority = GoalPriority.MEDIUM
    state: GoalState = GoalState.PENDING
    required_capabilities: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    deadline: datetime | None = None
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class GoalProgress:
    """Progrès d'un goal."""
    goal_id: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    current_task: str | None = None
    progress_percent: float = 0.0
    estimated_completion: datetime | None = None