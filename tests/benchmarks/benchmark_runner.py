"""ETHAN CLI Benchmark Runner — orchestrates benchmark execution."""

from __future__ import annotations

import os
import sys
import json
import time
import math
import shlex
import subprocess
import platform
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


BENCH_DIR = Path(__file__).parent
RESULTS_DIR = BENCH_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class BenchmarkMetric:
    """A single metric measurement."""
    name: str
    value: float
    unit: str
    threshold_warn: float | None = None
    threshold_fail: float | None = None

    @property
    def status(self) -> str:
        if self.threshold_fail and self.value > self.threshold_fail:
            return "FAIL"
        if self.threshold_warn and self.value > self.threshold_warn:
            return "WARN"
        return "PASS"


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    group: str
    name: str
    metrics: list[BenchmarkMetric] = field(default_factory=list)
    samples: int = 1
    errors: int = 0
    duration_ms: float = 0.0

    def add_metric(self, name: str, value: float, unit: str = "ms",
                   warn: float | None = None, fail: float | None = None) -> None:
        self.metrics.append(BenchmarkMetric(name, value, unit, warn, fail))

    @property
    def pass_count(self) -> int:
        return sum(1 for m in self.metrics if m.status == "PASS")

    @property
    def warn_count(self) -> int:
        return sum(1 for m in self.metrics if m.status == "WARN")

    @property
    def fail_count(self) -> int:
        return sum(1 for m in self.metrics if m.status == "FAIL")

    @property
    def score(self) -> float:
        total = len(self.metrics)
        if total == 0:
            return 100.0
        return (self.pass_count / total) * 100.0


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""
    timestamp: str = ""
    commit: str = ""
    branch: str = ""
    python_version: str = ""
    platform: str = ""
    results: list[BenchmarkResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.python_version:
            self.python_version = sys.version
        if not self.platform:
            self.platform = platform.platform()
        if not self.commit:
            self.commit = self._get_git_commit()
        if not self.branch:
            self.branch = self._get_git_branch()

    @staticmethod
    def _get_git_commit() -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    @staticmethod
    def _get_git_branch() -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    @property
    def overall_score(self) -> float:
        if not self.results:
            return 100.0
        return sum(r.score for r in self.results) / len(self.results)

    @property
    def total_failures(self) -> int:
        return sum(r.fail_count for r in self.results)

    @property
    def total_warnings(self) -> int:
        return sum(r.warn_count for r in self.results)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "commit": self.commit,
            "branch": self.branch,
            "python_version": self.python_version,
            "platform": self.platform,
            "total_duration_ms": self.total_duration_ms,
            "overall_score": self.overall_score,
            "total_failures": self.total_failures,
            "total_warnings": self.total_warnings,
            "results": [
                {
                    "group": r.group,
                    "name": r.name,
                    "score": r.score,
                    "samples": r.samples,
                    "errors": r.errors,
                    "duration_ms": r.duration_ms,
                    "metrics": [
                        {"name": m.name, "value": m.value, "unit": m.unit, "status": m.status}
                        for m in r.metrics
                    ],
                }
                for r in self.results
            ],
        }

    def save_json(self, path: str | Path | None = None) -> Path:
        if path is None:
            filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            path = RESULTS_DIR / filename
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2))
        return path

    def save_markdown(self, path: str | Path | None = None) -> Path:
        """Generate a Markdown report."""
        if path is None:
            filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            path = RESULTS_DIR / filename
        path = Path(path)

        lines = [
            f"# ETHAN CLI Benchmark Report",
            f"",
            f"**Date:** {self.timestamp}",
            f"**Commit:** {self.commit}",
            f"**Branch:** {self.branch}",
            f"**Python:** {self.python_version}",
            f"**Platform:** {self.platform}",
            f"",
            f"## Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Overall Score | {self.overall_score:.1f}/100 |",
            f"| Total Duration | {self.total_duration_ms:.1f} ms |",
            f"| Benchmarks Run | {len(self.results)} |",
            f"| Failures | {self.total_failures} |",
            f"| Warnings | {self.total_warnings} |",
            f"",
        ]

        for result in self.results:
            lines.extend([
                f"## {result.group}: {result.name}",
                f"",
                f"Score: {result.score:.1f}/100 | Samples: {result.samples} | "
                f"Duration: {result.duration_ms:.1f}ms",
                f"",
                f"| Metric | Value | Status |",
                f"|--------|-------|--------|",
            ])
            for m in result.metrics:
                status_icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}.get(m.status, "?")
                value_str = f"{m.value:.1f} {m.unit}" if m.value else f"{m.value} {m.unit}"
                lines.append(f"| {m.name} | {value_str} | {status_icon} {m.status} |")
            lines.append("")

        path.write_text("\n".join(lines))
        return path


class BenchmarkRunner:
    """Orchestrates benchmark execution groups."""

    GROUPS = {
        "cold": "Cold Start & Discovery",
        "commands": "Command Performance",
        "api": "API Latency",
        "daemon": "Daemon Impact",
        "streaming": "Streaming Performance",
        "all": "All Benchmarks",
    }

    def __init__(self, groups: list[str] | None = None, verbose: bool = False):
        self.groups = groups or ["all"]
        self.verbose = verbose
        self.report = BenchmarkReport()
        self._start_time = 0.0

    def run_all(self) -> BenchmarkReport:
        """Run all selected benchmark groups."""
        self._start_time = time.perf_counter()
        self.report = BenchmarkReport()

        if "all" in self.groups:
            groups_to_run = list(self.GROUPS.keys())[:-1]  # exclude "all"
        else:
            groups_to_run = self.groups

        for group in groups_to_run:
            if group not in self.GROUPS:
                print(f"  {self._warn_icon()} Unknown group: {group}")
                continue
            self._run_group(group)

        self.report.total_duration_ms = (time.perf_counter() - self._start_time) * 1000.0
        return self.report

    def _run_group(self, group: str) -> None:
        """Run a single benchmark group."""
        label = self.GROUPS[group]
        if self.verbose:
            print(f"  {self._info_icon()} Benchmarking {label}...")

        if group == "cold":
            from .cold_start import ColdStartBenchmark
            results = ColdStartBenchmark().run()
        elif group == "commands":
            from .commands import CommandsBenchmark
            results = CommandsBenchmark().run()
        elif group == "api":
            from .api_latency import APILatencyBenchmark
            results = APILatencyBenchmark().run()
        elif group == "daemon":
            from .daemon import DaemonBenchmark
            results = DaemonBenchmark().run()
        elif group == "streaming":
            from .streaming import StreamingBenchmark
            results = StreamingBenchmark().run()
        else:
            return

        self.report.results.extend(results if isinstance(results, list) else [results])

    def print_report(self) -> None:
        """Print a human-readable report to stdout."""
        r = self.report

        print()
        print(f"\033[38;5;39m◆\033[0m  Benchmark Report")
        print(f"  Commit: {r.commit}  |  Branch: {r.branch}")
        print(f"  Python: {r.python_version.split()[0]}")
        print(f"  Platform: {r.platform}")
        print()
        print(f"  \033[38;5;44mScore: {r.overall_score:.0f}/100\033[0m"
              f"  |  Duration: {r.total_duration_ms:.0f}ms"
              f"  |  Failures: {r.total_failures}"
              f"  |  Warnings: {r.total_warnings}")
        print()

        for result in r.results:
            score_color = {True: "\033[38;5;42m", False: "\033[38;5;196m"}[result.score >= 80]
            status_line = f"  {result.group}: {result.name}"
            status_line += f"  {score_color}{result.score:.0f}/100\033[0m"
            print(status_line)

            for m in result.metrics:
                status_icon = {"PASS": "\033[38;5;42m✓\033[0m",
                               "WARN": "\033[38;5;220m⚠\033[0m",
                               "FAIL": "\033[38;5;196m✗\033[0m"}.get(m.status, "?")
                val = f"{m.value:.1f} {m.unit}" if m.value else f"{m.value} {m.unit}"
                print(f"    {status_icon} {m.name}: {val}")
            print()

    @staticmethod
    def _info_icon() -> str:
        return "\033[38;5;44mℹ\033[0m"

    @staticmethod
    def _warn_icon() -> str:
        return "\033[38;5;220m⚠\033[0m"