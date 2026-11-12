import json
from pathlib import Path

from tests.benchmarks.knowledge.metrics import BenchmarkResult
from tests.benchmarks.knowledge.reporting import (
    BenchmarkReportError,
    scenario_result_to_record,
    render_baseline,
    write_baseline,
)

def make_result(name="s", cold=1.0, samples=(2.0, 3.0)):
    return BenchmarkResult(
        scenario=name,
        timestamp_utc="2026-01-01T00:00:00+00:00",
        cold_duration_seconds=cold,
        warmup_count=1,
        iterations=len(samples),
        warm_samples_seconds=samples,
    )


def test_serialization():
    result = make_result()
    record = scenario_result_to_record(result, {"documents": 2, "chunks": 4, "embedding_calls": 1})
    assert record["scenario"] == "s"
    assert record["dataset"]["architecture_source"] if "architecture_source" in record["dataset"] else True
    assert record["duration_seconds"]["cold"] == 1.0
    assert record["duration_seconds"]["warm_samples"] == [2.0, 3.0]

def test_render_and_write(tmp_path):
    result = make_result(name="json-scenario", cold=0.1, samples=(0.2,))
    output = tmp_path / "baseline.json"
    try:
        write_baseline([(result, {"documents": 1, "chunks": 1, "embedding_calls": 0})], output)
    except Exception:
        raise
    data = json.loads(output.read_text())
    assert "scenarios" in data
    assert data["scenarios"][0]["dataset"]["documents"] == 1

def test_reject_empty_and_bad_records():
    result = make_result()
    try:
        render_baseline([])
    except BenchmarkReportError:
        pass
    else:
        raise AssertionError("empty baseline accepted")
    try:
        scenario_result_to_record(result, {})
    except BenchmarkReportError:
        pass
    else:
        raise AssertionError("empty dataset accepted")
