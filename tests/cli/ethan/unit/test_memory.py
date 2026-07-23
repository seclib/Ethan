"""Tests for cli/core/memory.py — local memory & sessions."""
from __future__ import annotations

import json

import pytest


class TestMemoryStore:
    """Memory storage tests."""

    def test_record_stores_entry(self) -> None:
        from cli.core.memory import record, MEM_FILE
        record("user", "Hello")
        with open(MEM_FILE) as f:
            entries = json.load(f)
        assert len(entries) == 1
        assert entries[0]["text"] == "Hello"

    def test_record_truncates_long_text(self) -> None:
        from cli.core.memory import record, MAX_TEXT
        long_text = "x" * (MAX_TEXT + 100)
        record("user", long_text)
        from cli.core.memory import recent
        entries = recent()
        assert len(entries[0]["text"]) <= MAX_TEXT

    def test_record_with_session(self) -> None:
        from cli.core.memory import record
        record("user", "Hello", session_id="session-1")
        from cli.core.memory import recent
        entries = recent()
        assert entries[0].get("session") == "session-1"

    def test_recent_ordering(self) -> None:
        from cli.core.memory import record, recent
        record("user", "first")
        record("user", "second")
        entries = recent(2)
        assert entries[-1]["text"] == "second"

    def test_recent_limit(self) -> None:
        from cli.core.memory import record, recent
        record("user", "a")
        record("user", "b")
        record("user", "c")
        entries = recent(2)
        assert len(entries) == 2

    def test_frequent_counts(self) -> None:
        from cli.core.memory import record, frequent
        for _ in range(3):
            record("user", "common")
        record("user", "rare")
        freq = frequent(5)
        common_entry = [e for e in freq if e["text"] == "common"]
        assert len(common_entry) == 1
        assert common_entry[0]["count"] >= 3


class TestMemorySuggest:
    """Suggestion tests."""

    def test_suggest_prefix_match(self) -> None:
        from cli.core.memory import record, suggest_prefix
        record("user", "hello world")
        record("user", "help me")
        record("user", "goodbye")
        suggestions = suggest_prefix("hel")
        assert "hello world" in suggestions
        assert "help me" in suggestions

    def test_suggest_prefix_no_match(self) -> None:
        from cli.core.memory import record, suggest_prefix
        record("user", "hello")
        suggestions = suggest_prefix("xyz")
        assert len(suggestions) == 0

    def test_suggest_prefix_empty_history(self) -> None:
        from cli.core.memory import suggest_prefix
        suggestions = suggest_prefix("test")
        assert suggestions == []

    def test_suggest_prefix_max_results(self) -> None:
        from cli.core.memory import record, suggest_prefix
        for i in range(10):
            record("user", f"test_{i}")
        suggestions = suggest_prefix("test", n=3)
        assert len(suggestions) == 3


class TestSessions:
    """Session management tests."""

    def test_new_session_creates_id(self) -> None:
        from cli.core.memory import new_session
        session_id = new_session()
        assert len(session_id) > 0

    def test_new_session_saves_to_file(self) -> None:
        from cli.core.memory import new_session, SESSION_FILE
        session_id = new_session()
        with open(SESSION_FILE) as f:
            saved = f.read().strip()
        assert saved == session_id

    def test_resume_existing_session(self) -> None:
        from cli.core.memory import new_session, resume_session, save_session
        session_id = new_session()
        resumed = resume_session()
        assert resumed == session_id

    def test_resume_missing_creates_new(self) -> None:
        from cli.core.memory import resume_session
        import os
        # Ensure no session file
        try:
            os.remove("tests/cli/ethan/unit/test.session.txt")
        except FileNotFoundError:
            pass
        with pytest.MonkeyPatch().context() as m:
            m.setattr("cli.core.memory.SESSION_FILE", "tests/cli/ethan/unit/test.session.txt")
            session_id = resume_session()
            assert len(session_id) > 0

    def test_save_session(self) -> None:
        from cli.core.memory import save_session, SESSION_FILE
        save_session("test-session-id")
        with open(SESSION_FILE) as f:
            saved = f.read().strip()
        assert saved == "test-session-id"

    def test_get_history(self) -> None:
        from cli.core.memory import record, get_history
        record("user", "msg1", session_id="s-1")
        record("user", "msg2", session_id="s-1")
        record("user", "other", session_id="s-2")
        history = get_history("s-1")
        assert len(history) == 2
        assert history[0]["text"] == "msg1"

    def test_get_history_limit(self) -> None:
        from cli.core.memory import record, get_history
        for i in range(20):
            record("user", f"msg_{i}", session_id="s-1")
        history = get_history("s-1", limit=5)
        assert len(history) == 5


class TestSessionInfo:
    """Session information tests."""

    def test_get_session_info(self) -> None:
        from cli.core.memory import record, get_session_info
        record("user", "first", session_id="s-1")
        info = get_session_info("s-1")
        assert "short_id" in info
        assert "message_count" in info
        assert info["message_count"] == 1

    def test_get_context_usage(self) -> None:
        from cli.core.memory import record, get_context_usage
        record("user", "msg", session_id="s-1")
        used, max_tokens = get_context_usage("s-1")
        assert used > 0
        assert max_tokens > 0

    def test_reset_context(self) -> None:
        from cli.core.memory import record, reset_context, get_history
        record("user", "msg", session_id="s-1")
        reset_context("s-1")
        history = get_history("s-1")
        assert len(history) == 0


class TestMaxEntries:
    """MAX_ENTRIES cap test."""

    def test_max_entries(self) -> None:
        from cli.core.memory import record, recent, MAX_ENTRIES
        for i in range(MAX_ENTRIES + 50):
            record("user", f"msg_{i}")
        entries = recent(MAX_ENTRIES + 100)
        assert len(entries) <= MAX_ENTRIES