"""Event schema — Core data model for all NATS events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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

    # ── Interface Events ──────────────────────────────
    INTERFACE_COMMAND = "interface.command"
    INTERFACE_MESSAGE = "interface.message"
    INTERFACE_INTENT = "interface.intent"
    INTERFACE_INTERACTION = "interface.interaction"
    INTERFACE_STATUS = "interface.status"

    # ── Kernel Events ─────────────────────────────────
    KERNEL_EVENT_VALIDATED = "kernel.event.validated"
    KERNEL_EVENT_REJECTED = "kernel.event.rejected"
    KERNEL_REQUEST_CREATED = "kernel.request.created"
    KERNEL_CAPABILITY_REQUIRED = "kernel.capability.required"
    KERNEL_CAPABILITY_RESOLVED = "kernel.capability.resolved"

    # ── Registry Events ───────────────────────────────
    REGISTRY_CAPABILITY_REGISTERED = "registry.capability.registered"
    REGISTRY_CAPABILITY_REMOVED = "registry.capability.removed"
    REGISTRY_MODULE_HEARTBEAT = "registry.module.heartbeat"
    REGISTRY_DEPENDENCY_MISSING = "registry.dependency.missing"
    REGISTRY_UPDATED = "registry.updated"

    # ── Intents ───────────────────────────────────────
    INTENT_USER = "intent.user"
    INTENT_RESPONSE = "intent.response"
    TASK_EXECUTED = "task.executed"

    # ── Task lifecycle ────────────────────────────────
    TASK_CREATED = "task.created"
    TASK_PLAN = "task.plan"
    TASK_PLANNED = "task.planned"
    TASK_ASSIGNED = "task.assigned"
    TASK_RUNNING = "task.running"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_TIMEOUT = "task.timeout"
    TASK_RETRYING = "task.retrying"

    # ── Planner Events ────────────────────────────────
    PLANNER_GOAL_CREATED = "planner.goal.created"
    PLANNER_GOAL_DECOMPOSED = "planner.goal.decomposed"
    PLANNER_PLAN_CREATED = "planner.plan.created"
    PLANNER_PLAN_REJECTED = "planner.plan.rejected"
    PLANNER_PLAN_FAILED = "planner.plan.failed"

    # ── Executor Events ───────────────────────────────
    EXECUTOR_TASK_ASSIGNED = "executor.task.assigned"
    EXECUTOR_TASK_RUNNING = "executor.task.running"
    EXECUTOR_TASK_COMPLETED = "executor.task.completed"
    EXECUTOR_TASK_FAILED = "executor.task.failed"
    EXECUTOR_TASK_TIMEOUT = "executor.task.timeout"
    EXECUTOR_TASK_RETRYING = "executor.task.retrying"
    EXECUTOR_PLAN_EXECUTING = "executor.plan.executing"
    EXECUTOR_PLAN_DONE = "executor.plan.done"

    # ── Memory events ─────────────────────────────────
    MEMORY_STORE_REQUEST = "memory.store.request"
    MEMORY_STORE_COMPLETE = "memory.store.complete"
    MEMORY_RECALL_REQUEST = "memory.recall.request"
    MEMORY_RECALL_COMPLETE = "memory.recall.complete"
    MEMORY_CONTEXT_ASSEMBLED = "memory.context.assembled"
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"

    # ── Response Events ───────────────────────────────
    RESPONSE_OK = "response.ok"
    RESPONSE_ERROR = "response.error"
    RESPONSE_TIMEOUT = "response.timeout"
    RESPONSE_REJECTED = "response.rejected"

    # ── Module Events ─────────────────────────────────
    MODULE_TASK_ASSIGNED = "module.task.assigned"
    MODULE_TASK_RESULT = "module.task.result"
    MODULE_CAPABILITY_INVOKE = "module.capability.invoke"
    MODULE_CAPABILITY_RESULT = "module.capability.result"
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
    MODULE_REASONING = "module.reasoning"
    MODULE_REASONING_DONE = "module.reasoning.done"
    MODULE_PLANNING = "module.planning"
    MODULE_PLANNING_DONE = "module.planning.done"
    MODULE_REFLECTION = "module.reflection"
    MODULE_REFLECTION_DONE = "module.reflection.done"

    # ── System Events ─────────────────────────────────
    SYSTEM_BOOT = "system.boot"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_TELEMETRY = "system.telemetry"
    SYSTEM_KERNEL_STARTED = "system.kernel.started"
    SYSTEM_KERNEL_SHUTDOWN = "system.kernel.shutdown"
    SYSTEM_MODULE_REGISTERED = "system.module.registered"
    SYSTEM_MODULE_UNREGISTERED = "system.module.unregistered"
    SYSTEM_OPTIMIZED = "system.optimized"
    SYSTEM_BOOTSTRAP_COMPLETED = "system.bootstrap.completed"
    INGEST_ERROR = "ingest.error"

    # ── Goals ─────────────────────────────────────────
    GOAL_CREATED = "goal.created"
    GOAL_COMPLETED = "goal.completed"
    GOAL_FAILED = "goal.failed"
    GOAL_PROPOSED = "goal.proposed"
    GOAL_PRIORITIZED = "goal.prioritized"
    EXPLORATION_GOAL_CREATED = "goal.exploration.created"
    NEW_GOAL_CREATED = "autonomy.goal.created"

    # ── Schedule ──────────────────────────────────────
    SCHEDULE_TRIGGER = "schedule.trigger"
    SCHEDULE_COMPLETED = "schedule.completed"

    # ── Audit ─────────────────────────────────────────
    AUDIT = "audit"

    # ── Capability ────────────────────────────────────
    CAPABILITY_INVOKE = "capability.invoke"
    CAPABILITY_COMPLETED = "capability.completed"
    CAPABILITY_FAILED = "capability.failed"

    # ── Learning ──────────────────────────────────────
    LEARNING_INSIGHT = "learning.insight"
    LEARNING_PATTERN = "learning.pattern"
    RULE_PROPOSAL = "learning.rule_proposal"
    SELF_MODEL_UPDATED = "learning.self_model_updated"
    SYSTEM_IMPROVEMENT_SUGGESTION = "learning.improvement_suggestion"

    # ── Meta-Cognition ────────────────────────────────
    STRATEGY_SELECTED = "meta.strategy_selected"
    COGNITIVE_MODE_CHANGED = "meta.mode_changed"
    MODULE_PRIORITY_UPDATED = "meta.priority_updated"
    THINKING_DEPTH_ADJUSTED = "meta.depth_adjusted"

    # ── Autonomous Goals ──────────────────────────────
    AUTONOMOUS_GOAL_GENERATED = "autonomy.goal_generated"

    # ── Autonomy Loop ─────────────────────────────────
    AUTONOMY_CYCLE_STARTED = "autonomy.cycle.started"
    AUTONOMY_CYCLE_COMPLETED = "autonomy.cycle.completed"
    SELF_HEAL_TRIGGERED = "autonomy.self_heal.triggered"
    IDLE_DETECTED = "autonomy.idle.detected"

    # ── Bootstrap ─────────────────────────────────────
    BOOTSTRAP_INTEGRITY_CHECK = "bootstrap.integrity.check"
    BOOTSTRAP_INTEGRITY_COMPLETED = "bootstrap.integrity.completed"
    BOOTSTRAP_REPAIR_REQUESTED = "bootstrap.repair.requested"
    BOOTSTRAP_CONFIG_PROPOSED = "bootstrap.config.proposed"
    BOOTSTRAP_CONFIG_APPLIED = "bootstrap.config.applied"
