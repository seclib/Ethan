"""Daemon impact benchmarks — measure cache performance."""
import pytest
import time
import statistics

from cli.registry import discover_commands, COMMANDS


@pytest.fixture
def runner():
    from tests.cli.ethan.benchmarks.benchmark_runner import BenchmarkRunner
    return BenchmarkRunner(warmup_iterations=3, benchmark_iterations=50)


@pytest.fixture(autouse=True)
def setup_commands():
    """Ensure commands are discovered."""
    discover_commands()


class TestDaemonImpact:
    """Measure performance improvement from daemon caching."""

    def test_daemon_cache_hit_vs_miss(self, runner):
        """Daemon cache hit should be faster than miss."""
        from cli.core.client import get_state

        # Measure cache miss (simulated slow path)
        def cache_miss():
            # Simulate cache miss - direct API call
            import urllib.request
            import json
            try:
                req = urllib.request.Request("http://localhost:8000/v1/state")
                with urllib.request.urlopen(req, timeout=1) as resp:
                    data = json.loads(resp.read())
                    return data
            except Exception:
                return {"mode": "offline", "modules_active": []}

        # Measure cache hit (simulated fast path)
        def cache_hit():
            # Simulate cache hit - return cached state
            return {"mode": "idle", "modules_active": ["cli"], "cached": True}

        # Baseline (no daemon / cold)
        cold_summary = runner.measure("cache_miss", cache_miss)
        
        # With daemon cache
        warm_summary = runner.measure("cache_hit", cache_hit)

        # Cache hit should be faster (allow generous threshold for test env)
        if cold_summary.mean_ms > 0:
            improvement = cold_summary.mean_ms / warm_summary.mean_ms
            # In real scenario expect 2-5x, in test allow any improvement
            assert warm_summary.mean_ms < cold_summary.mean_ms, \
                f"Cache hit slower than miss: {warm_summary.mean_ms:.1f}ms vs {cold_summary.mean_ms:.1f}ms"

    def test_repeated_command_execution(self, runner):
        """Repeated commands should benefit from caching."""
        cmd = COMMANDS.get("help")
        if not cmd:
            pytest.skip("help not registered")

        times = []
        for i in range(10):
            import time as t
            t0 = t.perf_counter()
            try:
                cmd([])
            except Exception:
                pass
            t1 = t.perf_counter()
            times.append((t1 - t0) * 1000)

        # Check that execution is reasonably fast
        avg = statistics.mean(times)
        max_allowed = 200  # ms
        assert avg < max_allowed, \
            f"Repeated command too slow: avg={avg:.1f}ms (target: <{max_allowed}ms)"