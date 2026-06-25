"""LLM Types — Types de données pour le moteur LLM multi-provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    """Types de tâches LLM."""
    CHAT = "chat"
    CODE = "code"
    EMBEDDING = "embedding"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


@dataclass
class LLMRequirements:
    """Besoins pour la sélection d'un modèle."""
    task_type: str = "chat"
    max_cost: float | None = None
    max_latency_ms: float | None = None
    min_quality: float | None = None
    require_local: bool = False
    require_private: bool = False
    context_length: int | None = None
    preferred_providers: list[str] = field(default_factory=list)
    excluded_providers: list[str] = field(default_factory=list)


@dataclass
class ModelInfo:
    """Informations sur un modèle LLM."""
    id: str
    provider: str
    name: str
    context_length: int = 4096
    pricing: dict | None = None
    quality_score: float = 0.8
    avg_latency_ms: float = 1000.0
    is_local: bool = False
    is_private: bool = False
    capabilities: list[str] = field(default_factory=list)
    is_available: bool = True
    metadata: dict = field(default_factory=dict)


@dataclass
class ScoredModel:
    """Modèle avec son score."""
    model: ModelInfo
    score: float
    reasoning: str = ""


@dataclass
class UsageStats:
    """Statistiques d'utilisation."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0