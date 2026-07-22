"""ETHAN up — démarre tous les services Docker avec diagnostic.

Usage:
    ethan up              # Démarrage standard
    ethan up --dev        # Avec services de dev (Qdrant, ChromaDB)
    ethan up --skip-pull  # Ignorer le téléchargement des images
    ethan up --json       # Sortie JSON

Si le démarrage échoue, affiche un diagnostic détaillé expliquant pourquoi.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any

from interfaces.cli.core import colors as clr
from interfaces.cli.core.diagnostic import BootDiagnostic
from interfaces.cli.core.errors import EthanError, error
from interfaces.cli.registry import register


@register(
    "up",
    group="infra",
    description="Démarrer tous les services Docker",
    usage="ethan up [--dev] [--skip-pull] [--json]",
)
def cmd_up(args: list[str]) -> int:
    """Démarre les services Docker avec diagnostic automatique en cas d'échec."""
    dev_mode = "--dev" in args
    skip_pull = "--skip-pull" in args
    json_mode = "--json" in args

    # ── Préflight : vérifier les prérequis ──────────────────────
    if not json_mode:
        print(f"\n  {clr.C.CYAN}→{clr.C.RESET} Démarrage d'ETHAN...\n")

    diag = BootDiagnostic()
    report = diag.check_all()

    if not report.all_passed:
        if json_mode:
            print(json.dumps({
                "status": "failed",
                "reason": "prerequisites_not_met",
                "checks": [
                    {"name": c.name, "passed": c.passed, "detail": c.detail, "fix": c.fix}
                    for c in report.checks
                ],
            }, indent=2))
            return 3

        print(diag.explain_failure())
        print(f"\n  {clr.C.RED}✗ ETHAN ne peut pas démarrer.{clr.C.RESET}")
        print(f"  {clr.C.DIM}Corrigez les problèmes ci-dessus puis relancez : ethan up{clr.C.RESET}\n")
        return 3

    if not json_mode:
        print(f"  {clr.C.GREEN}✓{clr.C.RESET} Tous les prérequis sont satisfaits ({report.passed_count}/{report.total_count})\n")

    # ── Build compose args ────────────────────────────────────────
    compose_files = ["docker-compose.yml"]
    if dev_mode:
        compose_files.append("docker-compose.dev.yml")

    compose_cmd = ["docker", "compose"]
    for f in compose_files:
        compose_cmd.extend(["-f", f])

    # ── Pull images (sauf si --skip-pull) ────────────────────────
    if not skip_pull and not json_mode:
        print(f"  {clr.C.CYAN}→{clr.C.RESET} Téléchargement des images Docker...\n")

    if not skip_pull:
        pull_result = subprocess.run(
            compose_cmd + ["pull"],
            capture_output=not json_mode,
            text=True,
        )
        if pull_result.returncode != 0:
            if json_mode:
                print(json.dumps({
                    "status": "failed",
                    "reason": "docker_pull_failed",
                    "stderr": pull_result.stderr,
                }, indent=2))
                return 1
            print(f"  {clr.C.RED}✗ Échec du téléchargement des images{clr.C.RESET}")
            print(f"  {clr.C.DIM}{pull_result.stderr}{clr.C.RESET}\n")
            return 1

    # ── Démarrer les services ────────────────────────────────────
    if not json_mode:
        print(f"  {clr.C.CYAN}→{clr.C.RESET} Démarrage des services...\n")

    up_result = subprocess.run(
        compose_cmd + ["up", "-d"],
        capture_output=not json_mode,
        text=True,
    )

    if up_result.returncode != 0:
        if json_mode:
            print(json.dumps({
                "status": "failed",
                "reason": "docker_up_failed",
                "stderr": up_result.stderr,
            }, indent=2))
            return 1

        print(f"  {clr.C.RED}✗ Échec du démarrage des services{clr.C.RESET}")
        print(f"  {clr.C.DIM}{up_result.stderr}{clr.C.RESET}\n")

        # ── Diagnostic détaillé ──────────────────────────────────
        print(f"  {clr.C.BOLD}Diagnostic:{clr.C.RESET}\n")
        print(diag.explain_failure())
        print()
        return 1

    # ── Attendre que les services soient prêts ───────────────────
    if not json_mode:
        print(f"  {clr.C.CYAN}→{clr.C.RESET} Attente des services prêts...\n")

    ready = _wait_for_services(compose_cmd, timeout=60, json_mode=json_mode)

    if not ready:
        if json_mode:
            print(json.dumps({
                "status": "partial",
                "reason": "services_not_ready",
            }, indent=2))
            return 4

        print(f"  {clr.C.YELLOW}⚠ Certains services ne sont pas prêts{clr.C.RESET}")
        print(f"  {clr.C.DIM}Vérifiez avec : ethan status{clr.C.RESET}\n")
        return 4

    if json_mode:
        print(json.dumps({
            "status": "ok",
            "services": _get_service_status(compose_cmd),
        }, indent=2))
        return 0

    print(f"  {clr.C.GREEN}✓ ETHAN est démarré !{clr.C.RESET}")
    print(f"  {clr.C.DIM}  → ethan status  pour voir l'état{clr.C.RESET}")
    print(f"  {clr.C.DIM}  → ethan logs    pour suivre les logs{clr.C.RESET}\n")
    return 0


def _wait_for_services(compose_cmd: list[str], timeout: int = 60, json_mode: bool = False) -> bool:
    """Attend que tous les services soient sains."""
    start = time.time()
    while time.time() - start < timeout:
        result = subprocess.run(
            compose_cmd + ["ps", "--format", "json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            try:
                services = json.loads(result.stdout)
                if services and all(s.get("Status", "").startswith("Up") for s in services):
                    return True
            except (json.JSONDecodeError, KeyError):
                pass
        time.sleep(2)
    return False


def _get_service_status(compose_cmd: list[str]) -> list[dict[str, Any]]:
    """Récupère le statut des services."""
    result = subprocess.run(
        compose_cmd + ["ps", "--format", "json"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
    return []
