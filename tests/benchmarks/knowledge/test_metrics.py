import json

from tests.benchmarks.knowledge.metrics import BenchmarkMetricsCollector


def test_cold_separate_and_warmup_excluded():
    ops = {"count": 0}

    def op():
        ops["count"] += 1

    collector = BenchmarkMetricsCollector("cold", warmup=2, iterations=2)
    result = collector.run(op)
    assert result.iterations == 2
    assert len(result.warm_samples_seconds) == 2
    assert result.warmup_count == 2
    # 1 cold + 2 warmup + 2 measured
    assert ops["count"] == 5


def test_median_and_p95():
    from tests.benchmarks.knowledge.metrics import BenchmarkResult
    result = BenchmarkResult(
        scenario="median",
        timestamp_utc="2026-01-01T00:00:00+00:00",
        cold_duration_seconds=0.0,
        warmup_count=0,
        iterations=10,
        warm_samples_seconds=tuple([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    )
    assert result.warmup_median == 5.5
    # percentile index = floor(0.95 * (10-1)) = 9
    assert result.p95() == 10.0


def test_invalid_params_and_exceptions():
    try:
        BenchmarkMetricsCollector("", warmup=0, iterations=1)
    except ValueError:
        pass
    else:
        raise AssertionError("empty scenario accepted")

    try:
        BenchmarkMetricsCollector("x", warmup=0, iterations=0)
    except ValueError:
        pass
    else:
        raise AssertionError("zero iterations accepted")

    collector = BenchmarkMetricsCollector("exception", 0, 1)

    def op():
        raise RuntimeError("boom")

    try:
        collector.run(op)
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("operation did not propagate exception")


def test_json():
    collector = BenchmarkMetricsCollector("json", 0, 1)
    result = collector.run(lambda: None)
    raw = result.to_json()
    data = json.loads(raw)
    assert data["scenario"] == "json"
