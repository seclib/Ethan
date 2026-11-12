"""Tests du router HTTP /connections (délégation pure, sans réseau).

Points de sécurité couverts :
- auth obligatoire (401 sans JWT), RBAC (403 sans permission) ;
- l'utilisateur opère sur SES connexions (user_id issu du JWT) ;
- aucune réponse ne contient de token ni de client_secret ;
- mapping d'erreurs Core → 404/422, 503 si manager non initialisé.
"""

from __future__ import annotations

import pytest
from core.integrations.connections import ConnectionManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from interfaces.api.auth import create_access_token
from interfaces.api.routers import connections as connections_router_module
from interfaces.api.routers.connections import router

from .conftest import FakeHttp, FakeResponse, make_manager  # noqa: F401


def _app_with_manager(manager: ConnectionManager) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    connections_router_module.set_connection_manager(manager)
    return app


def _auth(token_payload_role: str = "admin") -> dict[str, str]:
    claims = {"sub": "alice", "role": token_payload_role}
    return {"Authorization": f"Bearer {create_access_token(claims)}"}


async def _full_connected(manager: ConnectionManager, http: FakeHttp) -> None:
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])


def _github_oauth_http() -> FakeHttp:
    http = FakeHttp()
    http.queue(
        "POST",
        "github.com/login/oauth/access_token",
        FakeResponse(200, {"access_token": "gho_X", "scope": "repo read:user"}),
    )
    http.queue("GET", "api.github.com/user", FakeResponse(200, {"login": "seclib"}))
    return http


# __NEXT__


def _app_with_auth(manager: ConnectionManager) -> FastAPI:
    """App minimale : router + réplique fidèle du middleware d'auth réel
    (JWT → request.state.user / token_payload), sans dépendance réseau.
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from interfaces.api.auth import verify_token_string

    app = _app_with_manager(manager)

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


# ── Auth / RBAC ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoints_require_authentication(oauth_secrets):
    app = _app_with_auth(make_manager(secrets=oauth_secrets))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://t") as client:
        assert (await client.get("/connections")).status_code == 401
        assert (await client.post("/connections/github/connect", json={})).status_code == 401


@pytest.mark.asyncio
async def test_mutations_require_plugins_permission(oauth_secrets):
    app = _app_with_auth(make_manager(secrets=oauth_secrets))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://t") as client:
        viewer = _auth("viewer")  # viewer n'a pas PLUGINS
        resp = await client.post("/connections/github/connect", json={}, headers=viewer)
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unknown_provider_maps_to_422(oauth_secrets):
    app = _app_with_auth(make_manager(secrets=oauth_secrets))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://t") as client:
        resp = await client.post("/connections/gitlab/connect", json={}, headers=_auth())
        assert resp.status_code == 422


# __NEXT2__


# ── Cycle HTTP complet (start → callback → list → test → permissions → delete) ──


@pytest.mark.asyncio
async def test_full_http_flow_never_leaks_secrets(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    app = _app_with_auth(manager)
    headers = _auth()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://t") as client:
        # 1. Catalogue sans secret.
        resp = await client.get("/connections/providers", headers=headers)
        assert resp.status_code == 200
        ids = {p["id"] for p in resp.json()}
        assert {"email", "github", "medium", "notion"} <= ids
        assert "secret-test" not in resp.text

        # 2. Connecter → URL OAuth + state (client_secret absent de la réponse).
        connect = await client.post("/connections/github/connect", json={}, headers=headers)
        assert connect.status_code == 200
        body = connect.json()
        assert body["authorization_url"].startswith("https://github.com/login/oauth")
        assert "gh-secret-test" not in connect.text

        # 3. Callback OAuth → connexion réelle.
        callback = await client.post(
            "/connections/github/callback",
            json={"code": "abc", "state": body["state"]},
            headers=headers,
        )
        assert callback.status_code == 200
        assert callback.json()["status"] == "connected"
        assert "gho_X" not in callback.text

        # 4. Lister — aucune trace de token.
        listing = await client.get("/connections", headers=headers)
        assert listing.status_code == 200
        assert "gho_X" not in listing.text
        assert listing.json()[0]["user_id"] == "alice"

        # 5. Tester (nouveau client HTTP : le premier a servi au callback).
        test_http = FakeHttp()
        test_http.queue("GET", "api.github.com/user", FakeResponse(200, {"login": "seclib"}))
        manager._http_factory = lambda: test_http
        tested = await client.post("/connections/github/test", headers=headers)
        assert tested.status_code == 200
        assert tested.json()["account"]["login"] == "seclib"

        # 6. Voir les permissions.
        perms = await client.get("/connections/github/permissions", headers=headers)
        assert perms.status_code == 200
        assert [s["scope"] for s in perms.json()["requested"]] == [
            "repo",
            "read:user",
            "user:email",
        ]

        # 7. Déconnecter.
        deleted = await client.delete("/connections/github", headers=headers)
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "disconnected"
        assert "gho_X" not in deleted.text


@pytest.mark.asyncio
async def test_callback_without_code_or_state_is_422(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets)
    app = _app_with_auth(manager)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://t") as client:
        resp = await client.post(
            "/connections/github/callback",
            json={"code": "", "state": ""},
            headers=_auth(),
        )
        assert resp.status_code == 422
