"""Tests pour le module d'archivage des traces d'agents — partie 1."""

import json
import tempfile
from pathlib import Path

import pytest

from core.knowledge.agent_traces import (
    AgentType,
    ArchivedMessage,
    ArchivedSession,
    MessageType,
    SessionStatus,
    filter_secrets,
    session_to_markdown,
)


class TestSecretFiltering:
    def test_openai_key_redacted(self):
        text = "ma clé est sk-abcdefghijklmnopqrstuvwxyz123456"
        result, detected = filter_secrets(text)
        assert "[REDACTED:OPENAI_KEY]" in result
        assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in result

    def test_anthropic_key_redacted(self):
        text = "clé anthropic: sk-ant-api03-abcdefghijklmnopqrstuvwxyz"
        result, detected = filter_secrets(text)
        assert "[REDACTED:ANTHROPIC_KEY]" in result

    def test_github_token_redacted(self):
        text = "token: ghp_abcdefghijklmnopqrstuvwxyz1234567890AB"
        result, detected = filter_secrets(text)
        assert "[REDACTED:GITHUB_TOKEN]" in result

    def test_jwt_redacted(self):
        text = "jwt: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result, detected = filter_secrets(text)
        assert "[REDACTED:JWT]" in result

    def test_no_secrets_unchanged(self):
        text = "ceci est un texte normal sans secret"
        result, detected = filter_secrets(text)
        assert result == text
        assert detected == []

    def test_env_var_redacted(self):
        text = "PASSWORD=monmotdepasse123"
        result, detected = filter_secrets(text)
        assert "[REDACTED:ENV_VAR]" in result


class TestTypes:
    def test_archived_session_checksum(self):
        session = ArchivedSession(
            session_id="test-123",
            agent=AgentType.CLINE,
            messages=[
                ArchivedMessage(role="user", content="Hello"),
                ArchivedMessage(role="assistant", content="Hi"),
            ],
        )
        checksum = session.compute_checksum()
        assert len(checksum) == 64
        assert session.compute_checksum() == checksum

    def test_archived_session_to_dict(self):
        session = ArchivedSession(
            session_id="test-456",
            agent=AgentType.CODEX,
            model="gpt-4",
        )
        d = session.to_dict()
        assert d["session_id"] == "test-456"
        assert d["agent"] == "codex"
        assert d["model"] == "gpt-4"
class TestNormalizer:
    def test_session_to_markdown_basic(self):
        session = ArchivedSession(
            session_id="test-789",
            agent=AgentType.CLINE,
            agent_version="4.1.26",
            model="deepseek/deepseek-v4-flash",
            model_provider="cline",
            status=SessionStatus.COMPLETED,
            messages=[
                ArchivedMessage(role="user", content="Hello"),
                ArchivedMessage(role="assistant", content="Hi there"),
            ],
        )
        session.checksum = session.compute_checksum()
        md = session_to_markdown(session)
        assert "---" in md
        assert 'id: "test-789"' in md
        assert "Hello" in md
        assert "Hi there" in md
        assert "## Conversation" in md

    def test_session_to_markdown_with_secrets(self):
        session = ArchivedSession(
            session_id="test-secret",
            agent=AgentType.CLINE,
            messages=[
                ArchivedMessage(role="user", content="ma clé est sk-abcdefghijklmnopqrstuvwxyz123456"),
            ],
        )
        session.checksum = session.compute_checksum()
        md = session_to_markdown(session)
        assert "[REDACTED:OPENAI_KEY]" in md
        assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in md

    def test_session_to_markdown_tool_call(self):
        session = ArchivedSession(
            session_id="test-tool",
            agent=AgentType.COPILOT,
            messages=[
                ArchivedMessage(
                    role="assistant",
                    content="[Tool Call: read_file]",
                    message_type=MessageType.TOOL_CALL,
                    tool_name="read_file",
                    tool_args={"path": "test.py"},
                ),
            ],
        )
        session.checksum = session.compute_checksum()
        md = session_to_markdown(session)
        assert "read_file" in md
        assert "Tool Call" in md

        session = ArchivedSession(
            session_id="test-456",
            agent=AgentType.CODEX,
            model="gpt-4",
        )
        d = session.to_dict()
        assert d["session_id"] == "test-456"
        assert d["agent"] == "codex"
        assert d["model"] == "gpt-4"

    def test_message_to_dict(self):
        msg = ArchivedMessage(
            role="user",
            content="test",
            message_type=MessageType.USER,
        )
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "test"

class TestDeduplication:
    def test_duplicate_detection(self, tmp_path):
        from core.knowledge.agent_traces import SyncEngine
        engine = SyncEngine(knowledge_root=tmp_path / "kb")
        from core.knowledge.agent_traces import ArchivedSession, ArchivedMessage
        session = ArchivedSession(
            session_id="dup-test",
            agent=AgentType.CLINE,
            messages=[ArchivedMessage(role="user", content="test")],
        )
        session.checksum = session.compute_checksum()

        sync_state = engine._load_sync_state()
        session_key = f"{session.agent.value}:{session.session_id}"
        sync_state.setdefault("sessions", {})[session_key] = {
            "checksum": session.checksum,
            "path": "sessions/cline/2026-01-01/dup-test.md",
            "synced_at": "2026-01-01T00:00:00",
            "status": "completed",
        }
        engine._save_sync_state(sync_state)

        assert engine._is_duplicate(session, engine._load_sync_state()) is True

    def test_non_duplicate_detection(self, tmp_path):
        from core.knowledge.agent_traces import SyncEngine
        engine = SyncEngine(knowledge_root=tmp_path / "kb")
        from core.knowledge.agent_traces import ArchivedSession, ArchivedMessage
        session = ArchivedSession(
            session_id="new-test",
            agent=AgentType.CLINE,
            messages=[ArchivedMessage(role="user", content="new content")],
        )
        session.checksum = session.compute_checksum()

        sync_state = engine._load_sync_state()

class TestConnectors:
    def test_cline_unavailable(self):
        from core.knowledge.agent_traces import ClineConnector
        from pathlib import Path
        connector = ClineConnector(base_path=Path("/nonexistent/path"))
        assert connector.is_available() is False
        assert connector.list_sessions() == []
        assert connector.collect_session("123") is None

    def test_codex_unavailable(self):
        from core.knowledge.agent_traces import CodexConnector
        from pathlib import Path
        connector = CodexConnector(base_path=Path("/nonexistent/path"))
        assert connector.is_available() is False
        assert connector.list_sessions() == []
        assert connector.collect_session(Path("/nonexistent/path/session.jsonl")) is None

    def test_copilot_unavailable(self):
        from core.knowledge.agent_traces import CopilotConnector

class TestClineSyntheticParsing:
    def test_parse_synthetic_cline_session(self, tmp_path):
        import json
        from core.knowledge.agent_traces import ClineConnector
        base = tmp_path / "cline"
        tasks_dir = base / "tasks" / "12345"
        tasks_dir.mkdir(parents=True)
        (base / "state").mkdir(parents=True)

        ui_messages = [
            {"ts": 1700000000000, "type": "say", "say": "task", "text": "Hello"},
            {"ts": 1700000001000, "type": "say", "say": "text", "text": "Hi there"},
        ]
        with open(tasks_dir / "ui_messages.json", "w") as f:
            json.dump(ui_messages, f)

        task_metadata = {
            "files_in_context": [],
            "model_usage": [{"model_id": "test-model", "model_provider_id": "test", "mode": "act"}],
            "environment_history": [{"cline_version": "4.1.26"}],
        }
        with open(tasks_dir / "task_metadata.json", "w") as f:
            json.dump(task_metadata, f)

        task_history = [{"id": "12345", "ts": 1700000000000, "tokensIn": 100, "tokensOut": 50, "totalCost": 0.01, "cwdOnTaskInitialization": "/tmp"}]
        with open(base / "state" / "taskHistory.json", "w") as f:
            json.dump(task_history, f)

        connector = ClineConnector(base_path=base)
        assert connector.is_available()
        assert "12345" in connector.list_sessions()

        session = connector.collect_session("12345")
        assert session is not None
        assert session.agent == AgentType.CLINE
        assert session.model == "test-model"
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"
        assert session.tokens_in == 100
        assert session.status == SessionStatus.COMPLETED


class TestCodexSyntheticParsing:
    def test_parse_synthetic_codex_session(self, tmp_path):
        import json
        from core.knowledge.agent_traces import CodexConnector
        base = tmp_path / "codex"
        sessions_dir = base / "sessions" / "2026" / "01" / "01"
        sessions_dir.mkdir(parents=True)

        lines = [
            {"timestamp": "2026-01-01T00:00:00Z", "ordinal": 0, "type": "session_meta", "payload": {"session_id": "codex-123", "cwd": "/tmp", "cli_version": "0.1.0", "model_provider": "openai", "timestamp": "2026-01-01T00:00:00Z"}},
            {"timestamp": "2026-01-01T00:00:01Z", "ordinal": 1, "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Hello"}]}},
            {"timestamp": "2026-01-01T00:00:02Z", "ordinal": 2, "type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Hi"}]}},
        ]
        session_file = sessions_dir / "rollout-2026-01-01T00-00-00-codex-123.jsonl"
        with open(session_file, "w") as f:
            for line in lines:
                f.write(json.dumps(line) + "\n")

        connector = CodexConnector(base_path=base)
        assert connector.is_available()
        sessions = connector.list_sessions()
        assert len(sessions) == 1

        session = connector.collect_session(sessions[0])
        assert session is not None
        assert session.agent == AgentType.CODEX
        assert session.session_id == "codex-123"
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"


class TestCopilotSyntheticParsing:
    def test_parse_synthetic_copilot_session(self, tmp_path):
        import json
        from core.knowledge.agent_traces import CopilotConnector
        base = tmp_path / "copilot"
        session_dir = base / "session-abc"
        session_dir.mkdir(parents=True)

        events = [
            {"type": "session.start", "data": {"sessionId": "session-abc", "startTime": "2026-01-01T00:00:00Z", "selectedModel": "gpt-4", "context": {"cwd": "/tmp"}, "copilotVersion": "1.0"}, "timestamp": "2026-01-01T00:00:00Z"},
            {"type": "user.message", "data": {"content": "Hello"}, "timestamp": "2026-01-01T00:00:01Z"},
            {"type": "assistant.message", "data": {"content": "Hi there"}, "timestamp": "2026-01-01T00:00:02Z"},
        ]
        with open(session_dir / "events.jsonl", "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

        connector = CopilotConnector(base_path=base)
        assert connector.is_available()
        sessions = connector.list_sessions()
        assert len(sessions) == 1

        session = connector.collect_session(sessions[0])
        assert session is not None
        assert session.agent == AgentType.COPILOT
        assert session.model == "gpt-4"
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"
        assert session.status == SessionStatus.COMPLETED

        from pathlib import Path
        connector = CopilotConnector(base_path=Path("/nonexistent/path"))
        assert connector.is_available() is False
        assert connector.list_sessions() == []
        assert connector.collect_session(Path("/nonexistent/path")) is None
