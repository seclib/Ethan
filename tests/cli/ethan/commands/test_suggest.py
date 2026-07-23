"""Tests for cli/commands/suggest.py — ethan suggest command."""
from __future__ import annotations

from unittest import mock

import pytest


class TestSuggestCommand:
    """cmd_suggest/ethan suggest tests."""

    def test_suggest_default(self, capsys) -> None:
        from cli.commands.suggest import cmd_suggest
        with mock.patch("cli.commands.suggest.mem.recent", return_value=[
            {"text": "recent cmd"}
        ]):
            with mock.patch("cli.commands.suggest.mem.frequent", return_value=[
                {"text": "frequent cmd", "count": 5}
            ]):
                result = cmd_suggest([])
                captured = capsys.readouterr()
                assert result == 0
                assert "Recent" in captured.out
                assert "Frequent" in captured.out

    def test_suggest_prefix_match(self, capsys) -> None:
        from cli.commands.suggest import cmd_suggest
        with mock.patch("cli.commands.suggest.mem.suggest_prefix", return_value=[
            "hello world", "help"
        ]):
            result = cmd_suggest(["hel"])
            captured = capsys.readouterr()
            assert result == 0
            assert "hello world" in captured.out

    def test_suggest_no_history(self, capsys) -> None:
        from cli.commands.suggest import cmd_suggest
        with mock.patch("cli.commands.suggest.mem.recent", return_value=[]):
            with mock.patch("cli.commands.suggest.mem.frequent", return_value=[]):
                result = cmd_suggest([])
                captured = capsys.readouterr()
                assert result == 0

    def test_suggest_no_matches(self, capsys) -> None:
        from cli.commands.suggest import cmd_suggest
        with mock.patch("cli.commands.suggest.mem.suggest_prefix", return_value=[]):
            result = cmd_suggest(["xyz"])
            captured = capsys.readouterr()
            assert result == 0

    def test_suggest_empty_prefix(self, capsys) -> None:
        from cli.commands.suggest import cmd_suggest
        with mock.patch("cli.commands.suggest.mem.recent", return_value=[]):
            with mock.patch("cli.commands.suggest.mem.frequent", return_value=[]):
                result = cmd_suggest([""])
                captured = capsys.readouterr()
                assert result == 0