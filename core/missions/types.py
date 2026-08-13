"""Mission Types — Types de données pour le module Missions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MissionStatus(str, Enum):
    """États possibles d'une mission."""
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


class StepStatus(str, Enum):
    """États possibles d'un step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class MissionVerdict(str, Enum):
    """Verdicts possibles d'une mission."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    KILLED = "killed"


@dataclass
class MissionStep:
    """Étape d'une mission."""
    id: str
    mission_id: str
    title: str
    description: str = ""
    status: StepStatus = StepStatus.PENDING
    success_criterion: str = ""
    verification_command: str | None = None
    access_level: int = 0
    verified: bool = False
    depends_on: list[str] = field(default_factory=list)
    order: int = 0
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize a step without leaking enum/datetime objects."""
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "success_criterion": self.success_criterion,
            "verification_command": self.verification_command,
            "access_level": self.access_level,
            "verified": self.verified,
            "depends_on": self.depends_on,
            "order": self.order,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MissionStep":
        """Rebuild a step from its durable representation."""
        return cls(
            id=data["id"],
            mission_id=data["mission_id"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=StepStatus(data.get("status", "pending")),
            success_criterion=data.get("success_criterion", ""),
            verification_command=data.get("verification_command"),
            access_level=int(data.get("access_level", 0)),
            verified=bool(data.get("verified", False)),
            depends_on=list(data.get("depends_on", [])),
            order=int(data.get("order", 0)),
            result=data.get("result"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.utcnow(),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
        )


@dataclass
class Mission:
    """Mission — objectif long avec tâches et progression."""
    id: str
    title: str
    description: str = ""
    status: MissionStatus = MissionStatus.PENDING
    steps: list[MissionStep] = field(default_factory=list)
    steps_total: int = 0
    steps_completed: int = 0
    workspace_path: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    verdict: MissionVerdict | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Sérialise la mission en dict."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "steps_total": self.steps_total,
            "steps_completed": self.steps_completed,
            "workspace_path": self.workspace_path,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "verdict": self.verdict.value if self.verdict else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def progress(self) -> float:
        """Calcule la progression (0.0 à 1.0)."""
        if not self.steps:
            return 0.0
        return self.steps_completed / max(1, len(self.steps))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Mission":
        """Rebuild a mission from its durable representation."""
        mission = cls(
            id=data["id"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=MissionStatus(data.get("status", "pending")),
            workspace_path=data.get("workspace_path", ""),
            artifacts=data.get("artifacts", {}),
            logs=data.get("logs", []),
            verdict=MissionVerdict(data["verdict"]) if data.get("verdict") else None,
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.utcnow(),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
        )
        mission.steps = [MissionStep.from_dict(step) for step in data.get("steps", [])]
        mission.steps_total = int(data.get("steps_total", len(mission.steps)))
        mission.steps_completed = int(
            data.get(
                "steps_completed",
                sum(step.status == StepStatus.COMPLETED for step in mission.steps),
            )
        )
        return mission
