"""Command performance benchmarks."""

import sys
from io import StringIO
from unittest import mock

import pytest

from cli.registry import COMMAND_HANDLERS, discover_commands


@pytest.fixture
def runner():
    from tests.cli.ethan.benchmarks.benchmark_runner import BenchmarkRunner

    return BenchmarkRunner(warmup_iterations=3, benchmark_iterations=50)


@pytest.fixture(autouse=True)
def setup_commands():
    """Ensure commands are discovered before benchmarks."""
    discover_commands()


@pytest.fixture
def mock_docker_info():
    """Neutralise l'interrogation du démon Docker et de l'API Core.

    `status` lance `docker info` / `docker ps` en sous-processus ET interroge
    l'API Core (`/v1/state`, `/providers`, `/models`, `/diagnostics`) : la
    durée dépend de la charge de la machine et du réseau, pas du CLI. Sans
    ces mocks, le benchmark mesurait la latence externe (et échouait de
    façon intermittente). On mesure donc bien le temps de la commande CLI.
    """
    completed = mock.MagicMock()
    completed.returncode = 0
    completed.stdout = "Server Version: 26.1.5\n"
    completed.stderr = ""
    with mock.patch("cli.commands.status.subprocess.run", return_value=completed):
        with mock.patch("cli.core.client.alive", return_value=False):
            with mock.patch("cli.core.api.api_get", side_effect=Exception("offline")):
                yield


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

    def test_status_command_performance(self, runner, mock_api_offline, mock_docker_info):
        """Status command should respond in < 100ms mean."""
        cmd = COMMAND_HANDLERS.get("status")
        if not cmd:
            pytest.skip("status not registered")

        summary = runner.measure("status_command", lambda: _capture_output(cmd, []))

        assert summary.mean_ms < 100, (
            f"Status command too slow: {summary.mean_ms:.1f}ms (target: <100ms)"
        )
        assert summary.p95_ms < 150, f"Status P95 too slow: {summary.p95_ms:.1f}ms (target: <150ms)"
        assert summary.max_memory_mb < 30, f"Status memory too high: {summary.max_memory_mb:.1f}MB"

    def test_logs_command_performance(self, runner, mock_logs_empty):
        """Logs command should respond in < 100ms mean."""
        cmd = COMMAND_HANDLERS.get("logs")
        if not cmd:
            pytest.skip("logs not registered")

        summary = runner.measure("logs_command", lambda: _capture_output(cmd, []))

        assert summary.mean_ms < 100, f"Logs command too slow: {summary.mean_ms:.1f}ms"

    def test_memory_recent_performance(self, runner, mock_memory_empty):
        """Memory recent command should respond in < 200ms mean."""
        cmd = COMMAND_HANDLERS.get("memory")
        if not cmd:
            pytest.skip("memory not registered")

        summary = runner.measure("memory_recent", lambda: _capture_output(cmd, ["recent"]))

        assert summary.mean_ms < 200, f"Memory command too slow: {summary.mean_ms:.1f}ms"

    def test_startup_time(self, runner):
        """CLI startup (imports + discovery) should be < 300ms."""

        def full_startup():
            # Clear cached modules, then RESTORE them.
            #
            # Supprimer `sys.modules['cli.*']` sans les restaurer recharge les
            # modules avec les chemins RÉELS (`~/.ethan`, `~/.config/ethan`) :
            # les fixtures d'isolation du conftest cessent de s'appliquer et
            # les modules recréés ne portent plus les monkeypatch des autres
            # tests (frontière HTTP du TUI, journal local…). La pollution
            # croisée était observable sur tests/cli/ethan/tui.
            saved = {k: v for k, v in sys.modules.items() if k.startswith("cli.")}
            try:
                for m in list(saved):
                    del sys.modules[m]
                from cli.registry import discover_commands

                discover_commands()
            finally:
                for m in [k for k in list(sys.modules) if k.startswith("cli.")]:
                    del sys.modules[m]
                sys.modules.update(saved)

        summary = runner.measure("startup", full_startup)

        assert summary.mean_ms < 300, f"Startup too slow: {summary.mean_ms:.1f}ms (target: <300ms)"
