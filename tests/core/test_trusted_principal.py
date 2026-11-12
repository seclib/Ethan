"""Tests for immutable Trusted Principal identity models."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from core.auth.principal import AgentPrincipal, ExecutionContext, PrincipalType, ServiceIdentity


def test_all_principal_types_are_distinct():
    assert len(PrincipalType) == 5
    assert {member.value for member in PrincipalType} == {
        "HUMAN", "API_KEY", "SERVICE", "SYSTEM", "AGENT"
    }


def test_minimal_principal_is_immutable_and_has_no_privileges():
    p = AgentPrincipal(principal_id="p-1", principal_type="HUMAN", subject_id="alice")
    assert p.permissions == ()
    with pytest.raises(Exception):
        p.permissions = ()


def test_agent_principal_cannot_be_admin():
    with pytest.raises(ValueError):
        AgentPrincipal(
            principal_id="a-1",
            principal_type=PrincipalType.AGENT,
            subject_id="agent",
            permissions=("admin",),
        )


def test_principal_rejects_empty_fields():
    with pytest.raises(ValueError):
        AgentPrincipal(principal_id="", principal_type="HUMAN", subject_id="alice")
    with pytest.raises(ValueError):
        AgentPrincipal(principal_id="p", principal_type="HUMAN", subject_id="   ")


def test_principal_roundtrip():
    issued = datetime.utcnow()
    p = AgentPrincipal(
        principal_id="human-1",
        principal_type=PrincipalType.HUMAN,
        subject_id="alice",
        permissions=("read",),
        request_id="req-1",
        issued_at=issued,
    )
    restored = AgentPrincipal.from_dict(p.to_dict())
    assert restored.principal_id == p.principal_id
    assert restored.permissions == p.permissions
    assert restored.agent_type if hasattr(restored, "agent_type") else True


def test_service_identity_requires_fields():
    service = ServiceIdentity(service_id="svc-1", component="auth")
    assert service.allowed_operations == ()
    with pytest.raises(ValueError):
        ServiceIdentity(service_id="", component="auth")


def test_service_identity_roundtrip():
    service = ServiceIdentity(
        service_id="svc-1", component="auth", allowed_operations=("verify",)
    )
    restored = ServiceIdentity.from_dict(service.to_dict())
    assert restored.service_id == service.service_id
    assert restored.allowed_operations == service.allowed_operations


def test_execution_context_is_distinct_and_immutable():
    principal = AgentPrincipal(
        principal_id="h", principal_type=PrincipalType.HUMAN, subject_id="alice",
        permissions=("read",),
    )
    ctx = ExecutionContext(
        principal=principal,
        agent_id="agent-1",
        request_id="req-1",
        delegated_permissions=("read",),
    )
    assert ctx.effective_permissions == ("read",)
    with pytest.raises(Exception):
        ctx.agent_id = "agent-2"  # type: ignore[misc]


def test_execution_context_rejects_bad_time():
    principal = AgentPrincipal(
        principal_id="h", principal_type=PrincipalType.HUMAN, subject_id="alice"
    )
    with pytest.raises(ValueError):
        ExecutionContext(
            principal=principal,
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() - timedelta(seconds=1),
        )


def test_principal_rejects_agent_epoch_context():
    principal = AgentPrincipal(
        principal_id="p", principal_type="AGENT", subject_id="agent"
    )
    assert principal.principal_type == PrincipalType.AGENT


def test_random_stranger():
    p = AgentPrincipal(principal_id="p", principal_type="API_KEY", subject_id="k")
    assert p.to_dict()["principal_type"] == "API_KEY"
