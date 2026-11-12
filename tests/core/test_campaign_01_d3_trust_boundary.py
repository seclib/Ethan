import asyncio
import tempfile
from pathlib import Path

import pytest
import yaml

from core.applications.integration_approval import IntegrationApprovalService
from core.applications.integration_registration import ApplicationRegistrationService
from core.applications.application_registry import ApplicationIntegrationRegistry
from core.applications.models import ApplicationManifest
from core.applications.permissions import manifest_fingerprint
from core.auth.principal import AgentPrincipal, PrincipalType, issue_trusted_principal

MANIFEST = """identity:
  app_id: demo-trust
  instance_id: i
  name: Demo
  version: 1.0.0
  contract_version: 1.0.0
  publisher: P
  manifest_version: 1
capabilities:
  - analyze
"""


async def make_approval():
    tmp = Path(tempfile.mkdtemp())
    manifest = yaml.safe_load(MANIFEST)
    mf = manifest_fingerprint(ApplicationManifest.from_mapping(manifest))
    ar = IntegrationApprovalService(root=tmp / "hrot", ttl_seconds=300)
    principal = AgentPrincipal(
        principal_id="alice", principal_type=PrincipalType.HUMAN, subject_id="alice", auth_method="jwt"
    )
    req = await ar.create_request(
        application_id="demo-trust",
        repository_identity={"path": "r"},
        manifest_fingerprint=mf,
        manifest_validation_status="valid",
        integration_preview={"application_category": "backend"},
        requesting_actor="alice",
        principal=principal,
        requested_operation="application-integration-register",
    )
    await ar.approve(req.id, approver="reviewer", approved=True, reason="ok")
    return tmp, manifest, mf, ar, req


@pytest.mark.asyncio
async def test_missing_principal_is_rejected() -> None:
    tmp, manifest, mf, ar, req = await make_approval()
    reg = ApplicationIntegrationRegistry()
    svc = ApplicationRegistrationService(registry=reg, approval_service=ar)
    with pytest.raises(ValueError):
        await svc.register(
            manifest=manifest,
            repository_identity={"path": "r"},
            manifest_validation_status="valid",
            integration_preview={"application_category": "backend"},
            approval_id=req.id,
            requested_operation="application-integration-register",
        )


@pytest.mark.asyncio
async def test_trusted_actor_injection_is_blocked() -> None:
    tmp, manifest, mf, ar, req = await make_approval()
    reg = ApplicationIntegrationRegistry()
    svc = ApplicationRegistrationService(registry=reg, approval_service=ar)
    with pytest.raises(ValueError):
        await svc.register(
            manifest=manifest,
            repository_identity={"path": "r"},
            manifest_validation_status="valid",
            integration_preview={"application_category": "backend"},
            approval_id=req.id,
            trusted_actor="eve",
            requested_operation="application-integration-register",
        )


@pytest.mark.asyncio
async def test_freely_constructed_principal_without_proof_is_rejected() -> None:
    tmp, manifest, mf, ar, req = await make_approval()
    reg = ApplicationIntegrationRegistry()
    svc = ApplicationRegistrationService(registry=reg, approval_service=ar)
    freely = AgentPrincipal(principal_id="eve", principal_type=PrincipalType.HUMAN, subject_id="eve")
    with pytest.raises(ValueError):
        await svc.register(
            manifest=manifest,
            repository_identity={"path": "r"},
            manifest_validation_status="valid",
            integration_preview={"application_category": "backend"},
            approval_id=req.id,
            principal=freely,
            requested_operation="application-integration-register",
        )


@pytest.mark.asyncio
async def test_wrong_principal_is_rejected() -> None:
    tmp, manifest, mf, ar, req = await make_approval()
    reg = ApplicationIntegrationRegistry()
    svc = ApplicationRegistrationService(registry=reg, approval_service=ar)
    wrong = AgentPrincipal(principal_id="mallory", principal_type=PrincipalType.HUMAN, subject_id="mallory", auth_method="jwt")
    with pytest.raises(ValueError):
        await svc.register(
            manifest=manifest,
            repository_identity={"path": "r"},
            manifest_validation_status="valid",
            integration_preview={"application_category": "backend"},
            approval_id=req.id,
            principal=wrong,
            requested_operation="application-integration-register",
        )


@pytest.mark.asyncio
async def test_authenticated_principal_registers_successfully() -> None:
    tmp, manifest, mf, ar, req = await make_approval()
    reg = ApplicationIntegrationRegistry()
    svc = ApplicationRegistrationService(registry=reg, approval_service=ar)
    principal = issue_trusted_principal(AgentPrincipal(principal_id="alice", principal_type=PrincipalType.HUMAN, subject_id="alice", auth_method="jwt"))
    result = await svc.register(
        manifest=manifest,
        repository_identity={"path": "r"},
        manifest_validation_status="valid",
        integration_preview={"application_category": "backend"},
        approval_id=req.id,
        principal=principal,
        requested_operation="application-integration-register",
    )
    assert result.status == "registered"
    assert result.record.approval_reference == req.id


@pytest.mark.asyncio
async def test_approval_replay_is_rejected() -> None:
    tmp, manifest, mf, ar, req = await make_approval()
    reg = ApplicationIntegrationRegistry()
    svc = ApplicationRegistrationService(registry=reg, approval_service=ar)
    principal = issue_trusted_principal(AgentPrincipal(principal_id="alice", principal_type=PrincipalType.HUMAN, subject_id="alice", auth_method="jwt"))
    await svc.register(
        manifest=manifest,
        repository_identity={"path": "r"},
        manifest_validation_status="valid",
        integration_preview={"application_category": "backend"},
        approval_id=req.id,
        principal=principal,
        requested_operation="application-integration-register",
    )
    result = await svc.register(
        manifest=manifest,
        repository_identity={"path": "r"},
        manifest_validation_status="valid",
        integration_preview={"application_category": "backend"},
        approval_id=req.id,
        principal=principal,
        requested_operation="application-integration-register",
    )
    assert result.status == "already_registered" 
