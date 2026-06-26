"""Benchmarking framework for Ethan inference engines."""

from __future__ import annotations

from ethan.bench._stubs import BaseBenchmark, BenchmarkResult, BenchmarkSuite
from ethan.core.registry import BenchmarkRegistry


def ensure_registered() -> None:
    """Ensure all benchmark implementations are registered."""
    from ethan.bench.energy import ensure_registered as _reg_energy
    from ethan.bench.latency import ensure_registered as _reg_latency
    from ethan.bench.throughput import ensure_registered as _reg_throughput

    _reg_latency()
    _reg_throughput()
    _reg_energy()


# Trigger registration on import
ensure_registered()

__all__ = [
    "BaseBenchmark",
    "BenchmarkRegistry",
    "BenchmarkResult",
    "BenchmarkSuite",
    "ensure_registered",
]
