"""Tests for cli/commands/logs.py — ethan logs command."""
from __future__ import annotations

from unittest import mock

import pytest


class TestLogsCommand:
    """cmd_logs/ethan logs tests."""

    def test_logs_default(self, capsys) -> None:
        from cli.commands.logs import cmd_logs
        with mock.patch("cli.commands.logs.logs.query_last", return_value=[
            {"ts": "2024-01-01", "command": "chat", "status": "ok", "latency_ms": 42}
        ]):
            result = cmd_logs([])
            captured = capsys.readouterr()
            assert result == 0
            assert "chat" in captured.out
            assert "ok" in captured.out

    def test_logs_last_flag(self, capsys) -> None:
        from cli.commands.logs import cmd_logs
        with mock.patch("cli.commands.logs.logs.query_last", return_value=[
            {"ts": "2024-01-01", "command": "cmd", "status": "ok", "latency_ms": 10}
        ]):
            result = cmd_logs(["--last", "1"])
            captured = capsys.readouterr()
            assert result == 0

    def test_logs_last_default_count(self, capsys) -> None:
        from cli.commands.logs import cmd_logs
        with mock.patch("cli.commands.logs.logs.query_last", return_value=[]):
            result = cmd_logs(["--last"])
            captured = capsys.readouterr()
            assert result == 0

    def test_logs_errors(self, capsys) -> None:
        from cli.commands.logs import cmd_logs
        with mock.patch("cli.commands.logs.logs.query_errors", return_value=[
            {"ts": "2024-01-01", "command": "cmd", "status": "error", "latency_ms": 0, "error": "fail"}
        ]):
            result = cmd_logs(["--errors"])
            captured = capsys.readouterr()
            assert result == 0
            assert "error" in captured.out

    def test_logs_text_search(self, capsys) -> None:
        from cli.commands.logs import cmd_logs
        with mock.patch("cli.commands.logs.logs.query_text", return_value=[
            {"ts": "2024-01-01", "command": "build", "status": "ok", "latency_ms": 100}
        ]):
            result = cmd_logs(["build"])
            captured = capsys.readouterr()
            assert result == 0
            assert "build" in captured.out

    def test_logs_no_results(self, capsys) -> None:
        from cli.commands.logs import cmd_logs
        with mock.patch("cli.commands.logs.logs.query_text", return_value=[]):
            result = cmd_logs(["nonexistent"])
            captured = capsys.readouterr()
            assert result == 0
            # No output means no results found

    def test_logs_empty_log(self, capsys) -> None:
        from cli.commands.logs import cmd_logs
        with mock.patch("cli.commands.logs.logs.query_last", return_value=[]):
            result = cmd_logs([])
            captured = capsys.readouterr()
            assert result == 0

    def test_logs_with_error_in_output(self, capsys) -> None:
        from cli.commands.logs import cmd_logs
        with mock.patch("cli.commands.logs.logs.query_errors", return_value=[
            {"ts": "2024-01-01", "command": "fail_cmd", "status": "error", "latency_ms": 0, "error": "timeout"}
        ]):
            result = cmd_logs(["--errors"])
            captured = capsys.readouterr()
            assert "timeout" in captured.out