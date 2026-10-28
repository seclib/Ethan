"""Connecteur Codex pour l'archivage des traces d'agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.knowledge.agent_traces.types import (
    AgentType,
    ArchivedMessage,
    ArchivedSession,
    MessageType,
    SessionStatus,
    _parse_timestamp,
    _safe_read_jsonl,
)


class CodexConnector:
    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or Path.home() / ".codex"

    def is_available(self) -> bool:
        return self.base_path.exists() and (self.base_path / "sessions").exists()

    def list_sessions(self) -> list[Path]:
        sessions_dir = self.base_path / "sessions"
        if not sessions_dir.exists():
            return []
        return sorted(sessions_dir.rglob("rollout-*.jsonl"))

    def collect_session(self, session_path: Path) -> ArchivedSession | None:
        lines = _safe_read_jsonl(session_path)
        if not lines:
            return None

        session = ArchivedSession(
            session_id=session_path.stem.replace("rollout-", ""),
            agent=AgentType.CODEX,
            raw_source=f"raw/codex/sessions/{session_path.relative_to(self.base_path)}",
        )

        for line in lines:
            if line.get("type") == "session_meta":
                payload = line.get("payload", {})
                session.session_id = payload.get("session_id", session.session_id)
                session.cwd = payload.get("cwd", "")
                session.agent_version = payload.get("cli_version", "")
                session.model_provider = payload.get("model_provider", "")
                session.created_at = _parse_timestamp(payload.get("timestamp"))
                break

        for line in lines:
            msg_type = line.get("type", "")
            payload = line.get("payload", {})
            ts = _parse_timestamp(line.get("timestamp"))

            if msg_type == "response_item":
                payload_type = payload.get("type", "")
                if payload_type == "message":
                    role = payload.get("role", "")
                    if role in ("user", "assistant", "developer"):
                        content = payload.get("content", "")
                        if isinstance(content, list):
                            content = "\n".join(
                                c.get("text", "") if isinstance(c, dict) else str(c)
                                for c in content
                            )
                        if role == "developer":
                            role = "system"
                        session.messages.append(ArchivedMessage(
                            role=role,
                            content=content,
                            message_type=MessageType.USER if role == "user" else (MessageType.ASSISTANT if role == "assistant" else MessageType.SYSTEM),
                            timestamp=ts,
                            metadata={"ordinal": line.get("ordinal")},
                        ))
                elif payload_type == "custom_tool_call":
                    session.messages.append(ArchivedMessage(
                        role="assistant",
                        content=f"[Tool Call: {payload.get('name', 'unknown')}]",
                        message_type=MessageType.TOOL_CALL,
                        timestamp=ts,
                        tool_name=payload.get("name"),
                        tool_args=payload.get("input"),
                        metadata={"ordinal": line.get("ordinal")},
                    ))
                elif payload_type == "custom_tool_call_output":
                    session.messages.append(ArchivedMessage(
                        role="tool",
                        content=str(payload.get("output", "")),
                        message_type=MessageType.TOOL_RESULT,
                        timestamp=ts,
                        tool_result=str(payload.get("output", "")),
                        metadata={"ordinal": line.get("ordinal")},
                    ))
            elif msg_type == "event_msg":
                # Could contain additional events, skip for now
                pass

        index_path = self.base_path / "session_index.jsonl"
        if index_path.exists():
            for entry in _safe_read_jsonl(index_path):
                if entry.get("id") == session.session_id:
                    session.metadata["thread_name"] = entry.get("thread_name", "")
                    session.updated_at = _parse_timestamp(entry.get("updated_at"))
                    break

        if not session.messages:
            session.status = SessionStatus.SKIPPED
        else:
            session.status = SessionStatus.COMPLETED

        session.checksum = session.compute_checksum()
        return session
