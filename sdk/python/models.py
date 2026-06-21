"""Jarvis OS — Python SDK Data Models"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """Message de chat."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class ChatResponse:
    """Réponse de chat."""
    content: str
    model: str
    provider: str
    usage: dict | None = None
    finish_reason: str | None = None


@dataclass
class AgentInfo:
    """Informations sur un agent."""
    name: str
    description: str
    status: str
    uptime: float = 0.0
    events_processed: int = 0
    errors: int = 0


@dataclass
class MemoryEntry:
    """Entrée mémoire."""
    key: str
    value: str
    namespace: str = "default"
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0