"""Canonical event contract for every ETHAN component.

``EventType`` is defined only in this module. The SDK and legacy event
packages re-export it for compatibility; they must not introduce new enum
members independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class EventType(str, Enum):
    """Types d'événements du système — convention plate `ethan.<module>.<action>`."""

    # System
    SYSTEM_BOOT = "ethan.system.boot"
    SYSTEM_SHUTDOWN = "ethan.system.shutdown"
    SYSTEM_ERROR = "ethan.system.error"

    # Interface
    INTERFACE_MESSAGE = "ethan.interface.message"
    INTERFACE_COMMAND = "ethan.interface.command"
    INTERFACE_STATUS = "ethan.interface.status"

    # Intent
    INTENT_RESOLVED = "ethan.intent.resolved"
    INTENT_USER = "ethan.intent.user"

    # Executive
    EXECUTIVE_GOAL_CREATED = "ethan.executive.goal.created"
    EXECUTIVE_GOAL_UPDATED = "ethan.executive.goal.updated"
    EXECUTIVE_GOAL_CANCELLED = "ethan.executive.goal.cancelled"
    EXECUTIVE_GOAL_FAILED = "ethan.executive.goal.failed"
    EXECUTIVE_RESPONSE = "ethan.executive.response"

    # Planner
    PLANNER_PLAN_CREATED = "ethan.planner.plan.created"
    PLANNER_PLAN_FAILED = "ethan.planner.plan.failed"

    # Executor
    EXECUTOR_TASK_ASSIGNED = "ethan.executor.task.assigned"
    EXECUTOR_TASK_COMPLETED = "ethan.executor.task.completed"
    EXECUTOR_TASK_FAILED = "ethan.executor.task.failed"
    EXECUTOR_TASK_TIMEOUT = "ethan.executor.task.timeout"
    EXECUTOR_TASK_CANCELLED = "ethan.executor.task.cancelled"
    EXECUTOR_PLAN_DONE = "ethan.executor.plan.done"

    # Memory
    MEMORY_STORE = "ethan.memory.store"
    MEMORY_STORE_COMPLETE = "ethan.memory.store.complete"
    MEMORY_RECALL = "ethan.memory.recall"
    MEMORY_RECALL_COMPLETE = "ethan.memory.recall.complete"
    MEMORY_SEARCH = "ethan.memory.search"
    MEMORY_STORED = "ethan.memory.stored"

    # Context
    CONTEXT_ASSEMBLED = "ethan.context.assembled"

    # Reflective
    REFLECTIVE_EVALUATION = "ethan.reflective.evaluation"
    REFLECTIVE_INSIGHT = "ethan.reflective.insight"
    REFLECTION_DONE = "ethan.reflection.done"
    MODULE_REFLECTION_DONE = "ethan.module.reflection.done"

    # Autonomy
    AUTONOMY_INITIATIVE = "ethan.autonomy.initiative"
    AUTONOMY_SUGGESTION = "ethan.autonomy.suggestion"
    AUTONOMY_CYCLE_STARTED = "ethan.autonomy.cycle.started"
    AUTONOMY_CYCLE_COMPLETED = "ethan.autonomy.cycle.completed"

    # Learning
    LEARNING_OUTCOME = "ethan.learning.outcome"
    LEARNING_PATTERN = "ethan.learning.pattern"
    LEARNING_INSIGHT = "ethan.learning.insight"
    RULE_PROPOSAL = "ethan.learning.rule.proposal"
    SELF_MODEL_UPDATED = "ethan.learning.self_model.updated"

    # Metacognition
    METACOGNITION_REPORT = "ethan.metacognition.report"
    METACOGNITION_WARNING = "ethan.metacognition.warning"

    # Registry
    REGISTRY_REGISTERED = "ethan.registry.registered"
    REGISTRY_REMOVED = "ethan.registry.removed"
    REGISTRY_UPDATED = "ethan.registry.updated"

    # Module
    MODULE_HEARTBEAT = "ethan.module.heartbeat"

    # Cognition
    COGNITION_REQUEST = "ethan.cognition.request"
    COGNITION_RESPONSE = "ethan.cognition.response"
    COGNITION_INTENT_ANALYZED = "ethan.cognition.intent.analyzed"
    COGNITION_REASONING_COMPLETE = "ethan.cognition.reasoning.complete"
    COGNITION_PLAN_CREATED = "ethan.cognition.plan.created"
    COGNITION_EXECUTION_COMPLETE = "ethan.cognition.execution.complete"
    COGNITION_REFLECTION_COMPLETE = "ethan.cognition.reflection.complete"
    COGNITION_CLARIFICATION_NEEDED = "ethan.cognition.clarification.needed"
    COGNITION_ERROR = "ethan.cognition.error"

    # Tasks
    TASK_CREATED = "ethan.task.created"
    TASK_PLAN = "ethan.task.plan"
    TASK_PLANNED = "ethan.task.planned"
    TASK_EXECUTED = "ethan.task.executed"
    TASK_COMPLETED = "ethan.task.completed"
    TASK_FAILED = "ethan.task.failed"

    # Goals
    GOAL_CREATED = "ethan.goal.created"
    GOAL_COMPLETED = "ethan.goal.completed"
    GOAL_FAILED = "ethan.goal.failed"
    NEW_GOAL_CREATED = "ethan.goal.new_created"

    # Agents
    AGENT_CREATED = "ethan.agent.created"
    AGENT_UPDATED = "ethan.agent.updated"
    AGENT_DELETED = "ethan.agent.deleted"

    # Missions
    MISSION_CREATED = "ethan.mission.created"
    MISSION_UPDATED = "ethan.mission.updated"
    MISSION_COMPLETED = "ethan.mission.completed"
    MISSION_FAILED = "ethan.mission.failed"
    MISSION_STEP_VERIFIED = "ethan.mission.step.verified"
    MISSION_STEP_APPROVED = "ethan.mission.step.approved"

    # Knowledge
    KNOWLEDGE_CREATED = "ethan.knowledge.created"
    KNOWLEDGE_UPDATED = "ethan.knowledge.updated"
    KNOWLEDGE_DELETED = "ethan.knowledge.deleted"

    # Chats
    CHAT_CREATED = "ethan.chat.created"
    CHAT_UPDATED = "ethan.chat.updated"
    CHAT_DELETED = "ethan.chat.deleted"
    CHAT_MESSAGE = "ethan.chat.message"

    # Files
    FILE_UPLOADED = "ethan.file.uploaded"
    FILE_DELETED = "ethan.file.deleted"

    # Users
    USER_CREATED = "ethan.user.created"
    USER_UPDATED = "ethan.user.updated"
    USER_DELETED = "ethan.user.deleted"

    # Groups
    GROUP_CREATED = "ethan.group.created"
    GROUP_UPDATED = "ethan.group.updated"
    GROUP_DELETED = "ethan.group.deleted"

    # Automations
    AUTOMATION_CREATED = "ethan.automation.created"
    AUTOMATION_UPDATED = "ethan.automation.updated"
    AUTOMATION_DELETED = "ethan.automation.deleted"
    AUTOMATION_TRIGGERED = "ethan.automation.triggered"

    # Channels
    CHANNEL_CREATED = "ethan.channel.created"
    CHANNEL_UPDATED = "ethan.channel.updated"
    CHANNEL_DELETED = "ethan.channel.deleted"
    CHANNEL_MESSAGE = "ethan.channel.message"

    # Notes
    NOTE_CREATED = "ethan.note.created"
    NOTE_UPDATED = "ethan.note.updated"
    NOTE_DELETED = "ethan.note.deleted"

    # Tool Servers
    TOOL_SERVER_REGISTERED = "ethan.tool.server.registered"
    TOOL_SERVER_UPDATED = "ethan.tool.server.updated"
    TOOL_SERVER_DELETED = "ethan.tool.server.deleted"

    # Scheduler and Security
    SCHEDULE_TRIGGER = "ethan.schedule.trigger"
    SECURITY_AUDIT = "ethan.security.audit"



@dataclass
class Event:
    """Événement système — unité fondamentale de communication.

    Toute communication entre composants passe par un Event.
    Les Events sont immutables une fois publiés.

    Backward compatibility: `data` is accepted as an alias for `payload`.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    type: EventType | str = EventType.SYSTEM_BOOT
    source: str = "system"
    timestamp: datetime | str = field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"
    reply_to: str | None = None
    # Accept `data` as an alias for `payload` in constructor
    data: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        # Merge `data` into `payload` for backward compatibility.
        # If both are provided, `payload` wins. If only `data`, use it as payload.
        if self.data and not self.payload:
            self.payload = self.data
        # Clear the `data` field — canonical access is via `payload`
        object.__setattr__(self, 'data', self.payload)
        # Normalize type: accept plain strings
        if isinstance(self.type, str) and not isinstance(self.type, EventType):
            try:
                self.type = EventType(self.type)
            except ValueError:
                pass  # Keep as plain string for SDK/custom event types

    @property
    def correlation_id(self) -> str | None:
        """Récupère le correlation_id du metadata, s'il existe."""
        return self.metadata.get("correlation_id")

    @correlation_id.setter
    def correlation_id(self, value: str) -> None:
        """Définit le correlation_id dans le metadata."""
        self.metadata["correlation_id"] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value if hasattr(self.type, "value") else str(self.type),
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "payload": self.payload,
            "data": self.payload,  # backward compat for SDK consumers
            "metadata": self.metadata,
            "version": self.version,
            "reply_to": self.reply_to,
        }

    def to_json(self) -> bytes:
        """Convert to JSON bytes for NATS."""
        import json
        return json.dumps(self.to_dict()).encode()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Event":
        """Deserialize from dict, accepting both `payload` and `data`."""
        payload = raw.get("payload") or raw.get("data", {})
        return cls(
            id=raw.get("id", str(uuid4())),
            type=raw.get("type", "generic"),
            source=raw.get("source", "unknown"),
            timestamp=raw.get("timestamp", datetime.utcnow().isoformat()),
            payload=payload,
            metadata=raw.get("metadata", {}),
            version=raw.get("version", "1.0"),
            reply_to=raw.get("reply_to"),
        )

    @classmethod
    def from_json(cls, raw_bytes: bytes) -> "Event":
        """Deserialize from JSON bytes."""
        import json
        return cls.from_dict(json.loads(raw_bytes))
