"""ETHAN CLI Telemetry — minimal instrumentation for benchmark.

Provides lightweight timers and counters for measuring CLI performance
without modifying existing command handlers. Designed for the benchmark
suite, not for production monitoring (use core/metrics/ for that).
"""

import os
import time
import threading
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class TelemetrySnapshot:
    """Point-in-time snapshot of CLI telemetry."""
    cold_start_ms: float = 0.0
    discovery_ms: float = 0.0
    dispatch_ms: float = 0.0
    command_timings: dict[str, float] = field(default_factory=dict)
    api_latencies: list[float] = field(default_factory=list)
    prompt_count: int = 0
    rss_mb: float = 0.0


class CLITelemetry:
    """Minimal CLI instrumentation.

    Usage:
        telemetry = CLITelemetry()
        telemetry.start("cold_start")
        # ... work ...
        ms = telemetry.stop("cold_start")
    """

    def __init__(self, enabled: bool = True):
        self._enabled = enabled and os.environ.get("ETHAN_BENCH", "") != ""
        self._timers: dict[str, float] = {}
        self._counters: dict[str, int] = {}
        self._command_timings: dict[str, float] = {}
        self._api_latencies: list[float] = []
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self, label: str) -> None:
        """Start a named timer."""
        if not self._enabled:
            return
        with self._lock:
            self._timers[label] = time.perf_counter()

    def stop(self, label: str) -> float | None:
        """Stop a named timer and return duration in milliseconds.

        Returns None if timer wasn't started or telemetry disabled.
        """
        if not self._enabled:
            return None
        with self._lock:
            start = self._timers.pop(label, None)
            if start is None:
                return None
            duration_ms = (time.perf_counter() - start) * 1000.0
            self._command_timings[label] = duration_ms
            return duration_ms

    def inc(self, counter: str, delta: int = 1) -> None:
        """Increment a named counter."""
        if not self._enabled:
            return
        with self._lock:
            self._counters[counter] = self._counters.get(counter, 0) + delta

    def record_api_latency(self, duration_ms: float) -> None:
        """Record an API call latency."""
        if not self._enabled:
            return
        with self._lock:
            self._api_latencies.append(duration_ms)

    def snapshot(self) -> TelemetrySnapshot:
        """Return current telemetry snapshot."""
        snap = TelemetrySnapshot()
        with self._lock:
            snap.cold_start_ms = self._command_timings.get("cold_start", 0.0)
            snap.discovery_ms = self._command_timings.get("discovery", 0.0)
            snap.dispatch_ms = self._command_timings.get("dispatch", 0.0)
            snap.command_timings = dict(self._command_timings)
            snap.api_latencies = list(self._api_latencies)
            snap.prompt_count = self._counters.get("prompts", 0)
        snap.rss_mb = self._get_rss()
        return snap

    def reset(self) -> None:
        """Reset all telemetry."""
        with self._lock:
            self._timers.clear()
            self._counters.clear()
            self._command_timings.clear()
            self._api_latencies.clear()

    @staticmethod
    def _get_rss() -> float:
        """Return current RSS in MB (cross-platform)."""
        try:
            import psutil
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback: read /proc/self/status (Linux)
            try:
                with open("/proc/self/status") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            return float(line.split()[1]) / 1024.0
            except (OSError, IndexError, ValueError):
                pass
            return 0.0


# Global singleton
telemetry = CLITelemetry()


# Context manager for easy benchmarking
class benchmark:
    """Context manager for benchmarking a code block.

    Usage:
        with benchmark("cold_start"):
            cli_startup()
    """

    def __init__(self, label: str):
        self.label = label
        self._start = 0.0

    def __enter__(self):
        if telemetry.enabled:
            self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        if telemetry.enabled and self._start:
            duration_ms = (time.perf_counter() - self._start) * 1000.0
            with telemetry._lock:
                telemetry._command_timings[self.label] = duration_ms