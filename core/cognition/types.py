"""Cognition Types — Types de données pour le module Cognition."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    """Types d'intention."""
    QUERY = "query"                  # Question
    COMMAND = "command"              # Commande
    TASK = "task"                    # Tâche à accomplir
    CONVERSATION = "conversation"    # Conversation générale
    CLARIFICATION = "clarification"  # Demande de clarification


class Intent:
    """Intention extraite d'une requête."""
    type: IntentType
    entities: dict[str, Any]
    confidence: float
    raw_query: str
    ambiguity_score: float = 0.0


@dataclass
class CognitionRequest:
    """Requête abstraite vers le module Cognition."""
    query: str
    context: dict[str, Any] = field(default_factory=dict)
    session_id: str = "default"
    constraints: dict[str, Any] = field(default_factory=dict)
    expected_output: str = "text"  # "text", "code", "plan", "action"


@dataclass
class CognitionResponse:
    """Réponse du module Cognition."""
    success: bool
    output: Any = None
    reasoning: str = ""
    confidence: float = 1.0
    needs_clarification: bool = False
    clarification_questions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Reasoning:
    """Résultat du raisonnement."""
    chain_of_thought: str
    goal: str
    required_capabilities: list[str]
    tokens_used: int = 0
    model: str = ""
    latency_ms: float = 0.0


@dataclass
class CognitiveState:
    """État interne du module Cognition."""
    session_id: str
    current_intent: Intent | None = None
    working_memory: dict[str, Any] = field(default_factory=dict)
    active_goals: list[str] = field(default_factory=list)
    context_window: list[dict[str, Any]] = field(default_factory=list)
    last_reasoning: Reasoning | None = None
    metadata: dict[str, Any] = field(default_factory=dict)