"""Event schema — Core data model for all NATS events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class Event:
    """Standard event envelope for all NATS messages."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = "generic"
    source: str = "unknown"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    version: str = "1.0"

    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    reply_to: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        """Serialize to dict (JSON-compatible)."""
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp,
            "version": self.version,
            "data": self.data,
            "metadata": self.metadata,
            "reply_to": self.reply_to,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Event:
        """Deserialize from dict."""
        return Event(
            id=data.get("id", str(uuid4())),
            type=data.get("type", "generic"),
            source=data.get("source", "unknown"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            version=data.get("version", "1.0"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            reply_to=data.get("reply_to"),
        )


# ── Event type constants ────────────────────────────────

class EventType:
    """Well-known event types."""

    # Intents
    INTENT_USER = "intent.user"
    INTENT_RESPONSE = "intent.response"

    # Task lifecycle (Phase 0.3)
    TASK_CREATED = "task.created"
    TASK_PLAN = "task.plan"
    TASK_PLANNED = "task.planned"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Memory events (Phase 0.3)
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"

    # Reflection (Phase 0.3)
    REFLECTION_DONE = "reflection.done"

    # Modules
    MODULE_EXECUTIVE = "module.executive"
    MODULE_EXECUTIVE_DONE = "module.executive.done"
    MODULE_PLANNER = "module.planner"
    MODULE_PLANNER_DONE = "module.planner.done"
    MODULE_EXECUTION = "module.execution"
    MODULE_EXECUTION_DONE = "module.execution.done"
    MODULE_MEMORY = "module.memory"
    MODULE_MEMORY_DONE = "module.memory.done"
    MODULE_REFLECTIVE = "module.reflective"
    MODULE_REFLECTIVE_DONE = "module.reflective.done"

    # Legacy module events (compat)
    MODULE_REASONING = "module.reasoning"
    MODULE_REASONING_DONE = "module.reasoning.done"
    MODULE_PLANNING = "module.planning"
    MODULE_PLANNING_DONE = "module.planning.done"
    MODULE_REFLECTION = "module.reflection"
    MODULE_REFLECTION_DONE = "module.reflection.done"

    # System
    SYSTEM_KERNEL_STARTED = "system.kernel.started"
    SYSTEM_KERNEL_SHUTDOWN = "system.kernel.shutdown"
    SYSTEM_MODULE_REGISTERED = "system.module.registered"
    SYSTEM_MODULE_UNREGISTERED = "system.module.unregistered"
    SYSTEM_ERROR = "system.error"

    # Goals
    GOAL_CREATED = "goal.created"
    GOAL_COMPLETED = "goal.completed"
    GOAL_FAILED = "goal.failed"

    # Schedule
    SCHEDULE_TRIGGER = "schedule.trigger"
    SCHEDULE_COMPLETED = "schedule.completed"

    # Audit
    AUDIT = "audit"

    # Learning (Phase 4)
    LEARNING_INSIGHT = "learning.insight"
    LEARNING_PATTERN = "learning.pattern"
    RULE_PROPOSAL = "learning.rule_proposal"
    SELF_MODEL_UPDATED = "learning.self_model_updated"
    SYSTEM_IMPROVEMENT_SUGGESTION = "learning.improvement_suggestion"