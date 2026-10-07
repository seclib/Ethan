"""Tests for cli/commands/status.py — ethan status command.

The status command is an aggregate: Docker (local inspection) + Core (single
HTTP boundary). These tests mock BOTH sides so they never open a socket nor
spawn a docker process.
"""

from __future__ import annotations

import json
from unittest import mock

import pytest
from interfaces.cli.core.context import CLIContext, set_context
from interfaces.cli.core.errors import CLIError
from interfaces.cli.core.exit_codes import ExitCode


@pytest.fixture(autouse=True)
def _clean_context():
    set_context(CLIContext(output="human", timeout=5.0))
    yield
    set_context(CLIContext(output="human", timeout=5.0))


def _docker(state: str = "running") -> dict:
    return {
        "runtime": {"state": state, "uptime": "N/A", "memory": "N/A", "cpu": "N/A"},
        "services": [
            {
                "name": "api",
                "container": "ethan-api",
                "status": "running",
                "health": "healthy",
                "port": "8000",
                "image": "api:latest",
            }
        ],
        "error": None,
    }


class TestStatusJson:
    """`-o json` emits exactly one document with the two sections."""

    def test_json_aggregates_docker_and_core(self, capsys) -> None:
        from cli.commands.status import cmd_status

        with mock.patch("cli.commands.status._get_docker_info", return_value=_docker()):
            with mock.patch(
                "cli.commands.status._get_core_info",
                return_value={"reachable": True, "runtime": {"mode": "running"}},
            ):
                result = cmd_status(["--json"])

        assert result == ExitCode.SUCCESS
        payload = json.loads(capsys.readouterr().out)
        assert payload["docker"]["runtime"]["state"] == "running"
        assert payload["core"]["reachable"] is True

    def test_json_is_a_single_document(self, capsys) -> None:
        from cli.commands.status import cmd_status

        set_context(CLIContext(output="json"))
        with mock.patch("cli.commands.status._get_docker_info", return_value=_docker()):
            with mock.patch(
                "cli.commands.status._get_core_info",
                return_value={"reachable": True},
            ):
                cmd_status([])
        json.loads(capsys.readouterr().out)  # must parse as ONE document

    def test_watch_with_json_is_usage_error(self) -> None:
        from cli.commands.status import cmd_status

        set_context(CLIContext(output="json"))
        with pytest.raises(CLIError) as excinfo:
            cmd_status(["--watch"])
        assert excinfo.value.exit_code == ExitCode.USAGE


class TestStatusHuman:
    """Human mode renders both sections with the Core verdict."""

    def test_core_reachable_shows_mode(self, capsys) -> None:
        from cli.commands.status import cmd_status

        with mock.patch("cli.commands.status._get_docker_info", return_value=_docker()):
            with mock.patch(
                "cli.commands.status._get_core_info",
                return_value={
                    "reachable": True,
                    "api_url": "http://localhost:8000",
                    "runtime": {"mode": "running"},
                    "providers": [{"id": "ollama", "status": "connected", "enabled": True}],
                    "models": [],
                    "components": {"components": {"kernel": {"status": "ok"}}},
                    "errors": [],
                },
            ):
                result = cmd_status([])

        out = capsys.readouterr().out
        assert result == ExitCode.SUCCESS
        assert "Core API" in out
        assert "running" in out
        assert "ollama" in out

    def test_core_unreachable_is_reported_not_fatal(self, capsys) -> None:
        from cli.commands.status import cmd_status

        with mock.patch("cli.commands.status._get_docker_info", return_value=_docker()):
            with mock.patch(
                "cli.commands.status._get_core_info",
                return_value={"reachable": False, "api_url": "http://x", "errors": []},
            ):
                result = cmd_status([])

        out = capsys.readouterr().out
        assert result == ExitCode.SUCCESS  # status reports, it does not fail
        assert "unreachable" in out

    def test_docker_error_is_printed(self, capsys) -> None:
        from cli.commands.status import cmd_status

        with mock.patch(
            "cli.commands.status._get_docker_info",
            return_value={
                "runtime": {
                    "state": "unknown",
                    "uptime": "N/A",
                    "memory": "N/A",
                    "cpu": "N/A",
                },
                "services": [],
                "error": "Docker daemon not available",
            },
        ):
            with mock.patch(
                "cli.commands.status._get_core_info",
                return_value={"reachable": False, "errors": []},
            ):
                cmd_status([])

        assert "Docker daemon not available" in capsys.readouterr().out

    def test_watch_renders_once_then_stops(self, capsys) -> None:
        from cli.commands.status import cmd_status

        with mock.patch("cli.commands.status._get_docker_info", return_value=_docker()):
            with mock.patch(
                "cli.commands.status._get_core_info",
                return_value={"reachable": True, "runtime": {"mode": "running"}},
            ):
                with mock.patch(
                    "cli.commands.status.time.sleep",
                    side_effect=KeyboardInterrupt,
                ):
                    result = cmd_status(["--watch"])

        assert result == ExitCode.SUCCESS
        assert "Core API" in capsys.readouterr().out


class TestSummaryCounts:
    """Component counts come from the Core payload, never invented."""

    def test_counts_from_components_map(self) -> None:
        from cli.commands.status import _summary_counts

        counts = _summary_counts(
            {
                "components": {
                    "components": {
                        "kernel": {"status": "ok"},
                        "nats": {"status": "error"},
                        "rag": {"status": "warning"},
                    }
                }
            }
        )
        assert counts["ok"] == 1
        assert counts["error"] == 1
        assert counts["warning"] == 1

    def test_counts_from_summary_numbers(self) -> None:
        from cli.commands.status import _summary_counts

        counts = _summary_counts({"components": {"summary": {"counts": {"ok": 4, "error": 1}}}})
        assert counts["ok"] == 4
        assert counts["error"] == 1

    def test_missing_components_gives_zero_counts(self) -> None:
        from cli.commands.status import _summary_counts

        assert sum(_summary_counts({"components": None}).values()) == 0
        assert sum(_summary_counts({}).values()) == 0
