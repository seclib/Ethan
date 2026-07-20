"""Goal types — Contrat pour les objectifs du système."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class GoalState(str, Enum):
    """États possibles d'un goal."""
    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class GoalPriority(str, Enum):
    """Niveaux de priorité d'un goal."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Goal:
    """Objectif système.

    Un goal est la représentation d'une intention à réaliser.
    Il est créé par l'Executive, décomposé par le Planner,
    et suivi par le Goal Manager.
    """
    id: str = ""
    title: str = ""
    description: str = ""
    state: GoalState = GoalState.PENDING
    priority: GoalPriority = GoalPriority.MEDIUM
    source: str = ""  # Interface ou module qui a créé le goal
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    parent_id: str | None = None  # Pour les sous-goals
    metadata: dict[str, Any] = field(default_factory=dict)