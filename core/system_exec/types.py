"""Types for ETHAN's controlled local command capability.

This is intentionally separate from ``core.terminal``.  A terminal is an
interactive PTY; a system command is a bounded, non-shell operation with a
single argv, explicit approval and an auditable result.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class SystemExecError(Exception):
    """Base error with a stable code safe to expose through the API."""

    code = "SYSTEM-EXEC-ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class SystemExecDenied(SystemExecError):
    code = "SYSTEM-EXEC-DENIED"


class SystemExecValidationError(SystemExecError):
    code = "SYSTEM-EXEC-INVALID"


class SystemExecNotFound(SystemExecError):
    code = "SYSTEM-EXEC-NOT-FOUND"


class SystemExecState:
    PENDING_APPROVAL = "PENDING_APPROVAL"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    REFUSED = "REFUSED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"

    TERMINAL = frozenset({COMPLETED, REFUSED, TIMED_OUT, CANCELLED, ERROR})


@dataclass
class SystemExecOperation:
    """A Core-owned record for exactly one controlled command invocation."""

    id: str = field(default_factory=lambda: "exec_" + uuid.uuid4().hex[:16])
    actor: str = ""
    os_user: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    cwd: str = ""
    timeout_seconds: float = 30.0
    status: str = SystemExecState.PENDING_APPROVAL
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    approval_correlation_id: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    pid: int | None = None
    _task: Any = field(default=None, repr=False)
    _process: Any = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "actor": self.actor,
            "os_user": self.os_user,
            "command": self.command,
            "args": list(self.args),
            "cwd": self.cwd,
            "timeout_seconds": self.timeout_seconds,
            "status": self.status,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "approval_correlation_id": self.approval_correlation_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "pid": self.pid,
        }


__all__ = [
    "SystemExecDenied",
    "SystemExecError",
    "SystemExecNotFound",
    "SystemExecOperation",
    "SystemExecState",
    "SystemExecValidationError",
]
