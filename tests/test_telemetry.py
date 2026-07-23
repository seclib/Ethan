"""Tests for ETHAN CLI telemetry module — instrumentation for benchmarks."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))


def test_telemetry_import():
    from cli.core.telemetry import CLITelemetry, TelemetrySnapshot, benchmark
    assert CLITelemetry is not None
    assert TelemetrySnapshot is not None
    assert callable(benchmark)


def test_telemetry_init_disabled():
    from cli.core.telemetry import CLITelemetry
    t = CLITelemetry(enabled=False)
    assert t.enabled is False


def test_telemetry_init_enabled():
    import os
    os.environ["ETHAN_BENCH"] = "1"
    from cli.core.telemetry import CLITelemetry
    t = CLITelemetry(enabled=True)
    assert t.enabled is True


def test_telemetry_start_stop():
    import os
    os.environ["ETHAN_BENCH"] = "1"
    from cli.core.telemetry import CLITelemetry
    t = CLITelemetry(enabled=True)
    t.start("test_timer")
    time.sleep(0.01)
    duration = t.stop("test_timer")
    assert duration is not None
    assert duration > 0


def test_telemetry_stop_unknown():
    from cli.core.telemetry import CLITelemetry
    t = CLITelemetry(enabled=True)
    duration = t.stop("unknown_timer")
    assert duration is None


def test_telemetry_inc():
    import os
    os.environ["ETHAN_BENCH"] = "1"
    from cli.core.telemetry import CLITelemetry
    t = CLITelemetry(enabled=True)
    t.inc("counter_a")
    t.inc("counter_a")
    t.inc("counter_b", delta=5)
    assert t._counters.get("counter_a") == 2
    assert t._counters.get("counter_b") == 5


def test_telemetry_snapshot():
    import os
    os.environ["ETHAN_BENCH"] = "1"
    from cli.core.telemetry import CLITelemetry
    t = CLITelemetry(enabled=True)
    t.start("cold_start")
    time.sleep(0.005)
    t.stop("cold_start")
    snap = t.snapshot()
    assert snap.cold_start_ms > 0
    assert "cold_start" in snap.command_timings


def test_telemetry_reset():
    import os
    os.environ["ETHAN_BENCH"] = "1"
    from cli.core.telemetry import CLITelemetry
    t = CLITelemetry(enabled=True)
    t.start("x")
    t.stop("x")
    t.reset()
    snap = t.snapshot()
    assert snap.cold_start_ms == 0.0


def test_telemetry_record_api_latency():
    import os
    os.environ["ETHAN_BENCH"] = "1"
    from cli.core.telemetry import CLITelemetry
    t = CLITelemetry(enabled=True)
    t.record_api_latency(150.0)
    t.record_api_latency(250.0)
    snap = t.snapshot()
    assert len(snap.api_latencies) == 2
    assert snap.api_latencies[0] == 150.0


def test_telemetry_rss():
    from cli.core.telemetry import CLITelemetry
    rss = CLITelemetry._get_rss()
    assert rss >= 0