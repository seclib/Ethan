from datetime import UTC, datetime, timedelta

from core.security.hrot_provider_gateway import (
    ProviderGateway,
    ProviderGatewayRequest,
    ProviderMessage,
    SecretProvider,
)


def make_gateway() -> ProviderGateway:
    gateway = ProviderGateway()
    gateway.register_provider("fake-provider", lambda request, secret: {"value": "ok", "secret_echo": secret}, "controlled fake")
    secret_provider = SecretProvider()
    secret_provider.register_secret("fake-provider", "super-secret-token", "human-principal")
    gateway._secrets = secret_provider
    return gateway


def make_authorization(gateway: ProviderGateway) -> str:
    issued = gateway.issue_authorization(
        principal_id="user-principal",
        approver_id="human-approver",
        application_id="quantar",
        provider_id="fake-provider",
        model_id="fake-model",
        capability="quantar-analysis",
        resource="llm:quantar",
        action="infer",
        ttl_seconds=300,
    )
    return issued.authorization_id


def make_request(auth_id: str) -> ProviderGatewayRequest:
    return ProviderGatewayRequest(
        authorization_id=auth_id,
        principal_id="user-principal",
        application_id="quantar",
        provider_id="fake-provider",
        model_id="fake-model",
        capability="quantar-analysis",
        resource="llm:quantar",
        action="infer",
        messages=(ProviderMessage(role="user", content="hello"),),
        parameters={},
        correlation_id="corr-1",
    )


def test_authorized_request_succeeds():
    gateway = make_gateway()
    auth_id = make_authorization(gateway)
    response = gateway.execute(make_request(auth_id))
    assert response.status == "success"
    assert response.result == '{"value": "ok", "secret_echo": "super-secret-token"}' or "REDACTED" in str(response.result)


def test_unauthorized_request_missing_auth_is_denied():
    gateway = make_gateway()
    request = make_request("missing")
    response = gateway.execute(request)
    assert response.status == "denied"
    assert response.error_code == "invalid_authorization"


def test_wrong_principal_is_denied():
    gateway = make_gateway()
    auth_id = make_authorization(gateway)
    request = make_request(auth_id)
    request = ProviderGatewayRequest(**{**request.__dict__, "principal_id": "other"})
    response = gateway.execute(request)
    assert response.status == "denied"
    assert response.error_code == "authorization_mismatch"


def test_expired_authorization_is_denied():
    gateway = make_gateway()
    authorization = gateway.issue_authorization(
        principal_id="user-principal",
        approver_id="human-approver",
        application_id="quantar",
        provider_id="fake-provider",
        model_id="fake-model",
        capability="quantar-analysis",
        resource="llm:quantar",
        action="infer",
        ttl_seconds=1,
        issued_at=datetime.now(UTC) - timedelta(seconds=10),
    )
    response = gateway.execute(make_request(authorization.authorization_id))
    assert response.status == "denied"
    assert response.error_code == "authorization_not_active"


def test_revoked_authorization_is_denied():
    gateway = make_gateway()
    auth_id = make_authorization(gateway)
    gateway.revoke_authorization(auth_id, "test")
    response = gateway.execute(make_request(auth_id))
    assert response.status == "denied"
    assert response.error_code == "authorization_not_active"


def test_wrong_provider_is_denied():
    gateway = make_gateway()
    auth_id = make_authorization(gateway)
    request = ProviderGatewayRequest(**{**make_request(auth_id).__dict__, "provider_id": "other"})
    response = gateway.execute(request)
    assert response.status == "denied"
    assert response.error_code == "invalid_request"


def test_wrong_model_is_denied():
    gateway = make_gateway()
    auth_id = make_authorization(gateway)
    request = ProviderGatewayRequest(**{**make_request(auth_id).__dict__, "model_id": "other"})
    response = gateway.execute(request)
    assert response.status == "denied"
    assert response.error_code == "authorization_mismatch"


def test_malformed_request_is_denied():
    gateway = make_gateway()
    gateway.register_provider("fake-provider", lambda request, secret: "ok", "controlled fake")
    auth_id = make_authorization(gateway)
    request = ProviderGatewayRequest(**{**make_request(auth_id).__dict__, "messages": ()})
    response = gateway.execute(request)
    assert response.status == "denied"
    assert response.error_code == "invalid_request"


def test_unknown_parameter_is_denied():
    gateway = make_gateway()
    auth_id = make_authorization(gateway)
    request = ProviderGatewayRequest(**{**make_request(auth_id).__dict__, "parameters": {"foo": 1}})
    response = gateway.execute(request)
    assert response.status == "denied"
    assert response.error_code == "invalid_request"


def test_rate_limit_is_applied():
    gateway = ProviderGateway(max_requests_per_window=1, window_seconds=60)
    gateway.register_provider("fake-provider", lambda request, secret: "ok", "controlled fake")
    secret_provider = SecretProvider()
    secret_provider.register_secret("fake-provider", "s3cret", "human-principal")
    gateway._secrets = secret_provider
    auth_id = make_authorization(gateway)
    first = gateway.execute(make_request(auth_id))
    second = gateway.execute(make_request(auth_id))
    assert first.status == "success"
    assert second.status == "denied"
    assert second.error_code == "rate_limit_exceeded"


def test_provider_adapter_exception_returns_generic_error():
    def broken(request, secret):
        raise RuntimeError("secret-value-leaked")
    gateway = make_gateway()
    gateway.register_provider("fake-provider", broken, "controlled fake")
    auth_id = make_authorization(gateway)
    response = gateway.execute(make_request(auth_id))
    assert response.status == "error"
    assert response.error == "provider execution failed"


def test_payload_too_large_is_denied():
    gateway = make_gateway()
    auth_id = make_authorization(gateway)
    large_content = "x" * 40_000
    request = make_request(auth_id)
    request = ProviderGatewayRequest(**{**request.__dict__, "messages": (ProviderMessage(role="user", content=large_content),)})
    response = gateway.execute(request)
    assert response.status == "denied"
    assert response.error_code == "invalid_request"


def test_secret_is_redacted_from_string_result():
    def adapter(request, secret):
        return f"result includes {secret}"
    gateway = make_gateway()
    gateway.register_provider("fake-provider", adapter, "controlled fake")
    auth_id = make_authorization(gateway)
    response = gateway.execute(make_request(auth_id))
    assert response.status == "success"
    assert "super-secret-token" not in str(response.result)
    assert "REDACTED" in str(response.result)


def test_no_real_provider_is_needed():
    gateway = make_gateway()
    assert gateway.is_provider_allowlisted("fake-provider")
    assert not gateway.is_provider_allowlisted("arbitrary")
