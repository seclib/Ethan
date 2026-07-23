"""Tests for cli/commands/memory.py — ethan memory command."""
from __future__ import annotations

from unittest import mock

import pytest


class TestMemoryCmd:
    """cmd_memory/ethan memory tests."""

    def test_memory_default_shows_recent(self, capsys) -> None:
        from cli.commands.memory import cmd_memory
        with mock.patch("cli.commands.memory.mem.recent", return_value=[
            {"text": "recent entry"}
        ]):
            result = cmd_memory([])
            captured = capsys.readouterr()
            assert result == 0
            assert "recent entry" in captured.out

    def test_memory_recent_subcommand(self, capsys) -> None:
        from cli.commands.memory import cmd_memory
        with mock.patch("cli.commands.memory.mem.recent", return_value=[
            {"text": "entry 1"}, {"text": "entry 2"}
        ]):
            result = cmd_memory(["recent"])
            captured = capsys.readouterr()
            assert result == 0
            assert "entry 1" in captured.out

    def test_memory_recent_with_count(self, capsys) -> None:
        from cli.commands.memory import cmd_memory
        with mock.patch("cli.commands.memory.mem.recent", return_value=[
            {"text": "only one"}
        ]):
            result = cmd_memory(["recent", "1"])
            captured = capsys.readouterr()
            assert result == 0

    def test_memory_frequent(self, capsys) -> None:
        from cli.commands.memory import cmd_memory
        with mock.patch("cli.commands.memory.mem.frequent", return_value=[
            {"text": "frequent cmd", "count": 5}
        ]):
            result = cmd_memory(["frequent"])
            captured = capsys.readouterr()
            assert result == 0
            assert "frequent cmd" in captured.out

    def test_memory_frequent_with_count(self, capsys) -> None:
        from cli.commands.memory import cmd_memory
        with mock.patch("cli.commands.memory.mem.frequent", return_value=[
            {"text": "top cmd", "count": 10}
        ]):
            result = cmd_memory(["frequent", "1"])
            captured = capsys.readouterr()
            assert result == 0

    def test_memory_invalid_subcommand_shows_usage(self, capsys) -> None:
        from cli.commands.memory import cmd_memory
        result = cmd_memory(["invalid_sub"])
        captured = capsys.readouterr()
        assert result == 0
        assert "usage" in captured.out.lower()

    def test_memory_no_history(self, capsys) -> None:
        from cli.commands.memory import cmd_memory
        with mock.patch("cli.commands.memory.mem.recent", return_value=[]):
            result = cmd_memory([])
            captured = capsys.readouterr()
            assert result == 0