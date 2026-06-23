"""Meta-Cognition schemas — CognitiveMode, Strategy, ThoughtTrace, Priority."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


# ── Cognitive Modes ─────────────────────────────────────

FAST_EXECUTION_MODE = "fast"
DEEP_REASONING_MODE = "deep"
EXPLORATION_MODE = "exploration"
DEBUG_MODE = "debug"
SAFE_MODE = "safe"

COGNITIVE_MODES = [
    FAST_EXECUTION_MODE,
    DEEP_REASONING_MODE,
    EXPLORATION_MODE,
    DEBUG_MODE,
    SAFE_MODE,
]


# ── Schemas ─────────────────────────────────────────────

@dataclass
class CognitiveMode:
    """Current thinking mode configuration."""
    mode: str = FAST_EXECUTION_MODE
    depth: int = 3  # 1-5
    speed_priority: bool = True
    thoroughness: float = 0.5  # 0.0-1.0
    safety_level: str = "normal"  # minimal | normal | strict
    reasoning: str = ""
    changed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "depth": self.depth,
            "speed_priority": self.speed_priority,
            "thoroughness": self.thoroughness,
            "safety_level": self.safety_level,
            "reasoning": self.reasoning,
            "changed_at": self.changed_at,
        }


@dataclass
class DecisionStrategy:
    """Strategy selection result."""
    strategy_id: str = field(default_factory=lambda: str(uuid4()))
    mode: str = FAST_EXECUTION_MODE
    depth: int = 3
    reasoning: str = ""
    confidence: float = 0.0
    selected_modules: List[str] = field(default_factory=list)
    estimated_duration_ms: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "mode": self.mode,
            "depth": self.depth,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "selected_modules": self.selected_modules,
            "estimated_duration_ms": self.estimated_duration_ms,
            "created_at": self.created_at,
        }


@dataclass
class ThoughtTrace:
    """Reasoning chain trace."""
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    task_id: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    total_duration_ms: float = 0.0
    loops_detected: int = 0
    inefficiencies: List[str] = field(default_factory=list)
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "steps": self.steps,
            "total_duration_ms": self.total_duration_ms,
            "loops_detected": self.loops_detected,
            "inefficiencies": self.inefficiencies,
            "completed": self.completed,
            "created_at": self.created_at,
        }


@dataclass
class ModulePriority:
    """Module ranking for a specific task."""
    task_type: str = ""
    rankings: List[Dict[str, Any]] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "rankings": self.rankings,
            "updated_at": self.updated_at,
        }