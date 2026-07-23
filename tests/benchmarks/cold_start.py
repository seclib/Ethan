"""Cold Start & Discovery Benchmark — measure CLI startup performance."""

from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path

from .benchmark_runner import BenchmarkResult


CLI_ROOT = Path(__file__).parent.parent.parent
CLI_ENTRY = str(CLI_ROOT / "cli" / "ethan")


class ColdStartBenchmark:
    """Benchmark CLI cold start, warming, command discovery, and dispatch."""

    def run(self, samples: int = 5) -> list[BenchmarkResult]:
        """Run cold start and discovery benchmarks.

        Returns two BenchmarkResult objects:
          - "Cold Start & Discovery" (cold_start_ms, warm_start_ms, discovery_ms)
          - "Command Dispatch" (dispatch_ms for each command)
        """
        os.environ["ETHAN_BENCH"] = "1"

        results = []

        # --- Cold Start ---
        cold_metrics = BenchmarkResult(group="cold", name="CLI Startup", samples=samples)
        cold_times = []
        for i in range(samples):
            start = time.perf_counter()
            result = subprocess.run(
                [sys.executable, CLI_ENTRY, "help"],
                capture_output=True, text=True, timeout=30
            )
            elapsed = (time.perf_counter() - start) * 1000.0
            cold_times.append(elapsed)

        if cold_times:
            avg_cold = sum(cold_times) / len(cold_times)
            min_cold = min(cold_times)
            max_cold = max(cold_times)
            cold_metrics.add_metric("avg_cold_start_ms", avg_cold, "ms", warn=500, fail=2000)
            cold_metrics.add_metric("min_cold_start_ms", min_cold, "ms")
            cold_metrics.add_metric("max_cold_start_ms", max_cold, "ms")
            if len(cold_times) > 1:
                std = (sum((t - avg_cold) ** 2 for t in cold_times) / len(cold_times)) ** 0.5
                cold_metrics.add_metric("std_cold_start_ms", std, "ms")
        cold_metrics.duration_ms = sum(cold_times)
        results.append(cold_metrics)

        # --- Warm Start (after cold start, Python caches imports) ---
        warm_times = []
        for i in range(samples):
            start = time.perf_counter()
            result = subprocess.run(
                [sys.executable, CLI_ENTRY, "help"],
                capture_output=True, text=True, timeout=30
            )
            elapsed = (time.perf_counter() - start) * 1000.0
            warm_times.append(elapsed)

        if warm_times:
            avg_warm = sum(warm_times) / len(warm_times)
            cold_metrics.add_metric("avg_warm_start_ms", avg_warm, "ms", warn=200, fail=500)

        # --- Command Discovery ---
        discovery_metrics = BenchmarkResult(group="cold", name="Command Discovery", samples=1)
        discover_times = []
        # Test discovery by importing the registry directly
        for i in range(samples):
            start = time.perf_counter()
            result = subprocess.run(
                [sys.executable, "-c", """
import sys
sys.path.insert(0, 'cli')
from registry import discover_commands, COMMANDS
discover_commands()
print(len(COMMANDS))
"""],
                capture_output=True, text=True, timeout=30, cwd=str(CLI_ROOT)
            )
            elapsed = (time.perf_counter() - start) * 1000.0
            discover_times.append(elapsed)
            last_discovery_result = result

        if discover_times:
            avg_discover = sum(discover_times) / len(discover_times)
            discovery_metrics.add_metric("avg_discovery_ms", avg_discover, "ms", warn=200, fail=500)
            try:
                cmd_count = int(last_discovery_result.stdout.strip())
                discovery_metrics.add_metric("commands_found", float(cmd_count), "count")
            except (ValueError, IndexError):
                pass
        discovery_metrics.duration_ms = sum(discover_times)
        results.append(discovery_metrics)

        return results