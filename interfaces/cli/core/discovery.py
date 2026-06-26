"""ETHAN CLI Discovery — command registry, fuzzy suggestions, help system."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Command:
    name: str
    group: str  # "core", "advanced", "plugin:<name>"
    description: str
    usage: str = ""
    examples: list[str] = field(default_factory=list)


class CommandRegistry:
    """Registry for all ETHAN commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, cmd: Command) -> None:
        self._commands[cmd.name] = cmd

    def get(self, name: str) -> Optional[Command]:
        return self._commands.get(name)

    def list_commands(self, group=None):
        cmds = []
        for cmd in self._commands.values():
            if group is None or cmd.group == group or (isinstance(group, str) and cmd.group.startswith(group + ":")):
                cmds.append(cmd)
        return cmds

    def suggest(self, input_str, limit=3):
        import difflib
        names = list(self._commands.keys())
        matches = difflib.get_close_matches(input_str, names, n=limit, cutoff=0.3)
        return [self._commands[name] for name in matches]

    def autocomplete(self, prefix: str):
        prefix = prefix.lower()
        return [name for name in self._commands if name.startswith(prefix)][:5]


# Global registry
registry = CommandRegistry()

# Core commands
registry.register(Command("chat", "core", "Interactive AI chat", "ethan chat", ["ethan chat", "ethan chat --resume"]))
registry.register(Command("run", "core", "Execute via capabilities", "ethan run <cmd>"))
registry.register(Command("status", "core", "Show system state", "ethan status"))
registry.register(Command("logs", "core", "Tail system logs", "ethan logs", ["ethan logs --follow", "ethan logs --lines 50"]))
registry.register(Command("help", "core", "Show help", "ethan help [topic]"))

# Advanced commands
registry.register(Command("plugin", "advanced", "Manage plugins", "ethan plugin <sub>"))
registry.register(Command("shell", "advanced", "Open ethan-shell", "ethan shell"))
registry.register(Command("config", "advanced", "Edit configuration", "ethan config <key> <value>"))
registry.register(Command("daemon", "advanced", "Control background daemon", "ethan daemon <start|stop|restart>"))