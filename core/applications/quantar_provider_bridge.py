from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.applications.quantar_service import QuantarTask
from core.security.hrot_provider_gateway import (
    HrotDurableAuthorizationAuthority,
    ProviderGateway,
    ProviderGatewayAuthorization,
    ProviderGatewayRequest,
    ProviderGatewayResponse,
    ProviderMessage,
)


@dataclass(frozen=True)
class QuantarProviderBridgeResult:
    task_id: str
    execution_id: str | None
    authorization_id: str
    response: ProviderGatewayResponse


class QuantarProviderBridge:
    def __init__(self, gateway: ProviderGateway, hrot_authority: HrotDurableAuthorizationAuthority | None = None):
        self._gateway = gateway
        self._hrot_authority = hrot_authority

    @property
    def gateway(self) -> ProviderGateway:
        return self._gateway

    @property
    def hrot_authority(self) -> HrotDurableAuthorizationAuthority | None:
        return self._hrot_authority

    def prepare_authorization(
        self,
        task: QuantarTask,
        *,
        application_id: str,
        provider_id: str,
        model_id: str,
        capability: str,
        approver_id: str,
        hrot_approval_id: str | None = None,
        ttl_seconds: int = 300,
    ) -> ProviderGatewayAuthorization:
        if task.execution_id is None:
            raise ValueError("execution identifier is required")
        if self._hrot_authority is not None:
            if not hrot_approval_id:
                raise ValueError("HROT durable approval is required")
            parameters = {
                "task_id": task.task_id,
                "execution_id": task.execution_id,
                "application_id": application_id,
                "provider_id": provider_id,
                "model_id": model_id,
                "capability": capability,
                "resource": f"task:{task.task_id}",
                "action": "provider:infer",
            }
            approved, consumed = self._hrot_authority.verify_and_consume(
                hrot_approval_id,
                consumer=f"quantar:{task.task_id}",
                parameters=parameters,
            )
            if not approved:
                raise ValueError(f"HROT authorization denied: {consumed}")
        authorization = self._gateway.issue_authorization(
            principal_id=task.task_id,
            approver_id=approver_id,
            application_id=application_id,
            provider_id=provider_id,
            model_id=model_id,
            capability=capability,
            resource=f"task:{task.task_id}",
            action="provider:infer",
            ttl_seconds=ttl_seconds,
        )
        return authorization

    def execute(
        self,
        task: QuantarTask,
        *,
        authorization: ProviderGatewayAuthorization,
        messages: tuple[ProviderMessage, ...],
        parameters: Mapping[str, object],
        correlation_id: str,
    ) -> QuantarProviderBridgeResult:
        if authorization.principal_id != task.task_id:
            raise ValueError("authorization does not belong to task")
        if task.execution_id is None:
            raise ValueError("task execution identifier is required")
        request = ProviderGatewayRequest(
            authorization_id=authorization.authorization_id,
            principal_id=task.task_id,
            application_id=authorization.application_id,
            provider_id=authorization.provider_id,
            model_id=authorization.model_id,
            capability=authorization.capability,
            resource=authorization.resource,
            action=authorization.action,
            messages=messages,
            parameters=dict(parameters),
            correlation_id=correlation_id,
        )
        response = self._gateway.execute(request)
        return QuantarProviderBridgeResult(
            task_id=task.task_id,
            execution_id=task.execution_id,
            authorization_id=authorization.authorization_id,
            response=response,
        )
