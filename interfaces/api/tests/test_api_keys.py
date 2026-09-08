"""Tests réels API Keys — /v1/api-keys (create / list / revoke / validate).

Utilise le VRAI APIKeyManager du Core (core/auth/api_keys.py) sur un
CoreRecordStore en mémoire et le VRAI AuditStore (JSONL isolé via tmp_path).
Les fonctions de route sont appelées directement (pattern test_analytics.py).
Aucun mock de la logique métier.

Règle centrale testée : le plaintext n'apparaît que dans la réponse de
création — jamais stocké, jamais renvoyé, jamais journalisé.
"""

import hashlib

import pytest
from fastapi import HTTPException

from core.auth.api_keys import APIKeyManager
from core.audit.store import AuditStore
from core.state.record_store import CoreRecordStore
from routers.api_keys import (
    CreateKeyRequest,
    configure_api_keys,
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from core.audit.types import AuditCategory, AuditDecision


@pytest.fixture()
def api_keys_env(tmp_path):
    """Vrai manager + vrai AuditStore (JSONL temporaire) + injection router."""
    store = CoreRecordStore()
    manager = APIKeyManager(store=store)
    audit = AuditStore(jsonl_path=str(tmp_path / "audit.jsonl"))
    configure_api_keys(manager, audit_store=audit)
    return manager, audit


@pytest.mark.asyncio
async def test_create_returns_plaintext_once(api_keys_env):
    manager, _ = api_keys_env
    result = await manager.create_key(user_id="admin", name="ci", scopes=["read"])

    assert result["key"].startswith("ethan_") and len(result["key"]) > 40
    # Le store ne contient JAMAIS le plaintext.
    stored = await manager.list_keys()
    assert len(stored) == 1
    assert "key" not in stored[0]
    assert stored[0]["key_hash"] == hashlib.sha256(result["key"].encode()).hexdigest()
    assert result["key"] not in str(stored[0])


@pytest.mark.asyncio
async def test_create_route_response_has_no_hash(api_keys_env):
    manager, _ = api_keys_env
    resp = await create_api_key(CreateKeyRequest(name="k1"), user="admin")

    assert resp["key"].startswith("ethan_")
    assert "key_hash" not in resp and "secret" not in resp
    # Le hash réellement stocké correspond au plaintext retourné (une fois).
    stored = (await manager.list_keys())[0]
    assert stored["key_hash"] == hashlib.sha256(resp["key"].encode()).hexdigest()


@pytest.mark.asyncio
async def test_create_requires_authenticated_user(api_keys_env):
    with pytest.raises(HTTPException) as e:
        await create_api_key(CreateKeyRequest(name="x"), user="")
    assert e.value.status_code == 422


@pytest.mark.asyncio
async def test_list_route_strips_secrets(api_keys_env):
    await create_api_key(CreateKeyRequest(name="a", scopes=["read"]), user="admin")
    await create_api_key(CreateKeyRequest(name="b"), user="admin")

    keys = await list_api_keys()
    assert len(keys) == 2
    for k in keys:
        assert "key" not in k and "key_hash" not in k and "secret" not in k
        assert k["active"] is True and k["name"] in ("a", "b")


@pytest.mark.asyncio
async def test_validate_ok_then_revoked(api_keys_env):
    manager, _ = api_keys_env
    created = await create_api_key(
        CreateKeyRequest(name="svc", scopes=["read", "write"]), user="admin",
    )

    validated = await manager.validate_key(created["key"])
    assert validated is not None and validated["id"] == created["id"]

    await revoke_api_key(created["id"], user="admin")
    assert await manager.validate_key(created["key"]) is None
    assert await manager.validate_key("ethan_totally_wrong") is None


@pytest.mark.asyncio
async def test_revoke_route_returns_public_view(api_keys_env):
    created = await create_api_key(CreateKeyRequest(name="k"), user="admin")

    view = await revoke_api_key(created["id"], user="admin")
    assert "key_hash" not in view and "key" not in view
    assert view["active"] is False and view["revoked_at"] is not None


@pytest.mark.asyncio
async def test_revoke_unknown_key_404(api_keys_env):
    with pytest.raises(HTTPException) as e:
        await revoke_api_key("does-not-exist", user="admin")
    assert e.value.status_code == 404


@pytest.mark.asyncio
async def test_expiration_is_enforced_by_core(api_keys_env):
    """L'expiration existe réellement (core/auth/api_keys.py _is_expired +
    validate_key) et est refusée dès expiration — jamais simulée côté API."""
    manager, _ = api_keys_env
    # Création AVEC expiration déjà passée (ISO-8601).
    created = await manager.create_key(
        user_id="admin", name="expiring", expires_at="2000-01-01T00:00:00+00:00",
    )
    # La validation échoue : le Core a rejeté l'expiration passée.
    assert await manager.validate_key(created["key"]) is None
    # Le hash est bien celui du plaintext (stocké une seule fois).
    stored = (await manager.list_keys())[0]
    assert stored["expires_at"] == "2000-01-01T00:00:00+00:00"
    assert stored["key_hash"] == hashlib.sha256(created["key"].encode()).hexdigest()


@pytest.mark.asyncio
async def test_rotation_preserves_expiration(api_keys_env):
    """La rotation recrée avec les MÊMES métadonnées (incl. expiration)."""
    manager, _ = api_keys_env
    created = await manager.create_key(
        user_id="admin", name="rotate-test", scopes=["read"],
        expires_at="2099-12-31T00:00:00+00:00",
    )
    rotated = await manager.rotate_key(created["id"])
    assert rotated is not None and rotated["id"] != created["id"]
    assert rotated["expires_at"] == "2099-12-31T00:00:00+00:00"
    assert rotated["scopes"] == ["read"]





@pytest.mark.asyncio
async def test_sensitive_actions_are_audited_without_secret(api_keys_env):
    manager, audit = api_keys_env
    created = await create_api_key(
        CreateKeyRequest(name="audited", scopes=["read"]), user="admin",
    )
    await revoke_api_key(created["id"], user="admin")

    entries = audit.search("api_key")
    actions = {e.action for e in entries}
    assert "api_key.create" in actions and "api_key.revoke" in actions
    # Le plaintext ne doit apparaître dans AUCUNE entrée d'audit.
    for e in entries:
        assert created["key"] not in str(e.to_dict())