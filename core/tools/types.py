"""Tool Types — Types de données pour le Tool Manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    """Niveaux de risque d'un outil."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Tool:
    """Outil avec toutes ses métadonnées."""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "generic"
    capabilities: list[str] = field(default_factory=list)
    cost_per_call: float = 0.0
    avg_duration_ms: float = 1000.0
    timeout_seconds: int = 30
    accuracy: float = 0.9
    success_rate: float = 0.95
    risk_level: RiskLevel = RiskLevel.LOW
    required_permissions: list[str] = field(default_factory=list)
    sandbox_required: bool = False
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    is_available: bool = True
    total_calls: int = 0
    success_count: int = 0
    tags: list[str] = field(default_factory=list)
    provider: str = "builtin"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ToolContext:
    """Contexte de sélection d'outil."""
    query: str
    source: str = "llm"
    user_id: str = "default"
    session_id: str = "default"
    trust_level: str = "low"
    max_cost: float | None = None
    max_duration_ms: float | None = None
    required_capabilities: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredTool:
    """Outil avec son score."""
    tool: Tool
    score: float
    reasoning: str = ""


@dataclass
class ToolResult:
    """Résultat d'exécution."""
    status: str  # "success", "failed", "timeout", "rejected"
    output: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)