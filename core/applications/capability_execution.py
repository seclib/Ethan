"""Trusted capability execution bridge for registered applications (Campaign 02-F1).

The bridge owns the association between an already validated application capability
contract and one explicitly allowlisted implementation.  The contract describes what
is expected; the allowlist decides what ETHAN can actually run.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Mapping

from core.applications.capability_contract import (
    ApplicationCapabilityContract,
    ApplicationCapabilityRegistration,
    get_application_capability_contracts,
)
from core.auth import ExecutionContext
from core.hrot.capability_authorization import (
    CapabilityAuthorizationRequest,
    CapabilityAuthorizationService,
)

logger = logging.getLogger(__name__)

TRUSTED_IMPLEMENTATION_ALIASES = {
    "odin.runtime-status",
    "frame.runtime-status",
}


async def _odin_runtime_status(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.plugins.odin import get_odin_service

    status = await get_odin_service().get_status()
    return {
        "application": status.get("id", "odin"),
        "state": status.get("status"),
        "healthy": bool(status.get("healthy")),
        "url": status.get("url"),
        "echo": payload.get("hello"),
    }


async def _frame_runtime_status(payload: Mapping[str, Any]) -> dict[str, Any]:
    from core.plugins.frame import get_frame_service

    status = await get_frame_service().get_status()
    return {
        "application": status.get("id", "frame"),
        "state": status.get("status"),
        "healthy": bool(status.get("healthy")),
        "url": status.get("url"),
        "echo": payload.get("hello"),
    }


_TRUSTED_IMPLEMENTATIONS: dict[str, Callable[[Mapping[str, Any]], Awaitable[Any]]] = {
    "odin.runtime-status": _odin_runtime_status,
    "frame.runtime-status": _frame_runtime_status,
}


@dataclass(frozen=True, slots=True)
class CapabilityExecutionBinding:
    binding_id: str
    application_id: str
    capability_id: str
    contract_version: str
    implementation_alias: str
    activated: bool
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CapabilityExecutionResult:
    invocation_id: str
    application_id: str
    capability_id: str
    status: str
    result: Any | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def bind_capability_implementation(
    registry,
    application_id: str,
    capability_id: str,
    implementation_alias: str,
    *,
    approved: bool = False,
) -> CapabilityExecutionBinding:
    """Create and validate an explicit implementation binding."""
    if implementation_alias not in _TRUSTED_IMPLEMENTATIONS:
        raise ValueError(f"Implementation alias is not allowlisted: {implementation_alias}")

    registrations = get_application_capability_contracts(registry)
    contract = None
    for item in registrations:
        if item.application_id == application_id and item.capability_id == capability_id:
            contract = item.contract
            break
    if contract is None:
        raise ValueError("capability contract is not registered")
    if not approved:
        raise ValueError("capability binding requires explicit approval")

    stores = getattr(registry, "_capability_execution_bindings", None)
    if stores is None:
        stores = registry._capability_execution_bindings = {}  # type: ignore[attr-defined]
    key = (application_id, capability_id)
    if key in stores:
        return stores[key]

    binding = CapabilityExecutionBinding(
        binding_id=str(uuid.uuid4()),
        application_id=application_id,
        capability_id=capability_id,
        contract_version=contract.contract_version,
        implementation_alias=implementation_alias,
        activated=False,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    stores[key] = binding
    return binding


def activate_capability_binding(registry, application_id: str, capability_id: str, activated: bool) -> CapabilityExecutionBinding:
    stores = getattr(registry, "_capability_execution_bindings", None) or {}
    binding = stores.get((application_id, capability_id))
    if binding is None:
        raise ValueError("capability binding is not registered")
    binding = CapabilityExecutionBinding(**{**binding.to_dict(), "activated": activated})
    stores[(application_id, capability_id)] = binding
    return binding


def _contracts_by_key(registry) -> dict[tuple[str, str], Any]:
    return {(item.application_id, item.capability_id): item.contract for item in get_application_capability_contracts(registry)}


async def invoke_capability(
    registry,
    application_id: str,
    capability_id: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout_override: int | None = None,
    execution_context: Any | None = None,
) -> CapabilityExecutionResult:
    """Invoke a validated capability through an allowlisted implementation.

    HROT authorization is evaluated *before* any implementation runs.
    The decision is fail-closed: missing, incomplete, or failing authorization
    results in a denied execution — never an implicit allow.
    """
    invocation_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    payload = dict(payload or {})
    contracts = _contracts_by_key(registry)
    contract = contracts.get((application_id, capability_id))
    if contract is None:
        return CapabilityExecutionResult(invocation_id, application_id, capability_id, "failed", error="capability contract is not registered", started_at=started_at, finished_at=datetime.now(timezone.utc).isoformat())

    stores = getattr(registry, "_capability_execution_bindings", None) or {}
    binding = stores.get((application_id, capability_id))
    if binding is None:
        return CapabilityExecutionResult(invocation_id, application_id, capability_id, "failed", error="capability binding is not registered", started_at=started_at, finished_at=datetime.now(timezone.utc).isoformat())
    if not binding.activated:
        return CapabilityExecutionResult(invocation_id, application_id, capability_id, "failed", error="capability is not activated", started_at=started_at, finished_at=datetime.now(timezone.utc).isoformat())
    if binding.contract_version != contract.contract_version:
        return CapabilityExecutionResult(invocation_id, application_id, capability_id, "failed", error="capability contract version mismatch", started_at=started_at, finished_at=datetime.now(timezone.utc).isoformat())

    # ── HROT authorization (fail-closed) ──────────────────────────────
    _hrot_decision = None
    try:
        # Share the registry's permission service so that grants created
        # through the HROT approval process are visible to authorization.
        perm_svc = getattr(registry, "permission_service", None)
        authz = CapabilityAuthorizationService(
            registry=registry,
            permission_service=perm_svc,
        )
        agent_id = ""
        if execution_context is not None:
            agent_id = getattr(execution_context, "agent_id", None) or ""
        hrot_request = CapabilityAuthorizationRequest(
            execution_context=execution_context,
            agent_id=agent_id,
            application_id=application_id,
            capability_id=capability_id,
            execution_id=invocation_id,
            requested_operation="execute",
            resource="capability",
            action="execute",
            binding=binding,
            binding_id=getattr(binding, "binding_id", None),
            registry=registry,
            permission_service=perm_svc,
        )
        _hrot_decision = authz.authorize(hrot_request)
    except Exception:  # Fail closed — never open on authorization error.
        logger.exception("HROT authorization evaluation failed closed")
        return CapabilityExecutionResult(
            invocation_id,
            application_id,
            capability_id,
            "failed",
            error="HROT authorization evaluation failed",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    if _hrot_decision is not None and not _hrot_decision.allowed:
        return CapabilityExecutionResult(
            invocation_id,
            application_id,
            capability_id,
            "failed",
            error=(
                f"HROT authorization denied: {_hrot_decision.reason_code}"
                f" — {_hrot_decision.message}"
            ),
            started_at=started_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    # ──────────────────────────────────────────────────────────────────

    from jsonschema import Draft202012Validator

    try:
        Draft202012Validator(contract.input_schema).validate(payload)
    except Exception as exc:
        return CapabilityExecutionResult(invocation_id, application_id, capability_id, "failed", error=f"invalid input: {exc}", started_at=started_at, finished_at=datetime.now(timezone.utc).isoformat())

    impl = _TRUSTED_IMPLEMENTATIONS.get(binding.implementation_alias)
    if impl is None:
        return CapabilityExecutionResult(invocation_id, application_id, capability_id, "failed", error="allowlisted implementation is unavailable", started_at=started_at, finished_at=datetime.now(timezone.utc).isoformat())

    timeout = timeout_override or contract.timeout_seconds
    try:
        raw_result = await asyncio.wait_for(impl(payload), timeout=timeout)
        Draft202012Validator(contract.output_schema).validate(raw_result)
        result = raw_result
        status = "success"
        error = None
    except asyncio.TimeoutError:
        result = None
        status = "failed"
        error = "capability execution timed out"
    except Exception as exc:
        result = None
        status = "failed"
        error = f"capability execution failed: {exc}"
    finished_at = datetime.now(timezone.utc).isoformat()
    return CapabilityExecutionResult(invocation_id=invocation_id, application_id=application_id, capability_id=capability_id, status=status, result=result, error=error, started_at=started_at, finished_at=finished_at)
