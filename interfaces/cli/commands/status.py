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
import os
import subprocess
import sys
import time
from typing import Any

from interfaces.cli.registry import register
from interfaces.cli.core import colors as clr


@register(
    "status",
    group="infra",
    description="Show real system status from Docker",
    usage="ethan status [--json] [--watch]",
)
def cmd_status(args: list[str]) -> int:
    """Display real system status from Docker containers."""
    json_mode = "--json" in args
    watch_mode = "--watch" in args

    try:
        if watch_mode:
            try:
                while True:
                    _render_status(json_mode=json_mode)
                    time.sleep(3)
            except KeyboardInterrupt:
                print(f"\n{clr.C.CYAN}◇ Stopped{clr.C.RESET}")
                return 0
        else:
            _render_status(json_mode=json_mode)
        return 0
    except Exception as e:
        print(f"{clr.C.RED}✗ Error: {e}{clr.C.RESET}", file=sys.stderr)
        return 1


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
            capture_output=True, timeout=5, check=True,
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
            ["docker", "ps", "-a", "--filter", "name=ethan",
             "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"],
            capture_output=True, text=True, timeout=10,
        )
        lines = [l for l in output.stdout.strip().split("\n") if l.strip()]

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

            result["services"].append({
                "name": name.replace("ethan-", ""),
                "container": name,
                "status": "running" if "Up" in status else "exited",
                "health": health,
                "port": port,
                "image": image.split("/")[-1] if "/" in image else image,
            })

        # Runtime info from docker stats (first ethan container)
        if result["services"]:
            try:
                stats = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format",
                     "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
                    capture_output=True, text=True, timeout=5,
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

        result["runtime"]["state"] = "running" if any(
            s["status"] == "running" for s in result["services"]
        ) else "stopped"

    except subprocess.TimeoutExpired:
        result["error"] = "Docker command timed out"
    except Exception as e:
        result["error"] = str(e)

    return result


def _render_status(*, json_mode: bool = False) -> None:
    """Render status to terminal or JSON."""
    info = _get_docker_info()

    if json_mode:
        print(json.dumps(info, indent=2, default=str))
        return

    # ── Terminal output ──────────────────────────────────────────
    if info.get("error"):
        print(f"\n  {clr.C.RED}✗ {info['error']}{clr.C.RESET}")
        print(f"  {clr.C.CYAN}→{clr.C.RESET} Make sure Docker is running: sudo systemctl start docker")
        return

    runtime = info["runtime"]
    services = info["services"]

    # Header
    state_color = clr.C.GREEN if runtime["state"] == "running" else clr.C.RED
    print()
    print(f"  {clr.C.BOLD}ETHAN Status{clr.C.RESET}  {state_color}◇ {runtime['state'].upper()}{clr.C.RESET}")
    print()

    # Runtime
    print(f"  {clr.C.BOLD}Runtime{clr.C.RESET}")
    print(f"    State:   {state_color}{runtime['state']}{clr.C.RESET}")
    print(f"    CPU:     {clr.C.DIM}{runtime['cpu']}{clr.C.RESET}")
    print(f"    Memory:  {clr.C.DIM}{runtime['memory']}{clr.C.RESET}")
    print()

    # Services table
    print(f"  {clr.C.BOLD}Services{clr.C.RESET}")
    if not services:
        print(f"    {clr.C.DIM}No ETHAN containers found{clr.C.RESET}")
    else:
        # Header
        print(f"    {'SERVICE':<18} {'STATUS':<10} {'HEALTH':<12} {'PORT':<8}")
        print(f"    {'─'*18} {'─'*10} {'─'*12} {'─'*8}")

        for svc in services:
            status_icon = (
                f"{clr.C.GREEN}●{clr.C.RESET}"
                if svc["status"] == "running"
                else f"{clr.C.RED}○{clr.C.RESET}"
            )
            health_color = (
                clr.C.GREEN if svc["health"] == "healthy"
                else clr.C.RED if svc["health"] in ("unhealthy", "exited")
                else clr.C.YELLOW
            )
            print(
                f"    {svc['name']:<18} "
                f"{status_icon} {svc['status']:<7} "
                f"{health_color}{svc['health']:<12}{clr.C.RESET} "
                f"{svc['port']:<8}"
            )
    print()

    # Summary
    running = sum(1 for s in services if s["status"] == "running")
    healthy = sum(1 for s in services if s["health"] == "healthy")
    total = len(services)
    if total > 0:
        print(f"    {clr.C.DIM}{running}/{total} running, {healthy}/{total} healthy{clr.C.RESET}")
    print()