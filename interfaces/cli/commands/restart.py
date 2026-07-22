"""ETHAN restart — redémarre tous les services Docker.

Usage:
    ethan restart           # Redémarrage standard
    ethan restart --json    # Sortie JSON
"""

from __future__ import annotations

import json
import subprocess

from interfaces.cli.core import colors as clr
from interfaces.cli.registry import register


@register(
    "restart",
    group="infra",
    description="Redémarrer les services Docker",
    usage="ethan restart [--json]",
)
def cmd_restart(args: list[str]) -> int:
    """Redémarre les services Docker."""
    json_mode = "--json" in args

    if not json_mode:
        print(f"\n  {clr.C.CYAN}→{clr.C.RESET} Redémarrage d'ETHAN...\n")

    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "restart"],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        if json_mode:
            print(json.dumps({"status": "failed", "stderr": result.stderr}, indent=2))
            return 1
        print(f"  {clr.C.RED}✗ Échec du redémarrage : {result.stderr}{clr.C.RESET}\n")
        return 1

    if json_mode:
        print(json.dumps({"status": "ok"}, indent=2))
        return 0

    print(f"  {clr.C.GREEN}✓ ETHAN redémarré.{clr.C.RESET}\n")
    return 0
