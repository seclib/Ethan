"""ETHAN status — show real system status from Docker.

Usage:
    ethan status              # Table view
    ethan status --json       # JSON output
    ethan status --watch      # Watch mode (refresh every 3s)

This command reads real data from:
  - Docker SDK (containers, health, ports)
  - NATS monitoring API (if available)
  - Redis ping (if available)
"""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any

from interfaces.cli.core.exit_codes import ExitCode
from interfaces.cli.registry import register
from interfaces.cli.core import colors as clr


def _get_core_info(timeout: float) -> dict[str, Any]:
    """Gather what the Core reports about itself.

    Every probe degrades independently: an unreachable Core yields
    ``reachable: False`` instead of aborting the whole status. Sections that
    fail are marked ``None`` rather than invented — the CLI never fabricates
    a health value the Core did not publish.
    """
    from interfaces.cli.core.api import api_get
    from interfaces.cli.core.client import get_base_url
    from interfaces.cli.core.errors import CLIError

    info: dict[str, Any] = {
        "reachable": False,
        "api_url": get_base_url(),
        "runtime": None,
        "providers": None,
        "models": None,
        "components": None,
        "errors": [],
    }

    try:
        state = api_get("/v1/state", timeout=timeout)
        info["runtime"] = state
        info["reachable"] = True
    except CLIError as exc:
        info["errors"].append({"section": "runtime", "detail": str(exc)})
        return info  # Core down: no point probing the other sections.

    for section, path in (
        ("providers", "/providers"),
        ("models", "/models"),
        ("components", "/diagnostics"),
    ):
        try:
            info[section] = api_get(path, timeout=timeout)
        except CLIError as exc:
            info[section] = None
            info["errors"].append({"section": section, "detail": str(exc)})

    return info


def _summary_counts(core: dict[str, Any]) -> dict[str, int]:
    """Counts of healthy / degraded / failed components from the Core."""
    payload = core.get("components")
    counts = {"ok": 0, "warning": 0, "error": 0, "unavailable": 0}
    if not isinstance(payload, dict):
        return counts
    components = payload.get("components") or payload.get("summary", {}).get("counts", {})
    if isinstance(components, dict) and all(
        isinstance(value, int) for value in components.values()
    ):
        return {**counts, **components}
    for check in (components or {}).values():
        status = str((check or {}).get("status", "")).lower()
        if status in counts:
            counts[status] += 1
    return counts


@register(
    "status",
    group="infra",
    description="Show ETHAN status (API, services, providers, models)",
    usage="ethan status [-o json] [--watch]",
)
def cmd_status(args: list[str]) -> int:
    """Display the real status of the stack and of the Core."""
    from interfaces.cli.core.context import get_context

    ctx = get_context()
    # `--json` stays accepted as an alias of `-o json` (§2.2).
    json_mode = ctx.is_json or "--json" in args
    watch_mode = "--watch" in args

    if json_mode and watch_mode:
        # A JSON document cannot be a live stream (§3.2).
        from interfaces.cli.core.errors import usage_error

        raise usage_error(
            "--watch is not supported with --output json",
            hint="drop --watch, or read the JSON once with -o json",
        )

    if watch_mode:
        try:
            while True:
                _render_status(core=_get_core_info(ctx.timeout))
                time.sleep(3)
        except KeyboardInterrupt:
            print(f"\n{clr.C.CYAN}◇ Stopped{clr.C.RESET}")
            return int(ExitCode.SUCCESS)

    info = _get_docker_info()
    core_info = _get_core_info(ctx.timeout)

    if json_mode:
        payload = {"docker": info, "core": core_info}
        print(json.dumps(payload, indent=2, default=str))
        return int(ExitCode.SUCCESS)

    _render_status(info=info, core=core_info)
    return int(ExitCode.SUCCESS)


def _get_docker_info() -> dict[str, Any]:
    """Gather real container info from Docker."""
    result = {
        "runtime": {"state": "unknown", "uptime": "N/A", "memory": "N/A", "cpu": "N/A"},
        "services": [],
        "error": None,
    }

    # Check if Docker is available
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        result["error"] = "Docker daemon not available"
        return result
    except subprocess.TimeoutExpired:
        result["error"] = "Docker daemon timeout"
        return result

    # Get container list
    try:
        output = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "name=ethan",
                "--format",
                "{{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = [line for line in output.stdout.strip().split("\n") if line.strip()]

        for line in lines:
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            name, status, ports, image = parts[0], parts[1], parts[2], parts[3]

            # Determine health from status string
            health = "unknown"
            if "healthy" in status.lower():
                health = "healthy"
            elif "unhealthy" in status.lower():
                health = "unhealthy"
            elif "up" in status.lower():
                health = "running"
            elif "exited" in status.lower():
                health = "exited"

            # Extract port
            port = ports.split("->")[0].split(":")[-1] if ports else "—"

            result["services"].append(
                {
                    "name": name.replace("ethan-", ""),
                    "container": name,
                    "status": "running" if "Up" in status else "exited",
                    "health": health,
                    "port": port,
                    "image": image.split("/")[-1] if "/" in image else image,
                }
            )

        # Runtime info from docker stats (first ethan container)
        if result["services"]:
            try:
                stats = subprocess.run(
                    [
                        "docker",
                        "stats",
                        "--no-stream",
                        "--format",
                        "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for stat_line in stats.stdout.strip().split("\n"):
                    if "ethan" in stat_line.lower():
                        parts = stat_line.split("\t")
                        if len(parts) >= 3:
                            result["runtime"]["cpu"] = parts[1].strip()
                            result["runtime"]["memory"] = parts[2].strip()
                            break
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        result["runtime"]["state"] = (
            "running" if any(s["status"] == "running" for s in result["services"]) else "stopped"
        )

    except subprocess.TimeoutExpired:
        result["error"] = "Docker command timed out"
    except Exception as e:
        result["error"] = str(e)

    return result


def _render_status(
    *, info: dict[str, Any] | None = None, core: dict[str, Any] | None = None
) -> None:
    """Render the Docker + Core status to the terminal."""
    if info is None:
        info = _get_docker_info()

    # ── Terminal output ──────────────────────────────────────────────
    if info.get("error"):
        print(f"\n  {clr.C.RED}✗ {info['error']}{clr.C.RESET}")
        print(
            f"  {clr.C.CYAN}→{clr.C.RESET} Make sure Docker is running: sudo systemctl start docker"
        )
    else:
        _render_docker_sections(info)

    if core is not None:
        _render_core_sections(core)

    print()


def _render_docker_sections(info: dict[str, Any]) -> None:
    """Render the Docker-derived part of the status."""
    runtime = info["runtime"]
    services = info["services"]

    state_color = clr.C.GREEN if runtime["state"] == "running" else clr.C.RED
    print()
    print(
        f"  {clr.C.BOLD}ETHAN Status{clr.C.RESET}  {state_color}◇ {runtime['state'].upper()}{clr.C.RESET}"
    )
    print()

    print(f"  {clr.C.BOLD}Runtime{clr.C.RESET}")
    print(f"    State:   {state_color}{runtime['state']}{clr.C.RESET}")
    print(f"    CPU:     {clr.C.DIM}{runtime['cpu']}{clr.C.RESET}")
    print(f"    Memory:  {clr.C.DIM}{runtime['memory']}{clr.C.RESET}")
    print()

    print(f"  {clr.C.BOLD}Services{clr.C.RESET}")
    if not services:
        print(f"    {clr.C.DIM}No ETHAN containers found{clr.C.RESET}")
    else:
        print(f"    {'SERVICE':<18} {'STATUS':<10} {'HEALTH':<12} {'PORT':<8}")
        print(f"    {'─' * 18} {'─' * 10} {'─' * 12} {'─' * 8}")

        for svc in services:
            status_icon = (
                f"{clr.C.GREEN}●{clr.C.RESET}"
                if svc["status"] == "running"
                else f"{clr.C.RED}○{clr.C.RESET}"
            )
            health_color = (
                clr.C.GREEN
                if svc["health"] == "healthy"
                else clr.C.RED
                if svc["health"] in ("unhealthy", "exited")
                else clr.C.YELLOW
            )
            print(
                f"    {svc['name']:<18} "
                f"{status_icon} {svc['status']:<7} "
                f"{health_color}{svc['health']:<12}{clr.C.RESET} "
                f"{svc['port']:<8}"
            )
    print()

    running = sum(1 for s in services if s["status"] == "running")
    healthy = sum(1 for s in services if s["health"] == "healthy")
    total = len(services)
    if total > 0:
        print(f"    {clr.C.DIM}{running}/{total} running, {healthy}/{total} healthy{clr.C.RESET}")


def _render_core_sections(core: dict[str, Any]) -> None:
    """Render the Core-derived part: API, providers, models, components."""
    print()
    if not core.get("reachable"):
        print(f"  {clr.C.BOLD}Core API{clr.C.RESET}  {clr.C.RED}○ unreachable{clr.C.RESET}")
        print(f"    {clr.C.DIM}↳ {core.get('api_url', '')}{clr.C.RESET}")
        for error in core.get("errors", []):
            print(f"    {clr.C.DIM}↳ {error['section']}: {error['detail']}{clr.C.RESET}")
        print(f"    {clr.C.DIM}↳ start the stack: ./ethan up{clr.C.RESET}")
        return

    runtime = core.get("runtime") or {}
    mode = runtime.get("mode") or runtime.get("status") or "running"
    colour = clr.C.GREEN if str(mode) in ("running", "ok", "healthy") else clr.C.YELLOW
    print(f"  {clr.C.BOLD}Core API{clr.C.RESET}  {colour}● {mode}{clr.C.RESET}")
    print(f"    {clr.C.DIM}{core.get('api_url', '')}{clr.C.RESET}")

    providers = core.get("providers")
    if isinstance(providers, list):
        connected = sum(1 for p in providers if (p or {}).get("status") == "connected")
        enabled = sum(1 for p in providers if (p or {}).get("enabled"))
        print(f"    providers: {connected}/{len(providers)} connected, {enabled} enabled")
        for provider in providers:
            state = (provider or {}).get("status", "unknown")
            icon = (
                f"{clr.C.GREEN}●{clr.C.RESET}"
                if state == "connected"
                else f"{clr.C.YELLOW}○{clr.C.RESET}"
            )
            print(f"      {icon} {provider.get('id')} — {state}")

    models = core.get("models")
    if isinstance(models, list):
        print(f"    models: {len(models)} available")
    elif isinstance(models, dict) and isinstance(models.get("models"), list):
        print(f"    models: {len(models['models'])} available")

    counts = _summary_counts(core)
    total = sum(counts.values())
    if total:
        colour = clr.C.GREEN if not counts["error"] else clr.C.RED
        print(
            f"    components: {colour}{counts['ok']}/{total} healthy{clr.C.RESET},"
            f" {counts['warning']} warning, {counts['error']} error"
        )
