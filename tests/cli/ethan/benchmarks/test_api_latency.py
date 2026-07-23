"""API latency benchmarks."""
import pytest
import time
from unittest.mock import patch

from cli.core.client import send
import urllib.error


@pytest.fixture
def runner():
    from tests.cli.ethan.benchmarks.benchmark_runner import BenchmarkRunner
    return BenchmarkRunner(warmup_iterations=2, benchmark_iterations=30)


def _make_call(msg="ping", session_id="test-123"):
    """Make API call."""
    return send(msg, session_id=session_id)


class TestAPILatency:
    """Benchmark API call latencies."""

    def test_direct_api_latency(self, runner, mock_api_direct):
        """Direct API call should complete in < 50ms mean."""
        def make_call():
            return _make_call()

        summary = runner.measure("api_direct", make_call)

        assert summary.mean_ms < 50, \
            f"Direct API too slow: {summary.mean_ms:.1f}ms (target: <50ms)"
        assert summary.max_memory_mb < 30, \
            f"API memory too high: {summary.max_memory_mb:.1f}MB"

    def test_api_with_retry_latency(self, runner):
        """API with retries should complete in < 300ms mean."""
        call_count = [0]

        def flaky_call(msg, session_id=None):
            call_count[0] += 1
            if call_count[0] < 3:
                time.sleep(0.005)  # Simulate partial timeout
                raise ConnectionError("timeout")
            return "ok", 10

        with patch("cli.core.client.send", side_effect=flaky_call):
            summary = runner.measure("api_retry", lambda: _make_call())

        assert summary.mean_ms < 300, \
            f"API with retry too slow: {summary.mean_ms:.1f}ms (target: <300ms)"

    def test_api_valid_input_validation(self, runner):
        """Empty input should be rejected quickly."""
        def empty_call():
            return send("", session_id="test")

        summary = runner.measure("api_empty_validation", empty_call)

        # Should fail fast (no network call)
        assert summary.mean_ms < 10, \
            f"Empty input validation too slow: {summary.mean_ms:.1f}ms"