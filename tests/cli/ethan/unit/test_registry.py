"""Tests for cli/registry.py — registration, discovery, dispatch."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest


class TestRegister:
    """@register decorator tests."""

    def test_register_adds_to_commands(self) -> None:
        from cli.registry import register, COMMANDS

        @register("mycmd")
        def _mycmd(args):
            return 0

        assert "mycmd" in COMMANDS
        assert COMMANDS["mycmd"] is _mycmd

    def test_register_multiple_commands(self) -> None:
        from cli.registry import register, COMMANDS

        @register("cmd_a")
        def _a(args):
            return 0

        @register("cmd_b")
        def _b(args):
            return 0

        assert "cmd_a" in COMMANDS
        assert "cmd_b" in COMMANDS

    def test_register_returns_function(self) -> None:
        from cli.registry import register

        @register("ret_test")
        def _fn(args):
            return 42

        assert _fn([1, 2, 3]) == 42
        assert "ret_test" in __import__("cli.registry", fromlist=["COMMANDS"]).COMMANDS

    def test_register_does_not_overwrite_unknown(self) -> None:
        """Redeclaring a command replaces the old handler."""
        from cli.registry import register, COMMANDS

        @register("dup")
        def _first(args):
            return 1

        @register("dup")
        def _second(args):
            return 2

        assert COMMANDS["dup"] is _second
        assert COMMANDS["dup"]([]) == 2

    def test_register_with_empty_name(self) -> None:
        """Registering with an empty string name is allowed but unusual."""
        from cli.registry import register, COMMANDS

        @register("")
        def _empty(args):
            return 0

        assert "" in COMMANDS


class TestDispatch:
    """dispatch() function tests."""

    def test_dispatch_empty_argv(self) -> None:
        from cli.registry import dispatch

        result = dispatch([])
        assert result == 0  # prints help

    def test_dispatch_known_command(self, registered_commands) -> None:
        from cli.registry import dispatch

        result = dispatch(["test_cmd"])
        assert result == 0

    def test_dispatch_unknown_command(self, clear_registry) -> None:
        from cli.registry import dispatch

        result = dispatch(["nonexistent"])
        assert result == 1  # unknown command
        assert "nonexistent" in str(result) or result == 1

    def test_dispatch_passes_args(self) -> None:
        from cli.registry import register, COMMANDS, dispatch

        captured = []

        @register("args_test")
        def _handler(args):
            captured.append(args)
            return 0

        dispatch(["args_test", "--foo", "bar"])
        assert captured == [["--foo", "bar"]]

    def test_dispatch_catches_exception(self) -> None:
        from cli.registry import register, dispatch

        @register("crash")
        def _crash(args):
            raise RuntimeError("boom")

        result = dispatch(["crash"])
        assert result == 1  # exception caught, returns 1

    def test_dispatch_lets_systemexit_through(self) -> None:
        from cli.registry import register, dispatch

        @register("exit_cmd")
        def _exit(args):
            raise SystemExit(2)

        with pytest.raises(SystemExit) as exc_info:
            dispatch(["exit_cmd"])
        assert exc_info.value.code == 2


class TestDiscoverCommands:
    """discover_commands() tests."""

    def test_discover_empty_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scans empty commands dir without error."""
        from cli.registry import discover_commands

        empty_dir = tmp_path / "commands"
        empty_dir.mkdir()
        monkeypatch.setattr("cli.registry.Path", lambda p: tmp_path if "commands" in str(p) else Path(p))
        # This test just ensures no exception
        discover_commands()

    def test_discover_does_not_crash(self) -> None:
        """Running discover on real filesystem should not raise."""
        from cli.registry import discover_commands

        discover_commands()  # should not crash

    def test_load_module_nonexistent(self) -> None:
        """_load_module with nonexistent path returns None."""
        from cli.registry import _load_module

        result = _load_module(Path("/nonexistent/file.py"))
        assert result is None

    def test_load_module_dir_without_plugin_py(self) -> None:
        """_load_module on a dir without plugin.py returns None."""
        from cli.registry import _load_module
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            result = _load_module(Path(d))
            assert result is None

    def test_load_module_broken_file(self) -> None:
        """_load_module on a file with syntax errors returns None."""
        from cli.registry import _load_module
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("this is not valid python @@@")
            f.flush()
            result = _load_module(Path(f.name))
            assert result is None


class TestPluginDiscovery:
    """Plugin-based command registration tests."""

    def test_plugin_dict_registration(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """ETHAN_PLUGIN dict in a loaded module registers commands."""
        from cli.registry import _load_module, COMMANDS

        plugin_dir = tmp_path / "plugins" / "test_plugin"
        plugin_dir.mkdir(parents=True)
        plugin_file = plugin_dir / "plugin.py"
        plugin_file.write_text("""
ETHAN_PLUGIN = {
    "commands": {
        "plugin_cmd": {
            "handler": lambda args: print("plugin executed")
        }
    }
}
""")
        _load_module(plugin_dir)
        assert "plugin_cmd" in COMMANDS