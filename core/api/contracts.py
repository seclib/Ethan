"""ETHAN Core API Contracts — Types partagés pour l'API publique."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    """Événement du système."""

    id: str
    type: str
    source: str
    timestamp: int  # Unix ms
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class EventResponse:
    """Réponse à un événement."""

    event_id: str
    accepted: bool
    error: str | None = None


@dataclass
class StateQuery:
    """Requête d'état."""

    key: str
    namespace: str = ""


@dataclass
class StateResponse:
    """Réponse d'état."""

    value: bytes | None
    ttl: int | None = None


@dataclass
class TaskRequest:
    """Requête de tâche."""

    task_id: str
    capability: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResponse:
    """Réponse de tâche."""

    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    result: bytes | None = None
    error: str | None = None


@dataclass
class HealthCheckResponse:
    """Réponse de health check."""

    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    uptime_seconds: int
    modules: dict[str, str] = field(default_factory=dict)
    connections: dict[str, str] = field(default_factory=dict)