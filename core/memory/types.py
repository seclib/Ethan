"""Memory Types — Types de données pour le système mémoire."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryType(str, Enum):
    """Types de mémoire."""
    WORKING = "working"              # Mémoire de travail (RAM)
    SHORT_TERM = "short_term"        # Mémoire à court terme (heures)
    EPISODIC = "episodic"            # Mémoire épisodique (jours)
    SEMANTIC = "semantic"            # Mémoire sémantique (permanent)
    PROCEDURAL = "procedural"        # Mémoire procédurale (skills)
    VECTOR = "vector"                # Mémoire vectorielle (embeddings)
    EVENT_LOG = "event_log"          # Journal des événements
    HISTORY = "history"              # Historique des conversations


class MemoryItem:
    """Item de mémoire."""
    type: MemoryType
    content: Any
    importance: float = 0.5
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    ttl: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryQuery:
    """Requête de récupération mémoire."""
    query: str
    memory_types: list[MemoryType] | None = None
    limit: int = 20
    min_importance: float = 0.0
    max_age_days: int | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryResult:
    """Résultat de récupération mémoire."""
    item: MemoryItem
    score: float
    source: MemoryType
    metadata: dict[str, Any] = field(default_factory=dict)