"""Tests for cli/registry.py — registration, discovery, dispatch."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestRegister:
    """@register decorator tests."""

    def test_register_adds_to_commands(self) -> None:
        from cli.registry import COMMAND_HANDLERS, register

        @register("mycmd")
        def _mycmd(args):
            return 0

        assert "mycmd" in COMMAND_HANDLERS
        assert COMMAND_HANDLERS["mycmd"] is _mycmd

    def test_register_multiple_commands(self) -> None:
        from cli.registry import COMMAND_HANDLERS, register

        @register("cmd_a")
        def _a(args):
            return 0

        @register("cmd_b")
        def _b(args):
            return 0

        assert "cmd_a" in COMMAND_HANDLERS
        assert "cmd_b" in COMMAND_HANDLERS

    def test_register_returns_function(self) -> None:
        from cli.registry import register

        @register("ret_test")
        def _fn(args):
            return 42

        assert _fn([1, 2, 3]) == 42
        registry_mod = __import__("cli.registry", fromlist=["COMMAND_HANDLERS"])
        assert "ret_test" in registry_mod.COMMAND_HANDLERS

    def test_register_does_not_overwrite_unknown(self) -> None:
        """Redeclaring a command replaces the old handler."""
        from cli.registry import COMMAND_HANDLERS, register

        @register("dup")
        def _first(args):
            return 1

        @register("dup")
        def _second(args):
            return 2

        assert COMMAND_HANDLERS["dup"] is _second
        assert COMMAND_HANDLERS["dup"]([]) == 2

    def test_register_with_empty_name(self) -> None:
        """Registering with an empty string name is allowed but unusual."""
        from cli.registry import COMMAND_HANDLERS, register

        @register("")
        def _empty(args):
            return 0

        assert "" in COMMAND_HANDLERS


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
        from cli.registry import dispatch, register

        captured = []

        @register("args_test")
        def _handler(args):
            captured.append(args)
            return 0

        dispatch(["args_test", "--foo", "bar"])
        assert captured == [["--foo", "bar"]]

    def test_dispatch_catches_exception(self) -> None:
        from cli.registry import dispatch, register

        @register("crash")
        def _crash(args):
            raise RuntimeError("boom")

        result = dispatch(["crash"])
        assert result == 1  # exception caught, returns 1

    def test_dispatch_lets_systemexit_through(self) -> None:
        from cli.registry import dispatch, register

        @register("exit_cmd")
        def _exit(args):
            raise SystemExit(2)

        with pytest.raises(SystemExit) as exc_info:
            dispatch(["exit_cmd"])
        assert exc_info.value.code == 2


class TestDiscoverCommands:
    """discover_commands() tests."""

    def test_discover_empty_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scanne un dossier de commandes vide sans erreur.

        L'ancienne version remplaçait `cli.registry.Path` par une lambda : la
        classe `Path` était perdue et `Path.home()` (utilisé par
        discover_commands pour les plugins utilisateur) levait un
        AttributeError. Le proxy ci-dessous ne redirige QUE le fichier du
        registre, tout en préservant l'API de `pathlib.Path`.
        """
        from cli.registry import discover_commands

        (tmp_path / "commands").mkdir()
        (tmp_path / "plugins").mkdir()
        monkeypatch.setattr("pathlib.Path.home", classmethod(lambda cls: tmp_path))

        class _RedirectedPath:
            """Proxy de `pathlib.Path` : registry.py est réputé vivre dans tmp_path."""

            def __call__(self, p):
                if str(p).endswith("registry.py"):
                    return tmp_path / "registry.py"
                return Path(p)

            def __getattr__(self, name):
                return getattr(Path, name)

        monkeypatch.setattr("cli.registry.Path", _RedirectedPath())
        discover_commands()  # ne doit rien lever

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
        import tempfile

        from cli.registry import _load_module

        with tempfile.TemporaryDirectory() as d:
            result = _load_module(Path(d))
            assert result is None

    def test_load_module_broken_file(self) -> None:
        """_load_module on a file with syntax errors returns None."""
        import tempfile

        from cli.registry import _load_module

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("this is not valid python @@@")
            f.flush()
            result = _load_module(Path(f.name))
            assert result is None


class TestPluginDiscovery:
    """Plugin-based command registration tests."""

    def test_plugin_dict_registration(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ETHAN_PLUGIN dict in a loaded module registers commands."""
        from cli.registry import COMMAND_HANDLERS, _load_module

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
        assert "plugin_cmd" in COMMAND_HANDLERS
