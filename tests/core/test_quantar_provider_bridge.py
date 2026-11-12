import pathlib
import tempfile

from core.applications.quantar_provider_bridge import QuantarProviderBridge
from core.applications.quantar_service import QuantarTaskService
from core.hrot.durable import DurableHrotStore
from core.security.hrot_provider_gateway import (
    HrotDurableAuthorizationAuthority,
    ProviderGateway,
    ProviderMessage,
    SecretProvider,
)


def _store():
    return DurableHrotStore(root=pathlib.Path(tempfile.mkdtemp()), database_url=None)


def test_bridge_requires_durable_hrot_authorization():
    gateway = ProviderGateway()
    gateway.register_provider("fake", lambda request, secret: {"value": "provider-ok"}, "fake")
    secrets = SecretProvider()
    secrets.register_secret("fake", "secret", "human")
    gateway._secrets = secrets

    store = _store()
    authority = HrotDurableAuthorizationAuthority(store)
    from asyncio import run

    approval_id = authority.create_approval(
        requester="phase50-task",
        requester_type="service",
        service_id="quantar-provider",
        operation="provider:infer",
        parameters={
            "task_id": "phase50-task",
            "execution_id": "phase50-task",
            "application_id": "quantar",
            "provider_id": "fake",
            "model_id": "fake-model",
            "capability": "quantar-analysis",
            "resource": "task:phase50-task",
            "action": "provider:infer",
        },
        ttl_seconds=300,
    )
    authority.resolve_approval(approval_id, "human-approver", True)

    service = QuantarTaskService()
    task = service._get_task(service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "phase50-task"})["task_id"])
    bridge = QuantarProviderBridge(gateway, hrot_authority=authority)
    authorization = bridge.prepare_authorization(
        task,
        application_id="quantar",
        provider_id="fake",
        model_id="fake-model",
        capability="quantar-analysis",
        approver_id="human-approver",
        hrot_approval_id=approval_id,
    )
    result = bridge.execute(
        task,
        authorization=authorization,
        messages=(ProviderMessage(role="user", content="hello"),),
        parameters={},
        correlation_id="corr-phase50",
    )
    assert result.response.status == "success"
    assert "secret" not in str(result.response.to_safe_dict())


def test_bridge_refuses_unapproved_durable_authorization():
    gateway = ProviderGateway()
    gateway.register_provider("fake", lambda request, secret: {"value": "provider-ok"}, "fake")
    secrets = SecretProvider()
    secrets.register_secret("fake", "secret", "human")
    gateway._secrets = secrets
    store = _store()
    authority = HrotDurableAuthorizationAuthority(store)
    approval_id = authority.create_approval(
        requester="phase50-task-denied",
        requester_type="service",
        service_id="quantar-provider",
        operation="provider:infer",
        parameters={
            "task_id": "phase50-task-denied",
            "execution_id": "phase50-task-denied",
            "application_id": "quantar",
            "provider_id": "fake",
            "model_id": "fake-model",
            "capability": "quantar-analysis",
            "resource": "task:phase50-task-denied",
            "action": "provider:infer",
        },
        ttl_seconds=300,
    )
    service = QuantarTaskService()
    task = service._get_task(service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "phase50-task-denied"})["task_id"])
    bridge = QuantarProviderBridge(gateway, hrot_authority=authority)
    try:
        bridge.prepare_authorization(
            task,
            application_id="quantar",
            provider_id="fake",
            model_id="fake-model",
            capability="quantar-analysis",
            approver_id="human-approver",
            hrot_approval_id=approval_id,
        )
    except ValueError as exc:
        assert "denied" in str(exc)
    else:
        raise AssertionError("unapproved authorization should have been rejected")
