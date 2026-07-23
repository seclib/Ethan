"""Daemon Impact Benchmark — measure daemon's effect on CLI responsiveness."""

from __future__ import annotations

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

from .benchmark_runner import BenchmarkResult


CLI_ROOT = Path(__file__).parent.parent.parent
CLI_ENTRY = str(CLI_ROOT / "cli" / "ethan")


class DaemonBenchmark:
    """Benchmark daemon impact on CLI speed and measure daemon resource usage."""

    def run(self, samples: int = 3) -> list[BenchmarkResult]:
        """Run daemon benchmarks: with, without daemon, and resource usage."""
        os.environ["ETHAN_BENCH"] = "1"
        results = []

        # --- Without daemon ---
        without = self._benchmark_without_daemon(samples)
        results.append(without)

        # --- With daemon ---
        with_daemon = self._benchmark_with_daemon(samples)
        results.append(with_daemon)

        # --- Daemon resource usage ---
        resources = self._benchmark_daemon_resources()
        results.append(resources)

        return results

    def _benchmark_without_daemon(self, samples: int) -> BenchmarkResult:
        """Benchmark commands when daemon is NOT running."""
        metrics = BenchmarkResult(group="daemon", name="CLI Without Daemon", samples=samples)
        timings = []

        for i in range(samples):
            start = time.perf_counter()
            subprocess.run(
                [sys.executable, CLI_ENTRY, "--help"],
                capture_output=True, text=True, timeout=30
            )
            elapsed = (time.perf_counter() - start) * 1000.0
            timings.append(elapsed)

        if timings:
            avg = sum(timings) / len(timings)
            metrics.add_metric("avg_no_daemon_ms", avg, "ms", warn=500, fail=2000)
        metrics.duration_ms = sum(timings)
        return metrics

    def _benchmark_with_daemon(self, samples: int) -> BenchmarkResult:
        """Benchmark commands when daemon IS running."""
        metrics = BenchmarkResult(group="daemon", name="CLI With Daemon", samples=samples)
        timings = []
        daemon_proc = None

        try:
            # Start daemon in background
            daemon_proc = subprocess.Popen(
                [sys.executable, CLI_ENTRY, "daemon", "start"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(1)  # Wait for daemon to start

            for i in range(samples):
                start = time.perf_counter()
                subprocess.run(
                    [sys.executable, CLI_ENTRY, "--help"],
                    capture_output=True, text=True, timeout=30
                )
                elapsed = (time.perf_counter() - start) * 1000.0
                timings.append(elapsed)
        finally:
            if daemon_proc:
                daemon_proc.terminate()
                try:
                    daemon_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    daemon_proc.kill()

        if timings:
            avg = sum(timings) / len(timings)
            metrics.add_metric("avg_with_daemon_ms", avg, "ms", warn=300, fail=1000)
        metrics.duration_ms = sum(timings)
        return metrics

    def _benchmark_daemon_resources(self) -> BenchmarkResult:
        """Measure daemon resource usage (RSS, CPU)."""
        metrics = BenchmarkResult(group="daemon", name="Daemon Resource Usage", samples=1)
        daemon_proc = None

        try:
            daemon_proc = subprocess.Popen(
                [sys.executable, CLI_ENTRY, "daemon", "start"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(2)  # Let it stabilize

            # Measure RSS
            try:
                import psutil
                proc = psutil.Process(daemon_proc.pid)
                rss_mb = proc.memory_info().rss / (1024 * 1024)
                cpu_pct = proc.cpu_percent(interval=1.0)
                metrics.add_metric("daemon_rss_mb", rss_mb, "MB", warn=50, fail=200)
                metrics.add_metric("daemon_cpu_pct", cpu_pct, "%", warn=10, fail=50)
            except ImportError:
                # Fallback: read /proc
                try:
                    with open(f"/proc/{daemon_proc.pid}/status") as f:
                        for line in f:
                            if line.startswith("VmRSS:"):
                                rss_kb = float(line.split()[1])
                                metrics.add_metric("daemon_rss_mb", rss_kb / 1024, "MB")
                                break
                except (OSError, ValueError):
                    metrics.add_metric("daemon_rss_mb", -1, "MB")

        finally:
            if daemon_proc:
                daemon_proc.terminate()
                try:
                    daemon_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    daemon_proc.kill()

        return metrics