"""Command matrix tests — smoke test all commands."""
import pytest

from cli.registry import discover_commands, COMMANDS


class TestCommandMatrix:
    """Smoke test all registered commands."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure commands are discovered."""
        discover_commands()

    def test_all_commands_registered(self):
        """All expected commands should be registered."""
        expected_commands = [
            "chat", "status", "logs", "memory", "suggest",
            "daemon", "service", "plugin", "plugins", "config",
            "hello", "weather", "think", "run",
        ]

        for cmd in expected_commands:
            assert cmd in COMMANDS, f"Command '{cmd}' not registered"

    def test_all_commands_callable(self):
        """All registered commands must be callable."""
        non_callable = []
        for name, fn in COMMANDS.items():
            if not callable(fn):
                non_callable.append(name)

        assert len(non_callable) == 0, f"Non-callable commands: {non_callable}"

    def test_no_circular_imports(self):
        """Commands should not have circular imports."""
        import importlib
        import sys

        # Clear modules to force reimport
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith("cli.")]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Re-import should work without circular import errors
        try:
            from cli.registry import discover_commands, COMMANDS
            discover_commands()
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")

    def test_command_handlers_return_int(self):
        """Command handlers should return int exit codes."""
        bad_returns = []
        for name, fn in COMMANDS.items():
            try:
                result = fn([])
                if result is not None and not isinstance(result, int):
                    bad_returns.append(f"{name}: returned {type(result).__name__}")
            except SystemExit:
                pass  # OK
            except Exception:
                pass  # OK for smoke test

        assert len(bad_returns) == 0, f"Commands with bad return types:\n" + "\n".join(bad_returns)