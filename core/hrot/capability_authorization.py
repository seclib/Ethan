"""Reusable HROT authorization for agent application-capability invocations (02-F2-R4-B).

This module implements the canonical, fail-closed authorization evaluation that
protects future application-capability projection and invocation from ETHAN
agents.  It deliberately does not invoke any capability implementation; it only
evaluates and records an auditable authorization decision.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional

from core.auth.principal import verify_trusted_principal

logger = logging.getLogger(__name__)


class CapabilityAuthorizationDecisionValue(str, Enum):
    """Possible outcomes of an agent capability authorization evaluation."""

    ALLOW = "ALLOW"
    DENY = "DENY"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_execution_context(value: Any) -> Any | None:
    if value is None:
        return None
    if hasattr(value, "principal") and hasattr(value, "to_dict"):
        return value
    if isinstance(value, Mapping):
        try:
            from core.auth import ExecutionContext

            return ExecutionContext.from_dict(dict(value))
        except Exception:
            try:
                from core.auth.principal import ExecutionContext

                return ExecutionContext.from_dict(dict(value))
            except Exception:
                return None
    return None


def _actor_id(context: Any) -> str | None:
    principal = getattr(context, "principal", None)
    if principal is None:
        return None
    for attr in ("actor_id", "subject_id", "principal_id"):
        value = getattr(principal, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


@dataclass(frozen=True)
class CapabilityAuthorizationRequest:
    """Typed authorization request for an agent application-capability invocation."""

    execution_context: Any
    agent_id: str
    application_id: str
    capability_id: str
    execution_id: str | None = None
    correlation_id: str | None = None
    requested_operation: str | None = None
    binding: Any | None = None
    binding_id: str | None = None
    resource: str | None = None
    action: str | None = None
    context: Mapping[str, Any] | None = None
    registry: Any | None = None
    permission_service: Any | None = None


@dataclass(frozen=True)
class CapabilityAuthorizationDecision:
    """Auditable result of an agent capability authorization evaluation."""

    decision: CapabilityAuthorizationDecisionValue
    allowed: bool
    reason_code: str
    message: str
    actor_id: str | None = None
    agent_id: str | None = None
    execution_id: str | None = None
    correlation_id: str | None = None
    application_id: str | None = None
    instance_id: str | None = None
    capability_id: str | None = None
    binding_id: str | None = None
    binding: Any | None = None
    permission: str | None = None
    evaluated_at: datetime = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Compatibility aliases for callers expecting HTTP-HROT vocabulary.
    @property
    def permission_id(self) -> str | None:
        return self.binding_id

    @property
    def timestamp(self) -> datetime:
        return self.evaluated_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "allowed": self.allowed,
            "reason_code": self.reason_code,
            "message": self.message,
            "actor_id": self.actor_id,
            "agent_id": self.agent_id,
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
            "application_id": self.application_id,
            "instance_id": self.instance_id,
            "capability_id": self.capability_id,
            "binding_id": self.binding_id,
            "permission": self.permission,
            "policy": self.permission,
            "evaluated_at": self.evaluated_at.isoformat(),
            "timestamp": self.evaluated_at.isoformat(),
            "metadata": dict(self.metadata),
        }


def _deny(
    reason_code: str,
    message: str,
    *,
    request: CapabilityAuthorizationRequest | None = None,
    execution_context: Any | None = None,
    actor_id: str | None = None,
    agent_id: str | None = None,
    application_id: str | None = None,
    instance_id: str | None = None,
    capability_id: str | None = None,
    binding_id: str | None = None,
    binding: Any | None = None,
    permission: str | None = None,
    execution_id: str | None = None,
    correlation_id: str | None = None,
) -> CapabilityAuthorizationDecision:
    actor = actor_id if actor_id is not None else (_actor_id(execution_context) if execution_context is not None else None)
    agent = agent_id if agent_id is not None else (getattr(execution_context, "agent_id", None) if execution_context is not None else None)
    exec_id = execution_id
    if exec_id is None and execution_context is not None:
        exec_id = getattr(execution_context, "request_id", None)
    corr = correlation_id if correlation_id is not None else exec_id
    app = application_id
    if request is not None:
        app = app or request.application_id
        capability_id = capability_id or request.capability_id
        agent = agent if agent is not None else request.agent_id
        exec_id = exec_id if exec_id is not None else request.execution_id
        corr = corr if corr is not None else request.correlation_id
        binding_id = binding_id if binding_id is not None else request.binding_id
        binding = binding if binding is not None else request.binding
        permission = permission if permission is not None else request.requested_operation
    if app is None and request is not None:
        app = request.application_id
    if capability_id is None and request is not None:
        capability_id = request.capability_id
    return CapabilityAuthorizationDecision(
        decision=CapabilityAuthorizationDecisionValue.DENY,
        allowed=False,
        reason_code=reason_code,
        message=message,
        actor_id=actor,
        agent_id=agent,
        execution_id=exec_id,
        correlation_id=corr,
        application_id=app,
        instance_id=instance_id,
        capability_id=capability_id,
        binding_id=binding_id,
        binding=binding,
        permission=permission,
        evaluated_at=_now(),
    )


class CapabilityAuthorizationService:
    """Fail-closed HROT authorization service for agent capability invocations."""

    def __init__(
        self,
        registry: Any | None = None,
        permission_service: Any | None = None,
        audit: bool = True,
        rbac_engine: Any | None = None,
    ) -> None:
        self.registry = registry
        if permission_service is None:
            raise ValueError("permission_service is required")
        if not hasattr(permission_service, "authorize") or not callable(
            permission_service.authorize
        ):
            raise ValueError("permission_service must have an 'authorize' method")
        self.permission_service = permission_service
        self.audit = bool(audit)
        self.rbac_engine = rbac_engine
        self._decisions: list[CapabilityAuthorizationDecision] = []

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------
    def _contracts(self, registry: Any) -> list[Any]:
        try:
            from core.applications.capability_contract import get_application_capability_contracts

            return list(get_application_capability_contracts(registry))
        except Exception:
            return []

    def _binding_store(self, registry: Any) -> dict[Any, Any]:
        try:
            stores = getattr(registry, "_capability_execution_bindings", None)
            if isinstance(stores, dict):
                return stores
            if stores is None:
                return {}
            return dict(stores)
        except Exception:
            return {}

    def resolve_application(self, registry: Any, application_id: str) -> Any | None:
        if registry is None or not hasattr(registry, "get"):
            return None
        try:
            # Prefer exact application, then first matching app_id.
            app = registry.get(application_id)
            if app is not None:
                return app
            if hasattr(registry, "list"):
                for candidate in registry.list():
                    if getattr(candidate, "app_id", None) == application_id:
                        return candidate
        except Exception:
            return None
        return None

    def resolve_contract(self, registry: Any, application_id: str, capability_id: str) -> Any | None:
        for item in self._contracts(registry):
            if getattr(item, "application_id", None) == application_id and getattr(item, "capability_id", None) == capability_id:
                return item.contract if hasattr(item, "contract") else item
        return None

    def resolve_registration(self, registry: Any, application_id: str, capability_id: str) -> Any | None:
        for item in self._contracts(registry):
            if getattr(item, "application_id", None) == application_id and getattr(item, "capability_id", None) == capability_id:
                return item
        return None

    def resolve_binding(self, registry: Any, application_id: str, capability_id: str) -> Any | None:
        return self._binding_store(registry).get((application_id, capability_id))

    def _permission_service_for(self, request: CapabilityAuthorizationRequest) -> Any | None:
        if request.permission_service is not None:
            return request.permission_service
        return self.permission_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def authorize(self, request: CapabilityAuthorizationRequest | Mapping[str, Any], **kwargs: Any) -> CapabilityAuthorizationDecision:
        if not isinstance(request, CapabilityAuthorizationRequest):
            try:
                request = CapabilityAuthorizationRequest(**dict(request), **kwargs)
            except Exception:
                # Fall back to a best-effort construction from keyword arguments.
                request = CapabilityAuthorizationRequest(
                    execution_context=kwargs.get("execution_context"),
                    agent_id=kwargs.get("agent_id", ""),
                    application_id=kwargs.get("application_id", ""),
                    capability_id=kwargs.get("capability_id", ""),
                    execution_id=kwargs.get("execution_id"),
                    correlation_id=kwargs.get("correlation_id"),
                    requested_operation=kwargs.get("requested_operation"),
                    binding=kwargs.get("binding"),
                    binding_id=kwargs.get("binding_id"),
                    resource=kwargs.get("resource"),
                    action=kwargs.get("action"),
                    context=kwargs.get("context"),
                    registry=kwargs.get("registry") or self.registry,
                    permission_service=kwargs.get("permission_service"),
                )

        return self._evaluate(request)

    def _evaluate(self, request: CapabilityAuthorizationRequest) -> CapabilityAuthorizationDecision:
        try:
            registry = request.registry if request.registry is not None else self.registry

            # 1. Trusted execution context is mandatory.
            context = _coerce_execution_context(request.execution_context)
            if context is None:
                return self._record(_deny(
                    "MISSING_EXECUTION_CONTEXT",
                    "trusted execution context is missing or invalid",
                    request=request,
                ))

            # 1b. Principal identity must be cryptographically verified.
            principal = getattr(context, "principal", None)
            if principal is None:
                return self._record(_deny(
                    "MISSING_PRINCIPAL",
                    "trusted execution context has no principal",
                    request=request,
                    execution_context=context,
                ))
            if not verify_trusted_principal(principal):
                return self._record(_deny(
                    "UNTRUSTED_PRINCIPAL",
                    "principal signature verification failed",
                    request=request,
                    execution_context=context,
                    actor_id=_actor_id(context),
                ))

            # 2. Actor identity is mandatory.
            actor = _actor_id(context)
            if actor is None:
                return self._record(_deny(
                    "MISSING_ACTOR_IDENTITY",
                    "authenticated actor identity is missing",
                    request=request,
                    execution_context=context,
                ))

            # 3. Agent identity must match the executing agent.
            context_agent = getattr(context, "agent_id", None)
            if context_agent is None or str(context_agent).strip() == "":
                return self._record(_deny(
                    "MISSING_AGENT_IDENTITY",
                    "executing agent identity is missing from the trusted context",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                ))
            if str(context_agent).strip() != str(request.agent_id).strip():
                return self._record(_deny(
                    "AGENT_IDENTITY_MISMATCH",
                    "the trusted execution context does not match the executing agent",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                    agent_id=request.agent_id,
                ))

            # 4. Application must be registered.
            application = self.resolve_application(registry, request.application_id)
            if application is None:
                return self._record(_deny(
                    "UNKNOWN_APPLICATION",
                    "the target application is not registered",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                ))
            instance_id = getattr(application, "instance_id", None) or request.application_id

            # 5. Capability must be registered for that application.
            registration = self.resolve_registration(registry, request.application_id, request.capability_id)
            contract = self.resolve_contract(registry, request.application_id, request.capability_id)
            if registration is None or contract is None:
                return self._record(_deny(
                    "UNKNOWN_CAPABILITY",
                    "the target capability is not registered for this application",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                    instance_id=instance_id,
                ))

            # 6 / 7. Active registration and binding.
            if getattr(registration, "registration_state", "registered") != "registered" or getattr(registration, "approved", True) is False:
                return self._record(_deny(
                    "INACTIVE_CAPABILITY",
                    "the target capability is inactive or not approved",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                    instance_id=instance_id,
                ))

            resolved_binding = self.resolve_binding(registry, request.application_id, request.capability_id)
            if resolved_binding is None:
                return self._record(_deny(
                    "MISSING_BINDING",
                    "a capability execution binding is not registered",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                    instance_id=instance_id,
                ))

            # Do not trust caller-supplied binding/binding_id.
            if request.binding is not None and getattr(request.binding, "binding_id", None) not in (None, getattr(resolved_binding, "binding_id", None)):
                return self._record(_deny(
                    "BINDING_MISMATCH",
                    "the supplied binding does not match the canonical registry binding",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                    instance_id=instance_id,
                    binding_id=getattr(request.binding, "binding_id", None),
                ))
            if request.binding_id is not None and request.binding_id != getattr(resolved_binding, "binding_id", None):
                return self._record(_deny(
                    "BINDING_MISMATCH",
                    "the supplied binding identifier does not match the canonical registry binding",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                    instance_id=instance_id,
                    binding_id=request.binding_id,
                ))

            if getattr(resolved_binding, "activated", False) is not True:
                return self._record(_deny(
                    "INACTIVE_BINDING",
                    "the capability execution binding is not activated",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                    instance_id=instance_id,
                    binding_id=getattr(resolved_binding, "binding_id", None),
                    binding=resolved_binding,
                ))

            resolved_contract_version = getattr(contract, "contract_version", None)
            binding_contract_version = getattr(resolved_binding, "contract_version", None)
            if binding_contract_version is not None and resolved_contract_version is not None and binding_contract_version != resolved_contract_version:
                return self._record(_deny(
                    "BINDING_CONTRACT_VERSION_MISMATCH",
                    "the binding no longer matches the capability contract",
                    request=request,
                    execution_context=context,
                    actor_id=actor,
                    instance_id=instance_id,
                    binding_id=getattr(resolved_binding, "binding_id", None),
                    binding=resolved_binding,
                ))

            for attr, expected in (("application_id", request.application_id), ("capability_id", request.capability_id)):
                actual = getattr(resolved_binding, attr, None)
                if actual is not None and actual != expected:
                    return self._record(_deny(
                        "BINDING_SCOPE_MISMATCH",
                        "the binding does not target the requested application and capability",
                        request=request,
                        execution_context=context,
                        actor_id=actor,
                        instance_id=instance_id,
                        binding_id=getattr(resolved_binding, "binding_id", None),
                        binding=resolved_binding,
                    ))

            # 8. Required actor permissions (RBAC) from the trusted context.
            principal = getattr(context, "principal", None)
            required_permissions = getattr(contract, "required_permissions", ()) or ()
            for permission in required_permissions:
                has = False
                if principal is not None and hasattr(principal, "has_permission"):
                    has = bool(principal.has_permission(permission))
                if not has:
                    return self._record(_deny(
                        "MISSING_REQUIRED_PERMISSION",
                        "the authenticated actor lacks a required capability permission",
                        request=request,
                        execution_context=context,
                        actor_id=actor,
                        instance_id=instance_id,
                        binding_id=getattr(resolved_binding, "binding_id", None),
                        binding=resolved_binding,
                        permission=permission,
                    ))

            # 8/9. HROT application-level policy evaluation.
            permission_service = self._permission_service_for(request)
            operation = request.requested_operation or "execute"
            resource = request.resource if request.resource is not None else (request.action or "capability")
            action = request.action if request.action is not None else operation
            if permission_service is not None and hasattr(permission_service, "authorize"):
                try:
                    result = permission_service.authorize(
                        request.application_id,
                        instance_id,
                        request.capability_id,
                        resource,
                        action,
                        context=dict(request.context or {}),
                    )
                except Exception as exc:  # Fail closed.
                    logger.exception("HROT authorization evaluation failed: %s", exc)
                    return self._record(_deny(
                        "AUTHORIZATION_EVALUATION_ERROR",
                        "authorization evaluation failed",
                        request=request,
                        execution_context=context,
                        actor_id=actor,
                        instance_id=instance_id,
                        binding_id=getattr(resolved_binding, "binding_id", None),
                        binding=resolved_binding,
                        permission=operation,
                    ))
                allowed = bool(getattr(result, "allowed", False)) or getattr(result, "decision", None) in ("allow", "ALLOW", CapabilityAuthorizationDecisionValue.ALLOW)
                if not allowed:
                    reason = getattr(result, "reason_code", None) or "HROT_PERMISSION_DENIED"
                    return self._record(_deny(
                        reason,
                        getattr(result, "message", "HROT authorization denied"),
                        request=request,
                        execution_context=context,
                        actor_id=actor,
                        instance_id=instance_id,
                        binding_id=getattr(resolved_binding, "binding_id", None),
                        binding=resolved_binding,
                        permission=operation,
                    ))

            # 10. Allow.
            exec_id = request.execution_id
            if exec_id is None:
                exec_id = getattr(context, "request_id", None)
            corr = request.correlation_id if request.correlation_id is not None else exec_id
            decision = CapabilityAuthorizationDecision(
                decision=CapabilityAuthorizationDecisionValue.ALLOW,
                allowed=True,
                reason_code="ALLOWED",
                message="agent application-capability authorization granted",
                actor_id=actor,
                agent_id=request.agent_id,
                execution_id=exec_id,
                correlation_id=corr,
                application_id=request.application_id,
                instance_id=instance_id,
                capability_id=request.capability_id,
                binding_id=getattr(resolved_binding, "binding_id", None),
                binding=resolved_binding,
                permission=operation,
                evaluated_at=_now(),
                metadata={
                    "hrot_permission": "evaluated",
                },
            )
            return self._record(decision)
        except Exception as exc:  # Fail closed on any evaluation error.
            logger.exception("Agent capability authorization failed closed: %s", exc)
            return self._record(_deny(
                "AUTHORIZATION_EVALUATION_ERROR",
                "authorization evaluation failed",
                request=request,
                execution_context=request.execution_context,
                actor_id=_actor_id(request.execution_context) if request.execution_context is not None else None,
                agent_id=request.agent_id,
                application_id=request.application_id,
                capability_id=request.capability_id,
                execution_id=request.execution_id,
                correlation_id=request.correlation_id,
                binding_id=request.binding_id,
                binding=request.binding,
                permission=request.requested_operation,
            ),)

    def _record(self, decision: CapabilityAuthorizationDecision) -> CapabilityAuthorizationDecision:
        try:
            self._decisions.append(decision)
        except Exception as exc:
            logger.exception("Failed to record authorization decision: %s", exc)
        return decision

    def audit_trail(self) -> tuple[CapabilityAuthorizationDecision, ...]:
        return tuple(self._decisions)


# Convenience function (fail-closed).
def authorize_agent_capability(*args: Any, **kwargs: Any) -> CapabilityAuthorizationDecision:
    registry = kwargs.get("registry")
    service = CapabilityAuthorizationService(registry=registry, permission_service=kwargs.get("permission_service"))
    if args and not isinstance(args[0], CapabilityAuthorizationRequest) and "execution_context" not in kwargs:
        # Allow positional request.
        pass
    if args:
        first = args[0]
        if isinstance(first, CapabilityAuthorizationRequest):
            return service.authorize(first, **{k: v for k, v in kwargs.items() if k not in ("registry", "permission_service")})
    return service.authorize(CapabilityAuthorizationRequest(**{k: v for k, v in kwargs.items() if k not in ("registry", "permission_service")}), registry=registry)


# Compatibility aliases.
CapabilityAuthorizationService = CapabilityAuthorizationService
AgentCapabilityAuthorizationService = CapabilityAuthorizationService
ApplicationCapabilityAuthorizationService = CapabilityAuthorizationService
HrotCapabilityAuthorizationService = CapabilityAuthorizationService

CapabilityAuthorizationRequest = CapabilityAuthorizationRequest
AgentCapabilityAuthorizationRequest = CapabilityAuthorizationRequest
ApplicationCapabilityAuthorizationRequest = CapabilityAuthorizationRequest

CapabilityAuthorizationDecision = CapabilityAuthorizationDecision
AgentCapabilityAuthorizationDecision = CapabilityAuthorizationDecision
ApplicationCapabilityAuthorizationDecision = CapabilityAuthorizationDecision

# Enum compatibility under several historical names.
AuthorizationDecisionValue = CapabilityAuthorizationDecisionValue
HROTDicomAuthorizationDecisionValue = CapabilityAuthorizationDecisionValue
