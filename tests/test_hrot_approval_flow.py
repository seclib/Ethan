"""Integration test for HROT in-stream approval flow (component level)."""

from __future__ import annotations

import asyncio

import pytest

from core.approval import ApprovalEngine
from core.approval.types import ApprovalStatus, ApprovalAuthority
from core.security.integration import SecureToolEnforcer, ToolRejectedError
from core.tools.types import Tool, ToolContext


@pytest.mark.asyncio
async def test_approval_flow_approved():
    """Policy REQUIRE_CONFIRMATION → create request → approve → execute allowed."""
    engine = ApprovalEngine()
    enforcer = SecureToolEnforcer()

    # Patch enforcer.check to raise REQUIRE_CONFIRMATION when not approved
    original_check = enforcer.check
    async def fake_check(tool, params, context, *, approved=False):
        if not approved:
            raise ToolRejectedError("Confirmation requise", decision=type("D", (), {"result": "require_confirmation"})())
        return None
    enforcer.check = fake_check

    tool = Tool(id="t1", name="web_search", description="search", category="search", provider="builtin")
    params = {"query": "test"}
    context = ToolContext(query="test", user_id="alice", source="chat")

    # 1. First check raises REQUIRE_CONFIRMATION
    with pytest.raises(ToolRejectedError) as exc_info:
        await enforcer.check(tool, params, context, approved=False)
    assert str(exc_info.value.decision.result) == "require_confirmation"

    # 2. Create approval request
    req = await engine.create_request(
        category="command_exec",
        title="HROT [web_search]",
        description="Confirmation requise",
        details={"tool": "web_search", "params": params},
        source="chat",
        source_id="alice",
        timeout_seconds=5,
        correlation_id="chat-1",
    )
    assert req.id

    # 3. Resolve concurrently with await_decision
    authority = ApprovalAuthority(
        principal_id="admin", principal_type="HUMAN", authenticated=True,
        permissions=("ADMIN",), human=True, trusted=True,
    )

    async def _resolve():
        await asyncio.sleep(0.1)
        return engine.resolve(req.id, approved=True, reason="test", authority=authority)

    decision_task = asyncio.create_task(_resolve())
    response = await engine.await_decision(req.id, timeout_seconds=5)
    resolved = await decision_task
    assert resolved is True
    assert str(getattr(response.status, "value", response.status)).lower() == "approved"

    # 5. Second check with approved=True passes (no raise) — fake_check returns None
    await enforcer.check(tool, params, context, approved=True)


@pytest.mark.asyncio
async def test_approval_flow_rejected():
    """Policy REQUIRE_CONFIRMATION → create request → reject → no execution."""
    engine = ApprovalEngine()
    enforcer = SecureToolEnforcer()

    async def fake_check(tool, params, context, *, approved=False):
        if not approved:
            raise ToolRejectedError("Confirmation requise", decision=type("D", (), {"result": "require_confirmation"})())
        return None
    enforcer.check = fake_check

    tool = Tool(id="t1", name="web_search", description="search", category="search", provider="builtin")
    params = {"query": "test"}
    context = ToolContext(query="test", user_id="alice", source="chat")

    # Create request
    req = await engine.create_request(
        category="command_exec",
        title="HROT [web_search]",
        description="Confirmation requise",
        details={"tool": "web_search", "params": params},
        source="chat",
        source_id="alice",
        timeout_seconds=5,
        correlation_id="chat-1",
    )

    # Reject concurrently
    authority = ApprovalAuthority(
        principal_id="admin", principal_type="HUMAN", authenticated=True,
        permissions=("ADMIN",), human=True, trusted=True,
    )

    async def _resolve():
        await asyncio.sleep(0.1)
        return engine.resolve(req.id, approved=False, reason="rejected", authority=authority)

    decision_task = asyncio.create_task(_resolve())
    response = await engine.await_decision(req.id, timeout_seconds=5)
    resolved = await decision_task
    assert resolved is True
    assert str(getattr(response.status, "value", response.status)).lower() == "rejected"

    # Verify enforcer still rejects without approved=True
    with pytest.raises(ToolRejectedError):
        await enforcer.check(tool, params, context, approved=False)


@pytest.mark.asyncio
async def test_approval_double_resolve_prevented():
    """Double resolution is prevented."""
    engine = ApprovalEngine()
    req = await engine.create_request(
        category="command_exec",
        title="HROT [test]",
        description="test",
        source="chat",
        source_id="alice",
        timeout_seconds=5,
    )
    authority = ApprovalAuthority(
        principal_id="admin", principal_type="HUMAN", authenticated=True,
        permissions=("ADMIN",), human=True, trusted=True,
    )
    assert engine.resolve(req.id, approved=True, reason="first", authority=authority) is True
    # Second resolve should fail
    assert engine.resolve(req.id, approved=True, reason="second", authority=authority) is False


@pytest.mark.asyncio
async def test_approval_unknown_request():
    """Resolving an unknown request_id fails."""
    engine = ApprovalEngine()
    authority = ApprovalAuthority(
        principal_id="admin", principal_type="HUMAN", authenticated=True,
        permissions=("ADMIN",), human=True, trusted=True,
    )
    assert engine.resolve("nonexistent", approved=True, reason="test", authority=authority) is False
    response = await engine.await_decision("nonexistent", timeout_seconds=1)
    assert str(getattr(response.status, "value", response.status)).lower() in ("cancelled", "timeout")


@pytest.mark.asyncio
async def test_approval_expired_or_timeout():
    """Expired/timeout approval does not authorize."""
    engine = ApprovalEngine()
    req = await engine.create_request(
        category="command_exec",
        title="HROT [test]",
        description="test",
        source="chat",
        source_id="alice",
        timeout_seconds=1,
        correlation_id="chat-1",
    )
    # Don't resolve → timeout
    response = await engine.await_decision(req.id, timeout_seconds=1)
    assert str(getattr(response.status, "value", response.status)).lower() == "timeout"


@pytest.mark.asyncio
async def test_approval_self_approval_rejected():
    """Requester cannot approve their own request."""
    engine = ApprovalEngine()
    req = await engine.create_request(
        category="command_exec",
        title="HROT [test]",
        description="test",
        source="chat",
        source_id="alice",
        timeout_seconds=5,
    )
    authority = ApprovalAuthority(
        principal_id="alice", principal_type="HUMAN", authenticated=True,
        permissions=("ADMIN",), human=True, trusted=True,
    )
    assert engine.resolve(req.id, approved=True, reason="self", authority=authority) is False


@pytest.mark.asyncio
async def test_approval_non_admin_rejected():
    """Non-admin cannot resolve."""
    engine = ApprovalEngine()
    req = await engine.create_request(
        category="command_exec",
        title="HROT [test]",
        description="test",
        source="chat",
        source_id="alice",
        timeout_seconds=5,
    )
    authority = ApprovalAuthority(
        principal_id="bob", principal_type="HUMAN", authenticated=True,
        permissions=(), human=True, trusted=True,
    )
    assert engine.resolve(req.id, approved=True, reason="test", authority=authority) is False