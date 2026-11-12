"""Controlled local command execution owned by ETHAN Core.

No shell is ever started: commands use ``create_subprocess_exec`` with a
validated argv.  The catalogue is deliberately small and read-only.  Every
allowed command requires a human approval through ``ApprovalEngine`` before it
can run; Docker is denied by the Core security policy and this module never
mounts or otherwise grants access to ``/var/run/docker.sock``.
"""

from __future__ import annotations

import asyncio
import os
import pwd
import re
import shutil
import signal
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from core.approval import ApprovalCategory, ApprovalEngine, ApprovalStatus
from core.audit import AuditCategory, AuditDecision, AuditStore
from core.security.policy import Policy, PolicyEffect, PolicyEngine, PolicyLevel, PolicyResult
from core.security.policy.capabilities import PathSecurityError, resolve_safe_path
from core.security.policy.rules import default_rules
from core.system_exec.types import (
    SystemExecDenied,
    SystemExecNotFound,
    SystemExecOperation,
    SystemExecState,
    SystemExecValidationError,
)

DEFAULT_ROOT = "/workspace"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_TIMEOUT_SECONDS = 120.0
MAX_OUTPUT_BYTES = 256 * 1024
MAX_OPERATIONS = 128

_SECRET_VALUE = re.compile(
    r"(?i)\b(token|password|passwd|secret|api[_-]?key|authorization)\b\s*([:=])\s*([^\s]+)"
)
_BEARER_VALUE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*")
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/+\-=]{0,255}$")


def redact(value: str) -> str:
    """Redact common secret assignments before persistence or response."""
    value = _SECRET_VALUE.sub(lambda match: f"{match.group(1)}{match.group(2)}«redacted»", value)
    return _BEARER_VALUE.sub("Bearer «redacted»", value)


def clean_environment() -> dict[str, str]:
    """Return an allowlisted environment; no parent credentials propagate."""
    env: dict[str, str] = {}
    for key in ("PATH", "LANG", "LC_ALL", "TZ"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    env["ETHAN_SYSTEM_EXEC"] = "1"
    return env


def effective_user() -> str:
    try:
        return pwd.getpwuid(os.geteuid()).pw_name
    except KeyError:  # pragma: no cover - uncommon NSS configuration
        return str(os.geteuid())


def assert_not_root() -> None:
    if os.geteuid() == 0:
        raise SystemExecDenied(
            "system command execution is disabled while ETHAN runs as root",
            code="SYSTEM-EXEC-ROOT",
        )


def _no_args(args: list[str]) -> bool:
    return not args


def _version(args: list[str]) -> bool:
    return args in (["--version"], ["-V"])


def _ollama(args: list[str]) -> bool:
    return (args and args[0] in {"list", "ps"} and len(args) == 1) or (
        len(args) == 2 and args[0] == "show" and bool(_SAFE_TOKEN.fullmatch(args[1]))
    )


def _git(args: list[str]) -> bool:
    if not args:
        return False
    verb, rest = args[0], args[1:]
    allowed = {
        "status": {"--short", "--branch", "--porcelain"},
        "log": {"--oneline", "--decorate", "--max-count=1", "--max-count=5", "--max-count=10"},
        "diff": {"--stat", "--name-only", "--cached"},
        "branch": set(),
        "rev-parse": {"--show-toplevel", "--is-inside-work-tree"},
    }
    return verb in allowed and all(part in allowed[verb] for part in rest)


def _docker_read_only(args: list[str]) -> bool:
    # Kept for an explicit denial/audit.  The Core policy denies Docker by
    # default, and this service never makes a socket available to the process.
    return args in (["version"], ["ps"], ["images"])


DEFAULT_COMMANDS: dict[str, Callable[[list[str]], bool]] = {
    "ollama": _ollama,
    "git": _git,
    "python": _version,
    "python3": _version,
    "node": _version,
    "docker": _docker_read_only,
}


class SystemExecService:
    """Run approved commands from the Core-controlled catalogue only."""

    def __init__(
        self,
        *,
        root: str = DEFAULT_ROOT,
        approval_engine: ApprovalEngine,
        audit_store: AuditStore | None = None,
        command_validators: dict[str, Callable[[list[str]], bool]] | None = None,
        max_output_bytes: int = MAX_OUTPUT_BYTES,
    ) -> None:
        self._root = str(Path(root).resolve(strict=False))
        self._approval = approval_engine
        self._audit_store = audit_store
        self._validators = command_validators or DEFAULT_COMMANDS
        self._max_output_bytes = max_output_bytes
        self._operations: dict[str, SystemExecOperation] = {}
        self._policy = PolicyEngine(
            [
                *default_rules(),
                *[
                    Policy(
                        id=f"system.exec.{name}",
                        level=PolicyLevel.SYSTEM,
                        category="process",
                        action="execute",
                        resource=f"command:{name}",
                        effect=PolicyEffect.REQUIRE_CONFIRMATION,
                        reason="A human approval is required for every system command.",
                    )
                    for name in self._validators
                    if name != "docker"
                ],
            ]
        )

    def catalogue(self) -> list[dict[str, Any]]:
        """Expose the fixed capability catalogue, never host PATH contents."""
        return [
            {
                "command": name,
                "available": shutil.which(name) is not None,
                "requires_approval": True,
                "docker_socket_granted": False,
            }
            for name in sorted(self._validators)
        ]

    def submit(
        self,
        *,
        actor: str,
        command: str,
        args: list[str],
        cwd: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> SystemExecOperation:
        """Validate and request human approval; never execute synchronously."""
        assert_not_root()
        argv, executable = self._validate(command, args)
        working_dir = self._resolve_cwd(cwd)
        timeout = self._validate_timeout(timeout_seconds)
        category = "docker" if command == "docker" else "process"
        decision = self._policy.check(category, "execute", f"command:{command}", source="api")
        if decision.result is PolicyResult.DENY:
            self._audit(
                AuditDecision.DENIED,
                "system_exec.refused",
                actor,
                {
                    "command": command,
                    "args": self._redacted_args(args),
                    "reason": decision.reason,
                },
            )
            raise SystemExecDenied(decision.reason)
        operation = SystemExecOperation(
            actor=actor,
            os_user=effective_user(),
            command=command,
            args=self._redacted_args(args),
            cwd=working_dir,
            timeout_seconds=timeout,
        )
        operation.approval_correlation_id = operation.id
        self._operations[operation.id] = operation
        self._trim_operations()
        self._audit(
            AuditDecision.PENDING, "system_exec.request", actor, self._audit_details(operation)
        )
        operation._task = asyncio.create_task(self._approve_then_run(operation, executable, argv))
        return operation

    def get(self, operation_id: str, *, actor: str) -> SystemExecOperation:
        operation = self._operations.get(operation_id)
        if operation is None:
            raise SystemExecNotFound("system command operation was not found")
        if operation.actor != actor:
            raise SystemExecDenied("operation belongs to another user")
        return operation

    async def cancel(self, operation_id: str, *, actor: str) -> SystemExecOperation:
        operation = self.get(operation_id, actor=actor)
        if operation.status in SystemExecState.TERMINAL:
            return operation
        self._approval.cancel_by_correlation(operation.id, "cancelled by requester")
        if operation._process is not None and operation._process.returncode is None:
            self._terminate_group(operation._process.pid)
        if operation._task is not None and not operation._task.done():
            operation._task.cancel()
        operation.status = SystemExecState.CANCELLED
        operation.error = "cancelled by requester"
        operation.finished_at = time.time()
        self._audit(
            AuditDecision.CANCELLED, "system_exec.cancel", actor, self._audit_details(operation)
        )
        return operation

    async def shutdown(self) -> None:
        """Cancel every pending/running operation during API shutdown."""
        for operation in list(self._operations.values()):
            if operation.status in SystemExecState.TERMINAL:
                continue
            await self.cancel(operation.id, actor=operation.actor)

    async def _approve_then_run(
        self, operation: SystemExecOperation, executable: str, argv: list[str]
    ) -> None:
        try:
            response = await self._approval.request(
                ApprovalCategory.COMMAND_EXEC,
                title=f"Run local command: {operation.command}",
                description="ETHAN requests a bounded local system command.",
                details=self._audit_details(operation),
                source="system_exec",
                source_id=operation.actor,
                timeout_seconds=min(300, max(1, int(operation.timeout_seconds))),
                correlation_id=operation.id,
            )
            if response.status is not ApprovalStatus.APPROVED:
                operation.status = SystemExecState.REFUSED
                operation.error = response.reason or response.status.value
                operation.finished_at = time.time()
                decision = (
                    AuditDecision.TIMEOUT
                    if response.status is ApprovalStatus.TIMEOUT
                    else AuditDecision.REJECTED
                )
                self._audit(
                    decision,
                    "system_exec.approval",
                    operation.actor,
                    self._audit_details(operation),
                )
                return
            self._audit(
                AuditDecision.APPROVED,
                "system_exec.approval",
                operation.actor,
                self._audit_details(operation),
            )
            await self._run(operation, executable, argv)
        except asyncio.CancelledError:
            if operation.status not in SystemExecState.TERMINAL:
                operation.status = SystemExecState.CANCELLED
                operation.error = "cancelled"
                operation.finished_at = time.time()
            raise
        except Exception as exc:  # noqa: BLE001 - failure is a terminal operation state
            operation.status = SystemExecState.ERROR
            operation.error = redact(str(exc))
            operation.finished_at = time.time()
            self._audit(
                AuditDecision.ERROR,
                "system_exec.error",
                operation.actor,
                self._audit_details(operation),
            )

    async def _run(self, operation: SystemExecOperation, executable: str, argv: list[str]) -> None:
        operation.status = SystemExecState.RUNNING
        operation.started_at = time.time()
        process = await asyncio.create_subprocess_exec(
            executable,
            *argv,
            cwd=operation.cwd,
            env=clean_environment(),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        operation._process = process
        operation.pid = process.pid
        communicate = asyncio.create_task(process.communicate())
        try:
            stdout, stderr = await asyncio.wait_for(
                asyncio.shield(communicate), operation.timeout_seconds
            )
        except TimeoutError:
            self._terminate_group(process.pid)
            stdout, stderr = await communicate
            operation.status = SystemExecState.TIMED_OUT
            operation.error = f"timed out after {operation.timeout_seconds:g}s"
            decision = AuditDecision.TIMEOUT
        else:
            operation.status = SystemExecState.COMPLETED
            decision = AuditDecision.ALLOWED
        operation.exit_code = process.returncode
        operation.stdout = self._decode_output(stdout)
        operation.stderr = self._decode_output(stderr)
        operation.finished_at = time.time()
        self._audit(
            decision, "system_exec.completed", operation.actor, self._audit_details(operation)
        )

    def _validate(self, command: str, args: list[str]) -> tuple[list[str], str]:
        if command not in self._validators:
            raise SystemExecValidationError("command is not in ETHAN's approved catalogue")
        if not isinstance(args, list) or any(not isinstance(arg, str) for arg in args):
            raise SystemExecValidationError("args must be a list of strings")
        if len(args) > 32 or any("\x00" in arg or len(arg) > 256 for arg in args):
            raise SystemExecValidationError("invalid command arguments")
        if not self._validators[command](args):
            raise SystemExecValidationError("arguments are not allowed for this command")
        executable = shutil.which(command)
        if executable is None:
            raise SystemExecNotFound(f"approved command '{command}' is not installed")
        return list(args), executable

    def _resolve_cwd(self, requested: str | None) -> str:
        root = Path(self._root)
        if not root.is_dir():
            raise SystemExecDenied("controlled execution root is unavailable")
        if requested and Path(requested).is_absolute():
            raise SystemExecValidationError("cwd must be relative to the execution root")
        try:
            return resolve_safe_path(str(root / (requested or ".")), [str(root)])
        except PathSecurityError as exc:
            raise SystemExecValidationError("cwd escapes the controlled execution root") from exc

    @staticmethod
    def _validate_timeout(value: float) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise SystemExecValidationError("timeout must be a number") from None
        if not 0 < value <= MAX_TIMEOUT_SECONDS:
            raise SystemExecValidationError(
                f"timeout must be between 0 and {MAX_TIMEOUT_SECONDS:g} seconds"
            )
        return value

    def _decode_output(self, value: bytes) -> str:
        suffix = b"\n... output truncated by ETHAN\n"
        if len(value) > self._max_output_bytes:
            value = value[: self._max_output_bytes - len(suffix)] + suffix
        return redact(value.decode("utf-8", errors="replace"))

    @staticmethod
    def _redacted_args(args: list[str]) -> list[str]:
        return [redact(arg) for arg in args]

    def _audit_details(self, operation: SystemExecOperation) -> dict[str, Any]:
        return {
            "operation_id": operation.id,
            "command": operation.command,
            "args": list(operation.args),
            "cwd": operation.cwd,
            "os_user": operation.os_user,
            "timeout_seconds": operation.timeout_seconds,
            "status": operation.status,
            "exit_code": operation.exit_code,
            "error": redact(operation.error),
        }

    def _audit(
        self, decision: AuditDecision, action: str, actor: str, details: dict[str, Any]
    ) -> None:
        if self._audit_store is not None:
            self._audit_store.log(
                AuditCategory.COMMAND,
                decision,
                action,
                actor=actor,
                source="system_exec",
                details=details,
                correlation_id=details.get("operation_id", ""),
            )

    @staticmethod
    def _terminate_group(pid: int) -> None:
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            return

    def _trim_operations(self) -> None:
        if len(self._operations) <= MAX_OPERATIONS:
            return
        for operation_id, operation in list(self._operations.items()):
            if operation.status in SystemExecState.TERMINAL:
                self._operations.pop(operation_id, None)
                if len(self._operations) <= MAX_OPERATIONS:
                    return


__all__ = [
    "DEFAULT_COMMANDS",
    "DEFAULT_ROOT",
    "DEFAULT_TIMEOUT_SECONDS",
    "MAX_TIMEOUT_SECONDS",
    "SystemExecService",
    "assert_not_root",
    "clean_environment",
    "effective_user",
    "redact",
]
