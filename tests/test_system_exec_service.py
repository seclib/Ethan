"""Tests for the Core controlled system-command capability.

These tests exercise real subprocesses but install a test-only catalogue.  The
production catalogue remains read-only and does not permit ``python -c``.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

import pytest
from core.approval import ApprovalEngine
from core.system_exec import (
    SystemExecDenied,
    SystemExecService,
    SystemExecState,
    SystemExecValidationError,
)


class AuditCapture:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def log(self, category, decision, action, **kwargs) -> None:
        self.entries.append(
            {"category": category, "decision": decision, "action": action, **kwargs}
        )


def _service(tmp_path, monkeypatch, validators=None):
    monkeypatch.setattr("core.system_exec.service.os.geteuid", lambda: 1000)
    audit = AuditCapture()
    approval = ApprovalEngine()
    service = SystemExecService(
        root=str(tmp_path),
        approval_engine=approval,
        audit_store=audit,
        command_validators=validators or {"python3": lambda args: True},
    )
    return service, approval, audit


async def _approve(approval: ApprovalEngine) -> None:
    for _ in range(50):
        pending = approval.list_pending()
        if pending:
            assert pending[0]["category"] == "command_exec"
            assert approval.resolve(pending[0]["id"], True, responder="reviewer")
            return
        await asyncio.sleep(0.01)
    pytest.fail("approval was never published")


def _run(coro):
    return asyncio.run(coro)


def _dead(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
            return handle.read().split(") ", 1)[1].split(" ", 1)[0] == "Z"
    except OSError:
        return True


def test_authorized_command_captures_separate_streams_exit_and_audit(tmp_path, monkeypatch):
    async def scenario():
        service, approval, audit = _service(tmp_path, monkeypatch)
        operation = service.submit(
            actor="alice",
            command="python3",
            args=["-c", "import sys; print('OUT'); print('ERR', file=sys.stderr)"],
        )
        await _approve(approval)
        await operation._task
        assert operation.status == SystemExecState.COMPLETED
        assert operation.exit_code == 0
        assert operation.stdout == "OUT\n"
        assert operation.stderr == "ERR\n"
        assert operation.os_user
        assert any(entry["action"] == "system_exec.completed" for entry in audit.entries)

    _run(scenario())


def test_refuses_unknown_unsafe_args_and_escape_from_controlled_cwd(tmp_path, monkeypatch):
    service, _, _ = _service(tmp_path, monkeypatch)
    with pytest.raises(SystemExecValidationError):
        service.submit(actor="alice", command="sh", args=["-c", "id"])

    production = SystemExecService(root=str(tmp_path), approval_engine=ApprovalEngine())
    with pytest.raises(SystemExecValidationError):
        production.submit(actor="alice", command="python3", args=["-c", "print(1)"])
    with pytest.raises(SystemExecValidationError):
        service.submit(actor="alice", command="python3", args=["--version"], cwd="../../etc")


def test_root_and_docker_are_denied(tmp_path, monkeypatch):
    service, _, _ = _service(
        tmp_path, monkeypatch, validators={"docker": lambda args: args == ["ps"]}
    )
    monkeypatch.setattr("core.system_exec.service.shutil.which", lambda _: sys.executable)
    with pytest.raises(SystemExecDenied):
        service.submit(actor="alice", command="docker", args=["ps"])

    monkeypatch.setattr("core.system_exec.service.os.geteuid", lambda: 0)
    with pytest.raises(SystemExecDenied) as exc:
        service.submit(actor="alice", command="docker", args=["ps"])
    assert exc.value.code == "SYSTEM-EXEC-ROOT"


def test_timeout_kills_the_process_group(tmp_path, monkeypatch):
    async def scenario():
        service, approval, _ = _service(tmp_path, monkeypatch)
        code = (
            "import subprocess,sys,time; "
            "child=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
            "print(child.pid, flush=True); time.sleep(30)"
        )
        operation = service.submit(
            actor="alice", command="python3", args=["-c", code], timeout_seconds=0.2
        )
        await _approve(approval)
        await operation._task
        assert operation.status == SystemExecState.TIMED_OUT
        child_pid = int(operation.stdout.strip())
        await asyncio.sleep(0.1)
        assert _dead(child_pid)

    _run(scenario())


def test_cancelled_command_and_secrets_do_not_leak(tmp_path, monkeypatch):
    async def scenario():
        service, approval, audit = _service(tmp_path, monkeypatch)
        operation = service.submit(
            actor="alice",
            command="python3",
            args=["-c", "import time; print('TOKEN=super-secret', flush=True); time.sleep(30)"],
        )
        await _approve(approval)
        for _ in range(50):
            if operation.status == SystemExecState.RUNNING:
                break
            await asyncio.sleep(0.01)
        await service.cancel(operation.id, actor="alice")
        with pytest.raises(asyncio.CancelledError):
            await operation._task
        assert operation.status == SystemExecState.CANCELLED
        assert all("super-secret" not in str(entry) for entry in audit.entries)

    _run(scenario())


def test_operations_are_private_to_the_requesting_user(tmp_path, monkeypatch):
    async def scenario():
        service, _, _ = _service(tmp_path, monkeypatch)
        operation = service.submit(actor="alice", command="python3", args=["--version"])
        with pytest.raises(SystemExecDenied):
            service.get(operation.id, actor="bob")
        await service.cancel(operation.id, actor="alice")
        with pytest.raises(asyncio.CancelledError):
            await operation._task

    _run(scenario())
