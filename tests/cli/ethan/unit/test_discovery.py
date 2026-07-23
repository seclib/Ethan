"""Tests for cli/core/discovery.py — command registry."""
from __future__ import annotations

import pytest


class TestCommand:
    """Command dataclass tests."""

    def test_command_creation(self) -> None:
        from cli.core.discovery import Command
        cmd = Command("test", "core", "A test command")
        assert cmd.name == "test"
        assert cmd.group == "core"
        assert cmd.description == "A test command"

    def test_command_with_examples(self) -> None:
        from cli.core.discovery import Command
        cmd = Command("test", "core", "desc", "usage", ["ex1", "ex2"])
        assert cmd.examples == ["ex1", "ex2"]

    def test_command_defaults(self) -> None:
        from cli.core.discovery import Command
        cmd = Command("test", "core", "desc")
        assert cmd.usage == ""
        assert cmd.examples == []


class TestCommandRegistry:
    """CommandRegistry tests."""

    def test_register_and_get(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        cmd = Command("test", "core", "A test")
        reg.register(cmd)
        assert reg.get("test") is cmd

    def test_get_nonexistent(self) -> None:
        from cli.core.discovery import CommandRegistry
        reg = CommandRegistry()
        assert reg.get("nonexistent") is None

    def test_list_all(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        reg.register(Command("a", "core", "A"))
        reg.register(Command("b", "advanced", "B"))
        cmds = reg.list_commands()
        assert len(cmds) == 2

    def test_list_by_group(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        reg.register(Command("chat", "core", "Chat"))
        reg.register(Command("plugin", "advanced", "Plugin"))
        cmds = reg.list_commands("core")
        assert len(cmds) == 1
        assert cmds[0].name == "chat"

    def test_list_with_prefix_group(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        reg.register(Command("p1", "plugin:foo", "Plugin 1"))
        reg.register(Command("p2", "plugin:bar", "Plugin 2"))
        cmds = reg.list_commands("plugin:")
        assert len(cmds) == 2
        assert all(c.group.startswith("plugin:") for c in cmds)

    def test_suggest(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        reg.register(Command("chat", "core", "Chat"))
        reg.register(Command("changelog", "core", "Changelog"))
        reg.register(Command("run", "core", "Run"))
        suggestions = reg.suggest("chatt")
        assert len(suggestions) > 0
        assert suggestions[0].name == "chat"

    def test_suggest_no_match(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        reg.register(Command("chat", "core", "Chat"))
        suggestions = reg.suggest("xyzabc")
        assert len(suggestions) == 0

    def test_autocomplete(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        reg.register(Command("chat", "core", "Chat"))
        reg.register(Command("check", "core", "Check"))
        reg.register(Command("run", "core", "Run"))
        results = reg.autocomplete("ch")
        assert "chat" in results
        assert "check" in results

    def test_autocomplete_empty_prefix(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        reg.register(Command("chat", "core", "Chat"))
        results = reg.autocomplete("")
        assert "chat" in results

    def test_autocomplete_no_matches(self) -> None:
        from cli.core.discovery import CommandRegistry, Command
        reg = CommandRegistry()
        reg.register(Command("chat", "core", "Chat"))
        results = reg.autocomplete("xyz")
        assert results == []


class TestGlobalRegistry:
    """Global registry instance tests."""

    def test_global_registry_exists(self) -> None:
        from cli.core.discovery import registry
        assert registry is not None

    def test_global_registry_has_core_commands(self) -> None:
        from cli.core.discovery import registry
        cmds = registry.list_commands("core")
        names = {c.name for c in cmds}
        assert "chat" in names
        assert "run" in names
        assert "status" in names
        assert "logs" in names
        assert "help" in names

    def test_global_registry_has_advanced_commands(self) -> None:
        from cli.core.discovery import registry
        cmds = registry.list_commands("advanced")
        names = {c.name for c in cmds}
        assert "plugin" in names
        assert "shell" in names
        assert "config" in names
        assert "daemon" in names