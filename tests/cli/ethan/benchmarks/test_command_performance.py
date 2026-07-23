"""Command performance benchmarks."""
import pytest
import sys
from io import StringIO

from cli.registry import discover_commands, COMMANDS


@pytest.fixture
def runner():
    from tests.cli.ethan.benchmarks.benchmark_runner import BenchmarkRunner
    return BenchmarkRunner(warmup_iterations=3, benchmark_iterations=50)


@pytest.fixture(autouse=True)
def setup_commands():
    """Ensure commands are discovered before benchmarks."""
    discover_commands()


def _capture_output(func, *args):
    """Capture stdout from command function."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        exit_code = func(*args)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return exit_code, output


class TestCommandResponseTime:
    """Benchmark command execution times."""

    def test_status_command_performance(self, runner, mock_api_offline):
        """Status command should respond in < 100ms mean."""
        cmd = COMMANDS.get("status")
        if not cmd:
            pytest.skip("status not registered")

        summary = runner.measure("status_command", lambda: _capture_output(cmd, []))

        assert summary.mean_ms < 100, \
            f"Status command too slow: {summary.mean_ms:.1f}ms (target: <100ms)"
        assert summary.p95_ms < 150, \
            f"Status P95 too slow: {summary.p95_ms:.1f}ms (target: <150ms)"
        assert summary.max_memory_mb < 30, \
            f"Status memory too high: {summary.max_memory_mb:.1f}MB"

    def test_logs_command_performance(self, runner, mock_logs_empty):
        """Logs command should respond in < 100ms mean."""
        cmd = COMMANDS.get("logs")
        if not cmd:
            pytest.skip("logs not registered")

        summary = runner.measure("logs_command", lambda: _capture_output(cmd, []))

        assert summary.mean_ms < 100, \
            f"Logs command too slow: {summary.mean_ms:.1f}ms"

    def test_memory_recent_performance(self, runner, mock_memory_empty):
        """Memory recent command should respond in < 200ms mean."""
        cmd = COMMANDS.get("memory")
        if not cmd:
            pytest.skip("memory not registered")

        summary = runner.measure("memory_recent", lambda: _capture_output(cmd, ["recent"]))

        assert summary.mean_ms < 200, \
            f"Memory command too slow: {summary.mean_ms:.1f}ms"

    def test_startup_time(self, runner):
        """CLI startup (imports + discovery) should be < 300ms."""
        def full_startup():
            import importlib
            # Clear cached modules
            mods = [k for k in list(sys.modules.keys()) if k.startswith("cli.")]
            for m in mods:
                del sys.modules[m]
            # Re-import
            from cli.registry import discover_commands
            discover_commands()

        summary = runner.measure("startup", full_startup)

        assert summary.mean_ms < 300, \
            f"Startup too slow: {summary.mean_ms:.1f}ms (target: <300ms)"