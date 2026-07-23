"""Tests for cli/commands/daemon.py — ethan daemon command."""
from __future__ import annotations

from unittest import mock

import pytest


class TestDaemonCmd:
    """cmd_daemon/ethan daemon tests."""

    def test_daemon_start(self) -> None:
        from cli.commands.daemon import cmd_daemon
        with mock.patch("cli.commands.daemon.daemon_core.cmd_start") as m:
            result = cmd_daemon(["start"])
            assert result == 0
            m.assert_called_once()

    def test_daemon_stop(self) -> None:
        from cli.commands.daemon import cmd_daemon
        with mock.patch("cli.commands.daemon.daemon_core.cmd_stop") as m:
            result = cmd_daemon(["stop"])
            assert result == 0
            m.assert_called_once()

    def test_daemon_status(self) -> None:
        from cli.commands.daemon import cmd_daemon
        with mock.patch("cli.commands.daemon.daemon_core.cmd_status") as m:
            result = cmd_daemon(["status"])
            assert result == 0
            m.assert_called_once()

    def test_daemon_no_args_shows_usage(self, capsys) -> None:
        from cli.commands.daemon import cmd_daemon
        result = cmd_daemon([])
        captured = capsys.readouterr()
        assert result == 1
        assert "usage" in captured.out.lower()

    def test_daemon_invalid_subcommand(self, capsys) -> None:
        from cli.commands.daemon import cmd_daemon
        result = cmd_daemon(["invalid"])
        captured = capsys.readouterr()
        assert result == 1
        assert "usage" in captured.out.lower()

    def test_daemon_start_with_args(self) -> None:
        from cli.commands.daemon import cmd_daemon
        with mock.patch("cli.commands.daemon.daemon_core.cmd_start") as m:
            result = cmd_daemon(["start", "--interval", "10"])
            assert result == 0
            m.assert_called_once_with(["--interval", "10"])