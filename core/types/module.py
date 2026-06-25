"""Module types — Contrat pour la configuration et l'état des modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ModuleState(str, Enum):
    """États possibles d'un module."""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"
    CRASHED = "crashed"


@dataclass
class ModuleConfig:
    """Configuration d'un module worker.

    Définit comment le Kernel doit démarrer et superviser un module.
    """
    name: str
    module_path: str  # Chemin Python (e.g., "core.agents.executive")
    enabled: bool = True
    capabilities: list[str] = field(default_factory=list)
    auto_start: bool = True
    restart_policy: str = "always"  # "always", "on_failure", "never"
    max_restarts: int = 5
    healthcheck_interval: int = 15  # secondes
    timeout: int = 30  # secondes
    env: dict[str, str] = field(default_factory=dict)
    args: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleStateData:
    """État courant d'un module (stocké dans Redis)."""
    name: str
    state: ModuleState = ModuleState.CREATED
    pid: int = 0
    started_at: datetime | None = None
    last_heartbeat: datetime | None = None
    restart_count: int = 0
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)