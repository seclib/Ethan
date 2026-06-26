"""Message types — Contrat pour les échanges entre utilisateurs et système."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """Message de聊天 standardisé pour les appels LLM."""
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
    latency_ms: float = 0.0


@dataclass
class Message:
    """Message métier échangé entre interfaces et modules.

    Représente un message complet avec son contexte de session.
    """
    id: str = ""
    session_id: str = ""
    role: str = "user"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0