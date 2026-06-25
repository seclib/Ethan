"""Orchestrator Context — Contexte d'exécution de l'orchestrateur."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class OrchestratorContext:
    """Contexte global de l'orchestrateur.
    
    Contient toutes les références aux modules et l'état courant.
    """

    # Identifiants
    request_id: str
    user_id: str = "default"
    session_id: str = "default"

    # Modules
    cognition: Any = None
    memory: Any = None
    planner: Any = None
    tools: Any = None
    security: Any = None
    events: Any = None
    llm: Any = None
    skills: Any = None

    # État
    current_goal: str | None = None
    current_plan: Any = None
    current_skill: Any = None
    context_items: list[Any] = field(default_factory=list)

    # Métadonnées
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)