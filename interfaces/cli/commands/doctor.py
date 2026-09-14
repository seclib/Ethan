"""ETHAN doctor — real system diagnostics.

Consomme la capacité Core-owned ``core.diagnostics`` exposée par l'API
(``GET /diagnostics``) — la même source de vérité que la page WebUI
Diagnostics.  Aucune donnée fictive.

Stratégie :
  1. si l'API ETHAN répond → rapport complet (12 composants réels) ;
  2. sinon → BootDiagnostic (prérequis système réels) + cause probable,
     car si l'API est down, c'est précisément ce que doctor doit expliquer.

Token optionnel : env ``ETHAN_TOKEN`` ou ``--token`` (l'endpoint exige un JWT).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

from interfaces.cli.core import colors as clr
from interfaces.cli.core.diagnostic import BootDiagnostic
from interfaces.cli.registry import register

STATUS_ICONS = {
    "ok": (clr.C.GREEN, "✓"),
    "warning": (clr.C.YELLOW, "▲"),
    "error": (clr.C.RED, "✗"),
    "unavailable": (clr.C.DIM, "○"),
}


@register(
    "doctor",
    group="infra",
    description="Run real system diagnostics (via ETHAN Core)",
    usage="ethan doctor [--json] [--token TOKEN]",
)
def cmd_doctor(args: list[str]) -> int:
    json_mode = "--json" in args
    token = _extract_token(args)
    return _run(json_mode=json_mode, token=token)


def _extract_token(args: list[str]) -> str | None:
    if "--token" in args:
        idx = args.index("--token")
        if idx + 1 < len(args):
            return args[idx + 1]
    return os.getenv("ETHAN_TOKEN") or None


def _api_url() -> str:
    return os.getenv("ETHAN_API_URL", "http://localhost:8000").rstrip("/")


def _fetch_api_report(token: str | None) -> dict | None:
    """Récupère le rapport Core via l'API — None si injoignable/refusé."""
    req = urllib.request.Request(f"{_api_url()}/diagnostics")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — le fallback gère l'affichage
        return None


def _run(*, json_mode: bool, token: str | None) -> int:
    report = _fetch_api_report(token)
    if report is not None:
        if json_mode:
            print(json.dumps(report, indent=2))
            return 0
        _render_api_report(report)
        counts = report.get("summary", {}).get("counts", {})
        if counts.get("error") or counts.get("unavailable"):
            return 1
        return 0

    # ── Fallback : l'API ne répond pas — expliquons pourquoi ──────────
    if json_mode:
        print(json.dumps({"api": "unreachable", "detail": _api_url()}, indent=2))
        return 1

    print()
    print(clr.section("Doctor  ◇  System Check"))
    print()
    print(f"  {clr.C.RED}✗ API ETHAN injoignable ({_api_url()}){clr.C.RESET}")
    print(f"    {clr.C.DIM}Le diagnostic complet (providers, RAG, MCP…) nécessite"
          f" le Core.{clr.C.RESET}")
    print(f"    {clr.C.DIM}Astuce : ETHAN_TOKEN=<jwt> ethan doctor pour"
          f" l'authentification.{clr.C.RESET}")
    print()
    print(f"  {clr.C.BOLD}Prérequis système (BootDiagnostic) :{clr.C.RESET}")
    print()
    diag = BootDiagnostic()
    report_boot = diag.check_all()
    for check in report_boot.checks:
        icon = f"{clr.C.GREEN}✓{clr.C.RESET}" if check.passed else f"{clr.C.RED}✗{clr.C.RESET}"
        print(f"  {icon} {check.name}")
        if check.detail and not check.passed:
            print(f"      {clr.C.DIM}→ {check.detail}{clr.C.RESET}")
        if check.fix and not check.passed:
            print(f"      {clr.C.DIM}↳ {check.fix}{clr.C.RESET}")
    print()
    if report_boot.all_passed:
        print(clr.success(
            f"Prérequis OK ({report_boot.passed_count}/"
            f"{report_boot.total_count}) — l'API ETHAN devrait démarrer :"
            " ./ethan up"
        ))
    else:
        print(clr.error(
            f"{len(report_boot.failures)} problème(s) de prérequis —"
            " corrigez-les puis relancez ./ethan up"
        ))
    print()
    return 1


def _render_api_report(report: dict) -> None:
    print()
    print(clr.section("Doctor  ◇  System Check"))
    print()
    summary = report.get("summary", {})
    status = summary.get("status", "unknown")
    color = {"healthy": clr.C.GREEN, "degraded": clr.C.YELLOW}.get(status, clr.C.RED)
    print(f"  {clr.C.BOLD}État global :{clr.C.RESET} {color}{status.upper()}"
          f"{clr.C.RESET}  {clr.C.DIM}({summary.get('total', '?')} composants)"
          f"{clr.C.RESET}")
    print()

    components = report.get("components", {})
    for name in sorted(components):
        comp = components[name]
        color, icon = STATUS_ICONS.get(comp.get("status", "unavailable"),
                                       (clr.C.DIM, "○"))
        duration = comp.get("duration_ms")
        dur_str = f"  {clr.C.DIM}({duration:.0f} ms){clr.C.RESET}" if duration else ""
        print(f"  {color}{icon}{clr.C.RESET} {comp.get('component', name):<14}"
              f" {comp.get('message', '')}{dur_str}")
        detail = comp.get("detail")
        if detail:
            print(f"      {clr.C.DIM}→ {detail}{clr.C.RESET}")
        for provider in (comp.get("metadata") or {}).get("providers", []):
            state = provider.get("state", "unavailable")
            pcolor, picon = STATUS_ICONS.get(state, (clr.C.DIM, "○"))
            print(f"      {pcolor}{picon}{clr.C.RESET} provider "
                  f"{provider.get('name')}: {state}"
                  + (f" — {provider.get('status')}" if provider.get("status") else ""))
    print()
