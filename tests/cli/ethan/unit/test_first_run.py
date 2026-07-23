"""Tests for cli/core/first_run.py — first-run detection & welcome."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest


class TestFirstRun:
    """First-run detection tests."""

    def test_is_first_run_true(self) -> None:
        from cli.core.first_run import is_first_run, FIRST_RUN_MARKER
        # Marker does not exist
        assert is_first_run() is True

    def test_is_first_run_false(self) -> None:
        from cli.core.first_run import is_first_run, FIRST_RUN_MARKER, mark_installed
        mark_installed()
        assert is_first_run() is False

    def test_mark_installed_creates_marker(self) -> None:
        from cli.core.first_run import mark_installed, FIRST_RUN_MARKER
        mark_installed()
        assert Path(FIRST_RUN_MARKER).exists()

    def test_mark_installed_creates_directory(self) -> None:
        from cli.core.first_run import mark_installed, FIRST_RUN_MARKER
        mark_installed()
        assert Path(FIRST_RUN_MARKER).parent.exists()

    def test_mark_installed_content(self) -> None:
        from cli.core.first_run import mark_installed, FIRST_RUN_MARKER
        mark_installed()
        with open(FIRST_RUN_MARKER) as f:
            assert f.read().strip() == "installed"


class TestShowWelcome:
    """show_welcome() tests."""

    def test_show_welcome_output(self, capsys) -> None:
        from cli.core.first_run import show_welcome
        show_welcome()
        captured = capsys.readouterr()
        assert "ETHAN" in captured.out
        assert "ready" in captured.out.lower()

    def test_show_welcome_contains_commands(self, capsys) -> None:
        from cli.core.first_run import show_welcome
        show_welcome()
        captured = capsys.readouterr()
        assert "ethan chat" in captured.out
        assert "ethan run" in captured.out


class TestShowSystemCheck:
    """show_system_check() tests."""

    def test_show_system_check_api_reachable(self, capsys) -> None:
        from cli.core.first_run import show_system_check
        with mock.patch("cli.core.first_run.alive", return_value=True):
            show_system_check()
            captured = capsys.readouterr()
            assert "API reachable" in captured.out

    def test_show_system_check_api_unreachable(self, capsys) -> None:
        from cli.core.first_run import show_system_check
        with mock.patch("cli.core.first_run.alive", return_value=False):
            show_system_check()
            captured = capsys.readouterr()
            assert "API unreachable" in captured.out

    def test_show_system_check_memory_status(self, capsys) -> None:
        from cli.core.first_run import show_system_check
        with mock.patch("cli.core.first_run.alive", return_value=True):
            show_system_check()
            captured = capsys.readouterr()
            assert "Memory" in captured.out


class TestMaybeShowFirstRun:
    """maybe_show_first_run() tests."""

    def test_maybe_show_first_run_shows_welcome(self, capsys) -> None:
        from cli.core.first_run import maybe_show_first_run, FIRST_RUN_MARKER
        # Ensure first run
        try:
            Path(FIRST_RUN_MARKER).unlink()
        except FileNotFoundError:
            pass
        maybe_show_first_run(show_check=True)
        captured = capsys.readouterr()
        assert "ready" in captured.out.lower()

    def test_maybe_show_first_run_not_shown_again(self, capsys) -> None:
        from cli.core.first_run import maybe_show_first_run, mark_installed
        mark_installed()
        maybe_show_first_run()
        captured = capsys.readouterr()
        assert captured.out == "" or "ready" not in captured.out.lower()