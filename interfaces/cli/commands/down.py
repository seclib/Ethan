"""ETHAN down — arrête tous les services Docker.

Usage:
    ethan down              # Arrêt standard
    ethan down --volumes    # Supprimer aussi les volumes
    ethan down --json       # Sortie JSON
"""

from __future__ import annotations

import json
import subprocess

from interfaces.cli.core import colors as clr
from interfaces.cli.registry import register


@register(
    "down",
    group="infra",
    description="Arrêter tous les services Docker",
    usage="ethan down [--volumes] [--json]",
)
def cmd_down(args: list[str]) -> int:
    """Arrête les services Docker."""
    volumes = "--volumes" in args
    json_mode = "--json" in args

    compose_cmd = ["docker", "compose", "-f", "docker-compose.yml"]
    if volumes:
        compose_cmd.append("-f")
        compose_cmd.append("docker-compose.dev.yml")

    if not json_mode:
        print(f"\n  {clr.C.CYAN}→{clr.C.RESET} Arrêt d'ETHAN...\n")

    cmd = compose_cmd + ["down"]
    if volumes:
        cmd.append("--volumes")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        if json_mode:
            print(json.dumps({"status": "failed", "stderr": result.stderr}, indent=2))
            return 1
        print(f"  {clr.C.RED}✗ Échec de l'arrêt : {result.stderr}{clr.C.RESET}\n")
        return 1

    if json_mode:
        print(json.dumps({"status": "ok"}, indent=2))
        return 0

    print(f"  {clr.C.GREEN}✓ ETHAN est arrêté.{clr.C.RESET}\n")
    return 0
