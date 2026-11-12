"""Immutable identity models for ETHAN's trusted principals."""

from __future__ import annotations

import hmac
import hashlib
import json
from dataclasses import replace

from dataclasses import dataclass
from datetime import datetime

from core.security.jwt_bootstrap import get_or_create_jwt_secret
from enum import Enum
from typing import Any, Iterable


class PrincipalType(str, Enum):
    """Allowed principal identities in ETHAN."""

    HUMAN = "HUMAN"
    API_KEY = "API_KEY"
    SERVICE = "SERVICE"
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"


def _principal_strings(values: Iterable[Any], field_name: str) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        text = getattr(value, "value", value)
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings")
        normalized.append(text.strip())
    return tuple(normalized)


def _validate_name(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class AgentPrincipal:
    """Immutable identity established by ETHAN, never accepted as raw input."""

    principal_id: str
    principal_type: PrincipalType
    subject_id: str
    actor_id: str | None = None
    initiator_id: str | None = None
    permissions: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()
    owner_id: str | None = None
    request_id: str | None = None
    auth_proof: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    auth_method: str | None = None
    delegation_context: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principal_id", _validate_name(self.principal_id, "principal_id"))
        if not isinstance(self.principal_type, PrincipalType):
            try:
                object.__setattr__(self, "principal_type", PrincipalType(self.principal_type))
            except ValueError as exc:
                raise ValueError(f"unknown principal_type: {self.principal_type!r}") from exc
        object.__setattr__(self, "subject_id", _validate_name(self.subject_id, "subject_id"))

        if self.actor_id is not None:
            object.__setattr__(self, "actor_id", _validate_name(self.actor_id, "actor_id"))
        if self.initiator_id is not None:
            object.__setattr__(self, "initiator_id", _validate_name(self.initiator_id, "initiator_id"))
        if self.owner_id is not None:
            object.__setattr__(self, "owner_id", _validate_name(self.owner_id, "owner_id"))
        if self.request_id is not None:
            object.__setattr__(self, "request_id", _validate_name(self.request_id, "request_id"))
        if self.auth_method is not None:
            object.__setattr__(self, "auth_method", _validate_name(self.auth_method, "auth_method"))

        permissions = _principal_strings(self.permissions, "permissions")
        if self.principal_type is PrincipalType.AGENT and "admin" in {p.lower() for p in permissions}:
            raise ValueError("AGENT principals may not carry autonomous admin privileges")
        object.__setattr__(self, "permissions", permissions)
        object.__setattr__(self, "scopes", _principal_strings(self.scopes, "scopes"))

        # Immutability also applies to the delegation payload's values.
        delegation: list[tuple[str, str]] = []
        if isinstance(self.delegation_context, dict):
            for key, value in self.delegation_context.items():
                if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
                    raise ValueError("delegation_context keys and values must be non-empty strings")
                delegation.append((key.strip(), value.strip()))
        elif isinstance(self.delegation_context, (tuple, list)):
            for item in self.delegation_context:
                if not isinstance(item, tuple) or len(item) != 2:
                    raise ValueError("delegation_context items must be two-item tuples")
                key, value = item
                if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
                    raise ValueError("delegation_context keys and values must be non-empty strings")
                delegation.append((key.strip(), value.strip()))
        else:
            raise ValueError("delegation_context must be a dict or tuple of two-item tuples")
        object.__setattr__(self, "delegation_context", tuple(delegation))

        if self.issued_at and self.expires_at and self.issued_at > self.expires_at:
            raise ValueError("issued_at must not be later than expires_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "principal_type": self.principal_type.value,
            "subject_id": self.subject_id,
            "actor_id": self.actor_id,
            "initiator_id": self.initiator_id,
            "permissions": list(self.permissions),
            "scopes": list(self.scopes),
            "owner_id": self.owner_id,
            "request_id": self.request_id,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "auth_method": self.auth_method,
            "delegation_context": dict(self.delegation_context),
            "auth_proof": self.auth_proof,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentPrincipal":
        if not isinstance(data, dict):
            raise ValueError("principal data must be a dict")
        delegation = data.get("delegation_context")
        if delegation is None or delegation == {}:
            delegation = ()
        try:
            issued = datetime.fromisoformat(str(data["issued_at"])) if data.get("issued_at") is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("issued_at must be ISO-8601") from exc
        try:
            expired = datetime.fromisoformat(str(data["expires_at"])) if data.get("expires_at") is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("expires_at must be ISO-8601") from exc
        return cls(
            principal_id=data["principal_id"],
            principal_type=data["principal_type"],
            subject_id=data["subject_id"],
            actor_id=data.get("actor_id"),
            initiator_id=data.get("initiator_id"),
            permissions=tuple(data.get("permissions") or ()),
            scopes=tuple(data.get("scopes") or ()),
            owner_id=data.get("owner_id"),
            request_id=data.get("request_id"),
            issued_at=issued,
            expires_at=expired,
            auth_method=data.get("auth_method"),
            auth_proof=data.get("auth_proof"),
            delegation_context=delegation,
        )

    def is_expired(self, at: datetime | None = None) -> bool:
        return self.expires_at is not None and (at or datetime.now()) > self.expires_at

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


@dataclass(frozen=True)
class ServiceIdentity:
    """A verifiable service identity without an emission mechanism."""

    service_id: str
    component: str
    allowed_operations: tuple[str, ...] = ()
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    rotation_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "service_id", _validate_name(self.service_id, "service_id"))
        object.__setattr__(self, "component", _validate_name(self.component, "component"))
        object.__setattr__(self, "allowed_operations", _principal_strings(self.allowed_operations, "allowed_operations"))
        if self.expires_at is not None and self.issued_at is not None and self.issued_at > self.expires_at:
            raise ValueError("issued_at must not be later than expires_at")
        if self.rotation_id is not None:
            object.__setattr__(self, "rotation_id", _validate_name(self.rotation_id, "rotation_id"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "component": self.component,
            "allowed_operations": list(self.allowed_operations),
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rotation_id": self.rotation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceIdentity":
        if not isinstance(data, dict):
            raise ValueError("service identity data must be a dict")
        try:
            issued = datetime.fromisoformat(str(data["issued_at"])) if data.get("issued_at") is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("issued_at must be ISO-8601") from exc
        try:
            expired = datetime.fromisoformat(str(data["expires_at"])) if data.get("expires_at") is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("expires_at must be ISO-8601") from exc
        return cls(
            service_id=data.get("service_id", ""),
            component=data.get("component", ""),
            allowed_operations=tuple(data.get("allowed_operations") or ()),
            issued_at=issued,
            expires_at=expired,
            rotation_id=data.get("rotation_id"),
        )

    def is_expired(self, at: datetime | None = None) -> bool:
        return self.expires_at is not None and (at or datetime.now()) > self.expires_at


@dataclass(frozen=True)
class ExecutionContext:
    """A typed execution identity envelope. Delegation is represented, not active."""

    principal: AgentPrincipal
    agent_id: str | None = None
    service_id: str | None = None
    request_id: str | None = None
    delegated_permissions: tuple[str, ...] = ()
    started_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "agent_id", None if self.agent_id is None else _validate_name(self.agent_id, "agent_id"))
        object.__setattr__(self, "service_id", None if self.service_id is None else _validate_name(self.service_id, "service_id"))
        object.__setattr__(self, "request_id", None if self.request_id is None else _validate_name(self.request_id, "request_id"))
        delegated = _principal_strings(self.delegated_permissions, "delegated_permissions")
        # A delegation may never widen the principal's effective authority,
        # including an empty subset, which is represented by an empty tuple.
        if not set(delegated).issubset(set(self.principal.permissions)):
            raise ValueError("delegated_permissions must be a subset of principal.permissions")
        object.__setattr__(self, "delegated_permissions", delegated)
        if self.started_at and self.expires_at and self.started_at > self.expires_at:
            raise ValueError("started_at must not be later than expires_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "principal": self.principal.to_dict(),
            "agent_id": self.agent_id,
            "service_id": self.service_id,
            "request_id": self.request_id,
            "delegated_permissions": list(self.delegated_permissions),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionContext":
        if not isinstance(data, dict):
            raise ValueError("execution context data must be a dict")
        principal = AgentPrincipal.from_dict(data.get("principal", {}))
        try:
            started = datetime.fromisoformat(str(data["started_at"])) if data.get("started_at") is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("started_at must be ISO-8601") from exc
        try:
            expired = datetime.fromisoformat(str(data["expires_at"])) if data.get("expires_at") is not None else None
        except (TypeError, ValueError) as exc:
            raise ValueError("expires_at must be ISO-8601") from exc
        return cls(
            principal=principal,
            agent_id=data.get("agent_id"),
            service_id=data.get("service_id"),
            request_id=data.get("request_id"),
            delegated_permissions=tuple(data.get("delegated_permissions") or ()),
            started_at=started,
            expires_at=expired,
        )

    @property
    def effective_permissions(self) -> tuple[str, ...]:
        return self.delegated_permissions if self.delegated_permissions else self.principal.permissions

    def is_expired(self, at: datetime | None = None) -> bool:
        return self.expires_at is not None and (at or datetime.now()) > self.expires_at


def _principal_canonical(principal: "AgentPrincipal") -> str:
    return json.dumps(
        {
            "principal_id": principal.principal_id,
            "principal_type": principal.principal_type.value,
            "subject_id": principal.subject_id,
            "actor_id": principal.actor_id,
            "initiator_id": principal.initiator_id,
            "permissions": list(principal.permissions),
            "scopes": list(principal.scopes),
            "owner_id": principal.owner_id,
            "request_id": principal.request_id,
            "issued_at": principal.issued_at.isoformat() if principal.issued_at else None,
            "expires_at": principal.expires_at.isoformat() if principal.expires_at else None,
            "auth_method": principal.auth_method,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def issue_trusted_principal(principal: "AgentPrincipal") -> "AgentPrincipal":
    if not isinstance(principal, AgentPrincipal):
        raise ValueError("principal must be an AgentPrincipal")
    if not principal.auth_method or not principal.subject_id:
        raise ValueError("principal must carry an authenticated identity")
    secret = get_or_create_jwt_secret()
    proof = hmac.new(secret.encode("utf-8"), _principal_canonical(principal).encode("utf-8"), hashlib.sha256).hexdigest()
    return replace(principal, auth_proof=proof)


def verify_trusted_principal(principal: "AgentPrincipal") -> bool:
    if not isinstance(principal, AgentPrincipal):
        return False
    if not principal.auth_proof:
        return False
    try:
        expected = hmac.new(
            get_or_create_jwt_secret().encode("utf-8"),
            _principal_canonical(principal).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    except Exception:
        return False
    return hmac.compare_digest(expected, principal.auth_proof)
