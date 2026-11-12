"""Modèles typés du TUI ETHAN.

Chaque type est une donnée d'interface : le TUI ne possède ni agents, ni
modèles, ni outils, ni sessions. Il ne fait que projeter les contrats du
Core (API v1) dans des structures immutables ou à mutation contrôlée, et ne
décode que les champs qu'il sait lire.

Aucun ``Any`` : les payloads JSON sont typés par un union récursif fermé
(`JSONValue`) et chaque parseur convertit explicitement une valeur inconnue
vers un type connu (jamais de cast silencieux).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias, Union

# ── JSON ───────────────────────────────────────────────────────────────

JSONScalar: TypeAlias = Union[str, int, float, bool, None]
JSONValue: TypeAlias = Union[JSONScalar, list["JSONValue"], dict[str, "JSONValue"]]


# ── Clavier ────────────────────────────────────────────────────────────


class KeyKind(StrEnum):
    """Familles de touches reconnues par le terminal."""

    CHARACTER = "character"
    ENTER = "enter"
    NEWLINE = "newline"
    ESCAPE = "escape"
    BACKSPACE = "backspace"
    DELETE = "delete"
    TAB = "tab"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    HOME = "home"
    END = "end"
    PAGE_UP = "pageup"
    PAGE_DOWN = "pagedown"
    CTRL_A = "ctrl-a"
    CTRL_C = "ctrl-c"
    CTRL_D = "ctrl-d"
    CTRL_E = "ctrl-e"
    CTRL_K = "ctrl-k"
    CTRL_L = "ctrl-l"
    CTRL_U = "ctrl-u"
    CTRL_W = "ctrl-w"
    SCROLL_UP = "scroll-up"
    SCROLL_DOWN = "scroll-down"


@dataclass(frozen=True, slots=True)
class Keypress:
    """Une touche décodée, prête à être traitée par l'application."""

    kind: KeyKind
    text: str = ""


# ── Panneaux ───────────────────────────────────────────────────────────


class PanelKind(StrEnum):
    """Panneau superposé actif dans le TUI."""

    NONE = "none"
    HELP = "help"
    SESSIONS = "sessions"
    AGENTS = "agents"
    MODELS = "models"
    PROVIDERS = "providers"
    TOOLS = "tools"
    APPROVALS = "approvals"
    STATUS = "status"
    PALETTE = "palette"


# ── Connexion ──────────────────────────────────────────────────────────


class ConnectionStatus(StrEnum):
    """État de la frontière HTTP vers le Core."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


# ── Contrats Core projetés ─────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Agent:
    """Agent Core (GET /v1/agents)."""

    id: str
    name: str
    description: str = ""
    model: str = ""
    provider: str = ""
    status: str = ""
    tool_ids: tuple[str, ...] = ()
    skill_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Model:
    """Modèle Core (GET /models)."""

    id: str
    name: str = ""
    provider: str = ""
    context_length: int = 0
    is_available: bool = True
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Provider:
    """Provider Core (GET /providers)."""

    id: str
    name: str = ""
    type: str = ""
    enabled: bool = False
    status: str = ""
    is_default: bool = False
    default_model: str = ""
    models: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Tool:
    """Outil Core (GET /v1/tools)."""

    id: str
    name: str = ""
    description: str = ""
    category: str = ""
    provider: str = ""
    risk_level: str = "low"
    is_available: bool = True
    parameters: dict[str, JSONValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChatSummary:
    """Conversation Core (GET /chats)."""

    id: str
    title: str = ""
    updated_at: str = ""
    created_at: str = ""
    message_count: int = 0


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Message Core (GET /chats/{id}/messages)."""

    id: str
    role: str
    content: str
    created_at: str = ""
    status: str = ""
    tool_calls: tuple[JSONValue, ...] = ()


@dataclass(frozen=True, slots=True)
class ApprovalItem:
    """Demande d'autorisation HROT/approbation Core.

    Couvre les deux contrats Core existants :
    ``GET /internal/approval/pending`` (ApprovalEngine) et
    ``GET /internal/hrot/pending`` (DurableHrotStore).
    """

    id: str
    kind: str  # "approval" | "hrot"
    title: str
    category: str = ""
    description: str = ""
    status: str = ""
    source: str = ""
    requester: str = ""
    expires_at: str = ""
    details: dict[str, JSONValue] = field(default_factory=dict)


# ── Événements de flux SSE ─────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ContentEvent:
    """Token de réponse (type ``content``)."""

    type: str
    chat_id: str | None
    content: str


@dataclass(frozen=True, slots=True)
class ContentReplaceEvent:
    """Remplacement autoritaire de la réponse (type ``content_replace``)."""

    type: str
    chat_id: str | None
    content: str


@dataclass(frozen=True, slots=True)
class ToolCallEvent:
    """Appel d'outil détecté par le Core (type ``tool_call``)."""

    type: str
    chat_id: str | None
    tool: str
    params: dict[str, JSONValue]


@dataclass(frozen=True, slots=True)
class ToolResultEvent:
    """Résultat d'outil (type ``tool_result``).

    ``status`` vient du Core : ``success``, ``failed``, ``timeout``,
    ``rejected``. Un ``rejected`` est une décision d'autorisation Core
    (PolicyEngine / SecureToolEnforcer) : le TUI l'affiche comme un refus
    HROT, jamais comme un succès.
    """

    type: str
    chat_id: str | None
    tool: str
    status: str
    output: str


@dataclass(frozen=True, slots=True)
class DoneEvent:
    """Fin de flux (type ``done``)."""

    type: str
    chat_id: str | None
    message_id: str | None


@dataclass(frozen=True, slots=True)
class ErrorEvent:
    """Erreur de génération (type ``error``)."""

    type: str
    error: str


@dataclass(frozen=True, slots=True)
class PermissionRequestEvent:
    """Demande d'autorisation HROT in-stream (type ``permission_request``)."""

    type: str
    chat_id: str | None
    request_id: str
    tool: str
    params: dict[str, JSONValue]
    reason: str
    timeout_seconds: int


@dataclass(frozen=True, slots=True)
class PermissionResolvedEvent:
    """Résolution d'une autorisation HROT in-stream (type ``permission_resolved``)."""

    type: str
    chat_id: str | None
    request_id: str
    tool: str
    approved: bool


StreamEvent: TypeAlias = Union[
    ContentEvent,
    ContentReplaceEvent,
    ToolCallEvent,
    ToolResultEvent,
    PermissionRequestEvent,
    PermissionResolvedEvent,
    DoneEvent,
    ErrorEvent,
]


@dataclass(frozen=True, slots=True)
class StreamError:
    """Erreur de transport survenue dans le thread de flux."""

    message: str
    exit_code: int = 1
    status: int | None = None


# ── État de conversation ───────────────────────────────────────────────


@dataclass(slots=True)
class ToolCallView:
    """Appel d'outil tel qu'affiché dans la conversation."""

    name: str
    params: str
    status: str | None = None
    output: str | None = None
    expanded: bool = False
    started_at: float = 0.0
    ended_at: float = 0.0


@dataclass(slots=True)
class Message:
    """Message affiché dans la conversation."""

    role: str  # "user" | "assistant" | "system"
    content: str = ""
    tool_calls: list[ToolCallView] = field(default_factory=list)
    status: str = ""  # "pending" | "done" | "error" | "stopped" | ""
    chat_id: str | None = None
    message_id: str | None = None
    metadata: dict[str, JSONValue] = field(default_factory=dict)
    _version: int = field(default=0, repr=False)
    _rendered: list[object] = field(default_factory=list, repr=False)
    _rendered_version: int = field(default=-1, repr=False)

    def touch(self) -> None:
        """Invalide le cache de rendu après une mutation."""
        self._version += 1


__all__ = [
    "ApprovalItem",
    "Agent",
    "ChatMessage",
    "ChatSummary",
    "ConnectionStatus",
    "ContentEvent",
    "ContentReplaceEvent",
    "DoneEvent",
    "ErrorEvent",
    "PermissionRequestEvent",
    "PermissionResolvedEvent",
    "JSONScalar",
    "JSONValue",
    "KeyKind",
    "Keypress",
    "Message",
    "Model",
    "Provider",
    "StreamError",
    "StreamEvent",
    "Tool",
    "ToolCallEvent",
    "ToolCallView",
    "ToolResultEvent",
]
