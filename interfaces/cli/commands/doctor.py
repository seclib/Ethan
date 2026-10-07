"""ETHAN doctor — real diagnostics, reported as PASS / WARN / FAIL.

Contract : docs/specs/CLI_CONTRACT.md §8.15.

Every check comes from the Core: `GET /diagnostics` runs the real probes of
`core/diagnostics/system.py` (postgres, redis, nats, kernel, docker,
providers, models, knowledge, tools, mcp, plugins, filesystem + host
resources) and the CLI only renders the verdict. No check is invented here —
a diagnostic the Core does not perform does not exist for ETHAN.

The Core statuses are mapped, not re-invented:

    ok          → PASS
    warning     → WARN
    unavailable → WARN  (an absent optional component is not an outage)
    error       → FAIL

Exit code: 0 when nothing failed, 1 as soon as one component FAILs (§8.15).
When the Core cannot be reached, the local pre-flight (`BootDiagnostic`) is
reported instead — explaining WHY the report is missing is precisely what
doctor is for. `-o json` returns the Core report verbatim (§4.2).
"""

from __future__ import annotations

from interfaces.cli.core import colors as clr
from interfaces.cli.core.api import ExitCode, api_get, emit, subcommand
from interfaces.cli.core.client import get_base_url
from interfaces.cli.core.context import get_context
from interfaces.cli.core.diagnostic import BootDiagnostic
from interfaces.cli.core.errors import CLIError
from interfaces.cli.registry import register

VERBS = {
    "run": "run the full Core diagnostic",
    "preflight": "run the local pre-flight checks only",
}

USAGE = "ethan doctor [run|preflight] [--components a,b] [-o json]"

#: Core status → operator-facing verdict.
VERDICTS = {
    "ok": ("PASS", clr.C.GREEN, "✓"),
    "warning": ("WARN", clr.C.YELLOW, "▲"),
    "unavailable": ("WARN", clr.C.YELLOW, "○"),
    "error": ("FAIL", clr.C.RED, "✗"),
}


def verdict_of(status: str) -> tuple[str, str, str]:
    """Map a Core status onto (PASS|WARN|FAIL, colour, icon)."""
    return VERDICTS.get(str(status).lower(), ("WARN", clr.C.YELLOW, "?"))


def _components_option(args: list[str]) -> list[str] | None:
    """Parse `--components a,b` so an operator can narrow the run."""
    if "--components" not in args:
        return None
    index = args.index("--components")
    if index + 1 >= len(args):
        return None
    return [part.strip() for part in args[index + 1].split(",") if part.strip()]


@register(
    "doctor",
    group="infra",
    description="Run real system diagnostics (PASS/WARN/FAIL)",
    usage=USAGE,
)
def cmd_doctor(args: list[str]) -> int:
    """Diagnose ETHAN through the Core, or explain why it cannot be reached."""
    # `preflight` never touches the network, so it bypasses the verb parser.
    if args and args[0] == "preflight":
        return _run_preflight()

    verb, rest = subcommand(args, VERBS, command="doctor", usage=USAGE, default="run")
    if verb == "preflight":
        return _run_preflight()

    wanted = _components_option(rest)
    try:
        report = api_get(
            "/diagnostics",
            params={"components": ",".join(wanted)} if wanted else None,
        )
    except CLIError as exc:
        # No Core report: fall back to the local pre-flight and say why.
        # Every transport failure is a CLIError subclass (APIError for HTTP,
        # connection_error for an unreachable Core, timeout_error for a
        # deadline), so one catch covers them all.
        if get_context().is_json:
            emit(
                {
                    "error": {
                        "code": "unavailable",
                        "message": str(exc),
                        "hint": "start ETHAN first: ./ethan up",
                    }
                }
            )
            return int(ExitCode.OPERATION_FAILED)
        _render_unreachable(exc)
        return _run_preflight(json_mode=False)

    if get_context().is_json:
        # The Core report is passed through untouched (§4.2).
        emit(report)
    else:
        _render_report(report)

    counts = (report.get("summary") or {}).get("counts") or {}
    if counts.get("error"):
        return int(ExitCode.OPERATION_FAILED)
    return int(ExitCode.SUCCESS)


def _render_report(report: dict) -> None:
    """Render the Core report as an aligned PASS/WARN/FAIL table."""
    summary = report.get("summary") or {}
    overall = summary.get("status", "unknown")
    colour = {"healthy": clr.C.GREEN, "degraded": clr.C.YELLOW}.get(overall, clr.C.RED)

    print()
    print(clr.section("Doctor — system check"))
    print(
        f"  overall: {colour}{overall.upper()}{clr.C.RESET}"
        f"  {clr.C.DIM}({summary.get('total', '?')} components){clr.C.RESET}"
    )
    print()

    components = report.get("components") or {}
    # Deterministic order: failures first, then warnings, then passes.
    ordered = sorted(
        components.items(),
        key=lambda item: (
            {"error": 0, "warning": 1, "unavailable": 1}.get(
                str(item[1].get("status", "")).lower(), 2
            ),
            item[0],
        ),
    )

    for name, check in ordered:
        status = str(check.get("status", "unavailable"))
        label, colour, icon = verdict_of(status)
        duration = check.get("duration_ms")
        timing = f"  {clr.C.DIM}{float(duration):.0f} ms{clr.C.RESET}" if duration else ""
        print(f"  {colour}{icon} {label:<4}{clr.C.RESET} {check.get('component', name)}{timing}")
        message = check.get("message")
        if message:
            print(f"        {clr.C.DIM}→ {message}{clr.C.RESET}")
        detail = check.get("detail")
        if detail:
            print(f"        {clr.C.DIM}↳ {detail}{clr.C.RESET}")
        for provider in (check.get("metadata") or {}).get("providers", []):
            p_label, p_colour, p_icon = verdict_of(provider.get("state", "unavailable"))
            print(
                f"        {p_colour}{p_icon}{clr.C.RESET} provider"
                f" {provider.get('name')}: {p_label}"
                + (f" — {provider['status']}" if provider.get("status") else "")
            )
    print()


def _render_unreachable(exc: Exception) -> None:
    """Explain why no Core report could be obtained."""
    print()
    print(clr.section("Doctor — system check"))
    status = getattr(exc, "status", None)
    if status in (401, 403):
        print(f"  {clr.C.YELLOW}▲ WARN{clr.C.RESET} Core API reachable but unauthenticated")
        print(f"    {clr.C.DIM}↳ run: ethan auth login{clr.C.RESET}")
    else:
        print(f"  {clr.C.RED}✗ FAIL{clr.C.RESET} Core API unreachable ({get_base_url()})")
        print(f"    {clr.C.DIM}↳ {exc}{clr.C.RESET}")
        print(f"    {clr.C.DIM}↳ start the stack first: ./ethan up{clr.C.RESET}")
    print(f"  {clr.C.DIM}the full report (providers, RAG, MCP…) needs the Core{clr.C.RESET}")
    print()


def _run_preflight(json_mode: bool = False) -> int:
    """Run the local pre-flight checks (no Core required)."""
    report = BootDiagnostic().check_all()

    if json_mode or get_context().is_json:
        emit(
            {
                "summary": {
                    "total": report.total_count,
                    "passed": report.passed_count,
                    "failed": report.total_count - report.passed_count,
                },
                "checks": [
                    {
                        "check": check.name,
                        "status": "ok" if check.passed else "error",
                        "detail": check.detail,
                        "fix": check.fix,
                    }
                    for check in report.checks
                ],
            }
        )
        return (
            int(ExitCode.SUCCESS)
            if report.passed_count == report.total_count
            else int(ExitCode.OPERATION_FAILED)
        )

    print()
    print(clr.section("Preflight — local prerequisites"))
    print()
    for check in report.checks:
        if check.passed:
            label, colour, icon = "PASS", clr.C.GREEN, "✓"
        elif check.name == "Ports requis":
            # Occupied ports while the stack runs are expected, not a failure.
            label, colour, icon = "WARN", clr.C.YELLOW, "▲"
        else:
            label, colour, icon = "FAIL", clr.C.RED, "✗"
        print(f"  {colour}{icon} {label:<4}{clr.C.RESET} {check.name}")
        if check.detail and not check.passed:
            print(f"        {clr.C.DIM}→ {check.detail}{clr.C.RESET}")
        if check.fix and not check.passed:
            print(f"        {clr.C.DIM}↳ {check.fix}{clr.C.RESET}")
    print()
    print(
        f"  {clr.C.DIM}{report.passed_count}/{report.total_count} prerequisite(s) met{clr.C.RESET}"
    )
    print()
    return (
        int(ExitCode.SUCCESS)
        if report.passed_count == report.total_count
        else int(ExitCode.OPERATION_FAILED)
    )
