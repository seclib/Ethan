"""Tests du router HTTP /files (interfaces/api/routers/domains.py).

Le Core (``core/state/files.FileStore``) possède les fichiers ; ce router ne
fait que les exposer.

Point de sécurité couvert : l'identité propriétaire d'un fichier est TOUJOURS
déduite du JWT (``request.state.user`` peuplé par ``auth_middleware``) et non
d'un ``user_id`` fourni par le client — un utilisateur authentifié ne peut donc
ni lister ni s'approprier les fichiers d'un autre compte (cf. AGENTS.md :
isolation par utilisateur, aucune confiance dans l'identité déclarée).
"""

from __future__ import annotations

import asyncio

import pytest
from core.state.files import FileStore
from core.state.record_store import CoreRecordStore
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from interfaces.api.auth import create_access_token, verify_token_string
from interfaces.api.routers import domains as domains_router_module
from interfaces.api.routers.domains import router


def _app(store: FileStore) -> FastAPI:
    """App minimale : router + réplique fidèle du middleware d'auth réel."""
    app = FastAPI()
    app.include_router(router)
    domains_router_module.set_domain_managers(files=store)

    @app.middleware("http")
    async def fake_auth_middleware(request: Request, call_next):
        token = None
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header.split(" ", 1)[1]
        if not token:
            return JSONResponse({"detail": "Authentification requise."}, status_code=401)
        try:
            payload = await verify_token_string(token)
        except Exception as exc:
            return JSONResponse({"detail": str(getattr(exc, "detail", exc))}, status_code=401)
        request.state.user = payload.get("sub", "unknown")
        request.state.token_payload = payload
        return await call_next(request)

    return app


def _auth(user: str, role: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': user, 'role': role})}"}


@pytest.fixture()
def store() -> FileStore:
    fs = FileStore(store=CoreRecordStore())
    domains_router_module.set_domain_managers(files=fs)
    yield fs
    domains_router_module.set_domain_managers(files=None)


def _seed(fs: FileStore, filename: str, user_id: str) -> None:
    asyncio.run(
        fs.register(
            filename=filename,
            content_type="text/plain",
            size=1,
            user_id=user_id,
        )
    )


async def _seed_async(fs: FileStore, filename: str, user_id: str) -> None:
    await fs.register(
        filename=filename,
        content_type="text/plain",
        size=1,
        user_id=user_id,
    )


# ── Isolation par JWT ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_files_isolated_by_jwt(store):
    await _seed_async(store, "alice.txt", "alice")
    await _seed_async(store, "bob.txt", "bob")

    async with AsyncClient(
        transport=ASGITransport(app=_app(store)), base_url="https://t"
    ) as client:
        resp = await client.get("/files", headers=_auth("alice"))

    assert resp.status_code == 200
    assert [f["filename"] for f in resp.json()] == ["alice.txt"]


@pytest.mark.asyncio
async def test_list_files_cannot_spoof_other_user(store):
    await _seed_async(store, "bob.txt", "bob")

    async with AsyncClient(
        transport=ASGITransport(app=_app(store)), base_url="https://t"
    ) as client:
        resp = await client.get("/files?user_id=bob", headers=_auth("alice"))

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_upload_attributes_file_to_jwt_user(store):
    async with AsyncClient(
        transport=ASGITransport(app=_app(store)), base_url="https://t"
    ) as client:
        resp = await client.post(
            "/files/upload",
            files={"file": ("secret.txt", b"hello", "text/plain")},
            data={"user_id": "bob"},
            headers=_auth("alice"),
        )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "alice"

        listing = await client.get("/files", headers=_auth("alice"))

    assert [f["filename"] for f in listing.json()] == ["secret.txt"]


@pytest.mark.asyncio
async def test_files_require_authentication(store):
    async with AsyncClient(
        transport=ASGITransport(app=_app(store)), base_url="https://t"
    ) as client:
        assert (await client.get("/files")).status_code == 401
        assert (
            await client.post("/files/upload", files={"file": ("x.txt", b"x", "text/plain")})
        ).status_code == 401


# ── Repli interne (appel direct sans Request) ─────────────────────────────


def test_list_files_direct_call_uses_user_id_fallback(store):
    """Sans ``Request`` (client interne / Open WebUI), le repli ``user_id`` demeure."""
    _seed(store, "alice.txt", "alice")
    _seed(store, "bob.txt", "bob")

    alice = asyncio.run(domains_router_module.list_files(request=None, user_id="alice"))
    assert [f["filename"] for f in alice] == ["alice.txt"]

    everything = asyncio.run(domains_router_module.list_files(request=None))
    assert len(everything) == 2
