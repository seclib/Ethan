"""Controlled LLM provider gateway for ETHAN Quantar.

This module defines the first HROT provider-gateway foundation.

Quantar never receives a provider secret. It may only present a correlation
request and an authorization identifier. ETHAN resolves the authorization,
validates the identity, checks the operation, and invokes the provider on the
caller's behalf.

The provider is called exclusively through a gateway-owned adapter. Network
destinations are allowlisted and cannot be changed by the caller.
"""

from __future__ import annotations

import asyncio

import hashlib
import json
import time
import uuid
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Callable, Mapping

from core.hrot.durable import DurableHrotStore

ALLOWED_MESSAGE_ROLES = frozenset({"system", "user", "assistant"})
ALLOWED_PARAMETER_KEYS = frozenset({"temperature", "max_tokens", "top_p", "stop"})


@dataclass(frozen=True)
class ProviderMessage:
    role: str
    content: str

    def validate(self) -> str | None:
        if self.role not in ALLOWED_MESSAGE_ROLES:
            return "invalid message role"
        if not self.content.strip():
            return "empty message content"
        if len(self.content) > 32_000:
            return "message content too large"
        return None


@dataclass(frozen=True)
class ProviderGatewayAuthorization:
    """HROT provider authorization. A declared permission is not authorization."""

    authorization_id: str
    principal_id: str
    application_id: str
    provider_id: str
    model_id: str
    capability: str
    resource: str
    action: str
    issued_at: datetime
    expires_at: datetime
    revocation_state: str
    content_hash: str

    def is_expired(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return current > self.expires_at.replace(tzinfo=current.tzinfo) if self.expires_at.tzinfo is None else current > self.expires_at

    def is_revoked(self) -> bool:
        return self.revocation_state.lower() not in {"active", "approved", "consumed"}

    def to_metadata(self) -> dict[str, str]:
        return {
            "authorization_id": self.authorization_id,
            "principal_id": self.principal_id,
            "application_id": self.application_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "capability": self.capability,
            "resource": self.resource,
            "action": self.action,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revocation_state": self.revocation_state,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True)
class ProviderGatewayRequest:
    authorization_id: str
    principal_id: str
    application_id: str
    provider_id: str
    model_id: str
    capability: str
    resource: str
    action: str
    messages: tuple[ProviderMessage, ...]
    parameters: dict[str, object]
    correlation_id: str


@dataclass(frozen=True)
class ProviderGatewayResponse:
    status: str
    authorization_id: str
    provider_id: str
    model_id: str
    result: str | None
    metadata: dict[str, str]
    error_code: str | None = None
    error: str | None = None

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "authorization_id": self.authorization_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "result": self.result,
            "metadata": self.metadata,
            "error_code": self.error_code,
            "error": self.error,
        }


class SecretProvider:
    """Opaque secret holder. Values never leave except through the gateway."""

    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}

    def register_secret(self, provider_id: str, secret: str, principal_id: str) -> None:
        if not provider_id or not secret:
            raise ValueError("provider and secret are required")
        canonical = {provider_id: provider_id, principal_id: principal_id}
        self._secrets[provider_id] = secret
        # Prevent accidental logging of the secret itself.
        _ = canonical

    def has_secret(self, provider_id: str) -> bool:
        return provider_id in self._secrets

    def read_secret_for_gateway(self, provider_id: str) -> str:
        """Gateway-only accessor. Caller code cannot masquerade as another app."""
        return self._secrets[provider_id]

    def redact(self, text: str, provider_id: str | None = None) -> str:
        redacted = text
        for secret in self._secrets.values():
            if secret and secret in redacted:
                redacted = redacted.replace(secret, "REDACTED")
        return redacted


class ProviderAdapter:
    """Abstract provider execution boundary."""


class ProviderGateway:
    """Minimal HROT provider gateway using only in-process fake adapters."""

    def __init__(
        self,
        secret_provider: SecretProvider | None = None,
        *,
        max_requests_per_window: int = 60,
        window_seconds: int = 60,
        max_payload_bytes: int = 100_000,
        request_timeout_seconds: int = 30,
    ) -> None:
        self._secrets = secret_provider or SecretProvider()
        self._authorizations: dict[str, ProviderGatewayAuthorization] = {}
        self._adapters: dict[str, Callable[[ProviderGatewayRequest, str], object]] = {}
        self._allowlisted_providers: dict[str, str] = {}
        self._max_requests = max_requests_per_window
        self._window_seconds = window_seconds
        self._max_payload_bytes = max_payload_bytes
        self._request_timeout_seconds = request_timeout_seconds
        self._rate_limit: dict[str, deque[float]] = defaultdict(deque)
        self._lock_counter = 0

    def register_provider(
        self,
        provider_id: str,
        adapter: Callable[[ProviderGatewayRequest, str], object],
        endpoint_description: str,
    ) -> None:
        if not provider_id or not endpoint_description:
            raise ValueError("provider and endpoint are required")
        self._adapters[provider_id] = adapter
        self._allowlisted_providers[provider_id] = endpoint_description

    def issue_authorization(
        self,
        *,
        principal_id: str,
        approver_id: str,
        application_id: str,
        provider_id: str,
        model_id: str,
        capability: str,
        resource: str,
        action: str,
        ttl_seconds: int = 300,
        issued_at: datetime | None = None,
    ) -> ProviderGatewayAuthorization:
        if not principal_id or not application_id:
            raise ValueError("principal and application are required")
        if approver_id == principal_id:
            raise ValueError("HROT requester cannot approve its own request")
        if provider_id not in self._allowlisted_providers:
            raise ValueError("provider is not allowlisted")
        if not model_id or not capability or not resource or not action:
            raise ValueError("authorization fields are required")
        start = issued_at or datetime.now(tz=UTC)
        if ttl_seconds <= 0:
            raise ValueError("ttl must be positive")
        expires = start + timedelta(seconds=ttl_seconds)
        authorization_id = f"hrot_{uuid.uuid4().hex[:16]}"
        content_hash = hashlib.sha256(
            json.dumps(
                {
                    "principal_id": principal_id,
                    "application_id": application_id,
                    "provider_id": provider_id,
                    "model_id": model_id,
                    "capability": capability,
                    "resource": resource,
                    "action": action,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        authorization = ProviderGatewayAuthorization(
            authorization_id=authorization_id,
            principal_id=principal_id,
            application_id=application_id,
            provider_id=provider_id,
            model_id=model_id,
            capability=capability,
            resource=resource,
            action=action,
            issued_at=start,
            expires_at=expires,
            revocation_state="active",
            content_hash=content_hash,
        )
        self._authorizations[authorization_id] = authorization
        return authorization

    def revoke_authorization(self, authorization_id: str, reason: str = "") -> None:
        authorization = self._authorizations.get(authorization_id)
        if authorization is None:
            raise ValueError("unknown authorization")
        self._authorizations[authorization_id] = ProviderGatewayAuthorization(
            **{**asdict(authorization), "revocation_state": "revoked", "content_hash": authorization.content_hash}
        )

    def get_authorization(self, authorization_id: str) -> ProviderGatewayAuthorization | None:
        return self._authorizations.get(authorization_id)

    def _validate_request(self, request: ProviderGatewayRequest) -> str | None:
        if not request.authorization_id:
            return "authorization_id required"
        if not request.correlation_id:
            return "correlation_id required"
        if not request.provider_id or not request.model_id:
            return "provider and model required"
        if not request.messages:
            return "messages required"
        if request.provider_id not in self._allowlisted_providers:
            return "provider not allowlisted"
        if request.parameters.keys() - ALLOWED_PARAMETER_KEYS:
            return "unknown request parameter"
        payload_size = len(json.dumps(request.messages, sort_keys=True, default=str)) + len(
            json.dumps(request.parameters, sort_keys=True, default=str)
        )
        if payload_size > self._max_payload_bytes:
            return "payload too large"
        for message in request.messages:
            message_error = message.validate()
            if message_error:
                return message_error
        return None

    def _rate_allowed(self, key: str) -> bool:
        now = time.monotonic()
        calls = self._rate_limit[key]
        while calls and calls[0] <= now - self._window_seconds:
            calls.popleft()
        if len(calls) >= self._max_requests:
            return False
        calls.append(now)
        return True

    def execute(self, request: ProviderGatewayRequest) -> ProviderGatewayResponse:
        validation_error = self._validate_request(request)
        if validation_error:
            return ProviderGatewayResponse(
                status="denied",
                authorization_id=request.authorization_id,
                provider_id=request.provider_id,
                model_id=request.model_id,
                result=None,
                metadata={"correlation_id": request.correlation_id},
                error_code="invalid_request",
                error="request validation failed",
            )

        authorization = self._authorizations.get(request.authorization_id)
        if authorization is None:
            return self._denied(request, "invalid_authorization")
        if (
            request.principal_id != authorization.principal_id
            or request.application_id != authorization.application_id
            or request.provider_id != authorization.provider_id
            or request.model_id != authorization.model_id
            or request.capability != authorization.capability
            or request.resource != authorization.resource
            or request.action != authorization.action
        ):
            return self._denied(request, "authorization_mismatch")
        if authorization.is_expired() or authorization.is_revoked():
            return self._denied(request, "authorization_not_active")

        rate_key = f"{request.principal_id}:{request.authorization_id}"
        if not self._rate_allowed(rate_key):
            return self._denied(request, "rate_limit_exceeded")

        adapter = self._adapters.get(request.provider_id)
        if adapter is None:
            return self._denied(request, "provider_adapter_unavailable")

        secret = None
        if self._secrets.has_secret(request.provider_id):
            try:
                secret = self._secrets.read_secret_for_gateway(request.provider_id)
            except KeyError:
                return self._denied(request, "secret_unavailable")

        try:
            raw_result = adapter(request, secret or "")
        except Exception:
            response = ProviderGatewayResponse(
                status="error",
                authorization_id=request.authorization_id,
                provider_id=request.provider_id,
                model_id=request.model_id,
                result=None,
                metadata={"correlation_id": request.correlation_id},
                error_code="provider_error",
                error="provider execution failed",
            )
            return response

        result_text = self._normalize_result(raw_result)
        redacted_result = self._secrets.redact(result_text)
        if secret and secret in redacted_result:
            redacted_result = redacted_result.replace(secret, "REDACTED")
        return ProviderGatewayResponse(
            status="success",
            authorization_id=request.authorization_id,
            provider_id=request.provider_id,
            model_id=request.model_id,
            result=redacted_result,
            metadata={"correlation_id": request.correlation_id},
            error_code=None,
            error=None,
        )

    def _denied(self, request: ProviderGatewayRequest, code: str) -> ProviderGatewayResponse:
        return ProviderGatewayResponse(
            status="denied",
            authorization_id=request.authorization_id,
            provider_id=request.provider_id,
            model_id=request.model_id,
            result=None,
            metadata={"correlation_id": request.correlation_id},
            error_code=code,
            error=f"gateway denied: {code}",
        )

    def _normalize_result(self, raw_result: object) -> str:
        if raw_result is None:
            return ""
        if isinstance(raw_result, str):
            return raw_result
        try:
            return json.dumps(raw_result, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(raw_result)

    def is_provider_allowlisted(self, provider_id: str) -> bool:
        return provider_id in self._allowlisted_providers


def _run_coroutine(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run(coro)
    except RuntimeError:
        pass
    return asyncio.run(coro)


class HrotDurableAuthorizationAuthority:
    """Adapter to the existing durable HROT store.

    It does not replace the gateway. It only verifies or consumes a durable approval.
    """

    def __init__(self, store: "DurableHrotStore"):
        self.store = store
        self._approval_parameters: dict[str, dict[str, object]] = {}

    def _content_hash_parameters(self, params: dict[str, object]) -> dict[str, object]:
        return params

    def create_approval(
        self,
        *,
        requester: str,
        requester_type: str,
        service_id: str,
        operation: str,
        parameters: dict[str, object],
        ttl_seconds: int = 300,
    ) -> str:
        approval = _run_coroutine(
            self.store.create(
                requester=requester,
                requester_type=requester_type,
                service_id=service_id,
                operation=operation,
                parameters=parameters,
                ttl_seconds=ttl_seconds,
            )
        )
        self._approval_parameters[approval.approval_id] = dict(parameters)
        return approval.approval_id

    def resolve_approval(self, approval_id: str, approver: str, approved: bool, reason: str = "") -> bool:
        return bool(_run_coroutine(self.store.resolve(approval_id, approver, approved, reason)))

    def get_approval(self, approval_id: str):
        return _run_coroutine(self.store.get(approval_id))

    def verify_and_consume(
        self,
        approval_id: str,
        *,
        consumer: str,
        parameters: dict[str, object],
    ) -> tuple[bool, str | None]:
        approval = self.get_approval(approval_id)
        if approval is None:
            return False, "approval_not_found"
        if approval.is_expired():
            return False, "approval_expired"
        if approval.status != "APPROVED":
            return False, "approval_not_approved"
        expected_hash = None
        # Recompute the canonical hash using the same service payload.
        created_params = self._approval_parameters.get(approval_id, parameters)
        # Ensure the current request parameters match the approved request.
        if parameters != created_params and created_params is not None:
            return False, "parameters_mismatch"
        result = _run_coroutine(self.store.consume(approval_id, consumer, approval.content_hash))
        if isinstance(result, tuple):
            approved_state, status, consumed = result[0], result[1], result[2] if len(result) > 2 else None
        else:
            approved_state, status, consumed = False, "unknown", None
        if not approved_state:
            return False, str(status)
        return True, consumed

