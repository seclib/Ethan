"""Skill Types — Types de données pour le Skills System."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SkillStatus(str, Enum):
    """Statut d'une skill."""
    AVAILABLE = "available"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SkillStep:
    """Étape d'une skill."""
    id: str
    name: str
    description: str
    tool_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    optional: bool = False
    retry_policy: dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    """Skill avec toutes ses métadonnées."""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    steps: list[SkillStep] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    estimated_duration_ms: int = 60000
    risk_level: str = "low"
    author: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_builtin: bool = False
    is_enabled: bool = True
    success_count: int = 0
    total_executions: int = 0


@dataclass
class SkillContext:
    """Contexte d'exécution d'une skill."""
    skill_id: str
    user_id: str = "default"
    session_id: str = "default"
    parameters: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    max_cost: float | None = None
    max_duration_ms: float | None = None


@dataclass
class SkillResult:
    """Résultat d'exécution d'une skill."""
    skill_id: str
    status: SkillStatus
    output: Any = None
    error: str | None = None
    steps_completed: int = 0
    steps_total: int = 0
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)