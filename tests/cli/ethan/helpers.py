"""Test utilities for ETHAN CLI tests.

Provides helper functions for common test patterns:
- Fake HTTP responses
- Session/file setup
- Output capture helpers
"""

from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from typing import Any, Generator
from unittest import mock


def make_state_response(
    mode: str = "running",
    active_goal: str = "test",
    running_tasks: int = 0,
    **extra: Any,
) -> bytes:
    """Create a JSON-encoded state response body."""
    data = {"mode": mode, "active_goal": active_goal, "running_tasks": running_tasks, **extra}
    return json.dumps(data).encode()


def make_message_response(response_text: str = "Hello from Ethan") -> bytes:
    """Create a JSON-encoded message response body."""
    return json.dumps({"response": response_text}).encode()


def write_memory_file(path: str, entries: list[dict]) -> None:
    """Write entries to a memory/log JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f)


def write_cache_file(path: str, state: dict) -> None:
    """Write a daemon cache file."""
    from datetime import datetime

    payload = {"ts": datetime.now().isoformat(), "state": state}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f)


def write_pid_file(path: str, pid: int) -> None:
    """Write a PID file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(str(pid))


@contextmanager
def patch_os_kill() -> Generator[mock.MagicMock, None, None]:
    """Patch os.kill to avoid actual signal sending.

    Default behaviour:
    - Raises ProcessLookupError for pid < 0 (simulating dead process)
    - Succeeds for pid > 0 (simulates running process)
    """
    with mock.patch("cli.core.daemon.os.kill") as m:

        def _kill(pid: int, sig: int) -> None:
            if pid < 0:
                raise ProcessLookupError(f"Process {pid} not found")
            # success — process exists

        m.side_effect = _kill
        yield m


@contextmanager
def patch_fork() -> Generator[mock.MagicMock, None, None]:
    """Patch os.fork to avoid actual forking in tests.

    Returns child_pid > 0 to simulate successful fork.
    """
    with mock.patch("cli.core.daemon.os.fork") as m:
        m.return_value = 12345  # Simulate parent receiving child PID
        yield m