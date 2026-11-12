from datetime import datetime, timedelta, timezone

from core.applications import (
    AuthorizationDecisionValue,
    HumanAuthority,
    PermissionService,
    PermissionState,
    manifest_fingerprint,
)
from core.applications.models import ApplicationManifest


MANIFEST_A = """identity:
  app_id: alpha
  instance_id: instance-a
  name: Alpha
  version: 1.0.0
  contract_version: 1.0.0
  publisher: Publisher
  manifest_version: 1
"""


def test_default_deny_when_no_permission() -> None:
    service = PermissionService()
    decision = service.authorize("alpha", "instance-a", "cap", "resource", "read")
    assert decision.decision == AuthorizationDecisionValue.DENY
    assert decision.reason_code == "NO_MATCHING_PERMISSION"


def test_permission_requires_human_authority() -> None:
    service = PermissionService()
    try:
        service.grant_permission("alpha", "instance-a", "cap", "resource", "read", approved_by="")
        raise AssertionError("permission granted without HROT authority")
    except ValueError:
        pass


def test_granted_permission_allows_exact_scope() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    service.grant_permission("alpha", "instance-a", "cap", "resource", "read", approved_by="human-1", authority=authority)
    decision = service.authorize("alpha", "instance-a", "cap", "resource", "read")
    assert decision.decision == AuthorizationDecisionValue.ALLOW


def test_wrong_instance_or_capability_is_denied() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    service.grant_permission("alpha", "instance-a", "cap", "resource", "read", approved_by="human-1", authority=authority)
    assert service.authorize("beta", "instance-a", "cap", "resource", "read").decision == AuthorizationDecisionValue.DENY
    assert service.authorize("alpha", "instance-b", "cap", "resource", "read").decision == AuthorizationDecisionValue.DENY
    assert service.authorize("alpha", "instance-a", "other", "resource", "read").decision == AuthorizationDecisionValue.DENY


def test_revoked_permission_is_denied() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    grant = service.grant_permission("alpha", "instance-a", "cap", "resource", "read", approved_by="human-1", authority=authority)
    service.revoke(grant.permission_id, reason="manual")
    decision = service.authorize("alpha", "instance-a", "cap", "resource", "read")
    assert decision.decision == AuthorizationDecisionValue.DENY
    assert decision.reason_code == "REVOKED"


def test_expired_permission_is_denied() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    service.grant_permission(
        "alpha",
        "instance-a",
        "cap",
        "resource",
        "read",
        approved_by="human-1",
        authority=authority,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    decision = service.authorize("alpha", "instance-a", "cap", "resource", "read")
    assert decision.decision == AuthorizationDecisionValue.DENY
    assert decision.reason_code == "EXPIRED"


def test_manifest_change_invalidates_permission() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    manifest = ApplicationManifest.from_yaml(MANIFEST_A)
    digest = manifest_fingerprint(manifest)
    service.grant_permission("alpha", "instance-a", "cap", "resource", "read", approved_by="human-1", authority=authority, manifest_digest=digest)
    changed = ApplicationManifest.from_yaml(MANIFEST_A.replace("version: 1.0.0", "version: 1.0.1"))
    changed_digest = manifest_fingerprint(changed)
    decision = service.authorize("alpha", "instance-a", "cap", "resource", "read", manifest_digest=changed_digest)
    assert decision.decision == AuthorizationDecisionValue.DENY
    assert decision.reason_code == "MANIFEST_CHANGED"


def test_context_constraint_mismatch_is_denied() -> None:
    service = PermissionService()
    authority = HumanAuthority(principal_id="human-1", principal_type="human", trusted=True, human=True)
    service.grant_permission(
        "alpha",
        "instance-a",
        "cap",
        "resource",
        "read",
        approved_by="human-1",
        authority=authority,
        context_constraints={"tenant": "t1"},
    )
    assert service.authorize("alpha", "instance-a", "cap", "resource", "read", context={"tenant": "t1"}).decision == AuthorizationDecisionValue.ALLOW
    assert service.authorize("alpha", "instance-a", "cap", "resource", "read", context={"tenant": "t2"}).decision == AuthorizationDecisionValue.DENY


def test_no_capability_execution_is_triggered() -> None:
    service = PermissionService()
    listed = service.list_requests()
    assert listed == ()
    assert service.audit_trail() == ()
