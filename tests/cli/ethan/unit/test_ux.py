"""Tests for cli/core/ux.py — UX helpers."""
from __future__ import annotations

import pytest


class TestLevenshtein:
    """levenshtein() distance tests."""

    def test_identical_strings(self) -> None:
        from cli.core.ux import UX
        assert UX.levenshtein("hello", "hello") == 0

    def test_one_insertion(self) -> None:
        from cli.core.ux import UX
        assert UX.levenshtein("cat", "cats") == 1

    def test_one_deletion(self) -> None:
        from cli.core.ux import UX
        assert UX.levenshtein("cats", "cat") == 1

    def test_one_substitution(self) -> None:
        from cli.core.ux import UX
        assert UX.levenshtein("cat", "car") == 1

    def test_completely_different(self) -> None:
        from cli.core.ux import UX
        assert UX.levenshtein("abc", "xyz") == 3

    def test_empty_string(self) -> None:
        from cli.core.ux import UX
        assert UX.levenshtein("", "") == 0

    def test_one_empty(self) -> None:
        from cli.core.ux import UX
        assert UX.levenshtein("hello", "") == 5
        assert UX.levenshtein("", "hello") == 5


class TestSuggestCommand:
    """suggest_command() tests."""

    def test_exact_match(self) -> None:
        from cli.core.ux import UX
        result = UX.suggest_command("chat", ["chat", "run", "status"])
        assert result == "chat"

    def test_close_match(self) -> None:
        from cli.core.ux import UX
        result = UX.suggest_command("chatt", ["chat", "run", "status"])
        assert result == "chat"

    def test_no_match(self) -> None:
        from cli.core.ux import UX
        result = UX.suggest_command("xyzabc", ["chat", "run"])
        assert result is None

    def test_empty_input(self) -> None:
        from cli.core.ux import UX
        result = UX.suggest_command("", ["chat", "run"])
        assert result is None

    def test_empty_commands_list(self) -> None:
        from cli.core.ux import UX
        result = UX.suggest_command("chat", [])
        assert result is None

    def test_short_typo(self) -> None:
        from cli.core.ux import UX
        # "sttus" vs "status" — Levenshtein distance 1
        result = UX.suggest_command("sttus", ["status", "chat"])
        assert result == "status"


class TestSmartError:
    """smart_error() tests."""

    def test_unknown_command(self) -> None:
        from cli.core.ux import UX
        result = UX.smart_error("unknown_command", input="chatt", suggestion="chat")
        assert "Unknown command" in result
        assert "chatt" in result

    def test_missing_argument(self) -> None:
        from cli.core.ux import UX
        result = UX.smart_error("missing_argument", arg="cmd", usage="ethan run <cmd>", example="ethan run build")
        assert "Missing argument" in result
        assert "cmd" in result

    def test_command_failed(self) -> None:
        from cli.core.ux import UX
        result = UX.smart_error("command_failed", command="build", code=1)
        assert "Command failed" in result
        assert "build" in result

    def test_api_unreachable(self) -> None:
        from cli.core.ux import UX
        result = UX.smart_error("api_unreachable")
        assert "API unreachable" in result

    def test_permission_denied(self) -> None:
        from cli.core.ux import UX
        result = UX.smart_error("permission_denied", reason="no write access", run_as="root")
        assert "Permission denied" in result

    def test_unknown_kind(self) -> None:
        from cli.core.ux import UX
        result = UX.smart_error("unknown_kind")
        assert "Error" in result


class TestShowHelp:
    """show_help() tests."""

    def test_help_without_topic(self, capsys) -> None:
        from cli.core.ux import UX
        UX.show_help(None)
        captured = capsys.readouterr()
        assert "ETHAN" in captured.out
        assert "chat" in captured.out

    def test_help_with_topic(self, capsys) -> None:
        from cli.core.ux import UX
        UX.show_help("chat")
        captured = capsys.readouterr()
        assert "chat" in captured.out

    def test_help_unknown_topic_falls_back(self, capsys) -> None:
        from cli.core.ux import UX
        UX.show_help("nonexistent")
        captured = capsys.readouterr()
        assert "ETHAN" in captured.out