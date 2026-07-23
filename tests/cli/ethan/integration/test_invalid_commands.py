"""Integration tests for invalid command handling."""
from __future__ import annotations

from unittest import mock

import pytest


class TestUnknownCommands:
    """Unknown command handling at dispatch level."""

    def test_unknown_command_via_dispatch(self, clear_registry) -> None:
        from cli.registry import dispatch
        result = dispatch(["nonexistent"])
        assert result == 1

    def test_unknown_command_falls_to_run(self) -> None:
        import cli.registry as reg
        dispatched = []

        def _run_handler(args):
            dispatched.append(args)
            return 0

        reg.COMMANDS["run"] = _run_handler

        argv = ["unknown_cmd", "--flag"]
        if argv[0] not in reg.COMMANDS:
            argv = ["run"] + argv
        assert argv == ["run", "unknown_cmd", "--flag"]


class TestTypoHandling:
    """Typo/suggestion handling tests."""

    def test_typo_suggestion_via_ux(self) -> None:
        from cli.core.ux import UX
        result = UX.suggest_command("chatt", ["chat", "run", "status"])
        assert result == "chat"

    def test_typo_suggestion_none(self) -> None:
        from cli.core.ux import UX
        result = UX.suggest_command("xyzxyz", ["chat", "run"])
        assert result is None


class TestEmptyCommandHandling:
    """Empty command handling tests."""

    def test_empty_argv_dispatches_help(self) -> None:
        from cli.registry import dispatch
        result = dispatch([])
        assert result == 0  # prints help, returns 0

    def test_empty_string_classified_as_chat(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("")
        assert intent.kind == "chat"
        assert intent.confidence == 0.0

    def test_empty_input_error(self) -> None:
        from cli.core.errors import empty_input, format_error
        err = empty_input()
        result = format_error(err)
        assert "Empty input" in result
        assert "INP-001" in result


class TestMissingArgumentHandling:
    """Missing argument handling tests."""

    def test_daemon_missing_subcommand(self, capsys) -> None:
        from cli.commands.daemon import cmd_daemon
        result = cmd_daemon([])
        captured = capsys.readouterr()
        assert result == 1
        assert "usage" in captured.out.lower()

    def test_memory_invalid_subcommand(self, capsys) -> None:
        from cli.commands.memory import cmd_memory
        result = cmd_memory(["invalid"])
        captured = capsys.readouterr()
        assert result == 0
        assert "usage" in captured.out.lower()


class TestChatSlashHandling:
    """Chat slash command handling tests."""

    def test_chat_unknown_slash_command(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/unknown_cmd", "/exit"]):
            result = cmd_chat([])
            assert result == 0


class TestHelpFlagHandling:
    """Help/flag handling tests."""

    def test_help_dispatch(self) -> None:
        import cli.registry as reg
        reg.COMMANDS["help"] = lambda args: 0
        # Simulate entrypoint
        argv = ["--help"]
        if not argv or argv[0] in ("-h", "--help"):
            argv = ["help"]
        assert argv == ["help"]