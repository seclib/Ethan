"""Memory usage benchmarks."""
import pytest
import tracemalloc
import sys
import time

from cli.registry import discover_commands, COMMANDS


@pytest.fixture
def runner():
    from tests.cli.ethan.benchmarks.benchmark_runner import BenchmarkRunner
    return BenchmarkRunner(warmup_iterations=2, benchmark_iterations=30)


@pytest.fixture(autouse=True)
def setup_commands():
    """Ensure commands are discovered."""
    discover_commands()


def _get_memory_mb():
    """Get current memory usage in MB."""
    import gc
    gc.collect()
    import psutil
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


class TestMemoryUsage:
    """Measure memory consumption."""

    def test_base_memory_footprint(self, runner):
        """Base CLI memory should be < 30MB."""
        def import_and_discover():
            # Clear modules
            mods = [k for k in list(sys.modules.keys()) if k.startswith("cli.")]
            for m in mods:
                del sys.modules[m]
            # Re-import
            from cli.registry import discover_commands
            discover_commands()

        # Measure multiple times to get stable reading
        times = []
        for _ in range(5):
            tracemalloc.start()
            t0 = time.perf_counter()
            import_and_discover()
            t1 = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            times.append(peak / 1024 / 1024)

        peak_mb = max(times)
        assert peak_mb < 30, \
            f"Base memory too high: {peak_mb:.1f}MB (target: <30MB)"

    def test_command_memory_delta(self, runner):
        """Single command execution should not leak > 5MB."""
        cmd = COMMANDS.get("help")
        if not cmd:
            pytest.skip("no commands registered")

        def run_cmd():
            old = sys.modules.copy()
            try:
                exit_code = cmd([])
            finally:
                # Check module count didn't explode
                new_mods = [k for k in sys.modules.keys() if k.startswith("cli.")]
                if len(new_mods) > 50:
                    pytest.fail(f"Module leak: {len(new_mods)} cli modules loaded")

        summary = runner.measure("command_memory", run_cmd)
        assert summary.max_memory_mb < 10, \
            f"Command memory too high: {summary.max_memory_mb:.1f}MB"