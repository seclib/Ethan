"""Plugin compatibility tests — ensure plugins load and register correctly."""
import pytest

from ..plugin_compat import PluginCompatibilityChecker


@pytest.fixture
def checker():
    """Provide plugin checker."""
    return PluginCompatibilityChecker()


class TestPluginRegistry:
    """Ensure all plugins load and register correctly."""

    def test_all_plugins_load(self, checker):
        """All plugins should load without errors."""
        results = checker.check_all()

        failed = [r for r in results if not r.loaded]

        if failed:
            messages = [f"{r.plugin}: {', '.join(r.errors)}" for r in failed]
            pytest.fail(f"Failed plugins:\n" + "\n".join(messages))

    def test_no_duplicate_commands(self, checker):
        """No two plugins should register the same command."""
        from cli.registry import discover_commands, COMMANDS

        # Capture state before
        before = set(COMMANDS.keys())

        discover_commands()

        after = set(COMMANDS.keys())
        new_commands = after - before

        # Check for duplicates
        duplicates = []
        for cmd in new_commands:
            if cmd in before:
                duplicates.append(cmd)

        assert len(duplicates) == 0, f"Duplicate commands: {duplicates}"

    def test_all_plugin_commands_callable(self, checker):
        """Every registered plugin command must be callable."""
        from cli.registry import discover_commands, COMMANDS

        discover_commands()

        non_callable = []
        for name, fn in COMMANDS.items():
            if not callable(fn):
                non_callable.append(name)

        assert len(non_callable) == 0, f"Non-callable commands: {non_callable}"