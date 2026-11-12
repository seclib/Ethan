"""Tests du point d'entrée TUI."""

from __future__ import annotations

from unittest import mock

import pytest


def test_main_help():
    from interfaces.cli.tui.app import main
    rc = main(["--help"])
    assert rc == 0


def test_main_version():
    from interfaces.cli.tui.app import main
    rc = main(["--version"])
    assert rc == 0


def test_cmd_cli_registered():
    # Trigger discovery
    from interfaces.cli.registry import discover_commands, Registry
    discover_commands()
    reg = Registry()
    assert "cli" in reg.commands
    assert "tui" not in reg.commands


def test_cmd_cli_no_args_launches(monkeypatch):
    import interfaces.cli.commands.tui as tui_mod
    monkeypatch.setattr(tui_mod, "_launch", lambda args: 0)
    rc = tui_mod.cmd_cli([])
    assert rc == 0


def test_cmd_cli_forwards(monkeypatch):
    import interfaces.cli.commands.tui as tui_mod
    from interfaces.cli.registry import COMMAND_HANDLERS
    called = {"n": 0}

    def fake_handler(args):
        called["n"] += 1
        return 0

    COMMAND_HANDLERS["status"] = fake_handler
    try:
        rc = tui_mod.cmd_cli(["status", "x"])
        assert rc == 0
        assert called["n"] == 1
    finally:
        del COMMAND_HANDLERS["status"]
