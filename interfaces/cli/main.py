#!/usr/bin/env python3
"""ETHAN CLI — Terminal interface for ETHAN Cognitive Runtime.

Usage:
  ethan <command> [args...]

Commands:
  Infrastructure:
    up          Boot all services (docker compose)
    down        Shutdown all services
    status      Show system status (real data from Docker)
    logs        Show service logs
    restart     Restart services
    doctor      Run full system diagnostics

  Cognitive:
    repl        Start interactive REPL chat
    memory      Show memory / state
    plugin      Manage plugins
    think       Send a thought to the kernel
    router      Route LLM model selection

  System:
    install     Install ETHAN (deps, systemd, config)
    update      Update ETHAN via git
    version     Show version info
    help        Show extended help
"""

from __future__ import annotations

import sys
import os

from interfaces.cli.registry import Registry
from interfaces.cli.core import colors as clr

# ── Import all command modules so @register decorators fire ──────
# pylint: disable=unused-import
from interfaces.cli.commands import (
    status,
    doctor,
    logs,
    memory,
    plugin,
    router,
    think,
    chat,
    daemon,
    version,
    suggest,
    bench,
    update,
    config_cmd,
)
# pylint: enable=unused-import


def main() -> None:
    """Main entry point — dispatch to registered commands or fallback to REPL."""
    registry = Registry()

    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        _show_help(registry)
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Special case: version
    if command in ("version", "--version", "-v"):
        from interfaces.cli._version import __version__
        print(f"ETHAN CLI v{__version__}")
        sys.exit(0)

    # Special case: repl is the default fallback
    if command == "repl" or command not in registry.commands:
        if command != "repl":
            print(f"{clr.C.YELLOW}⚠ Unknown command: {command}{clr.C.RESET}")
            print(f"  {clr.C.CYAN}→{clr.C.RESET} Starting REPL instead. Use '{clr.C.BOLD}help{clr.C.RESET}' for commands.\n")
        from interfaces.cli.repl import repl_loop
        try:
            repl_loop()
        except KeyboardInterrupt:
            print(f"\n{clr.C.GREEN}◆ Goodbye{clr.C.RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"{clr.C.RED}✗ Fatal error: {e}{clr.C.RESET}", file=sys.stderr)
            sys.exit(1)
        return

    # Dispatch to registered command handler
    handler = registry.commands[command]
    try:
        exit_code = handler(args)
        sys.exit(exit_code if isinstance(exit_code, int) else 0)
    except KeyboardInterrupt:
        print(f"\n{clr.C.CYAN}◇ Interrupted{clr.C.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"{clr.C.RED}✗ Command '{command}' failed: {e}{clr.C.RESET}", file=sys.stderr)
        sys.exit(1)


def _show_help(registry: Registry) -> None:
    """Display formatted help with all registered commands."""
    print()
    print(f"{clr.C.BOLD}{clr.C.CYAN}◆ ETHAN CLI{clr.C.RESET}  {clr.C.DIM}Cognitive OS Terminal{clr.C.RESET}")
    print()

    # Group commands by category
    groups: dict[str, list[tuple[str, str]]] = {}
    for name, handler in sorted(registry.commands.items()):
        meta = getattr(handler, "__meta__", {})
        group = meta.get("group", "other")
        desc = meta.get("description", "")
        groups.setdefault(group, []).append((name, desc))

    # Known groups ordering
    group_order = ["infra", "core", "system", "other"]

    for group_name in group_order:
        if group_name not in groups:
            continue
        label = {
            "infra": "Infrastructure",
            "core": "Cognitive",
            "system": "System",
            "other": "Other",
        }.get(group_name, group_name.capitalize())

        print(f"  {clr.C.BOLD}{label}{clr.C.RESET}")
        for name, desc in groups[group_name]:
            print(f"    {clr.C.CYAN}{name:<16}{clr.C.RESET} {desc}")
        print()

    # Also show the bash commands that aren't in Python CLI yet
    print(f"  {clr.C.BOLD}Bash-only (external){clr.C.RESET}")
    bash_cmds = [
        ("up", "Boot all Docker services"),
        ("down", "Shutdown all Docker services"),
        ("restart", "Restart services"),
        ("install", "Install ETHAN system-wide"),
        ("preflight", "Check system prerequisites"),
        ("migrate", "Run PostgreSQL migrations"),
        ("watchdog", "Monitor container health"),
    ]
    for name, desc in bash_cmds:
        print(f"    {clr.C.CYAN}{name:<16}{clr.C.RESET} {desc}")
    print()

    print(f"  {clr.C.DIM}Usage: ./ethan <command> [options]{clr.C.RESET}")
    print(f"  {clr.C.DIM}       ethan <command> [options]{clr.C.RESET}")
    print()


if __name__ == "__main__":
    main()