"""ETHAN Core API Contracts — Types partagés pour l'API publique.

P0-3: Event is now imported from the canonical core.ethan_types.event module.
This file previously defined a duplicate, incompatible Event class (timestamp: int
vs datetime, no to_json/from_dict). That duplication is removed to enforce a
single source of truth for the Event contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.ethan_types.event import Event  # noqa: F401 — re-exported for API consumers


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