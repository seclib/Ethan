"""ETHAN TUI — interface plein écran du CLI ETHAN.

Le TUI est une **interface** ETHAN : il affiche et contrôle, il ne
réimplémente aucune logique métier (AGENTS.md, Première Loi). Toute
capacité vient du Core via la frontière HTTP unique
(`interfaces.cli.core.client`).

Point d'entrée : ``python3 -m interfaces.cli.tui`` ou ``ethan tui``.
"""

from __future__ import annotations

from interfaces.cli.tui.app import TuiApp, main

__all__ = ["TuiApp", "main"]
