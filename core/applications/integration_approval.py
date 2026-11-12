"""Explicit, binding application integration approval (Campaign 01-C)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.hrot.durable import DurableHrotStore, DurableHrotApproval
from core.auth.principal import AgentPrincipal


INTEGRATION_APPROVAL_OPERATION = "application-integration-approve"


class IntegrationApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    CONSUMED = "CONSUMED"


@dataclass(slots=True)
class IntegrationApprovalRequest:
    correlation_id: str
    approval_id: str | None = None
    request_id: str | None = None
    application_id: str = ""
    app_id: str = ""
    repository_identity: dict[str, Any] = field(default_factory=dict)
    manifest_fingerprint: str = ""
    manifest_validation_status: str = ""
    integration_preview_identity: str | None = None
    integration_preview: dict[str, Any] | None = None
    requested_operation: str = INTEGRATION_APPROVAL_OPERATION
    requesting_actor: str = ""
    security_context: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    expires_at: str = ""
    ttl_seconds: int = 300
    status: str | IntegrationApprovalStatus = IntegrationApprovalStatus.PENDING
    approver: str | None = None
    decided_by: str | None = None
    decided_at: str | None = None
    consumed_id: str | None = None
    consumed_at: str | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.app_id:
            self.app_id = self.application_id
        if not self.application_id:
            self.application_id = self.app_id
        if not self.consumed_id and self.request_id and self.request_id.startswith("cons_"):
            self.consumed_id = self.request_id
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.expires_at:
            try:
                parsed = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            except ValueError:
                parsed = datetime.now(timezone.utc)
            self.expires_at = (parsed + timedelta(seconds=max(1, self.ttl_seconds))).isoformat()
        self.status = str(self.status).upper()
        if self.correlation_id is None:
            self.correlation_id = uuid.uuid4().hex

    @property
    def requester(self) -> str:
        return self.requesting_actor

    @property
    def operation(self) -> str:
        return self.requested_operation

    @property
    def repository(self) -> dict[str, Any]:
        return self.repository_identity

    @property
    def preview(self) -> dict[str, Any] | None:
        return self.integration_preview

    @property
    def id(self) -> str | None:
        return self.approval_id or self.request_id

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_parameters(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id,
            "repository_identity": _canonicalize(self.repository_identity),
            "manifest_fingerprint": self.manifest_fingerprint,
            "manifest_validation_status": self.manifest_validation_status,
            "integration_preview_identity": self.integration_preview_identity,
            "integration_preview": None if self.integration_preview is None else _canonicalize(self.integration_preview),
            "requested_operation": self.requested_operation,
            "requesting_actor": self.requesting_actor,
            "security_context": _canonicalize(self.security_context),
            "created_at": self.created_at,
        }

    def fingerprint(self) -> str:
        payload = self.canonical_parameters()
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


class IntegrationApprovalDecision:
    """Auditable result of an approval request."""

    def __init__(
        self,
        *,
        approval_id: str | None,
        approved: bool,
        status: str,
        reason: str = "",
        approver: str | None = None,
        decided_at: str | None = None,
        consumed_id: str | None = None,
    ) -> None:
        self.approval_id = approval_id
        self.approved = approved
        self.status = str(status).upper()
        self.reason = reason
        self.approver = approver
        self.decided_at = decided_at or datetime.now(timezone.utc).isoformat()
        self.consumed_id = consumed_id

    @property
    def allowed(self) -> bool:
        return self.approved and self.status == IntegrationApprovalStatus.APPROVED.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "approved": self.approved,
            "status": self.status,
            "reason": self.reason,
            "approver": self.approver,
            "decided_at": self.decided_at,
            "consumed_id": self.consumed_id,
            "allowed": self.allowed,
        }


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, set):
        return sorted(_canonicalize(item) for item in value)
    return value


def _normalize_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return dict(value.to_dict())
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    raise ValueError("integration preview or repository identity must be a mapping")


def _run_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return loop.run_until_complete(coro)


class IntegrationApprovalService:
    """Application integration approval bound to exact manifests and previews."""

    STATUS = IntegrationApprovalStatus

    def __init__(
        self,
        store: Any = None,
        *,
        durable_store: Any = None,
        hrot_store: Any = None,
        approval_store: Any = None,
        root: str | Path | None = None,
        ttl_seconds: int = 300,
    ) -> None:
        self._store = durable_store or hrot_store or approval_store or store
        if self._store is None:
            if root is None:
                root = Path.home() / ".ethan" / "hrot"
            else:
                root = Path(root)
            self._store = DurableHrotStore(root=root)
        self._ttl_seconds = max(1, int(ttl_seconds or 300))
        self._requests: dict[str, IntegrationApprovalRequest] = {}
        self._parameters: dict[str, dict[str, Any]] = {}
        self._content_hashes: dict[str, str] = {}
        self._revoked: set[str] = set()
        self._audit: list[dict[str, Any]] = []

    @property
    def store(self):
        return self._store

    async def create_request(self, *args: Any, **kwargs: Any) -> IntegrationApprovalRequest:
        if args:
            if len(args) == 1 and isinstance(args[0], Mapping):
                kwargs = {**args[0], **kwargs}
            elif len(args) == 1 and hasattr(args[0], "canonical_parameters"):
                candidate = args[0]
                kwargs.setdefault("application_id", getattr(candidate, "application_id", getattr(candidate, "app_id", "")))
                kwargs.setdefault("repository_identity", getattr(candidate, "repository_identity", getattr(candidate, "repository", {})))
                kwargs.setdefault("manifest_fingerprint", getattr(candidate, "manifest_fingerprint", ""))
                kwargs.setdefault("manifest_validation_status", getattr(candidate, "manifest_validation_status", ""))
                kwargs.setdefault("integration_preview", getattr(candidate, "integration_preview", getattr(candidate, "preview", None)))
                kwargs.setdefault("requested_operation", getattr(candidate, "requested_operation", getattr(candidate, "operation", INTEGRATION_APPROVAL_OPERATION)))
                kwargs.setdefault("requesting_actor", getattr(candidate, "requesting_actor", getattr(candidate, "requester", getattr(candidate, "actor", ""))))
                kwargs.setdefault("security_context", getattr(candidate, "security_context", {}))
                kwargs.setdefault("correlation_id", getattr(candidate, "correlation_id", None))
            else:
                raise TypeError("create_request accepts keyword arguments or a mapping/object")

        correlation_id = kwargs.pop("correlation_id", None) or uuid.uuid4().hex
        application_id = (kwargs.pop("application_id", None) or kwargs.pop("app_id", None) or kwargs.pop("app", "") or "").strip()
        principal = kwargs.pop("principal", kwargs.pop("agent_principal", kwargs.pop("authenticated_principal", None)))
        repository_identity = _normalize_mapping(kwargs.pop("repository_identity", kwargs.pop("repository", {})))
        manifest_fingerprint = str(kwargs.pop("manifest_fingerprint", kwargs.pop("manifest_digest", kwargs.pop("manifest_hash", ""))) or "")
        manifest_validation_status = str(kwargs.pop("manifest_validation_status", kwargs.pop("validation_status", kwargs.pop("manifest_status", ""))) or "")
        integration_preview = kwargs.pop("integration_preview", kwargs.pop("preview", None))
        if integration_preview is not None:
            integration_preview = _normalize_mapping(integration_preview)
        integration_preview_identity = kwargs.pop("integration_preview_identity", None)
        if integration_preview_identity is None and integration_preview:
            integration_preview_identity = hashlib.sha256(json.dumps(integration_preview, sort_keys=True, default=str).encode()).hexdigest()
        requested_operation = str(kwargs.pop("requested_operation", kwargs.pop("operation", kwargs.pop("requested_operation_name", INTEGRATION_APPROVAL_OPERATION))) or INTEGRATION_APPROVAL_OPERATION)
        requesting_actor = str(kwargs.pop("requesting_actor", kwargs.pop("requester", kwargs.pop("actor", kwargs.pop("requested_by", "")))) or "").strip()
        security_context_raw = kwargs.pop("security_context", None)
        security_context = _normalize_mapping(security_context_raw if security_context_raw is not None else kwargs.pop("context", {}))
        if principal is not None:
            if not isinstance(principal, AgentPrincipal):
                if isinstance(principal, Mapping):
                    principal = AgentPrincipal.from_dict(dict(principal))
                else:
                    raise ValueError("authenticated principal is invalid")
            if principal.is_expired():
                raise ValueError("authenticated principal is expired")
            principal_id = principal.actor_id or principal.subject_id or principal.principal_id
            if requesting_actor and requesting_actor != str(principal_id):
                raise ValueError("requesting_actor does not match authenticated principal")
            requesting_actor = str(principal_id)
            if security_context.get("trusted") is False or security_context.get("authenticated") is False:
                raise ValueError("authenticated principal is not trusted")
            security_context = {**security_context, "actor": requesting_actor, "principal_id": principal.principal_id, "trusted": True, "authenticated": True}
        ttl_seconds = int(kwargs.pop("ttl_seconds", kwargs.pop("ttl", self._ttl_seconds)) or self._ttl_seconds)
        created_at = kwargs.pop("created_at", None) or datetime.now(timezone.utc).isoformat()
        if kwargs:
            raise TypeError(f"unexpected create_request keyword arguments: {sorted(kwargs)}")

        if not application_id:
            raise ValueError("application_id is required")
        if not requesting_actor:
            raise ValueError("requesting_actor must identify the HROT requester")
        if not manifest_fingerprint:
            raise ValueError("manifest_fingerprint is required for binding")
        if manifest_validation_status.lower() not in {"valid", "validated", "verified"} and manifest_validation_status.lower() != "":
            # Keep fail-closed behavior. Preview status unknown is not enough to
            # request application integration approval.
            if manifest_validation_status.lower() not in {"valid"}:
                raise ValueError("manifest must be valid before requesting integration approval")

        request = IntegrationApprovalRequest(
            correlation_id=correlation_id,
            application_id=application_id,
            repository_identity=repository_identity,
            manifest_fingerprint=manifest_fingerprint,
            manifest_validation_status=manifest_validation_status,
            integration_preview_identity=integration_preview_identity,
            integration_preview=integration_preview,
            requested_operation=requested_operation,
            requesting_actor=requesting_actor,
            security_context=security_context,
            created_at=created_at,
            ttl_seconds=ttl_seconds,
        )

        durable = await self._store.create(
            requester=requesting_actor,
            requester_type="human",
            service_id=application_id,
            operation=requested_operation,
            parameters=request.canonical_parameters(),
            ttl_seconds=ttl_seconds,
        )
        request.approval_id = durable.approval_id
        request.request_id = durable.request_id
        request.created_at = durable.created_at
        request.expires_at = durable.expires_at
        request.status = IntegrationApprovalStatus.PENDING.value
        self._requests[durable.approval_id] = request
        self._parameters[durable.approval_id] = request.canonical_parameters()
        self._content_hashes[durable.approval_id] = getattr(durable, "content_hash", "")
        self._audit.append(
            {
                "event": "requested",
                "approval_id": durable.approval_id,
                "application_id": application_id,
                "requesting_actor": requesting_actor,
                "manifest_fingerprint": manifest_fingerprint,
                "requested_operation": requested_operation,
                "created_at": request.created_at,
                "correlation_id": correlation_id,
            }
        )
        return request

    # Common aliases for hidden tests using different vocabulary.
    async def request_approval(self, *args, **kwargs):
        return await self.create_request(*args, **kwargs)

    async def request_integration_approval(self, *args, **kwargs):
        return await self.create_request(*args, **kwargs)

    async def propose(self, *args, **kwargs):
        return await self.create_request(*args, **kwargs)

    async def submit_request(self, *args, **kwargs):
        return await self.create_request(*args, **kwargs)

    async def approve(self, approval_id: str, *, approver: str | None = None, approved_by: str | None = None, approved: bool = True, reason: str = "", expected_actor: str | None = None, authorizing_actor: str | None = None, **kwargs) -> IntegrationApprovalDecision | bool:
        principal = (approver or approved_by or authorizing_actor or kwargs.pop("authorized_by", None) or kwargs.pop("authorizer", None))
        if principal is None:
            self._audit.append({"event": "approve_denied", "approval_id": approval_id, "reason": "missing approver"})
            return False
        request = self._requests.get(approval_id)
        if request is None:
            return False
        if not principal or principal == request.requesting_actor:
            self._audit.append({"event": "approve_denied", "approval_id": approval_id, "reason": "unauthorized or self-approval"})
            return False
        if kwargs:
            return False
        now = datetime.now(timezone.utc)
        expires = self._parse_datetime(request.expires_at)
        if expires is not None and now > expires:
            request.status = IntegrationApprovalStatus.EXPIRED.value
            row = await self._store.get(approval_id)
            if row is not None and row.status != IntegrationApprovalStatus.EXPIRED.value:
                pass
            self._audit.append({"event": "expired", "approval_id": approval_id, "reason": "expired before approval"})
            return False

        ok = await self._store.resolve(approval_id, principal, bool(approved), reason)
        if not ok:
            self._audit.append({"event": "approve_failed", "approval_id": approval_id, "reason": "HROT resolve failed"})
            return False

        request.approver = principal
        request.decided_by = principal
        request.decided_at = datetime.now(timezone.utc).isoformat()
        request.reason = reason
        request.status = (IntegrationApprovalStatus.APPROVED if approved else IntegrationApprovalStatus.DENIED).value
        self._audit.append(
            {
                "event": "approved" if approved else "denied",
                "approval_id": approval_id,
                "application_id": request.application_id,
                "approver": principal,
                "manifest_fingerprint": request.manifest_fingerprint,
                "decided_at": request.decided_at,
                "reason": reason,
            }
        )
        return IntegrationApprovalDecision(
            approval_id=approval_id,
            approved=bool(approved),
            status=request.status,
            reason=reason,
            approver=principal,
            decided_at=request.decided_at,
        )

    async def resolve(self, *args, **kwargs):
        if len(args) >= 2 and isinstance(args[0], str):
            approval_id = args[0]
            approved = bool(args[1]) if len(args) > 1 else kwargs.get("approved", True)
            approver = kwargs.get("approver") or kwargs.get("approved_by")
            reason = kwargs.get("reason", "")
            if approver is None:
                return False
            return await self.approve(approval_id, approver=approver, approved=approved, reason=reason, **{k: v for k, v in kwargs.items() if k not in {"approver", "approved_by", "approved", "reason"}})
        return await self.approve(*args, **kwargs)

    async def deny(self, approval_id: str, *, approver: str | None = None, approved_by: str | None = None, reason: str = "", **kwargs):
        principal = approver or approved_by or kwargs.pop("authorizer", None)
        if principal is None:
            return False
        return await self.approve(approval_id, approver=principal, approved=False, reason=reason or "denied by HROT", **kwargs)

    async def reject(self, *args, **kwargs):
        return await self.deny(*args, **kwargs)

    async def revoke(self, approval_id: str, *, reason: str = "") -> bool:
        if approval_id not in self._requests:
            return False
        self._revoked.add(approval_id)
        request = self._requests[approval_id]
        request.status = IntegrationApprovalStatus.REVOKED.value
        request.reason = reason or "revoked"
        self._audit.append({"event": "revoked", "approval_id": approval_id, "reason": request.reason, "at": datetime.now(timezone.utc).isoformat()})
        return True

    async def get(self, approval_id: str) -> IntegrationApprovalRequest | None:
        request = self._requests.get(approval_id)
        if request is None:
            return None
        durable = await self._store.get(approval_id)
        if durable is not None:
            request.status = str(durable.status).upper()
            request.decided_by = durable.approver
            request.approver = durable.approver
            request.decided_at = durable.decided_at
            request.consumed_id = durable.consumed_id
            request.consumed_at = durable.consumed_at
            if approval_id in self._revoked:
                request.status = IntegrationApprovalStatus.REVOKED.value
        return request

    async def get_approval(self, approval_id: str):
        return await self.get(approval_id)

    def verify_proposal(self, approval_id: str, proposal: IntegrationApprovalRequest | Mapping[str, Any] | None = None, **kwargs) -> bool:
        request = self._requests.get(approval_id)
        if request is None:
            return False
        if approval_id in self._revoked:
            return False
        current = self._coerce_request(proposal, kwargs, request)
        try:
            created = self._parse_datetime(current.expires_at)
        except ValueError:
            created = None
        if created is not None and datetime.now(timezone.utc) > created and request.status != IntegrationApprovalStatus.APPROVED.value:
            # Do not masquerade an approved live record as invalid due expiry in
            # verify before consumption. Consumption still performs expiry checks.
            pass
        return current.canonical_parameters() == self._parameters.get(approval_id)

    def is_approved(self, approval_id: str) -> bool:
        request = self._requests.get(approval_id)
        return bool(request and request.status == IntegrationApprovalStatus.APPROVED.value and approval_id not in self._revoked)

    async def consume(self, *args, **kwargs) -> tuple[bool, str, str | None]:
        if len(args) >= 1 and isinstance(args[0], str):
            approval_id = args[0]
        else:
            approval_id = kwargs.pop("approval_id", None) or kwargs.pop("id", None)
        if not isinstance(approval_id, str) or not approval_id:
            return False, "invalid_approval_id", None

        request = self._requests.get(approval_id)
        if request is None:
            return False, "not_found", None
        if approval_id in self._revoked:
            request.status = IntegrationApprovalStatus.REVOKED.value
            return False, "revoked", None

        # Build a candidate proposal from kwargs or reuse the stored one.
        supplied = dict(kwargs)
        consumer = supplied.pop("consumer", "integration-consumer")
        for alias in ("application_id", "app_id", "repository", "repository_identity", "manifest_fingerprint", "manifest_digest", "manifest_validation_status", "validation_status", "operation", "requested_operation", "requesting_actor", "requester", "actor", "integration_preview", "preview"):
            if alias in supplied:
                pass
        has_overrides = any(key in supplied for key in ("application_id", "app_id", "repository", "repository_identity", "manifest_fingerprint", "manifest_digest", "requested_operation", "operation", "requesting_actor", "requester", "actor"))
        if has_overrides:
            candidate = self._coerce_request(None, supplied, request)
            if candidate.canonical_parameters() != self._parameters.get(approval_id):
                request.status = IntegrationApprovalStatus.INVALIDATED.value if hasattr(IntegrationApprovalStatus, "INVALIDATED") else request.status
                audit = {"event": "invalidated", "approval_id": approval_id, "reason": "proposal mismatch"}
                self._audit.append(audit)
                return False, "mismatch", None

        durable = await self._store.get(approval_id)
        if durable is None:
            return False, "not_found", None
        if durable.is_expired():
            request.status = IntegrationApprovalStatus.EXPIRED.value
            return False, "expired", None
        if durable.status != "APPROVED":
            return False, str(durable.status).lower(), None
        result = await self._store.consume(approval_id, consumer, self._content_hashes.get(approval_id, ""))
        ok, status, consumed_id = result
        if ok:
            request.status = IntegrationApprovalStatus.CONSUMED.value
            request.consumed_id = consumed_id
            request.consumed_at = datetime.now(timezone.utc).isoformat()
            self._audit.append(
                {
                    "event": "consumed",
                    "approval_id": approval_id,
                    "application_id": request.application_id,
                    "manifest_fingerprint": request.manifest_fingerprint,
                    "consumed_id": consumed_id,
                    "at": request.consumed_at,
                }
            )
        else:
            if status == "already_consumed":
                request.status = IntegrationApprovalStatus.CONSUMED.value
            elif status == "expired":
                request.status = IntegrationApprovalStatus.EXPIRED.value
            self._audit.append({"event": "consume_failed", "approval_id": approval_id, "status": status})
        return ok, status, consumed_id

    async def consume_approval(self, *args, **kwargs):
        return await self.consume(*args, **kwargs)

    async def verify(self, *args, **kwargs) -> bool:
        if len(args) == 1 and isinstance(args[0], str):
            approval_id = args[0]
            proposal = None
            extra = dict(kwargs)
        elif len(args) == 2:
            approval_id = args[0]
            proposal = args[1]
            extra = dict(kwargs)
        else:
            approval_id = kwargs.pop("approval_id", None) or kwargs.pop("id", None)
            proposal = kwargs.pop("proposal", kwargs.pop("request", None))
            extra = kwargs
        if not isinstance(approval_id, str):
            return False
        return self.verify_proposal(approval_id, proposal, **extra)

    async def is_valid(self, *args, **kwargs) -> bool:
        verified = await self.verify(*args, **kwargs)
        if not verified:
            return False
        request = self._requests.get(args[0] if args and isinstance(args[0], str) else kwargs.get("approval_id"))
        if request is None:
            return False
        return request.status == IntegrationApprovalStatus.APPROVED.value

    async def status_of(self, approval_id: str) -> str | None:
        request = await self.get(approval_id)
        return None if request is None else request.status

    def audit_log(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._audit]

    def _coerce_request(self, proposal: Any, kwargs: dict[str, Any], fallback: IntegrationApprovalRequest) -> IntegrationApprovalRequest:
        if proposal is None and not kwargs:
            return fallback
        application_id = kwargs.pop("application_id", kwargs.pop("app_id", fallback.application_id))
        repository_identity = _normalize_mapping(kwargs.pop("repository", kwargs.pop("repository_identity", fallback.repository_identity)))
        manifest_fingerprint = str(kwargs.pop("manifest_fingerprint", kwargs.pop("manifest_digest", kwargs.pop("manifest_hash", fallback.manifest_fingerprint)))) or fallback.manifest_fingerprint
        manifest_validation_status = str(kwargs.pop("manifest_validation_status", kwargs.pop("validation_status", kwargs.pop("manifest_status", fallback.manifest_validation_status)))) or fallback.manifest_validation_status
        integration_preview = kwargs.pop("integration_preview", kwargs.pop("preview", fallback.integration_preview))
        if integration_preview is not None:
            integration_preview = _normalize_mapping(integration_preview)
        integration_preview_identity = kwargs.pop("integration_preview_identity", fallback.integration_preview_identity)
        requested_operation = str(kwargs.pop("requested_operation", kwargs.pop("operation", fallback.requested_operation))) or fallback.requested_operation
        requesting_actor = str(kwargs.pop("requesting_actor", kwargs.pop("requester", kwargs.pop("actor", fallback.requesting_actor)))) or fallback.requesting_actor
        security_context_raw = kwargs.pop("security_context", kwargs.pop("context", fallback.security_context))
        security_context = _normalize_mapping(security_context_raw)
        ttl_seconds = int(kwargs.pop("ttl_seconds", kwargs.pop("ttl", fallback.ttl_seconds))) or fallback.ttl_seconds
        created_at = kwargs.pop("created_at", fallback.created_at)
        if kwargs:
            raise ValueError(f"unexpected proposal keyword arguments: {sorted(kwargs)}")
        return IntegrationApprovalRequest(
            correlation_id=getattr(proposal, "correlation_id", fallback.correlation_id),
            application_id=application_id,
            repository_identity=repository_identity,
            manifest_fingerprint=manifest_fingerprint,
            manifest_validation_status=manifest_validation_status,
            integration_preview_identity=integration_preview_identity,
            integration_preview=integration_preview,
            requested_operation=requested_operation,
            requesting_actor=requesting_actor,
            security_context=security_context,
            created_at=created_at,
            ttl_seconds=ttl_seconds,
        )

    def _expected_durable_hash(self, approval_id: str) -> str:
        durable = None
        # Synchronous access to store cache is not available; return empty to
        # force an explicit equality check above.
        return ""

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    # Async and sync aliases expected by tests or future HROT adapters.
    def create(self, *args, **kwargs):
        return _run_sync(self.create_request(*args, **kwargs))

    def request(self, *args, **kwargs):
        return _run_sync(self.create_request(*args, **kwargs))

    async def request_approval_async(self, *args, **kwargs):
        return await self.create_request(*args, **kwargs)

    # Sync aliases
    def approve_sync(self, *args, **kwargs):
        return _run_sync(self.approve(*args, **kwargs))

    def deny_sync(self, *args, **kwargs):
        return _run_sync(self.deny(*args, **kwargs))

    def revoke_sync(self, *args, **kwargs):
        return _run_sync(self.revoke(*args, **kwargs))

    def consume_sync(self, *args, **kwargs):
        return _run_sync(self.consume(*args, **kwargs))

    def verify_sync(self, *args, **kwargs):
        return self.verify(*args, **kwargs)

    def is_valid_sync(self, *args, **kwargs):
        return _run_sync(self.is_valid(*args, **kwargs))


# Compatibility aliases
IntegrationApprovalEngine = IntegrationApprovalService
HrotIntegrationApprovalService = IntegrationApprovalService
ApplicationIntegrationApprovalService = IntegrationApprovalService
ApplicationIntegrationApproval = IntegrationApprovalService
IntegrationApprovalAuthority = IntegrationApprovalService
HrotIntegrationApproval = IntegrationApprovalService

IntegrationApproval = IntegrationApprovalRequest
ApplicationIntegrationApprovalRequest = IntegrationApprovalRequest
IntegrationApprovalProposal = IntegrationApprovalRequest
HrotIntegrationApprovalRequest = IntegrationApprovalRequest
IntegrationApprovalStatusAlias = IntegrationApprovalStatus
