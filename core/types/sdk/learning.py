"""Learning Engine schemas — Experience, Pattern, Rule, SelfModel."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class Experience:
    """Structured experience extracted from a system event."""
    experience_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str = ""
    event_id: str = ""
    user_id: str = "anonymous"
    goal_id: str = ""
    outcome: str = "unknown"  # success | failure | partial
    duration_ms: float = 0.0
    module_used: str = ""
    skill_invoked: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "goal_id": self.goal_id,
            "outcome": self.outcome,
            "duration_ms": self.duration_ms,
            "module_used": self.module_used,
            "skill_invoked": self.skill_invoked,
            "context": self.context,
            "metadata": self.metadata,
        }


@dataclass
class Pattern:
    """Detected pattern from multiple experiences."""
    pattern_id: str = field(default_factory=lambda: str(uuid4()))
    pattern_type: str = ""  # failure_repeat | success_repeat | inefficiency
    skill: str = ""
    frequency: int = 0
    avg_duration_ms: float = 0.0
    success_rate: float = 0.0
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

    def dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "skill": self.skill,
            "frequency": self.frequency,
            "avg_duration_ms": self.avg_duration_ms,
            "success_rate": self.success_rate,
            "detected_at": self.detected_at,
            "details": self.details,
        }


@dataclass
class RuleProposal:
    """Structured improvement proposal."""
    rule_id: str = field(default_factory=lambda: str(uuid4()))
    rule_type: str = ""  # parameter_tuning | capability_enhancement | workflow_optimization
    condition: str = ""
    suggestion: str = ""
    target_module: str = ""
    confidence: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    based_on_pattern_id: str = ""

    def dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "condition": self.condition,
            "suggestion": self.suggestion,
            "target_module": self.target_module,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "based_on_pattern_id": self.based_on_pattern_id,
        }


@dataclass
class SelfModel:
    """System self-model — skills and reliability."""
    skills: Dict[str, float] = field(default_factory=dict)  # skill -> confidence 0.0-1.0
    reliability: float = 0.0  # 0.0-1.0
    error_rate: float = 0.0  # 0.0-1.0
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "skills": self.skills,
            "reliability": self.reliability,
            "error_rate": self.error_rate,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "updated_at": self.updated_at,
        }