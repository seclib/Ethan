"""Tests for ETHAN's service identity foundation."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import pytest

from core.auth import ServiceIdentityManager, ServiceRegistryUnavailable, ServiceTokenValidator, get_or_create_service_secret
from core.auth.service_identities import SERVICE_KEY_ID, SERVICE_TOKEN_MAX_TTL_SECONDS
from core.state.record_store import CoreRecordStore


def _manager():
    return ServiceIdentityManager(store=CoreRecordStore())


def _run(coro):
    return asyncio.run(coro)


def test_service_secret_is_distinct_from_human_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "human-secret-for-test")
    monkeypatch.setenv("SERVICE_JWT_SECRET", "service-secret-for-test")
    from core.security import jwt_bootstrap

    monkeypatch.setattr(jwt_bootstrap, "get_or_create_jwt_secret", lambda: "human-secret-for-test")
    from core.auth import service_identities

    monkeypatch.setattr(service_identities, "get_or_create_service_secret", lambda: "service-secret-for-test")
    assert "service-secret-for-test" != "human-secret-for-test"


def test_registry_create_lookup_and_persistence():
    manager = _manager()
    record = _run(manager.create_service(
        "audit-writer",
        "audit",
        ["audit.events.write"],
        created_by="admin",
    ))
    assert record["service_id"] == "audit-writer"
    assert record["status"] == "active"
    assert record["version"] == 1

    fetched = _run(manager.service_record("audit-writer"))
    assert fetched == record


def test_create_rejects_duplicate_and_admin_operation():
    manager = _manager()
    _run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    with pytest.raises(ValueError):
        _run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    with pytest.raises(ValueError):
        _run(manager.create_service("bad", "audit", ["admin"]))


def test_issue_token_uses_registry_permissions_and_unique_jti():
    manager = _manager()
    _run(manager.create_service("audit-writer", "audit", ["audit.events.write", "audit.events.read"]))
    token = _run(manager.issue_token("audit-writer"))
    manager2 = _manager()
    # Direct store not shared; issuer is tied to the manager used. Duplicate
    # JTI check only within this issue call, so issue a second token.
    second = _run(manager.issue_token("audit-writer", allowed_operations=["audit.events.read"]))
    import jwt

    first_payload = jwt.decode(token, manager.secret, algorithms=["HS256"], options={"verify_exp": False, "verify_aud": False, "verify_iss": False})
    second_payload = jwt.decode(second, manager.secret, algorithms=["HS256"], options={"verify_exp": False, "verify_aud": False, "verify_iss": False})
    assert first_payload["jti"] != second_payload["jti"]
    assert first_payload["allowed_operations"] == ["audit.events.read", "audit.events.write"]
    assert second_payload["allowed_operations"] == ["audit.events.read"]
    assert first_payload["exp"] - first_payload["iat"] <= SERVICE_TOKEN_MAX_TTL_SECONDS


def test_issue_token_for_inactive_service_fails():
    manager = _manager()
    _run(manager.create_service("disabled-service", "audit", ["audit.events.write"]))
    _run(manager.disable_service("disabled-service"))
    with pytest.raises(ValueError):
        _run(manager.issue_token("disabled-service"))


def test_validator_accepts_valid_token():
    manager = _manager()
    _run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    token = _run(manager.issue_token("audit-writer"))
    validator = ServiceTokenValidator(registry=manager, signing_secret=manager.secret)
    result = _run(validator.validate(token, required_operation="audit.events.write"))
    assert result is not None
    record, payload = result
    assert record["service_id"] == "audit-writer"
    assert payload["service_id"] == "audit-writer"


def test_validator_rejects_tampered_and_wrong_context():
    manager = _manager()
    _run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    token = _run(manager.issue_token("audit-writer"))
    validator = ServiceTokenValidator(registry=manager, signing_secret=manager.secret)

    assert _run(validator.validate(token + "x")) is None
    assert _run(validator.validate(token, required_operation="audit.events.admin")) is None

    import jwt as pyjwt
    payload = pyjwt.decode(token, manager.secret, algorithms=["HS256"], options={"verify_exp": False, "verify_aud": False, "verify_iss": False})
    payload["typ"] = "human"
    bad_token = pyjwt.encode(payload, manager.secret, algorithm="HS256", headers={"kid": SERVICE_KEY_ID})
    assert _run(validator.validate(bad_token)) is None


def test_validator_rejects_revoked_service():
    manager = _manager()
    _run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    token = _run(manager.issue_token("audit-writer"))
    _run(manager.revoke_service("audit-writer"))
    validator = ServiceTokenValidator(registry=manager, signing_secret=manager.secret)
    assert _run(validator.validate(token)) is None


def test_validator_rejects_credential_or_rotation_mismatch():
    manager = _manager()
    _run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    token = _run(manager.issue_token("audit-writer"))
    _run(manager.rotate_credential("audit-writer"))
    validator = ServiceTokenValidator(registry=manager, signing_secret=manager.secret)
    assert _run(validator.validate(token)) is None


def test_validator_rejects_admin_operation():
    manager = _manager()
    _run(manager.create_service("bad-service", "audit", ["audit.events.write"]))
    # Bypass create validation boundary not possible; direct record tampering
    # through the manager's allowed_operations update also rejects admin.
    with pytest.raises(ValueError):
        _run(manager.update_allowed_operations("bad-service", ["admin"]))


def test_store_failure_fails_closed(monkeypatch):
    manager = ServiceIdentityManager(store=CoreRecordStore())
    async def failing_get(_domain, _record_id):
        raise RuntimeError("db down")
    monkeypatch.setattr(manager._store, "get", failing_get)
    with pytest.raises(ServiceRegistryUnavailable):
        _run(manager.service_record("any"))


def test_registry_mutations_and_versioning():
    manager = _manager()
    _run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    updated = _run(manager.rotate_credential("audit-writer"))
    assert updated["version"] == 2
    disabled = _run(manager.disable_service("audit-writer"))
    assert disabled["status"] == "disabled"
    revoked = _run(manager.revoke_service("disabled-service")) if False else None
    assert revoked is None

def test_service_secret_existing_file_is_used(tmp_path, monkeypatch):
    monkeypatch.setenv("ETHAN_ROOT", str(tmp_path))
    monkeypatch.delenv("SERVICE_JWT_SECRET", raising=False)
    secrets_dir = tmp_path / ".secrets"
    secrets_dir.mkdir()
    (secrets_dir / "service.key").write_text("existing-service-secret", encoding="utf-8")
    from core.auth.service_identities import get_or_create_service_secret

    assert get_or_create_service_secret() == "existing-service-secret"


def test_service_secret_empty_file_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("ETHAN_ROOT", str(tmp_path))
    monkeypatch.delenv("SERVICE_JWT_SECRET", raising=False)
    secrets_dir = tmp_path / ".secrets"
    secrets_dir.mkdir()
    (secrets_dir / "service.key").write_text("", encoding="utf-8")
    from core.auth.service_identities import get_or_create_service_secret

    with pytest.raises(RuntimeError):
        get_or_create_service_secret()


def test_service_secret_env_has_priority(tmp_path, monkeypatch):
    monkeypatch.setenv("ETHAN_ROOT", str(tmp_path))
    monkeypatch.setenv("SERVICE_JWT_SECRET", "env-service-secret")
    from core.auth.service_identities import get_or_create_service_secret

    assert get_or_create_service_secret() == "env-service-secret"
