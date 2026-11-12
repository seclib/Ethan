"""ETHAN CLI/TUI — commande `ethan cli`.

`ethan cli` (sans argument) lance l'interface plein écran. Avec argument,
il délègue à la commande CLI correspondante (compatibilité préservée).

Aucune logique métier ici : le TUI est un client Core.
"""

from __future__ import annotations

from interfaces.cli.core.context import get_context
from interfaces.cli.core.errors import usage_error
from interfaces.cli.registry import register


USAGE = "ethan cli [--api-url URL] [--timeout SEC] [--session ID] [--no-color]"


def _launch(args: list[str]) -> int:
    from interfaces.cli.tui.app import main as tui_main

    return int(tui_main(args))


@register("cli", group="core", description="Launch the ETHAN CLI/TUI (full-screen if no argument)", usage=USAGE)
def cmd_cli(args: list[str]) -> int:
    """Lance le CLI/TUI ETHAN. Sans argument, lance l'interface plein écran."""
    ctx = get_context()
    if not args:
        if ctx.is_json:
            raise usage_error("TUI mode is not supported with --output json.")
        return _launch([])
    # Délégation à la commande demandée
    from interfaces.cli.registry import COMMAND_HANDLERS

    handler = COMMAND_HANDLERS.get(args[0])
    if handler is not None and handler is not cmd_cli:
        return int(handler(args[1:]))
    raise usage_error(f"unknown command: {args[0]}", hint="run 'ethan help' for the command list")


__all__ = ["cmd_cli"]