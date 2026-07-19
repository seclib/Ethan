"""Autonomous Goal schemas — GoalProposal, GoalScorer, GoalType."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


# ── Goal Types ──────────────────────────────────────────

IMPROVEMENT_GOAL = "improvement"
EXPLORATION_GOAL = "exploration"
OPTIMIZATION_GOAL = "optimization"
MAINTENANCE_GOAL = "maintenance"

GOAL_TYPES = [
    IMPROVEMENT_GOAL,
    EXPLORATION_GOAL,
    OPTIMIZATION_GOAL,
    MAINTENANCE_GOAL,
]


# ── Schemas ─────────────────────────────────────────────

@dataclass
class GoalProposal:
    """Proposed goal from autonomous generation."""
    proposal_id: str = field(default_factory=lambda: str(uuid4()))
    goal_type: str = IMPROVEMENT_GOAL
    title: str = ""
    description: str = ""
    target_domain: str = ""  # skill or module to improve
    priority: float = 0.5   # 0.0-1.0
    estimated_effort: str = "medium"  # low | medium | high
    expected_benefit: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_signal: str = ""  # failure | curiosity | weakness | environment
    context: Dict[str, Any] = field(default_factory=dict)

    def dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "goal_type": self.goal_type,
            "title": self.title,
            "description": self.description,
            "target_domain": self.target_domain,
            "priority": self.priority,
            "estimated_effort": self.estimated_effort,
            "expected_benefit": self.expected_benefit,
            "created_at": self.created_at,
            "source_signal": self.source_signal,
            "context": self.context,
        }


@dataclass
class GoalScore:
    """Scoring result for a proposed goal."""
    proposal_id: str = ""
    score: float = 0.0
    priority_rank: int = 0
    reasoning: str = ""
    factors: Dict[str, float] = field(default_factory=dict)
    scored_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "score": self.score,
            "priority_rank": self.priority_rank,
            "reasoning": self.reasoning,
            "factors": self.factors,
            "scored_at": self.scored_at,
        }