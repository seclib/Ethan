"""API Latency Benchmark — measure ETHAN API responsiveness."""

from __future__ import annotations

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

from .benchmark_runner import BenchmarkResult


class APILatencyBenchmark:
    """Benchmark API endpoint latency: /health, /state, /v1/chat."""

    HEALTH_ENDPOINT = "http://localhost:8000/health"
    STATE_ENDPOINT = "http://localhost:8000/state"
    CHAT_ENDPOINT = "http://localhost:8000/v1/chat"

    def run(self, samples: int = 5) -> list[BenchmarkResult]:
        """Run API latency benchmarks."""
        results = []

        # --- Health endpoint ---
        health_result = self._benchmark_endpoint(
            "API Health", self.HEALTH_ENDPOINT, samples,
            warn=200, fail=1000
        )
        results.append(health_result)

        # --- State endpoint ---
        state_result = self._benchmark_endpoint(
            "API State", self.STATE_ENDPOINT, samples,
            warn=500, fail=2000
        )
        results.append(state_result)

        # --- Latency percentiles ---
        if health_result.metrics:
            all_latencies = []
            all_latencies.extend(
                m.value for m in health_result.metrics if "latency" in m.name
            )
            all_latencies.extend(
                m.value for m in state_result.metrics if "latency" in m.name
            )
            if all_latencies:
                sorted_lat = sorted(all_latencies)
                p50 = sorted_lat[len(sorted_lat) // 2]
                p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
                p99 = sorted_lat[int(len(sorted_lat) * 0.99)]

                perc_metrics = BenchmarkResult(
                    group="api", name="API Latency Percentiles", samples=len(sorted_lat)
                )
                perc_metrics.add_metric("p50_latency_ms", p50, "ms", warn=300, fail=1000)
                perc_metrics.add_metric("p95_latency_ms", p95, "ms", warn=800, fail=3000)
                perc_metrics.add_metric("p99_latency_ms", p99, "ms", warn=1500, fail=5000)
                results.append(perc_metrics)

        return results

    def _benchmark_endpoint(
        self, name: str, url: str, samples: int,
        warn: float, fail: float
    ) -> BenchmarkResult:
        """Benchmark a single API endpoint."""
        metrics = BenchmarkResult(group="api", name=name, samples=samples)
        latencies = []
        errors = 0

        for i in range(samples):
            try:
                start = time.perf_counter()
                req = Request(url, headers={"Accept": "application/json"})
                resp = urlopen(req, timeout=10)
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000.0
                latencies.append(elapsed)
            except (URLError, OSError, ValueError) as e:
                errors += 1
                if i == 0:
                    metrics.add_metric("api_reachable", 0.0, "bool", fail=1)

        if latencies:
            avg = sum(latencies) / len(latencies)
            metrics.add_metric("avg_latency_ms", avg, "ms", warn=warn, fail=fail)
            metrics.add_metric("min_latency_ms", min(latencies), "ms")
            metrics.add_metric("max_latency_ms", max(latencies), "ms")
            if errors == 0:
                metrics.add_metric("api_reachable", 1.0, "bool")

        metrics.samples = len(latencies)
        metrics.errors = errors
        metrics.duration_ms = sum(latencies)
        return metrics