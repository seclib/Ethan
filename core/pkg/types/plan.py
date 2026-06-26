"""Plan types — Contrat pour les plans d'exécution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    """États possibles d'une tâche."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class Task:
    """Tâche atomique dans un plan.

    Une tâche est l'unité d'exécution la plus petite.
    Elle est assignée à une capability spécifique.
    """
    id: str = ""
    capability: str = ""  # Nom de la capability à invoquer
    params: dict[str, Any] = field(default_factory=dict)
    state: TaskState = TaskState.PENDING
    depends_on: list[str] = field(default_factory=list)  # IDs des tâches dont dépend celle-ci
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 30  # secondes
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    """Plan d'exécution — DAG de tâches.

    Un plan est produit par le Planner à partir d'un Goal.
    Il contient toutes les tâches nécessaires et leurs dépendances.
    """
    id: str = ""
    goal_id: str = ""
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    total_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDAG:
    """Représentation du DAG de tâches par niveaux.

    Utilisé par l'Orchestrator pour déterminer
    l'ordre d'exécution parallèle/séquentiel.
    """
    levels: list[list[Task]] = field(default_factory=list)

    def add_level(self, tasks: list[Task]) -> None:
        self.levels.append(tasks)