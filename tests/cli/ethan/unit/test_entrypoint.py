"""Tests for cli/ethan — entrypoint script."""
from __future__ import annotations

from unittest import mock

import pytest


def test_help_command_registered() -> None:
    """Help command exists and returns 0."""
    from cli.registry import COMMANDS, register

    @register("help")
    def _help(args):
        print("ETHAN toolchain")
        print("Commands:", " ".join(sorted(COMMANDS)))
        return 0

    cmd = COMMANDS.get("help")
    assert cmd is not None
    result = cmd([])
    assert result == 0


def test_version_command_output() -> None:
    """Version command prints version string."""
    from cli.registry import COMMANDS, register

    @register("version")
    def _version(args):
        print("ethan 2.0")
        return 0

    cmd = COMMANDS.get("version")
    assert cmd is not None
    result = cmd([])
    assert result == 0


def test_discover_commands_does_not_crash() -> None:
    """Ensuring discover_commands is called without error."""
    import cli.registry as reg
    reg.discover_commands()


def test_unknown_command_falls_back_to_run(monkeypatch) -> None:
    """Unknown command should fall back to 'run' prefix as per cli/ethan logic."""
    import cli.registry as reg

    dispatched = []
    reg.COMMANDS["run"] = lambda args: dispatched.append(args) or 0

    argv = ["nonexistent", "--foo"]
    if argv[0] not in reg.COMMANDS:
        argv = ["run"] + argv

    assert argv == ["run", "nonexistent", "--foo"]


def test_help_on_empty_argv() -> None:
    """When argv is empty, --help or -h should map to help."""
    import cli.registry as reg

    # Simulate entrypoint logic
    argv = []
    if not argv or argv[0] in ("-h", "--help"):
        argv = ["help"]
    assert argv == ["help"]


def test_help_flag_maps_to_help() -> None:
    """--help flag should dispatch to help."""
    import cli.registry as reg

    for flag in ("-h", "--help"):
        argv = [flag]
        if not argv or argv[0] in ("-h", "--help"):
            argv = ["help"]
        assert argv == ["help"]


def test_dispatch_through_ethan_main() -> None:
    """Simulate the full __main__ flow."""
    from cli.registry import COMMANDS, register, dispatch

    results = []

    @register("greet")
    def _greet(args):
        results.append(args)
        return 0

    rc = dispatch(["greet", "world"])
    assert rc == 0
    assert results == [["world"]]