"""Tests for cli/commands/status.py — ethan status command."""
from __future__ import annotations

from unittest import mock

import pytest


class TestStatusCommand:
    """cmd_status/ethan status tests."""

    def test_status_online(self, capsys) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=True):
            with mock.patch("cli.commands.status.get_state", return_value={
                "mode": "running", "active_goal": "test", "running_tasks": 2
            }):
                result = cmd_status([])
                captured = capsys.readouterr()
                assert result == 0
                assert "ONLINE" in captured.out
                assert "running" in captured.out

    def test_status_offline(self, capsys) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=False):
            result = cmd_status([])
            captured = capsys.readouterr()
            assert result == 0
            assert "OFFLINE" in captured.out

    def test_status_partial_state(self, capsys) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=True):
            with mock.patch("cli.commands.status.get_state", return_value={
                "mode": "running"
            }):
                result = cmd_status([])
                captured = capsys.readouterr()
                assert "ONLINE" in captured.out

    def test_status_empty_state(self, capsys) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=True):
            with mock.patch("cli.commands.status.get_state", return_value={}):
                result = cmd_status([])
                captured = capsys.readouterr()
                assert "ONLINE" in captured.out

    def test_status_none_state(self, capsys) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=True):
            with mock.patch("cli.commands.status.get_state", return_value=None):
                result = cmd_status([])
                captured = capsys.readouterr()
                assert "ONLINE" in captured.out

    def test_status_with_last_event(self, capsys) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=True):
            with mock.patch("cli.commands.status.get_state", return_value={
                "mode": "running",
                "active_goal": "test",
                "running_tasks": 0,
                "last_event": {"type": "chat", "data": "hello"}
            }):
                result = cmd_status([])
                captured = capsys.readouterr()
                assert "chat" in captured.out