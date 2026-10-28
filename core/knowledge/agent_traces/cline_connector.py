"""Connecteur Cline pour l'archivage des traces d'agents."""

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
)


class ClineConnector:
    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev"

    def is_available(self) -> bool:
        return self.base_path.exists() and (self.base_path / "tasks").exists()

    def list_sessions(self) -> list[str]:
        tasks_dir = self.base_path / "tasks"
        if not tasks_dir.exists():
            return []
        return sorted(d.name for d in tasks_dir.iterdir() if d.is_dir())

    def collect_session(self, session_id: str) -> ArchivedSession | None:
        task_dir = self.base_path / "tasks" / session_id
        if not task_dir.exists():
            return None

        session = ArchivedSession(
            session_id=session_id,
            agent=AgentType.CLINE,
            raw_source=f"raw/cline/tasks/{session_id}/",
        )

        metadata = _safe_read_json(task_dir / "task_metadata.json")
        if metadata:
            session.metadata = metadata
            if "environment_history" in metadata and metadata["environment_history"]:
                env = metadata["environment_history"][0]
                session.agent_version = env.get("cline_version", "")
            if "model_usage" in metadata and metadata["model_usage"]:
                model = metadata["model_usage"][0]
                session.model = model.get("model_id", "")
                session.model_provider = model.get("model_provider_id", "")
                session.mode = model.get("mode", "")
            if "files_in_context" in metadata:
                session.files_in_context = len(metadata["files_in_context"])
                session.files_modified = [
                    {"path": f["path"], "state": f["record_state"], "source": f["record_source"]}
                    for f in metadata["files_in_context"]
                ]

        task_history = _safe_read_json(self.base_path / "state" / "taskHistory.json")
        if task_history:
            for entry in task_history:
                if entry.get("id") == session_id:
                    session.created_at = _parse_timestamp(entry.get("ts"))
                    session.tokens_in = entry.get("tokensIn", 0)
                    session.tokens_out = entry.get("tokensOut", 0)
                    session.total_cost = entry.get("totalCost", 0.0)
                    session.cwd = entry.get("cwdOnTaskInitialization", "")
                    break

        ui_messages = _safe_read_json(task_dir / "ui_messages.json")
        if ui_messages:
            for msg in ui_messages:
                archived_msg = self._parse_ui_message(msg)
                if archived_msg:
                    session.messages.append(archived_msg)

        if not session.messages:
            session.status = SessionStatus.SKIPPED
        elif session.messages and session.messages[-1].role == "user":
            session.status = SessionStatus.INTERRUPTED
        else:
            session.status = SessionStatus.COMPLETED

        session.checksum = session.compute_checksum()
        return session

    def _parse_ui_message(self, msg: dict[str, Any]) -> ArchivedMessage | None:
        msg_type = msg.get("type", "")
        say = msg.get("say", "")
        text = msg.get("text", "")
        ts = _parse_timestamp(msg.get("ts"))

        if msg_type != "say":
            return None

        if say == "task":
            return ArchivedMessage(role="user", content=text, message_type=MessageType.USER, timestamp=ts, metadata={"say": say})
        elif say in ("text", "completion_result"):
            return ArchivedMessage(role="assistant", content=text, message_type=MessageType.ASSISTANT, timestamp=ts, metadata={"say": say})
        elif say == "api_req_started":
            return ArchivedMessage(role="system", content="[API Request Started]", message_type=MessageType.SYSTEM, timestamp=ts, metadata={"say": say})
        elif say == "checkpoint_created":
            return ArchivedMessage(role="system", content="[Checkpoint Created]", message_type=MessageType.CHECKPOINT, timestamp=ts, metadata={"say": say, "hash": msg.get("lastCheckpointHash")})
        elif say == "tool":
            return ArchivedMessage(role="assistant", content=text, message_type=MessageType.TOOL_CALL, timestamp=ts, metadata={"say": say})
        elif text:
            return ArchivedMessage(role="assistant", content=text, message_type=MessageType.ASSISTANT, timestamp=ts, metadata={"say": say})
        return None
