"""Types et utilitaires pour l'archivage des traces d'agents."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class AgentType(str, Enum):
    CLINE = "cline"
    CODEX = "codex"
    COPILOT = "copilot"
    CHATGPT = "chatgpt"
    UNKNOWN = "unknown"


class SessionStatus(str, Enum):
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"
    COMPACTED = "compacted"
    INCOMPLETE_METADATA = "incomplete_metadata"
    SKIPPED = "skipped"


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"
    CHECKPOINT = "checkpoint"
    COMPACTION = "compaction"


@dataclass
class ArchivedMessage:
    role: str
    content: str
    message_type: MessageType = MessageType.USER
    timestamp: datetime | None = None
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_result: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "tool_result": self.tool_result,
            "metadata": self.metadata,
        }



@dataclass
class ArchivedSession:
    session_id: str
    agent: AgentType
    agent_version: str = ""
    session_type: str = "task"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model: str = ""
    model_provider: str = ""
    mode: str = ""
    cwd: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    total_cost: float = 0.0
    files_in_context: int = 0
    status: SessionStatus = SessionStatus.COMPLETED
    messages: list[ArchivedMessage] = field(default_factory=list)
    files_modified: list[dict[str, Any]] = field(default_factory=list)
    checksum: str = ""
    raw_source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def compute_checksum(self) -> str:
        content = json.dumps(
            {
                "session_id": self.session_id,
                "agent": self.agent.value,
                "messages": [m.to_dict() for m in self.messages],
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent": self.agent.value,
            "agent_version": self.agent_version,
            "session_type": self.session_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "model": self.model,
            "model_provider": self.model_provider,
            "mode": self.mode,
            "cwd": self.cwd,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "total_cost": self.total_cost,
            "files_in_context": self.files_in_context,
            "status": self.status.value,
            "messages": [m.to_dict() for m in self.messages],
            "files_modified": self.files_modified,
            "checksum": self.checksum or self.compute_checksum(),
            "raw_source": self.raw_source,
            "metadata": self.metadata,
        }



# ── Secret filtering ──────────────────────────────────────────────────────

SECRET_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "[REDACTED:OPENAI_KEY]"),
    (re.compile(r"sk-ant-[a-zA-Z0-9-]{20,}"), "[REDACTED:ANTHROPIC_KEY]"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "[REDACTED:GITHUB_TOKEN]"),
    (re.compile(r"glpat-[a-zA-Z0-9-]{20}"), "[REDACTED:GITLAB_TOKEN]"),
    (re.compile(r"://[^:]+:[^@]+@"), "://[REDACTED:PASSWORD]@"),
    (re.compile(r"(?i)(PASSWORD|SECRET|TOKEN|API_KEY)\s*=\s*\S+"), "[REDACTED:ENV_VAR]"),
    (re.compile(r"-----BEGIN .* PRIVATE KEY-----"), "[REDACTED:PRIVATE_KEY]"),
    (re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"), "[REDACTED:JWT]"),
]


def filter_secrets(text: str) -> tuple[str, list[str]]:
    """Filtre les secrets dans un texte."""
    detected = []
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        if pattern.search(result):
            detected.append(replacement)
            result = pattern.sub(replacement, result)
    return result, detected


def _parse_timestamp(ts: Any) -> datetime | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        if ts > 1e12:
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _safe_read_json(path: Path) -> Any | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


def _safe_read_jsonl(path: Path) -> list[dict[str, Any]]:
    results = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except (OSError, UnicodeDecodeError):
        pass
    return results
