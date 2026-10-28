"""ETHAN Core — Agent Trace Archiver.

Collecte, normalise et archive les conversations des agents IA
(Cline, Codex, Copilot, etc.) en fichiers Markdown portables.
"""

from core.knowledge.agent_traces.cline_connector import ClineConnector
from core.knowledge.agent_traces.codex_connector import CodexConnector
from core.knowledge.agent_traces.copilot_connector import CopilotConnector
from core.knowledge.agent_traces.normalizer import session_to_markdown
from core.knowledge.agent_traces.sync_engine import SyncEngine
from core.knowledge.agent_traces.types import (
    AgentType,
    ArchivedMessage,
    ArchivedSession,
    MessageType,
    SessionStatus,
    filter_secrets,
)

__all__ = [
    "AgentType",
    "ArchivedMessage",
    "ArchivedSession",
    "ClineConnector",
    "CodexConnector",
    "CopilotConnector",
    "MessageType",
    "SessionStatus",
    "SyncEngine",
    "filter_secrets",
    "session_to_markdown",
]
