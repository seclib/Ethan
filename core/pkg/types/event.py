"""Event types — Contrat de données pour tous les événements du système."""

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

    # Context
    CONTEXT_ASSEMBLED = "ethan.context.assembled"

    # Reflective
    REFLECTIVE_EVALUATION = "ethan.reflective.evaluation"
    REFLECTIVE_INSIGHT = "ethan.reflective.insight"

    # Autonomy
    AUTONOMY_INITIATIVE = "ethan.autonomy.initiative"
    AUTONOMY_SUGGESTION = "ethan.autonomy.suggestion"

    # Learning
    LEARNING_OUTCOME = "ethan.learning.outcome"
    LEARNING_PATTERN = "ethan.learning.pattern"

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


@dataclass
class Event:
    """Événement système — unité fondamentale de communication.

    Toute communication entre composants passe par un Event.
    Les Events sont immutables une fois publiés.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    type: EventType = EventType.SYSTEM_BOOT
    source: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def correlation_id(self) -> str | None:
        """Récupère le correlation_id du metadata, s'il existe."""
        return self.metadata.get("correlation_id")

    @correlation_id.setter
    def correlation_id(self, value: str) -> None:
        """Définit le correlation_id dans le metadata."""
        self.metadata["correlation_id"] = value