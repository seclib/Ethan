"""ETHAN Bench — CLI performance benchmark command.

Usage:
    ethan bench                 Run all benchmarks
    ethan bench --cold          Cold start only
    ethan bench --commands      Command performance only
    ethan bench --api           API latency only
    ethan bench --daemon        Daemon impact only
    ethan bench --streaming     Streaming performance only
    ethan bench --json          Output as JSON
    ethan bench --md            Save Markdown report
    ethan bench --verbose       Show detailed output
"""

from __future__ import annotations

import sys
import json
from pathlib import Path
from interfaces.cli.registry import register
from interfaces.cli.core.telemetry import telemetry

# Ensure root project dir is importable for tests package
_ROOT = str(Path(__file__).resolve().parents[2])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _get_runner(groups, verbose):
    """Lazy import of benchmarks to avoid coupling with tests package."""
    from tests.benchmarks.benchmark_runner import BenchmarkRunner
    return BenchmarkRunner(groups=groups, verbose=verbose)


@register("bench")
def cmd_bench(args: list[str]) -> int:
    """Run the ETHAN CLI benchmark suite.

    Args:
        args: Command-line arguments (flags).

    Returns:
        Exit code (0 = success).
    """
    # Parse arguments
    flags = set(args)
    groups = _parse_groups(flags)
    verbose = "--verbose" in flags or "-v" in flags
    as_json = "--json" in flags or "-j" in flags
    save_md = "--md" in flags or "-m" in flags

    # Enable telemetry
    telemetry._enabled = True

    # Run benchmarks (lazy import)
    runner = _get_runner(groups, verbose)

    # Show header
    print()
    print("\033[38;5;39m◆\033[0m  ETHAN CLI Benchmark Suite")
    if groups == ["all"]:
        print("  Running: cold start, commands, API, daemon, streaming")
    else:
        print(f"  Groups: {', '.join(groups)}")
    print()

    report = runner.run_all()

    # Output
    if as_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        runner.print_report()

    # Save Markdown report
    if save_md:
        md_path = report.save_markdown()
        print(f"  \033[38;5;44mℹ\033[0m Report saved to: {md_path}")

    # Return exit code based on failures
    if report.total_failures > 0:
        return 1
    return 0


def _parse_groups(flags: set[str]) -> list[str]:
    """Parse command-line flags to determine benchmark groups."""
    group_map = {
        "--cold": "cold",
        "--commands": "commands",
        "--api": "api",
        "--daemon": "daemon",
        "--streaming": "streaming",
    }

    selected = []
    for flag, group in group_map.items():
        if flag in flags:
            selected.append(group)

    return selected if selected else ["all"]