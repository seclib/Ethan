"""Tests réels du cycle de vie utilisateurs (PUT/DELETE /users/{username}).

Un pool asyncpg factice émule la table ``users`` en mémoire : chaque action
est réellement exécutée contre ce store (pas de mock de la logique du router)
et l'état résultant est vérifié. Protections testées : auto-action, dernier
admin actif, validation, 404, gate admin.
"""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from interfaces.api.routers import security as security_router


# ── Pool / conn factices ──────────────────────────────────────────────────


class FakeConn:
    """Émule asyncpg.connection sur un store dict, patterns SQL du router."""

    def __init__(self, store):
        self._store = store

    async def fetchrow(self, sql: str, *args):
        if sql.startswith(
            "SELECT id, roles, is_active FROM users"
        ) or sql.startswith("SELECT id, username, roles, is_active FROM users"):
            rec = self._store.get(args[0])
            if rec is None:
                return None
            row = {"id": rec["id"], "roles": list(rec["roles"]),
                   "is_active": rec["is_active"]}
            if "username" in sql:
                row["username"] = args[0]
            return row
        if sql.startswith("UPDATE users SET") and "RETURNING" in sql:
            username = args[-1]
            rec = self._store.get(username)
            if rec is None:
                return None
            # Mappe les args sur les clauses SET dans l'ordre du router :
            # roles, puis is_active, puis password_hash.
            pos = 0
            if "roles = $" in sql:
                rec["roles"] = list(args[pos]); pos += 1
            if "is_active = $" in sql:
                rec["is_active"] = args[pos]; pos += 1
            if "password_hash = $" in sql:
                rec["password_hash"] = args[pos]; pos += 1
            return {"id": rec["id"], "username": username, "roles": list(rec["roles"]),
                    "is_active": rec["is_active"], "totp_enabled": rec["totp_enabled"],
                    "updated_at": "now"}
        return None

    async def fetchval(self, sql: str, *args):
        if "count(*)" in sql and "ANY(roles)" in sql:
            return sum(1 for r in self._store.values()
                       if "admin" in r["roles"] and r["is_active"])
        return None

    async def execute(self, sql: str, *args):
        if sql.startswith("DELETE FROM users"):
            return "DELETE 1" if self._store.pop(args[0], None) else "DELETE 0"
        return ""


class FakePool:
    def __init__(self, store):
        self._store = store

    def acquire(self):
        return self

    async def __aenter__(self):
        return FakeConn(self._store)

    async def __aexit__(self, *exc):
        return False


def make_store():
    """Deux admins actifs + un user : permet de tester « dernier admin »."""
    return {
        "root": {"id": 1, "roles": ["admin"], "is_active": True,
                 "totp_enabled": False, "password_hash": "x"},
        "admin2": {"id": 2, "roles": ["admin"], "is_active": True,
                   "totp_enabled": False, "password_hash": "x"},
        "bob": {"id": 3, "roles": ["user"], "is_active": True,
                "totp_enabled": False, "password_hash": "x"},
    }


def admin_request(sub="root", role="admin"):
    return SimpleNamespace(state=SimpleNamespace(
        token_payload={"sub": sub, "role": role}))


@pytest.fixture(autouse=True)
def fake_pool(monkeypatch):
    store = make_store()
    security_router.set_security_pool(FakePool(store))
    # Référence du store pour les assertions des tests.
    monkeypatch.setattr(security_router, "_store_ref", store, raising=False)
    yield store
    security_router.set_security_pool(None)


# ── PUT /users/{username} ─────────────────────────────────────────────────


def test_update_role_success():
    store = security_router._store_ref
    res = asyncio.run(security_router.update_user(
        admin_request(), "bob", {"role": "admin"}))
    assert res["roles"] == ["admin"]
    assert store["bob"]["roles"] == ["admin"]


def test_update_password_hashes():
    import bcrypt
    store = security_router._store_ref
    asyncio.run(security_router.update_user(
        admin_request(), "bob", {"password": "newsecret"}))
    assert bcrypt.checkpw(b"newsecret", store["bob"]["password_hash"].encode())


def test_update_self_role_forbidden():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.update_user(
            admin_request(sub="root"), "root", {"role": "user"}))
    assert exc.value.status_code == 403


def test_update_demote_last_admin_conflict():
    store = security_router._store_ref
    # root et admin2 seulement ; admin2 parti → root reste seul admin actif.
    # L'acteur est un admin « fantôme » (JWT valide émis avant la suppression
    # de son compte) : c'est le seul moyen d'atteindre le 409, car l'auto-
    # action (403) prime pour root lui-même — défense en profondeur.
    store.pop("admin2")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.update_user(
            admin_request(sub="ghost"), "root", {"role": "user"}))
    assert exc.value.status_code == 409


def test_update_demote_with_second_admin_ok():
    res = asyncio.run(security_router.update_user(
        admin_request(), "admin2", {"role": "user"}))
    assert res["roles"] == ["user"]


def test_update_unknown_user_404():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.update_user(
            admin_request(), "ghost", {"role": "user"}))
    assert exc.value.status_code == 404


def test_update_invalid_role_422():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.update_user(
            admin_request(), "bob", {"role": "superadmin"}))
    assert exc.value.status_code == 422


def test_update_short_password_422():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.update_user(
            admin_request(), "bob", {"password": "abc"}))
    assert exc.value.status_code == 422


def test_update_empty_payload_422():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.update_user(admin_request(), "bob", {}))
    assert exc.value.status_code == 422


def test_update_requires_admin():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.update_user(
            admin_request(sub="bob", role="user"), "admin2", {"role": "user"}))
    assert exc.value.status_code == 403


# ── DELETE /users/{username} ──────────────────────────────────────────────


def test_delete_success():
    store = security_router._store_ref
    res = asyncio.run(security_router.delete_user(admin_request(), "bob"))
    assert res == {"status": "deleted", "username": "bob"}
    assert "bob" not in store


def test_delete_self_forbidden():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.delete_user(
            admin_request(sub="root"), "root"))
    assert exc.value.status_code == 403


def test_delete_last_admin_conflict():
    store = security_router._store_ref
    # root devient le seul admin actif ; acteur = admin fantôme (cf. test
    # update_demote_last_admin_conflict) — l'auto-action (403) prime sinon.
    store.pop("admin2")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.delete_user(admin_request(sub="ghost"), "root"))
    assert exc.value.status_code == 409


def test_delete_inactive_last_admin_allowed():
    """Un admin DÉSACTIVÉ n'est plus « garant » : sa suppression est permise."""
    store = security_router._store_ref
    store["admin2"]["is_active"] = False
    asyncio.run(security_router.delete_user(admin_request(), "admin2"))
    assert "admin2" not in store


def test_delete_unknown_user_404():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.delete_user(admin_request(), "ghost"))
    assert exc.value.status_code == 404


def test_delete_requires_admin():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security_router.delete_user(
            admin_request(sub="bob", role="user"), "admin2"))
    assert exc.value.status_code == 403
