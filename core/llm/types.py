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
    model: str = ""
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
class ChatMessage:
    """Message de chat standardisé."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class ChatResponse:
    """Réponse de chat standardisée."""
    content: str
    model: str
    provider: str
    usage: dict | None = None
    finish_reason: str | None = None


@dataclass
class UsageStats:
    """Statistiques d'utilisation."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0


# ── Vision Types ──────────────────────────────────────────────────────────


@dataclass
class VisionImage:
    """Image reference for vision analysis.

    Supports either a base64 payload or a URL. Providers that only accept
    one form should raise NotImplementedError for the other.
    """
    data: str  # base64-encoded bytes OR URL
    mime_type: str = "image/png"
    is_url: bool = False


@dataclass
class VisionRequest:
    """Request to analyze an image with a vision-capable model."""
    images: list[VisionImage]
    prompt: str = "Describe this image in detail."
    model: str | None = None
    max_tokens: int | None = None


@dataclass
class VisionResponse:
    """Response from a vision analysis."""
    content: str
    model: str
    provider: str
    usage: dict | None = None


# ── Transcription Types ───────────────────────────────────────────────────


@dataclass
class TranscriptionRequest:
    """Request to transcribe audio to text."""
    audio_data: bytes
    mime_type: str = "audio/wav"
    model: str | None = None
    language: str | None = None  # ISO-639-1 (e.g., "en", "fr")


@dataclass
class TranscriptionResponse:
    """Response from audio transcription."""
    text: str
    model: str
    provider: str
    language: str | None = None
    duration_seconds: float | None = None
