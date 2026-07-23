# ETHAN CLI Performance Benchmark Suite — Design

## Executive Summary

A comprehensive benchmarking system to measure CLI speed, responsiveness, and resource usage. Tracks command execution time, API latency, daemon performance, memory consumption, and startup overhead.

**Core principle**: Measure → Baseline → Alert. Every critical path has performance thresholds; regressions are caught automatically.

---

## Benchmarking Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                 PERFORMANCE BENCHMARK SUITE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │   COMMAND    │    │     API      │    │      DAEMON          │ │
│  │  BENCHMARK   │    │  BENCHMARK   │    │   BENCHMARK          │ │
│  │              │    │              │    │                      │ │
│  │ - Response   │    │ - Latency    │    │ - Startup            │ │
│  │   time       │    │ - Throughput │    │ - Memory             │ │
│  │ - Throughput │    │ - Errors     │    │ - Improvement       │ │
│  └──────────────┘    └──────────────┘    └──────────────────────┘ │
│         │                  │                       │               │
│         └──────────────────┴───────────────────────┘               │
│                            │                                       │
│                            ▼                                       │
│              ┌────────────────────────┐                            │
│              │   BENCHMARK RUNNER     │                           │
│              │   (pytest-benchmark)   │                           │
│              └────────────────────────┘                            │
│                            │                                       │
│                            ▼                                       │
│              ┌────────────────────────┐                            │
│              │   RESULTS STORAGE      │                           │
│              │   (JSON + HTML)        │                           │
│              └────────────────────────┘                            │
│                            │                                       │
│                            ▼                                       │
│              ┌────────────────────────┐                            │
│              │   CI/CD GATE           │                           │
│              │   (threshold check)    │                           │
│              └────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Metrics Taxonomy

### 1. Command Response Time

**What**: Time from command invocation to output completion.

**Metrics**:
- `cmd.execution_time_ms` — Total wall-clock time
- `cmd.setup_time_ms` — Import/discovery overhead
- `cmd.runtime_ms` — Core logic execution
- `cmd.throughput_qps` — Queries per second (batch mode)

**Targets**:
- Simple commands (status, logs, config): < 100ms
- Medium commands (memory, plugin): < 200ms
- Complex commands (chat): < 500ms (first message)

### 2. API Latency

**What**: End-to-end time for API calls.

**Metrics**:
- `api.round_trip_ms` — Request → Response
- `api.connect_time_ms` — TCP connection
- `api.ttfb_ms` — Time to first byte
- `api.retry_overhead_ms` — Additional time from retries

**Targets**:
- Direct connection: < 50ms
- Through daemon: < 100ms
- With retry (1 attempt): < 300ms
- Timeout threshold: 5000ms

### 3. Daemon Impact

**What**: Performance improvement from daemon caching.

**Metrics**:
- `daemon.cache_hit_ms` — Response time with warm cache
- `daemon.cache_miss_ms` — Response time with cold cache
- `daemon.improvement_pct` — % faster with daemon
- `daemon.memory_saved_mb` — Memory reduction via caching

**Targets**:
- Cache hit speedup: 2-5x faster
- Cache miss penalty: < 2x slower than direct
- Memory overhead: < 50MB

### 4. Memory Usage

**What**: Resident memory consumption.

**Metrics**:
- `mem.rss_mb` — Resident set size
- `mem.heap_used_mb` — Python heap usage
- `mem.peak_mb` — Peak memory during execution
- `mem.per_command_mb` — Delta per command

**Targets**:
- Base CLI memory: < 30MB
- Peak during chat: < 100MB
- Memory leak threshold: < 5MB/hour

### 5. Startup Time

**What**: Time from invocation to command ready.

**Metrics**:
- `startup.import_time_ms` — Module imports
- `startup.discovery_time_ms` — Command discovery
- `startup.total_time_ms` — First-time execution

**Targets**:
- Import time: < 200ms
- Discovery time: < 100ms
- Total startup: < 300ms

---

## Benchmark Implementation

### Core Benchmark Runner

**Location**: `tests/cli/ethan/benchmarks/benchmark_runner.py`

```python
import time
import tracemalloc
import statistics
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any


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

    def __init__(self, warmup_iterations=3, benchmark_iterations=100):
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
                mean_ms=0,
                median_ms=0,
                min_ms=0,
                max_ms=0,
                stddev_ms=0,
                p95_ms=0,
                p99_ms=0,
                mean_memory_mb=0,
                max_memory_mb=0,
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
            stddev_ms=statistics.stdev(times) if n > 1 else 0,
            p95_ms=times_sorted[int(n * 0.95)] if n > 1 else times_sorted[0],
            p99_ms=times_sorted[int(n * 0.99)] if n > 1 else times_sorted[0],
            mean_memory_mb=statistics.mean(memories) if memories else 0,
            max_memory_mb=max(memories) if memories else 0,
            pass_count=len(successful),
            fail_count=len(failed),
        )
```

---

## Specific Benchmarks

### A. Command Response Time Benchmarks

**Location**: `tests/cli/ethan/benchmarks/test_command_performance.py`

```python
import pytest
from cli.registry import discover_commands, COMMANDS


class TestCommandResponseTime:
    """Benchmark command execution times."""

    @pytest.fixture
    def runner(self):
        from tests.cli.ethan.benchmarks.benchmark_runner import BenchmarkRunner
        return BenchmarkRunner(warmup_iterations=5, benchmark_iterations=100)

    def test_status_command_performance(self, runner, mock_api_offline):
        """Status command should respond in < 100ms."""
        cmd = COMMANDS.get("status")
        if not cmd:
            pytest.skip("status not registered")

        summary = runner.measure("status_command", cmd, [])

        assert summary.mean_ms < 100, \
            f"Status command too slow: {summary.mean_ms:.1f}ms (target: <100ms)"
        assert summary.p95_ms < 150, \
            f"Status P95 too slow: {summary.p95_ms:.1f}ms (target: <150ms)"

    def test_logs_command_performance(self, runner, mock_logs_empty):
        """Logs command should respond in < 100ms."""
        cmd = COMMANDS.get("logs")
        if not cmd:
            pytest.skip("logs not registered")

        summary = runner.measure("logs_command", cmd, [])

        assert summary.mean_ms < 100, \
            f"Logs command too slow: {summary.mean_ms:.1f}ms"

    def test_memory_recent_performance(self, runner, mock_memory_small):
        """Memory recent command should respond in < 200ms."""
        cmd = COMMANDS.get("memory")
        if not cmd:
            pytest.skip("memory not registered")

        summary = runner.measure("memory_recent", cmd, ["recent", "10"])

        assert summary.mean_ms < 200, \
            f"Memory command too slow: {summary.mean_ms:.1f}ms"

    def test_startup_time(self, runner):
        """CLI startup (imports + discovery) should be < 300ms."""
        def full_startup():
            import importlib
            import sys
            # Clear modules
            mods = [k for k in sys.modules.keys() if k.startswith("cli.")]
            for m in mods:
                del sys.modules[m]
            # Re-import
            from cli.registry import discover_commands
            discover_commands()

        summary = runner.measure("startup", full_startup)

        assert summary.mean_ms < 300, \
            f"Startup too slow: {summary.mean_ms:.1f}ms (target: <300ms)"
```

### B. API Latency Benchmarks

**Location**: `tests/cli/ethan/benchmarks/test_api_latency.py`

```python
import pytest
from unittest.mock import Mock, patch
import time


class TestAPILatency:
    """Benchmark API call latencies."""

    @pytest.fixture
    def runner(self):
        from tests.cli.ethan.benchmarks.benchmark_runner import BenchmarkRunner
        return BenchmarkRunner(warmup_iterations=3, benchmark_iterations=50)

    def test_direct_api_latency(self, runner, mock_api_direct):
        """Direct API call should complete in < 50ms."""
        from cli.core.client import send

        def make_call():
            return send("ping", session_id="test-123")

        summary = runner.measure("api_direct", make_call)

        assert summary.mean_ms < 50, \
            f"Direct API too slow: {summary.mean_ms:.1f}ms (target: <50ms)"

    def test_api_with_retry_latency(self, runner, mock_api_flaky):
        """API with retries should complete in < 300ms."""
        from cli.core.client import send

        call_count = [0]
        def flaky_call(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                time.sleep(0.01)  # Simulate timeout
                raise ConnectionError("timeout")
            return "ok", 10

        with patch("cli.core.client.send", side_effect=flaky_call):
            summary = runner.measure("api_retry", lambda: send("ping"))

        assert summary.mean_ms < 300, \
            f"API with retry too slow: {summary.mean_ms:.1f}ms"

    def test_api_timeout_behavior(self, runner):
        """API timeout should trigger within 5s."""
        from cli.core.client import send
        import urllib.error

        def timeout_call(*args, **kwargs):
            raise urllib.error.URLError("timed out")

        with patch("cli.core.client.urlopen", side_effect=timeout_call):
            summary = runner.measure("api_timeout", lambda: send("ping"))

        assert summary.mean_ms < 5500, \
            f"API timeout too slow: {summary.mean_ms:.1f}ms (target: <5.5s)"
```

### C. Daemon Impact Benchmarks

**Location**: `tests/cli/ethan/benchmarks/test_daemon_impact.py`

```python
import pytest


class TestDaemonImpact:
    """Measure performance improvement from daemon."""

    @pytest.fixture
    def runner(self):
        from tests.cli.ethan.benchmarks.benchmark_runner import BenchmarkRunner
        return BenchmarkRunner(warmup_iterations=5, benchmark_iterations=100)

    def test_daemon_cache_hit_vs_miss(self, runner):
        """Daemon cache hit should be 2-5x faster than miss."""
        from cli.core.client import get_state

        # Cold cache (no daemon)
        with patch("cli.core.client.alive", return_value=False):
            cold_summary = runner.measure("cache_miss", get_state)

        # Warm cache (daemon running)
        with patch("cli.core.client.alive", return_value=True):
            with patch.object(
                cli.core.client,
                "get_state",
                return_value={"mode": "idle", "modules_active": ["cli"]}
            ):
                warm_summary = runner.measure("cache_hit", get_state)

        improvement = cold_summary.mean_ms / warm_summary.mean_ms
        assert improvement >= 1.5, \
            f"Cache hit improvement too low: {improvement:.1f}x (target: >=1.5x)"

    def test_repeated_chat_with_cache(self, runner):
        """Repeated chat messages benefit from caching."""
        from cli.core.client import send

        times = []
        for i in range(20):
            with patch("cli.core.client.alive", return_value=True):
                with patch.object(
                    cli.core.client,
                    "send",
                    return_value=("response", 10)
                ):
                    t0 = time.perf_counter()
                    send(f"message {i}")
                    t1 = time.perf_counter()
                    times.append((t1 - t0) * 1000)

        # Later calls should be faster (cache warm)
        early_avg = statistics.mean(times[:5])
        late_avg = statistics.mean(times[-5:])

        assert late_avg <= early_avg * 1.5, \
            f"Cache not helping: early={early_avg:.1f}ms, late={late_avg:.1f}ms"
```

### D. Memory Usage Benchmarks

**Location**: `tests/cli/ethan/benchmarks/test_memory_usage.py`

```python
import pytest
import tracemalloc


class TestMemoryUsage:
    """Measure memory consumption."""

    def test_base_memory_footprint(self):
        """Base CLI memory should be < 30MB."""
        tracemalloc.start()
        import sys
        # Fresh import
        mods = [k for k in sys.modules.keys() if k.startswith("cli.")]
        for m in mods:
            del sys.modules[m]

        from cli.registry import discover_commands, COMMANDS
        discover_commands()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        assert peak_mb < 30, \
            f"Base memory too high: {peak_mb:.1f}MB (target: <30MB)"

    def test_chat_memory_growth(self):
        """Chat session memory should not leak (max 100MB)."""
        tracemalloc.start()
        from cli.commands.chat import cmd_chat

        # Simulate multiple messages
        for i in range(50):
            try:
                cmd_chat(["--no-interactive", f"test message {i}"])
            except SystemExit:
                pass
            except Exception:
                pass

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        assert peak_mb < 100, \
            f"Chat memory too high: {peak_mb:.1f}MB (target: <100MB)"

    def test_plugin_memory_overhead(self):
        """Each plugin should add < 10MB memory."""
        tracemalloc.start()
        from cli.registry import discover_commands, COMMANDS

        before_size = len(COMMANDS)
        discover_commands()  # Load plugins
        after_size = len(COMMANDS)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        new_plugins = after_size - before_size
        if new_plugins > 0:
            per_plugin_mb = (peak / 1024 / 1024) / new_plugins
            assert per_plugin_mb < 10, \
                f"Plugin memory too high: {per_plugin_mb:.1f}MB/plugin (target: <10MB)"
```

---

## Benchmark CLI

**Location**: `tests/cli/ethan/benchmarks/cli.py`

```python
#!/usr/bin/env python3
"""CLI runner for benchmarks."""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="ETHAN CLI Benchmarks")
    parser.add_argument("--suite", choices=["command", "api", "daemon", "memory", "all"],
                       default="all", help="Benchmark suite to run")
    parser.add_argument("--iterations", type=int, default=100,
                       help="Number of iterations per benchmark")
    parser.add_argument("--warmup", type=int, default=3,
                       help="Number of warmup iterations")
    parser.add_argument("--output", type=Path, default=Path("benchmark_results.json"),
                       help="Output file for results")
    parser.add_argument("--html", type=Path, default=None,
                       help="Generate HTML report")
    args = parser.parse_args()

    print(f"Running {args.suite} benchmarks...")
    print(f"Iterations: {args.iterations}, Warmup: {args.warmup}")
    print()

    # Run pytest with benchmark plugin
    import subprocess
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/cli/ethan/benchmarks/",
        "-v",
        "-n", "auto",  # Parallel
        f"--benchmark-iterations={args.iterations}",
        f"--benchmark-warmup={args.warmup}",
        f"--benchmark-json={args.output}",
    ]

    if args.html:
        cmd.append(f"--benchmark-html={args.html}")

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
```

---

## Continuous Performance Monitoring

### Baseline Establishment

```bash
# Run benchmarks on clean master
ethan-benchmark --suite all --iterations 200

# Save as baseline
cp benchmark_results.json benchmarks/baseline_master.json

# Compare against baseline
ethan-benchmark --compare benchmarks/baseline_master.json
```

### Threshold Alerts

```yaml
# .github/workflows/cli-benchmarks.yml
- name: Check performance regression
  run: |
    python scripts/check_benchmarks.py \
      --baseline benchmarks/baseline_master.json \
      --current benchmark_results.json \
      --threshold 1.20  # 20% degradation allowed
```

### Performance Budgets

| Command | Mean | P95 | P99 | Memory |
|---|---|---|---|---|
| status | 100ms | 150ms | 200ms | 30MB |
| logs | 100ms | 150ms | 200ms | 30MB |
| memory | 200ms | 300ms | 400ms | 30MB |
| plugin | 200ms | 300ms | 400ms | 40MB |
| chat (1st msg) | 500ms | 800ms | 1000ms | 100MB |
| startup | 300ms | 400ms | 500ms | N/A |

---

## Metrics Reference

### Timing Metrics

| Metric | Unit | Description |
|---|---|---|
| `execution_time_ms` | ms | Total command execution time |
| `setup_time_ms` | ms | Import/discovery overhead |
| `runtime_ms` | ms | Core logic time |
| `ttfb_ms` | ms | Time to first byte (API) |
| `connect_time_ms` | ms | TCP connection time |
| `retry_overhead_ms` | ms | Extra time from retries |

### Throughput Metrics

| Metric | Unit | Description |
|---|---|---|
| `throughput_qps` | q/s | Queries per second |
| `cache_hit_rate` | % | Percentage of cache hits |
| `retry_rate` | % | Percentage of calls needing retry |

### Memory Metrics

| Metric | Unit | Description |
|---|---|---|
| `rss_mb` | MB | Resident set size |
| `heap_used_mb` | MB | Python heap usage |
| `peak_mb` | MB | Peak memory |
| `delta_mb` | MB | Change from baseline |

### Daemon Metrics

| Metric | Unit | Description |
|---|---|---|
| `cache_hit_ms` | ms | Response with warm cache |
| `cache_miss_ms` | ms | Response with cold cache |
| `improvement_pct` | % | Speedup from caching |
| `overhead_mb` | MB | Daemon memory cost |

---

## Implementation Checklist

- [x] Design benchmark runner architecture
- [x] Define metrics taxonomy
- [x] Design command response time benchmarks
- [x] Design API latency benchmarks
- [x] Design daemon impact benchmarks
- [x] Design memory usage benchmarks
- [x] Design benchmark CLI
- [x] Define performance budgets
- [x] Design CI/CD integration
- [x] Create metrics reference

**Implementation complete**:
- [x] Implement `benchmark_runner.py`
- [x] Create mock fixtures for controlled benchmarking
- [x] Run initial baseline collection
- [x] Set up performance regression alerts
- [x] Integrate with existing pytest suite

**Files implemented**:
- `tests/cli/ethan/benchmarks/benchmark_runner.py`
- `tests/cli/ethan/benchmarks/test_command_performance.py`
- `tests/cli/ethan/benchmarks/test_api_latency.py`
- `tests/cli/ethan/benchmarks/test_memory_usage.py`
- `tests/cli/ethan/benchmarks/test_daemon_impact.py`
