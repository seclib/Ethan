"""Planner Types — Types de données pour le module Planner."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PlanState(str, Enum):
    """États d'un plan."""
    CREATED = "created"
    PLANNING = "planning"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskState(str, Enum):
    """États d'une tâche."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class Priority(str, Enum):
    """Niveaux de priorité."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


@dataclass
class Goal:
    """Objectif à accomplir."""
    id: str
    description: str
    priority: Priority = Priority.MEDIUM
    state: str = "active"
    required_capabilities: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    deadline: datetime | None = None
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Task:
    """Tâche atomique."""
    id: str
    capability: str
    params: dict[str, Any] = field(default_factory=dict)
    state: TaskState = TaskState.PENDING
    depends_on: list[str] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    max_retries: int = 3
    timeout: int = 30
    retry_count: int = 0
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    checkpoint_data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDAG:
    """Graphe acyclique de tâches."""
    tasks: dict[str, Task] = field(default_factory=dict)
    levels: list[list[str]] = field(default_factory=list)  # Niveaux d'exécution

    def add_task(self, task: Task) -> None:
        """Ajoute une tâche."""
        self.tasks[task.id] = task

    def add_level(self, task_ids: list[str], level: int) -> None:
        """Ajoute un niveau d'exécution."""
        while len(self.levels) <= level:
            self.levels.append([])
        self.levels[level].extend(task_ids)

    def get_task(self, task_id: str) -> Task | None:
        """Récupère une tâche."""
        return self.tasks.get(task_id)

    def get_dependencies(self, task_id: str) -> list[Task]:
        """Récupère les dépendances d'une tâche."""
        task = self.tasks.get(task_id)
        if not task:
            return []
        return [self.tasks[dep] for dep in task.depends_on if dep in self.tasks]

    def get_dependents(self, task_id: str) -> list[Task]:
        """Récupère les tâches qui dépendent de celle-ci."""
        dependents = []
        for task in self.tasks.values():
            if task_id in task.depends_on:
                dependents.append(task)
        return dependents


@dataclass
class Plan:
    """Plan d'exécution."""
    id: str
    goal_id: str
    state: PlanState = PlanState.CREATED
    tasks: list[Task] = field(default_factory=list)
    dag: TaskDAG | None = None
    priority: Priority = Priority.MEDIUM
    max_parallel: int = 4
    timeout: int = 3600
    checkpoint_interval: int = 60
    retry_policy: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def get_task(self, task_id: str) -> Task | None:
        """Récupère une tâche par ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_completed_tasks(self) -> list[Task]:
        """Récupère les tâches complétées."""
        return [t for t in self.tasks if t.state == TaskState.COMPLETED]

    def get_failed_tasks(self) -> list[Task]:
        """Récupère les tâches échouées."""
        return [t for t in self.tasks if t.state == TaskState.FAILED]

    def get_pending_tasks(self) -> list[Task]:
        """Récupère les tâches en attente."""
        return [t for t in self.tasks if t.state == TaskState.PENDING]

    def get_running_tasks(self) -> list[Task]:
        """Récupère les tâches en cours."""
        return [t for t in self.tasks if t.state == TaskState.RUNNING]

    def is_complete(self) -> bool:
        """Vérifie si toutes les tâches sont complétées."""
        return all(t.state == TaskState.COMPLETED for t in self.tasks)

    def is_failed(self) -> bool:
        """Vérifie si le plan a échoué."""
        return any(t.state == TaskState.FAILED for t in self.tasks)

    def progress(self) -> float:
        """Calcule le progrès (0.0 à 1.0)."""
        if not self.tasks:
            return 0.0
        completed = len(self.get_completed_tasks())
        return completed / len(self.tasks)


@dataclass
class Conflict:
    """Conflit entre goals."""
    type: str
    goals: list[str]
    description: str
    severity: str = "warning"


@dataclass
class Checkpoint:
    """Checkpoint de plan."""
    id: str
    plan_id: str
    timestamp: datetime
    completed_tasks: list[str]
    running_tasks: list[str]
    pending_tasks: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)