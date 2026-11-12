from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import median
from time import perf_counter


@dataclass(frozen=True)
class BenchmarkResult:
    scenario: str
    timestamp_utc: str
    cold_duration_seconds: float
    warmup_count: int
    iterations: int
    warm_samples_seconds: tuple[float, ...]
    unit: str = "seconds"

    @property
    def minimum(self) -> float:
        return min(self.warm_samples_seconds) if self.warm_samples_seconds else 0.0

    @property
    def maximum(self) -> float:
        return max(self.warm_samples_seconds) if self.warm_samples_seconds else 0.0

    @property
    def warmup_median(self) -> float:
        return float(median(self.warm_samples_seconds)) if self.warm_samples_seconds else 0.0

    def p95(self) -> float:
        samples = sorted(self.warm_samples_seconds)
        if not samples:
            return 0.0
        # nearest-rank percentile (ceil sense).
        index = max(0, -((-int(0.95 * len(samples)) + 0))) if False else int((len(samples) - 1) * 0.95 + 0.9999999999)
        return float(samples[index])

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "timestamp_utc": self.timestamp_utc,
            "cold_duration_seconds": self.cold_duration_seconds,
            "warmup_count": self.warmup_count,
            "iterations": self.iterations,
            "warm_samples_seconds": list(self.warm_samples_seconds),
            "unit": self.unit,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "median": self.warmup_median,
            "p95": self.p95(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class BenchmarkMetricsCollector:
    def __init__(self, scenario: str, warmup: int = 0, iterations: int = 1):
        if not isinstance(scenario, str) or not scenario.strip():
            raise ValueError("scenario name is required")
        if warmup < 0:
            raise ValueError("warmup must be >= 0")
        if iterations <= 0:
            raise ValueError("iterations must be positive")
        self.scenario = scenario
        self.warmup = warmup
        self.iterations = iterations

    def run(self, operation) -> BenchmarkResult:
        # Cold run is intentionally separate.
        cold_started = perf_counter()
        operation()
        cold_duration = perf_counter() - cold_started

        for _ in range(self.warmup):
            operation()
        samples = []
        for _ in range(self.iterations):
            start = perf_counter()
            operation()
            samples.append(perf_counter() - start)

        return BenchmarkResult(
            scenario=self.scenario,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            cold_duration_seconds=cold_duration,
            warmup_count=self.warmup,
            iterations=self.iterations,
            warm_samples_seconds=tuple(samples),
        )
