"""Streaming Performance Benchmark — measure streaming throughput and latency."""

from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path

from .benchmark_runner import BenchmarkResult


CLI_ROOT = Path(__file__).parent.parent.parent
CLI_ENTRY = str(CLI_ROOT / "cli" / "ethan")


class StreamingBenchmark:
    """Benchmark streaming output performance: first token latency, throughput."""

    def run(self, samples: int = 3) -> list[BenchmarkResult]:
        """Run streaming benchmarks."""
        os.environ["ETHAN_BENCH"] = "1"
        results = []

        # --- Streamer component benchmark ---
        streamer_result = self._benchmark_streamer_component(samples)
        results.append(streamer_result)

        # --- Spinner performance ---
        spinner_result = self._benchmark_spinner(samples)
        results.append(spinner_result)

        # --- Prompt rendering throughput ---
        prompt_result = self._benchmark_prompt_rendering(samples)
        results.append(prompt_result)

        return results

    def _benchmark_streamer_component(self, samples: int) -> BenchmarkResult:
        """Benchmark the Streamer class directly."""
        metrics = BenchmarkResult(group="streaming", name="Streamer Component", samples=samples)

        # Test by importing and using the streamer
        for i in range(samples):
            start = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, "-c", """
import sys
sys.path.insert(0, 'cli/core')
import time
from streaming import Streamer

# Benchmark streamer initialization
t0 = time.perf_counter()
s = Streamer()
t1 = time.perf_counter()
init_ms = (t1 - t0) * 1000

# Benchmark streamer write throughput
num_chunks = 100
s._start_time = time.time()
t0 = time.perf_counter()
for j in range(num_chunks):
    s.write(f"chunk {j} ")
t1 = time.perf_counter()
write_ms = (t1 - t0) * 1000

print(f"{init_ms:.2f},{write_ms:.2f}")
"""],
                capture_output=True, text=True, timeout=30, cwd=str(CLI_ROOT)
            )
            elapsed = (time.perf_counter() - start) * 1000.0

            try:
                parts = proc.stdout.strip().split(",")
                init_ms = float(parts[0])
                write_ms = float(parts[1])
                if i == 0:
                    metrics.add_metric("streamer_init_ms", init_ms, "ms", warn=5, fail=20)
                    metrics.add_metric("streamer_write_100chunks_ms", write_ms, "ms", warn=50, fail=200)
            except (ValueError, IndexError):
                pass

        metrics.duration_ms = 0
        return metrics

    def _benchmark_spinner(self, samples: int) -> BenchmarkResult:
        """Benchmark spinner frames per second."""
        metrics = BenchmarkResult(group="streaming", name="Spinner Performance", samples=samples)

        for i in range(samples):
            proc = subprocess.run(
                [sys.executable, "-c", """
import sys
sys.path.insert(0, 'cli/core')
import time
from streaming import Streamer

s = Streamer()
s._start_spinner()
time.sleep(1)
s._stop_spinner()
print("ok")
"""],
                capture_output=True, text=True, timeout=30, cwd=str(CLI_ROOT)
            )
            success = proc.stdout.strip() == "ok"
            if i == 0:
                metrics.add_metric("spinner_works", 1.0 if success else 0.0, "bool")

        metrics.duration_ms = 0
        return metrics

    def _benchmark_prompt_rendering(self, samples: int) -> BenchmarkResult:
        """Benchmark prompt rendering speed (formatting output)."""
        metrics = BenchmarkResult(group="streaming", name="Prompt Rendering", samples=samples)

        for i in range(samples):
            start = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, "-c", """
import sys
sys.path.insert(0, 'cli/core')
from colors import C, I

# Simulate rendering various output elements
outputs = []
for _ in range(1000):
    outputs.append(f"{C.GREEN}{I.CHECK} test output line{C.RESET}")
print(" ".join(outputs[:1]))
"""],
                capture_output=True, text=True, timeout=30, cwd=str(CLI_ROOT)
            )
            elapsed = (time.perf_counter() - start) * 1000.0
            if i == 0:
                metrics.add_metric("render_1000_lines_ms", elapsed, "ms", warn=100, fail=500)

        metrics.duration_ms = 0
        return metrics