"""Benchmark runner — core benchmarking engine."""
import time
import tracemalloc
import statistics
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any, Optional


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    execution_time_ms: float
    memory_rss_mb: float
    memory_heap_mb: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSummary:
    """Aggregated benchmark statistics."""
    name: str
    iterations: int
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    stddev_ms: float
    p95_ms: float
    p99_ms: float
    mean_memory_mb: float
    max_memory_mb: float
    pass_count: int
    fail_count: int


class BenchmarkRunner:
    """Execute benchmarks with precision timing."""

    def __init__(
        self,
        warmup_iterations: int = 3,
        benchmark_iterations: int = 100
    ):
        self.warmup_iterations = warmup_iterations
        self.benchmark_iterations = benchmark_iterations
        self.results: List[BenchmarkResult] = []

    def measure(
        self,
        name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> BenchmarkSummary:
        """Run benchmark with warmup and multiple iterations.

        Args:
            name: Benchmark name
            func: Function to benchmark
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            BenchmarkSummary with statistics
        """
        # Warmup runs (not recorded)
        for _ in range(self.warmup_iterations):
            try:
                func(*args, **kwargs)
            except Exception:
                pass

        # Actual benchmark runs
        self.results = []
        for _ in range(self.benchmark_iterations):
            tracemalloc.start()
            t0 = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                success = True
            except Exception:
                success = False
            finally:
                t1 = time.perf_counter()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

            self.results.append(BenchmarkResult(
                name=name,
                execution_time_ms=(t1 - t0) * 1000,
                memory_rss_mb=peak / 1024 / 1024,
                memory_heap_mb=current / 1024 / 1024,
                success=success,
            ))

        return self._summarize(name)

    def _summarize(self, name: str) -> BenchmarkSummary:
        """Compute statistics from results."""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        times = [r.execution_time_ms for r in successful]
        memories = [r.memory_rss_mb for r in successful]

        if not times:
            return BenchmarkSummary(
                name=name,
                iterations=len(self.results),
                mean_ms=0.0,
                median_ms=0.0,
                min_ms=0.0,
                max_ms=0.0,
                stddev_ms=0.0,
                p95_ms=0.0,
                p99_ms=0.0,
                mean_memory_mb=0.0,
                max_memory_mb=0.0,
                pass_count=0,
                fail_count=len(failed),
            )

        times_sorted = sorted(times)
        n = len(times_sorted)

        return BenchmarkSummary(
            name=name,
            iterations=len(self.results),
            mean_ms=statistics.mean(times),
            median_ms=statistics.median(times),
            min_ms=min(times),
            max_ms=max(times),
            stddev_ms=statistics.stdev(times) if n > 1 else 0.0,
            p95_ms=times_sorted[int(n * 0.95)] if n > 1 else times_sorted[0],
            p99_ms=times_sorted[int(n * 0.99)] if n > 1 else times_sorted[0],
            mean_memory_mb=statistics.mean(memories) if memories else 0.0,
            max_memory_mb=max(memories) if memories else 0.0,
            pass_count=len(successful),
            fail_count=len(failed),
        )

    def get_results(self) -> List[BenchmarkResult]:
        """Return all benchmark results."""
        return self.results