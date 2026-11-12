"""Snapshot regression tests — compare CLI outputs against golden snapshots."""

from pathlib import Path

import pytest

from cli.registry import COMMAND_HANDLERS, discover_commands
from tests.cli.ethan.comparator import Comparator
from tests.cli.ethan.snapshot import SnapshotEngine

SNAPSHOT_DIR = Path(__file__).parent.parent / "golden"


def _normalize_output(output: str) -> str:
    """Normalise une sortie pour la comparaison (règle publique du moteur).

    `SnapshotEngine.capture` normalise (ANSI, sessions, timestamps) avant
    d'écrire le golden. Comparer la sortie BRUTE au golden normalisé
    produirait un faux écart : on applique donc la même normalisation des
    deux côtés.
    """
    return SnapshotEngine.normalize(output)


@pytest.fixture(autouse=True)
def _discover_commands():
    """Charge les commandes CLI avant chaque test.

    La fixture autouse `_clear_registry_before_test` (conftest) vide le
    registre entre les tests pour éviter la contamination croisée. Sans
    re-découverte, les commandes seraient absentes et les snapshots
    seraient silencieusement ignorés (skip « command not registered »).
    """
    discover_commands()
    yield


@pytest.fixture
def snapshot_engine():
    """Provide snapshot engine."""
    return SnapshotEngine(snapshot_dir=str(SNAPSHOT_DIR))


@pytest.fixture
def comparator():
    """Provide comparison engine with tolerance."""
    return Comparator(
        tolerance_lines=2,
        ignore_patterns=[
            r"Session ID:",
            r"Timestamp:",
            r"\d{4}-\d{2}-\d{2}",
        ],
    )


class TestStatusSnapshots:
    """Snapshot tests for status command."""

    def test_status_offline(self, snapshot_engine, comparator, mock_api_offline):
        """Status output when API is offline."""
        cmd = COMMAND_HANDLERS.get("status")
        if not cmd:
            pytest.skip("status command not registered")

        # Capture output
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            exit_code = cmd([])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        # Load expected snapshot — le chemin est celui du moteur
        # (SnapshotEngine : `{command}__{hash(argv)}.txt`).
        expected = snapshot_engine.load("status", [])
        if expected is None:
            snapshot_engine.capture("status", [], output, exit_code)
            pytest.skip("Created snapshot: status")

        # Strip header
        expected_lines = []
        in_output = False
        for line in expected.split("\n"):
            if line.startswith("# ==="):
                in_output = True
                continue
            if in_output and not line.startswith("#"):
                expected_lines.append(line)
        expected_output = "\n".join(expected_lines).strip()

        result = comparator.compare(_normalize_output(output).strip(), expected_output, "status offline")
        assert result.passed, f"Snapshot mismatch:\n{result.diff}"


class TestLogsSnapshots:
    """Snapshot tests for logs command."""

    def test_logs_default(self, snapshot_engine, comparator, mock_logs_empty):
        """Logs command with no entries."""
        cmd = COMMAND_HANDLERS.get("logs")
        if not cmd:
            pytest.skip("logs command not registered")

        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            exit_code = cmd([])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        expected = snapshot_engine.load("logs", [])
        if expected is None:
            snapshot_engine.capture("logs", [], output, exit_code)
            pytest.skip("Created snapshot: logs")

        expected_lines = []
        in_output = False
        for line in expected.split("\n"):
            if line.startswith("# ==="):
                in_output = True
                continue
            if in_output and not line.startswith("#"):
                expected_lines.append(line)
        expected_output = "\n".join(expected_lines).strip()

        result = comparator.compare(_normalize_output(output).strip(), expected_output, "logs default")
        assert result.passed, f"Snapshot mismatch:\n{result.diff}"


class TestMemorySnapshots:
    """Snapshot tests for memory command."""

    def test_memory_recent_empty(self, snapshot_engine, comparator, mock_memory_empty):
        """Memory recent with no history."""
        cmd = COMMAND_HANDLERS.get("memory")
        if not cmd:
            pytest.skip("memory command not registered")

        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            exit_code = cmd(["recent"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        expected = snapshot_engine.load("memory", ["recent"])
        if expected is None:
            snapshot_engine.capture("memory", ["recent"], output, exit_code)
            pytest.skip("Created snapshot: memory")

        expected_lines = []
        in_output = False
        for line in expected.split("\n"):
            if line.startswith("# ==="):
                in_output = True
                continue
            if in_output and not line.startswith("#"):
                expected_lines.append(line)
        expected_output = "\n".join(expected_lines).strip()

        result = comparator.compare(_normalize_output(output).strip(), expected_output, "memory recent")
        assert result.passed, f"Snapshot mismatch:\n{result.diff}"
