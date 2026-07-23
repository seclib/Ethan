"""Command Performance Benchmark — measure individual CLI command response times."""

from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path

from .benchmark_runner import BenchmarkResult


CLI_ROOT = Path(__file__).parent.parent.parent
CLI_ENTRY = str(CLI_ROOT / "cli" / "ethan")


class CommandsBenchmark:
    """Benchmark individual CLI commands: help, status, version, suggest."""

    COMMANDS = [
        ("help", ["help"]),
        ("version", ["version"]),
        ("status", ["status"]),
        ("suggest", ["suggest"]),
        ("logs", ["logs"]),
        ("plugins", ["plugin", "list"]),
    ]

    def run(self, samples: int = 3) -> list[BenchmarkResult]:
        """Run benchmarks for each command."""
        os.environ["ETHAN_BENCH"] = "1"
        results = []

        for cmd_name, cmd_args in self.COMMANDS:
            result = self._benchmark_command(cmd_name, cmd_args, samples)
            results.append(result)

        return results

    def _benchmark_command(self, name: str, args: list[str], samples: int) -> BenchmarkResult:
        """Benchmark a single command."""
        metrics = BenchmarkResult(group="commands", name=f"`ethan {name}`", samples=samples)
        timings = []

        for i in range(samples):
            start = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, CLI_ENTRY] + args,
                capture_output=True, text=True, timeout=30
            )
            elapsed = (time.perf_counter() - start) * 1000.0
            timings.append(elapsed)

        if timings:
            avg = sum(timings) / len(timings)
            metrics.add_metric("avg_response_ms", avg, "ms",
                               warn=500 if name != "help" else 200,
                               fail=2000 if name != "help" else 1000)
            metrics.add_metric("min_response_ms", min(timings), "ms")
            metrics.add_metric("max_response_ms", max(timings), "ms")
            if len(timings) > 1:
                std = (sum((t - avg) ** 2 for t in timings) / len(timings)) ** 0.5
                metrics.add_metric("std_response_ms", std, "ms")

        metrics.duration_ms = sum(timings)
        return metrics