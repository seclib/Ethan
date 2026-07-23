"""Snapshot regression tests — compare CLI outputs against golden snapshots."""
import pytest
from pathlib import Path
from unittest.mock import patch

from cli.registry import COMMANDS
from tests.cli.ethan.snapshot import SnapshotEngine
from tests.cli.ethan.comparator import Comparator
from tests.cli.ethan.helpers import capture_output


SNAPSHOT_DIR = Path(__file__).parent.parent / "golden"


@pytest.fixture
def snapshot_engine():
    """Provide snapshot engine."""
    return SnapshotEngine(snapshot_dir=str(SNAPSHOT_DIR))


@pytest.fixture
def comparator():
    """Provide comparison engine with tolerance."""
    return Comparator(tolerance_lines=2, ignore_patterns=[
        r"Session ID:", r"Timestamp:", r"\d{4}-\d{2}-\d{2}",
    ])


class TestStatusSnapshots:
    """Snapshot tests for status command."""

    def test_status_offline(self, snapshot_engine, comparator, mock_api_offline):
        """Status output when API is offline."""
        cmd = COMMANDS.get("status")
        if not cmd:
            pytest.skip("status command not registered")

        # Capture output
        stdout_buf = []
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            exit_code = cmd([])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        # Load expected snapshot
        expected_path = SNAPSHOT_DIR / "status" / "offline.txt"
        if not expected_path.exists():
            # Create snapshot if missing
            snapshot_engine.capture("status", [], output, exit_code)
            pytest.skip(f"Created snapshot: {expected_path}")

        expected = expected_path.read_text()
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

        result = comparator.compare(output.strip(), expected_output, "status offline")
        assert result.passed, f"Snapshot mismatch:\n{result.diff}"


class TestLogsSnapshots:
    """Snapshot tests for logs command."""

    def test_logs_default(self, snapshot_engine, comparator, mock_logs_empty):
        """Logs command with no entries."""
        cmd = COMMANDS.get("logs")
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

        expected_path = SNAPSHOT_DIR / "logs" / "logs_default.txt"
        if not expected_path.exists():
            snapshot_engine.capture("logs", [], output, exit_code)
            pytest.skip(f"Created snapshot: {expected_path}")

        expected = expected_path.read_text()
        expected_lines = []
        in_output = False
        for line in expected.split("\n"):
            if line.startswith("# ==="):
                in_output = True
                continue
            if in_output and not line.startswith("#"):
                expected_lines.append(line)
        expected_output = "\n".join(expected_lines).strip()

        result = comparator.compare(output.strip(), expected_output, "logs default")
        assert result.passed, f"Snapshot mismatch:\n{result.diff}"


class TestMemorySnapshots:
    """Snapshot tests for memory command."""

    def test_memory_recent_empty(self, snapshot_engine, comparator, mock_memory_empty):
        """Memory recent with no history."""
        cmd = COMMANDS.get("memory")
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

        expected_path = SNAPSHOT_DIR / "memory" / "memory_recent.txt"
        if not expected_path.exists():
            snapshot_engine.capture("memory", ["recent"], output, exit_code)
            pytest.skip(f"Created snapshot: {expected_path}")

        expected = expected_path.read_text()
        expected_lines = []
        in_output = False
        for line in expected.split("\n"):
            if line.startswith("# ==="):
                in_output = True
                continue
            if in_output and not line.startswith("#"):
                expected_lines.append(line)
        expected_output = "\n".join(expected_lines).strip()

        result = comparator.compare(output.strip(), expected_output, "memory recent")
        assert result.passed, f"Snapshot mismatch:\n{result.diff}"