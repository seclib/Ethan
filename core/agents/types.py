"""Agent Types — Types de données pour le module Agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    """États possibles d'un agent."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class AgentExecutionStatus(str, Enum):
    """Terminal and transient states for an agent execution."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Agent:
    """Enregistrement d'un agent (persisté)."""
    id: str
    name: str
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    model: str | None = None
    provider: str | None = None
    memory_scope: str = "default"
    skill_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'agent en dict."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "model": self.model,
            "provider": self.provider,
            "memory_scope": self.memory_scope,
            "skill_ids": self.skill_ids,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent":
        """Désérialise un agent depuis un dict."""
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            status=AgentStatus(data.get("status", "idle")),
            model=data.get("model"),
            provider=data.get("provider"),
            memory_scope=data.get("memory_scope", "default"),
            skill_ids=data.get("skill_ids", data.get("skills", [])),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
        )


@dataclass
class AgentExecution:
    """An auditable request handled by an agent execution adapter."""

    id: str
    agent_id: str
    task: str
    status: AgentExecutionStatus = AgentExecutionStatus.RUNNING
    result: Any = None
    error: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    skill_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize this execution for storage and interfaces."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task": self.task,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "context": self.context,
            "skill_id": self.skill_id,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentExecution":
        """Rebuild an execution from its persisted representation."""
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            task=data.get("task", ""),
            status=AgentExecutionStatus(data.get("status", "running")),
            result=data.get("result"),
            error=data.get("error"),
            context=data.get("context", {}),
            skill_id=data.get("skill_id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow(),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
        )
