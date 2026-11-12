"""Explicit application permissions and Human Root of Trust contracts (MEM-014 Phase 3)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping, Protocol
from uuid import uuid4

from core.applications.models import ApplicationManifest


class PermissionState(StrEnum):
    """Permission lifecycle requested by or granted to an application."""

    REQUESTED = "requested"
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"


class AuthorizationDecisionValue(StrEnum):
    """Result of an authorization evaluation."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class HumanAuthority:
    """Proof that a human root of trust approved or refused a permission.

    This is a contract, not a cryptographic secret. Private material must never
    be stored here.
    """

    principal_id: str
    principal_type: str = "human"
    trusted: bool = False
    human: bool = False

    @property
    def is_human_authority(self) -> bool:
        return (
            bool(self.principal_id)
            and self.principal_type.upper() == "HUMAN"
            and self.trusted is True
            and self.human is True
        )


class HumanApprovalProvider(Protocol):
    """Contract expected from the Human Root of Trust layer."""

    def validate_human_approval(
        self, request_id: str, authority: HumanAuthority, approved: bool
    ) -> bool:
        ...


@dataclass(frozen=True, slots=True)
class PermissionScope:
    """Immutable permission scope."""

    app_id: str
    instance_id: str
    capability: str
    resource: str
    action: str
    context_constraints: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.app_id.strip():
            raise ValueError("app_id must not be empty")
        if not self.instance_id.strip():
            raise ValueError("instance_id must not be empty")
        if not self.capability.strip():
            raise ValueError("capability must not be empty")
        if not self.resource.strip():
            raise ValueError("resource must not be empty")
        if not self.action.strip():
            raise ValueError("action must not be empty")
        if not isinstance(self.context_constraints, dict):
            raise ValueError("context_constraints must be an object")

    def matches(self, request: "PermissionEvaluationRequest") -> bool:
        if self.app_id != request.app_id or self.instance_id != request.instance_id:
            return False
        if self.capability not in {request.capability, "*"}:
            return False
        if not _scope_value_matches(self.resource, request.resource):
            return False
        if not _scope_value_matches(self.action, request.action):
            return False
        return _context_matches(self.context_constraints, request.context)


@dataclass(frozen=True, slots=True)
class PermissionEvaluationRequest:
    """Authorization query with no ambient or implicit permission."""

    app_id: str
    instance_id: str
    capability: str
    resource: str
    action: str
    context: dict[str, Any] = field(default_factory=dict)
    manifest_digest: str | None = None
    contract_digest: str | None = None
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def validate(self) -> None:
        if not self.app_id.strip():
            raise ValueError("app_id must not be empty")
        if not self.instance_id.strip():
            raise ValueError("instance_id must not be empty")
        if not self.capability.strip():
            raise ValueError("capability must not be empty")
        if not self.resource.strip():
            raise ValueError("resource must not be empty")
        if not self.action.strip():
            raise ValueError("action must not be empty")
        if not isinstance(self.context, dict):
            raise ValueError("context must be an object")


@dataclass(slots=True)
class PermissionRequest:
    """A permission explicitly requested by an application."""

    request_id: str
    scope: PermissionScope
    state: PermissionState = PermissionState.PENDING
    reason: str = ""
    manifest_digest: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "state": self.state.value,
            "scope": {
                "app_id": self.scope.app_id,
                "instance_id": self.scope.instance_id,
                "capability": self.scope.capability,
                "resource": self.scope.resource,
                "action": self.scope.action,
                "context_constraints": dict(self.scope.context_constraints),
            },
            "reason": self.reason,
            "manifest_digest": self.manifest_digest,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(slots=True)
class PermissionGrant:
    """An explicitly granted permission, always tied to HROT and manifest integrity."""

    permission_id: str
    scope: PermissionScope
    state: PermissionState = PermissionState.GRANTED
    approved_by: str = ""
    manifest_digest: str | None = None
    contract_digest: str | None = None
    proof_id: str | None = None
    reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    def validate(self) -> None:
        self.scope.validate()
        if self.state != PermissionState.GRANTED:
            raise ValueError("a grant must be in granted state")
        if not self.approved_by.strip():
            raise ValueError("approved_by must identify the HROT principal")

    def is_expired(self, at: datetime | None = None) -> bool:
        when = at if at is not None else datetime.now(timezone.utc)
        if self.expires_at is None:
            return False
        return when >= self.expires_at

    def is_revoked(self) -> bool:
        return self.revoked_at is not None or self.state == PermissionState.REVOKED

    def is_valid(self, at: datetime | None = None) -> bool:
        if self.state != PermissionState.GRANTED:
            return False
        if self.is_revoked():
            return False
        if self.is_expired(at):
            return False
        return True

    def revoke(self, at: datetime | None = None, reason: str = "") -> None:
        self.state = PermissionState.REVOKED
        self.revoked_at = at if at is not None else datetime.now(timezone.utc)
        self.updated_at = self.revoked_at
        if reason:
            self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "permission_id": self.permission_id,
            "state": self.state.value,
            "scope": {
                "app_id": self.scope.app_id,
                "instance_id": self.scope.instance_id,
                "capability": self.scope.capability,
                "resource": self.scope.resource,
                "action": self.scope.action,
                "context_constraints": dict(self.scope.context_constraints),
            },
            "approved_by": self.approved_by,
            "manifest_digest": self.manifest_digest,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": None if self.expires_at is None else self.expires_at.isoformat(),
            "revoked_at": None if self.revoked_at is None else self.revoked_at.isoformat(),
            "is_valid": self.is_valid(),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """Explicit authorization result with a structured machine-readable reason."""

    decision: AuthorizationDecisionValue
    reason_code: str
    message: str
    permission_id: str | None = None
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def allowed(self) -> bool:
        return self.decision == AuthorizationDecisionValue.ALLOW

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_code": self.reason_code,
            "message": self.message,
            "permission_id": self.permission_id,
            "evaluated_at": self.evaluated_at.isoformat(),
            "allowed": self.allowed,
        }


class PermissionService:
    """In-memory explicit permission service.

    Nothing is granted implicitly. A grant requires HROT proof and remains valid
    only while it is not expired, revoked or invalidated by a manifest change.
    """

    def __init__(
        self,
        *,
        production_mode: bool = False,
        trust_verifier: Any = None,
        store: Any | None = None,
    ) -> None:
        self._production_mode = production_mode
        self._trust_verifier = trust_verifier
        self._store = store
        self._requests: dict[str, PermissionRequest] = {}
        self._grants: dict[str, PermissionGrant] = {}
        self._decisions: list[AuthorizationDecision] = []
        if store is not None:
            self._load_from_store()

    def request_permission(
        self,
        app_id: str,
        instance_id: str,
        capability: str,
        resource: str,
        action: str,
        *,
        context_constraints: Mapping[str, Any] | None = None,
        manifest_digest: str | None = None,
        reason: str = "",
    ) -> PermissionRequest:
        scope = PermissionScope(
            app_id=app_id,
            instance_id=instance_id,
            capability=capability,
            resource=resource,
            action=action,
            context_constraints=dict(context_constraints or {}),
        )
        scope.validate()
        request = PermissionRequest(
            request_id=str(uuid4()),
            scope=scope,
            state=PermissionState.REQUESTED,
            reason=reason,
            manifest_digest=manifest_digest,
        )
        self._requests[request.request_id] = request
        if self._store is not None:
            self._store.save_record("permission_requests", request.request_id, request.to_dict())
        return request

    def list_requests(self) -> tuple[PermissionRequest, ...]:
        return tuple(self._requests.values())

    def get_request(self, request_id: str) -> PermissionRequest | None:
        return self._requests.get(request_id)

    def approve_request(
        self,
        request_id: str,
        *,
        approved: bool,
        authority: HumanAuthority | None = None,
        approved_by: str | None = None,
        expires_at: datetime | None = None,
        manifest_digest: str | None = None,
        contract_digest: str | None = None,
        approval_proof: Any = None,
        hrot_proof: Any = None,
        proof: Any = None,
        reason: str = "",
    ) -> PermissionGrant | PermissionRequest:
        request = self._requests.get(request_id)
        if request is None:
            raise KeyError(f"unknown permission request: {request_id}")

        if not approved:
            request.state = PermissionState.DENIED
            request.reason = reason or "denied by Human Root of Trust"
            request.updated_at = datetime.now(timezone.utc)
            return request

        authority, principal_id = self._validate_human_approval(
            request, approved_by=approved_by, authority=authority
        )

        digest = manifest_digest if manifest_digest is not None else request.manifest_digest
        c_digest = contract_digest
        selected_proof = approval_proof if approval_proof is not None else (hrot_proof if hrot_proof is not None else proof)
        verified_proof_id: str | None = None
        if self._production_mode and (self._trust_verifier is None or selected_proof is None):
            raise ValueError("production mode requires a configured human-trust verifier and proof")
        if selected_proof is not None:
            if self._trust_verifier is None:
                raise ValueError("human-trust verifier is not configured")
            from core.applications.hrot_crypto import HrotApprovalProof, HrotApprovalContext
            proof_obj = selected_proof if isinstance(selected_proof, HrotApprovalProof) else HrotApprovalProof.from_mapping(selected_proof)
            expected = HrotApprovalContext(
                approval_id=proof_obj.context.approval_id,
                human_authority_id=principal_id,
                app_id=request.scope.app_id,
                instance_id=request.scope.instance_id,
                capability=request.scope.capability,
                permission=request.scope.capability,
                resource=request.scope.resource,
                action=request.scope.action,
                context_fingerprint=HrotApprovalContext.fingerprint_context(dict(request.scope.context_constraints)),
                manifest_fingerprint=digest,
                contract_fingerprint=c_digest,
            )
            result = self._trust_verifier.verify(proof_obj, expected, expected_manifest_fingerprint=digest, expected_contract_fingerprint=c_digest)
            if not result.valid:
                raise ValueError(f"HROT cryptographic verification failed: {result.status.value}")
            if hasattr(self._trust_verifier, "consume"):
                self._trust_verifier.consume(proof_obj.proof_id)
            verified_proof_id = proof_obj.proof_id
        grant = PermissionGrant(
            permission_id=str(uuid4()),
            scope=request.scope,
            state=PermissionState.GRANTED,
            approved_by=principal_id,
            manifest_digest=digest,
            contract_digest=c_digest,
            proof_id=verified_proof_id,
            reason=reason or "approved by Human Root of Trust",
            expires_at=expires_at,
        )
        grant.validate()
        self._grants[grant.permission_id] = grant
        # A request that has been granted through HROT moves out of the pending
        # queue. Keep the explicit intermediate state available for callers that
        # mark approval without creating a grant.
        request.state = PermissionState.GRANTED
        request.reason = grant.reason
        request.updated_at = datetime.now(timezone.utc)
        return grant

    def deny_request(
        self,
        request_id: str,
        *,
        authority: HumanAuthority | None = None,
        approved_by: str | None = None,
        reason: str = "",
    ) -> PermissionRequest:
        request = self._requests.get(request_id)
        if request is None:
            raise KeyError(f"unknown permission request: {request_id}")
        request.state = PermissionState.DENIED
        request.reason = reason or "denied by Human Root of Trust"
        request.updated_at = datetime.now(timezone.utc)
        if self._store is not None:
            self._store.save_record("permission_requests", request.request_id, request.to_dict())
        return request

    def mark_pending(self, request_id: str) -> PermissionRequest:
        request = self._requests.get(request_id)
        if request is None:
            raise KeyError(f"unknown permission request: {request_id}")
        request.state = PermissionState.PENDING
        request.updated_at = datetime.now(timezone.utc)
        return request

    def revoke_permission(self, permission_id: str, *, at: datetime | None = None, reason: str = "") -> PermissionGrant:
        grant = self._grants.get(permission_id)
        if grant is None:
            raise KeyError(f"unknown permission: {permission_id}")
        grant.revoke(at=at, reason=reason or "revoked")
        if self._store is not None:
            self._store.save_record("permission_grants", grant.permission_id, grant.to_dict())
        return grant

    def list_permissions(self, app_id: str | None = None) -> tuple[PermissionGrant, ...]:
        grants = tuple(self._grants.values())
        if app_id is None:
            return grants
        return tuple(grant for grant in grants if grant.scope.app_id == app_id)

    def get_permission(self, permission_id: str) -> PermissionGrant | None:
        return self._grants.get(permission_id)

    def grant_permission(
        self,
        app_id: str,
        instance_id: str,
        capability: str,
        resource: str,
        action: str,
        *,
        approved_by: str | None = None,
        authority: HumanAuthority | None = None,
        context_constraints: Mapping[str, Any] | None = None,
        manifest_digest: str | None = None,
        contract_digest: str | None = None,
        approval_proof: Any = None,
        hrot_proof: Any = None,
        proof: Any = None,
        expires_at: datetime | None = None,
        reason: str = "",
    ) -> PermissionGrant:
        scope = PermissionScope(
            app_id=app_id,
            instance_id=instance_id,
            capability=capability,
            resource=resource,
            action=action,
            context_constraints=dict(context_constraints or {}),
        )
        scope.validate()
        if authority is None:
            raise ValueError("HROT approval requires a verified HumanAuthority")
        if not isinstance(authority, HumanAuthority) or not authority.is_human_authority:
            raise ValueError("invalid HROT authority")
        if authority.principal_id == app_id:
            raise ValueError("HROT requester cannot approve its own permission")
        if approved_by is not None and approved_by.strip() and approved_by != authority.principal_id:
            raise ValueError("approved_by does not match HROT authority")
        selected_proof = approval_proof if approval_proof is not None else (hrot_proof if hrot_proof is not None else proof)
        verified_proof_id: str | None = None
        if self._production_mode and (self._trust_verifier is None or selected_proof is None):
            raise ValueError("production mode requires a configured human-trust verifier and proof")
        if selected_proof is not None:
            if self._trust_verifier is None:
                raise ValueError("human-trust verifier is not configured")
            from core.applications.hrot_crypto import HrotApprovalProof, HrotApprovalContext
            proof_obj = selected_proof if isinstance(selected_proof, HrotApprovalProof) else HrotApprovalProof.from_mapping(selected_proof)
            expected = HrotApprovalContext(
                approval_id=proof_obj.context.approval_id,
                human_authority_id=authority.principal_id,
                app_id=app_id,
                instance_id=instance_id,
                capability=capability,
                permission=permission if "permission" in locals() else capability,
                resource=resource,
                action=action,
                context_fingerprint=HrotApprovalContext.fingerprint_context(dict(context_constraints or {})),
                manifest_fingerprint=manifest_digest,
                contract_fingerprint=contract_digest,
            )
            result = self._trust_verifier.verify(proof_obj, expected, expected_manifest_fingerprint=manifest_digest, expected_contract_fingerprint=contract_digest)
            if not result.valid:
                raise ValueError(f"HROT cryptographic verification failed: {result.status.value}")
            if hasattr(self._trust_verifier, "consume"):
                self._trust_verifier.consume(proof_obj.proof_id)
            verified_proof_id = proof_obj.proof_id
        principal_id = authority.principal_id
        digest = manifest_digest
        grant = PermissionGrant(
            permission_id=str(uuid4()),
            scope=scope,
            state=PermissionState.GRANTED,
            approved_by=principal_id,
            manifest_digest=digest,
            contract_digest=contract_digest,
            proof_id=verified_proof_id,
            reason=reason or "approved by Human Root of Trust",
            expires_at=expires_at,
        )
        grant.validate()
        self._grants[grant.permission_id] = grant
        if self._store is not None:
            self._store.save_record("permission_grants", grant.permission_id, grant.to_dict())
        return grant

    def revoke(self, permission_id: str, *, at: datetime | None = None, reason: str = "") -> PermissionGrant:
        return self.revoke_permission(permission_id, at=at, reason=reason)

    def list_grants(self, app_id: str | None = None) -> tuple[PermissionGrant, ...]:
        return self.list_permissions(app_id=app_id)

    def get_grant(self, permission_id: str) -> PermissionGrant | None:
        return self.get_permission(permission_id)

    def grant(self, *args: Any, **kwargs: Any) -> PermissionGrant:
        return self.grant_permission(*args, **kwargs)

    def evaluate(self, request: PermissionEvaluationRequest) -> AuthorizationDecision:
        request.validate()
        evaluated_at = request.evaluated_at
        matching_grants = [
            grant
            for grant in self._grants.values()
            if grant.scope.matches(request)
        ]
        valid_grants = [
            grant for grant in matching_grants if grant.is_valid(evaluated_at)
        ]

        decision: AuthorizationDecision

        if not matching_grants:
            decision = AuthorizationDecision(
                decision=AuthorizationDecisionValue.DENY,
                reason_code="NO_MATCHING_PERMISSION",
                message="no permission is granted for this application, capability, resource, action and context",
                evaluated_at=evaluated_at,
            )
        elif not valid_grants:
            grant = sorted(matching_grants, key=lambda item: item.permission_id)[0]
            reason_code = "REVOKED" if grant.is_revoked() else "EXPIRED" if grant.is_expired(evaluated_at) else "INACTIVE"
            decision = AuthorizationDecision(
                decision=AuthorizationDecisionValue.DENY,
                reason_code=reason_code,
                message="matching permission is not currently valid",
                permission_id=grant.permission_id,
                evaluated_at=evaluated_at,
            )
        else:
            if request.manifest_digest is not None:
                manifest_mismatch = any(
                    grant.manifest_digest is not None and grant.manifest_digest != request.manifest_digest
                    for grant in valid_grants
                )
                if manifest_mismatch:
                    decision = AuthorizationDecision(
                        decision=AuthorizationDecisionValue.DENY,
                        reason_code="MANIFEST_CHANGED",
                        message="the current application manifest no longer matches the authorized manifest",
                        permission_id=valid_grants[0].permission_id,
                        evaluated_at=evaluated_at,
                    )
                    self._decisions.append(decision)
                    return decision

            grant = sorted(valid_grants, key=lambda item: item.permission_id)[0]
            decision = AuthorizationDecision(
                decision=AuthorizationDecisionValue.ALLOW,
                reason_code="GRANTED",
                message="explicit Human Root of Trust permission is valid",
                permission_id=grant.permission_id,
                evaluated_at=evaluated_at,
            )

        self._decisions.append(decision)
        if self._store is not None:
            self._store.save_record("authorization_decisions", str(uuid4()), decision.to_dict())
        return decision

    def authorize(
        self,
        app_id: str,
        instance_id: str,
        capability: str,
        resource: str,
        action: str,
        *,
        context: Mapping[str, Any] | None = None,
        manifest_digest: str | None = None,
        manifest: ApplicationManifest | None = None,
        contract_digest: str | None = None,
    ) -> AuthorizationDecision:
        digest = manifest_digest
        if digest is None and manifest is not None:
            digest = manifest_fingerprint(manifest)
        query = PermissionEvaluationRequest(
            app_id=app_id,
            instance_id=instance_id,
            capability=capability,
            resource=resource,
            action=action,
            context=dict(context or {}),
            manifest_digest=digest,
            contract_digest=contract_digest,
        )
        return self.evaluate(query)

    def _load_from_store(self) -> None:
        if self._store is None:
            return
        # Restore grants first so request links can be optional.
        for payload in self._store.load_records("permission_grants"):
            grant = _permission_grant_from_dict(payload)
            if grant is not None:
                self._grants[grant.permission_id] = grant
        # Restore requests.
        for payload in self._store.load_records("permission_requests"):
            request = _permission_request_from_dict(payload)
            if request is not None:
                self._requests[request.request_id] = request

    def audit_trail(self) -> tuple[AuthorizationDecision, ...]:
        return tuple(self._decisions)

    def _validate_human_approval(
        self,
        request: PermissionRequest,
        *,
        approved_by: str | None,
        authority: HumanAuthority | None,
    ) -> tuple[HumanAuthority | None, str]:
        if authority is None:
            raise ValueError("HROT approval requires a verified HumanAuthority")
        if not isinstance(authority, HumanAuthority) or not authority.is_human_authority:
            raise ValueError("invalid HROT authority")
        if authority.principal_id == request.scope.app_id:
            raise ValueError("HROT requester cannot approve its own permission")
        if approved_by is not None and approved_by.strip() and approved_by != authority.principal_id:
            raise ValueError("approved_by does not match HROT authority")
        return authority, authority.principal_id


def _permission_scope_from_dict(payload: Mapping[str, Any]) -> PermissionScope:
    return PermissionScope(
        app_id=str(payload["app_id"]),
        instance_id=str(payload["instance_id"]),
        capability=str(payload["capability"]),
        resource=str(payload["resource"]),
        action=str(payload["action"]),
        context_constraints=dict(payload.get("context_constraints", {})),
    )


def _permission_request_from_dict(payload: Mapping[str, Any]) -> PermissionRequest | None:
    try:
        scope = _permission_scope_from_dict(payload["scope"])
        created_raw = payload.get("created_at")
        updated_raw = payload.get("updated_at")
        created = datetime.fromisoformat(created_raw.replace("Z", "+00:00")) if created_raw else datetime.now(timezone.utc)
        updated = datetime.fromisoformat(updated_raw.replace("Z", "+00:00")) if updated_raw else created
        return PermissionRequest(
            request_id=str(payload["request_id"]),
            scope=scope,
            state=PermissionState(str(payload.get("state", "requested"))),
            reason=str(payload.get("reason", "")),
            manifest_digest=payload.get("manifest_digest"),
            created_at=created,
            updated_at=updated,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _permission_grant_from_dict(payload: Mapping[str, Any]) -> PermissionGrant | None:
    try:
        scope = _permission_scope_from_dict(payload["scope"])
        expires_raw = payload.get("expires_at")
        revoked_raw = payload.get("revoked_at")
        created_raw = payload.get("created_at")
        updated_raw = payload.get("updated_at")
        created = datetime.fromisoformat(created_raw.replace("Z", "+00:00")) if created_raw else datetime.now(timezone.utc)
        updated = datetime.fromisoformat(updated_raw.replace("Z", "+00:00")) if updated_raw else created
        grant = PermissionGrant(
            permission_id=str(payload["permission_id"]),
            scope=scope,
            state=PermissionState(str(payload.get("state", "granted"))),
            approved_by=str(payload.get("approved_by", "")),
            manifest_digest=payload.get("manifest_digest"),
            contract_digest=payload.get("contract_digest"),
            reason=str(payload.get("reason", "")),
            created_at=created,
            updated_at=updated,
            expires_at=datetime.fromisoformat(expires_raw.replace("Z", "+00:00")) if expires_raw else None,
            revoked_at=datetime.fromisoformat(revoked_raw.replace("Z", "+00:00")) if revoked_raw else None,
        )
        return grant
    except (KeyError, TypeError, ValueError):
        return None



def _scope_value_matches(grant_value: str, request_value: str) -> bool:
    return grant_value == request_value or grant_value == "*"


def _context_matches(constraints: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    for key, expected in constraints.items():
        actual = context.get(key, _MISSING)
        if expected == "*":
            if actual is _MISSING:
                return False
            continue
        if actual != expected:
            return False
    return True


_MISSING = object()


def manifest_fingerprint(manifest: ApplicationManifest) -> str:
    """Stable digest for an application manifest without exposing secrets."""
    payload = json.dumps(manifest.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# Phase-level aliases.
PermissionManager = PermissionService
AuthorizationService = PermissionService
PermissionAuthorizationService = PermissionService
ApplicationPermissionService = PermissionService
HROTPermissionService = PermissionService


__all__ = [
    "AuthorizationDecision",
    "AuthorizationDecisionValue",
    "HumanAuthority",
    "HumanApprovalProvider",
    "PermissionEvaluationRequest",
    "PermissionGrant",
    "PermissionManager",
    "PermissionRequest",
    "PermissionScope",
    "PermissionService",
    "PermissionState",
    "manifest_fingerprint",
]
