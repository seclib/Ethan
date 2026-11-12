"""Connecteur Copilot pour l'archivage des traces d'agents."""

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
    _safe_read_json,
    _safe_read_jsonl,
)


class CopilotConnector:
    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or Path.home() / ".copilot" / "session-state"

    def is_available(self) -> bool:
        return self.base_path.exists()

    def list_sessions(self) -> list[Path]:
        if not self.base_path.exists():
            return []
        return sorted(d for d in self.base_path.iterdir() if d.is_dir())

    def collect_session(self, session_dir: Path) -> ArchivedSession | None:
        events_path = session_dir / "events.jsonl"
        if not events_path.exists():
            return None

        events = _safe_read_jsonl(events_path)
        if not events:
            return None

        session = ArchivedSession(
            session_id=session_dir.name,
            agent=AgentType.COPILOT,
            raw_source=f"raw/copilot/session-state/{session_dir.name}/",
        )

        for event in events:
            if event.get("type") == "session.start":
                data = event.get("data", {})
                session.created_at = _parse_timestamp(data.get("startTime"))
                session.model = data.get("selectedModel", "")
                ctx = data.get("context", {})
                session.cwd = ctx.get("cwd", "")
                session.agent_version = data.get("copilotVersion", "")
                break

        for event in events:
            event_type = event.get("type", "")
            data = event.get("data", {})
            ts = _parse_timestamp(event.get("timestamp"))

            if event_type == "user.message":
                session.messages.append(ArchivedMessage(
                    role="user",
                    content=data.get("content", ""),
                    message_type=MessageType.USER,
                    timestamp=ts,
                ))
            elif event_type == "assistant.message":
                content = data.get("content", "")
                tool_calls = data.get("tool_calls", [])
                if tool_calls:
                    for tc in tool_calls:
                        session.messages.append(ArchivedMessage(
                            role="assistant",
                            content=f"[Tool Call: {tc.get('name', 'unknown')}]",
                            message_type=MessageType.TOOL_CALL,
                            timestamp=ts,
                            tool_name=tc.get("name"),
                            tool_args=tc.get("arguments"),
                        ))
                if content:
                    session.messages.append(ArchivedMessage(
                        role="assistant",
                        content=content,
                        message_type=MessageType.ASSISTANT,
                        timestamp=ts,
                    ))
            elif event_type == "tool.execution_complete":
                session.messages.append(ArchivedMessage(
                    role="tool",
                    content=str(data.get("result", "")),
                    message_type=MessageType.TOOL_RESULT,
                    timestamp=ts,
                    tool_name=data.get("tool_name"),
                    tool_result=str(data.get("result", "")),
                ))
            elif event_type == "session.compaction":
                session.messages.append(ArchivedMessage(
                    role="system",
                    content=data.get("summary", "[Conversation compacted]"),
                    message_type=MessageType.COMPACTION,
                    timestamp=ts,
                ))
                session.status = SessionStatus.COMPACTED

        workspace_path = session_dir / "workspace.yaml"
        if workspace_path.exists():
            try:
                import yaml
                with open(workspace_path) as f:
                    ws = yaml.safe_load(f)
                if ws:
                    session.metadata["workspace"] = ws
            except Exception:
                pass

        vscode_meta = _safe_read_json(session_dir / "vscode.metadata.json")
        if vscode_meta:
            session.metadata["vscode"] = vscode_meta

        if not session.messages:
            session.status = SessionStatus.SKIPPED
        elif session.status != SessionStatus.COMPACTED:
            session.status = SessionStatus.COMPLETED

        session.checksum = session.compute_checksum()
        return session
