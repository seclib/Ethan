"""Tests for cli/core/logging.py — structured logging."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestLog:
    """log() function tests."""

    def test_log_writes_entry(self) -> None:
        from cli.core.logging import log, LOG_FILE
        log("test_cmd", "ok", 42)
        with open(LOG_FILE) as f:
            entries = json.load(f)
        assert len(entries) == 1
        assert entries[0]["command"] == "test_cmd"

    def test_log_includes_timestamp(self) -> None:
        from cli.core.logging import log, LOG_FILE
        log("cmd", "ok", 0)
        with open(LOG_FILE) as f:
            entries = json.load(f)
        assert "ts" in entries[0]

    def test_log_with_error(self) -> None:
        from cli.core.logging import log, LOG_FILE
        log("cmd", "error", 0, "something broke")
        with open(LOG_FILE) as f:
            entries = json.load(f)
        assert entries[0]["error"] == "something broke"

    def test_log_increments(self) -> None:
        from cli.core.logging import log, LOG_FILE
        log("cmd1", "ok", 10)
        log("cmd2", "ok", 20)
        with open(LOG_FILE) as f:
            entries = json.load(f)
        assert len(entries) == 2

    def test_log_truncates_long_error(self) -> None:
        from cli.core.logging import log, LOG_FILE
        log("cmd", "error", 0, "x" * 500)
        with open(LOG_FILE) as f:
            entries = json.load(f)
        assert len(entries[0]["error"]) <= 200


class TestQuery:
    """Query function tests."""

    def test_query_last(self) -> None:
        from cli.core.logging import log, query_last
        log("cmd1", "ok", 10)
        log("cmd2", "ok", 20)
        log("cmd3", "ok", 30)
        entries = query_last(2)
        assert len(entries) == 2
        assert entries[-1]["command"] == "cmd3"

    def test_query_last_more_than_available(self) -> None:
        from cli.core.logging import log, query_last
        log("cmd", "ok", 10)
        entries = query_last(100)
        assert len(entries) == 1

    def test_query_errors(self) -> None:
        from cli.core.logging import log, query_errors
        log("ok_cmd", "ok", 10)
        log("err_cmd", "error", 0, "fail")
        errors = query_errors()
        assert len(errors) == 1
        assert errors[0]["command"] == "err_cmd"

    def test_query_errors_filters_ok(self) -> None:
        from cli.core.logging import log, query_errors
        log("cmd", "ok", 10)
        errors = query_errors()
        assert len(errors) == 0

    def test_query_text(self) -> None:
        from cli.core.logging import log, query_text
        log("build_cmd", "ok", 10)
        log("deploy_cmd", "ok", 20)
        results = query_text("build")
        assert len(results) == 1
        assert results[0]["command"] == "build_cmd"

    def test_query_text_no_match(self) -> None:
        from cli.core.logging import log, query_text
        log("build_cmd", "ok", 10)
        results = query_text("nonexistent")
        assert len(results) == 0


class TestMaxEntries:
    """MAX_ENTRIES cap tests."""

    def test_max_entries_cap(self) -> None:
        from cli.core.logging import log, LOG_FILE, MAX_ENTRIES
        for i in range(MAX_ENTRIES + 50):
            log(f"cmd_{i}", "ok", i)
        with open(LOG_FILE) as f:
            entries = json.load(f)
        assert len(entries) <= MAX_ENTRIES

    def test_max_entries_keeps_recent(self) -> None:
        """After cap, most recent entries should be kept."""
        from cli.core.logging import log, LOG_FILE, MAX_ENTRIES
        for i in range(MAX_ENTRIES + 10):
            log(f"cmd_{i}", "ok", i)
        with open(LOG_FILE) as f:
            entries = json.load(f)
        assert "cmd_0" not in [e["command"] for e in entries]


class TestFileHandling:
    """File error handling tests."""

    def test_corrupt_file_fallback(self) -> None:
        from cli.core.logging import LOG_FILE, _load, _ensure
        _ensure()
        with open(LOG_FILE, "w") as f:
            f.write("not json")
        entries = _load()
        assert entries == []