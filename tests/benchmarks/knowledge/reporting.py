"""JSON reporting for Knowledge benchmark results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .metrics import BenchmarkResult


class BenchmarkReportError(ValueError):
    """Raised for inconsistent or invalid benchmark reports."""


def scenario_result_to_record(result: BenchmarkResult, dataset: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, BenchmarkResult):
        raise BenchmarkReportError("result must be BenchmarkResult")
    if not dataset:
        raise BenchmarkReportError("dataset metadata is required")
    cold = float(result.cold_duration_seconds)
    warm = [float(sample) for sample in result.warm_samples_seconds]
    return {
        "scenario": result.scenario,
        "dataset": {
            "documents": int(dataset.get("documents", 0)),
            "chunks": int(dataset.get("chunks", 0)),
            "embedding_calls": int(dataset.get("embedding_calls", 0)),
        },
        "iterations": {
            "warmup": int(result.warmup_count),
            "measured": int(result.iterations),
        },
        "duration_seconds": {
            "cold": cold,
            "median": result.warmup_median,
            "p95": result.p95(),
            "minimum": result.minimum,
            "maximum": result.maximum,
            "warm_samples": warm,
        },
    }


def render_baseline(results: list[tuple[BenchmarkResult, dict[str, Any]]]) -> dict[str, Any]:
    if not results:
        raise BenchmarkReportError("empty baseline")
    records = [scenario_result_to_record(result, dataset) for result, dataset in results]
    return {
        "version": 1,
        "scope": "knowledge-rag-in-memory",
        "postgres": "not-validated",
        "scenarios": records,
    }


def write_baseline(records: list[tuple[BenchmarkResult, dict[str, Any]]], path: Path) -> Path:
    payload = render_baseline(records)
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_text(content)
    return path
