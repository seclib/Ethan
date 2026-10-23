"""Unit and integration tests for ApprovalEngine wired with HumanRoot (HROT)."""

from __future__ import annotations

import asyncio
import pytest

from core.approval.engine import ApprovalEngine
from core.approval.types import ApprovalCategory, ApprovalStatus
from core.human_root import HumanRoot, ApprovalOutcome


@pytest.fixture
def engine_with_hrot() -> ApprovalEngine:
    engine = ApprovalEngine()
    hrot = HumanRoot(approval_engine=engine)
    engine.set_human_root(hrot)
    return engine


@pytest.mark.asyncio
async def test_hrot_registers_trust_action_on_request(engine_with_hrot: ApprovalEngine) -> None:
    # Launch request as an async task
    task = asyncio.create_task(
        engine_with_hrot.request(
            category=ApprovalCategory.COMMAND_EXEC,
            title="Run diagnostic probe",
            description="Execute shell command",
            source="admin_user",
            details={"command": "ls -la /var/log"},
        )
    )

    # Allow task to progress to pending state
    await asyncio.sleep(0.01)

    req_ids = list(engine_with_hrot._requests.keys())
    assert len(req_ids) == 1
    req_id = req_ids[0]

    # Check HROT state
    hrot: HumanRoot = engine_with_hrot._human_root
    assert req_id in hrot._in_flight
    action = hrot._in_flight[req_id]
    assert action.caller == "admin_user"
    assert action.category == "command_exec"

    # Clean up task
    engine_with_hrot.resolve(req_id, approved=True, responder="admin")
    resp = await task
    assert resp.status == ApprovalStatus.APPROVED


@pytest.mark.asyncio
async def test_hrot_audit_log_recorded_on_resolve(engine_with_hrot: ApprovalEngine) -> None:
    task = asyncio.create_task(
        engine_with_hrot.request(
            category=ApprovalCategory.SYSTEM_MODIFY,
            title="Update port allocation",
            description="Modify config",
            source="sysadmin",
            details={"key": "port", "val": 3001},
        )
    )
    await asyncio.sleep(0.01)
    req_id = list(engine_with_hrot._requests.keys())[0]

    engine_with_hrot.resolve(
        request_id=req_id,
        approved=True,
        reason="Valid configuration change",
        responder="super_admin",
    )
    resp = await task
    assert resp.status == ApprovalStatus.APPROVED
    assert resp.responder == "super_admin"

    # Verify HROT audit log contains the entry
    hrot: HumanRoot = engine_with_hrot._human_root
    entries = hrot._audit.entries()
    assert len(entries) >= 1
    last = entries[-1]
    assert last["action_id"] == req_id
    assert last["outcome"] == ApprovalOutcome.APPROVED.value


@pytest.mark.asyncio
async def test_hrot_rejection_audit_log(engine_with_hrot: ApprovalEngine) -> None:
    task = asyncio.create_task(
        engine_with_hrot.request(
            category=ApprovalCategory.COMMAND_EXEC,
            title="Purge directory",
            description="rm -rf command",
            source="untrusted_agent",
            details={"path": "/"},
        )
    )
    await asyncio.sleep(0.01)
    req_id = list(engine_with_hrot._requests.keys())[0]

    engine_with_hrot.resolve(
        request_id=req_id,
        approved=False,
        reason="Dangerous action blocked",
        responder="security_officer",
    )
    resp = await task
    assert resp.status == ApprovalStatus.REJECTED

    hrot: HumanRoot = engine_with_hrot._human_root
    entries = hrot._audit.entries()
    last = entries[-1]
    assert last["action_id"] == req_id
    assert last["outcome"] == ApprovalOutcome.REJECTED.value

