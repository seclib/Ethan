"""Tests HTTP du routeur God's Eye View AI — adaptateur d'inference ETHAN.

Verifie le contrat sans logique metier :
- RBAC (READ / PLUGINS / ADMIN) declare sur les routes gerees ;
- provision -> JWT de portee ``plugins:gods-eye-view-ai`` (bref, scope) ;
- chat OpenAI-compatible relisant le vrai ProviderManager (fake) ;
- HUD summary : contrainte 5 mots appliquee cote serveur ;
- validation d'outils : allow-liste fermee (jamais d'execution auto).
"""

from __future__ import annotations

import os
import secrets
from types import SimpleNamespace

import pytest

# L'auth refuse de demarrer sans secret : meme convention que system_exec.
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))

from core.auth import Permission, rbac  # noqa: E402
from core.llm.types import ChatMessage  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from core.auth.api_keys import APIKeyManager  # noqa: E402
from interfaces.api.auth import (  # noqa: E402
    auth_middleware,
    create_access_token,
    set_api_key_manager,
    get_api_key_manager,
)
from interfaces.api.routers import gods_eye_view_ai as gev_ai  # noqa: E402

BASE = "/v1/plugins/gods-eye-view/ai"
CHAT = f"{BASE}/chat"
HUD = f"{BASE}/hud-summary"
CAP = f"{BASE}/capabilities"
CONFIG = f"{BASE}/config"
PROVISION = f"{BASE}/provision"
VALIDATE = f"{BASE}/tools/validate"

_DEFAULT_CONFIG = {
    "default_model": None,
    "default_provider": None,
    "context_limit": 8000,
    "timeout_seconds": 60,
}


class _FakeModel:
    def __init__(self, model_id: str, provider: str = "ollama"):
        self.id = model_id
        self.provider = provider
        self.name = model_id


class _FakeManager:
    """ProviderManager minimal : memes signatures que le reel."""

    def __init__(self, reply: str = "Nominal."):
        self.reply = reply
        self.fail: Exception | None = None
        self.models = [_FakeModel("llama3.2:3b"), _FakeModel("mistral:7b")]
        self.chat_calls: list[tuple] = []

    async def list_models(self, provider_id=None):
        return list(self.models)

    async def list_providers(self):
        return [{"id": "ollama"}]

    async def chat(self, messages, requirements=None):
        if self.fail is not None:
            raise self.fail
        self.chat_calls.append((messages, requirements))
        return SimpleNamespace(content=self.reply, model="llama3.2:3b")

    def chat_stream(self, messages, requirements=None):
        async def _gen():
            for token in self.reply.split():
                yield token + " "
        return _gen()


@pytest.fixture
def manager():
    m = _FakeManager()
    gev_ai.set_provider_manager(m)
    yield m
    gev_ai.set_provider_manager(None)
    gev_ai._gev_ai_config.clear()
    gev_ai._gev_ai_config.update(dict(_DEFAULT_CONFIG))


@pytest.fixture
def client(manager):
    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(gev_ai.router)
    with TestClient(app) as test_client:
        yield test_client


def _auth(role: str = "admin", user_id: str = "alice") -> dict[str, str]:
    token = create_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


def _agent() -> dict[str, str]:
    """Token de provision (portee GEV-AI) — flux serveur GEV."""
    payload = {"sub": "gevs-ai", "role": "gevs-ai",
               "scope": [gev_ai.AI_SCOPE]}
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}


def _msg(content: str = "status") -> list[dict]:
    return [{"role": "user", "content": content}]


def _required(path: str, method: str) -> set[Permission]:
    """Permissions RBAC declarees sur une route (contrat d'introspection)."""
    route = next(
        r for r in gev_ai.router.routes
        if getattr(r, "path", "") == path and method in (r.methods or set())
    )
    # depends de decorator (Depends.dependency) + depends de param
    # (Dependant.call) — les deux sont des closures avec .permission.
    candidates = [getattr(d, "dependency", None) for d in route.dependencies]
    candidates += [getattr(d, "call", None)
                   for d in route.dependant.dependencies]
    return {c.permission for c in candidates if hasattr(c, "permission")}


def test_routes_and_rbac_declared():
    by_path: dict[str, set[str]] = {}
    for r in gev_ai.router.routes:
        by_path.setdefault(r.path, set()).update(r.methods or set())
    assert by_path[CAP] == {"GET"}
    assert by_path[CONFIG] == {"GET", "PUT"}
    assert by_path[PROVISION] == {"POST"}
    assert by_path[CHAT] == {"POST"}
    assert by_path[HUD] == {"POST"}
    assert by_path[VALIDATE] == {"POST"}
    assert _required(CAP, "GET") == {Permission.READ}
    assert _required(CONFIG, "GET") == {Permission.READ}
    assert _required(CONFIG, "PUT") == {Permission.PLUGINS}
    assert _required(PROVISION, "POST") == {Permission.ADMIN}
    # chat / hud / validate : portee JWT geree par _verify_ai_token,
    # pas de require_permission (token de provision sans role utilisateur).
    assert not _required(CHAT, "POST")


def test_capabilities_lists_compatible_functions(client):
    res = client.get(CAP, headers=_auth("viewer"))
    assert res.status_code == 200
    data = res.json()
    funcs = {f["function"]: f for f in data["functions"]}
    assert funcs["hud_summary"]["compatible"] is True
    assert funcs["realtime_voice_audio"]["compatible"] is False
    assert data["realtime_voice"]["compatible"] is False
    assert data["realtime_voice"]["fallback"]


def test_config_lists_models_without_embeddings(client, manager):
    manager.models.append(_FakeModel("nomic-embed-text"))
    res = client.get(CONFIG, headers=_auth("viewer"))
    assert res.status_code == 200
    ids = [m["id"] for m in res.json()["allowed_models"]]
    assert "llama3.2:3b" in ids
    assert "nomic-embed-text" not in ids


def test_config_put_validates_against_ethan(client):
    unknown = client.put(
        CONFIG, headers=_auth(), json={"default_model": "nope"})
    assert unknown.status_code == 404
    ok = client.put(
        CONFIG, headers=_auth(),
        json={"default_model": "llama3.2:3b", "timeout_seconds": 30})
    assert ok.status_code == 200
    cfg = ok.json()["config"]
    assert cfg["default_model"] == "llama3.2:3b"
    assert cfg["timeout_seconds"] == 30
    forbidden = client.put(
        CONFIG, headers=_auth("viewer"), json={"default_model": "x"})
    assert forbidden.status_code == 403


def test_provision_requires_admin(client):
    assert client.post(PROVISION).status_code == 401
    assert client.post(
        PROVISION, headers=_auth("viewer")).status_code == 403


def test_provision_token_is_scoped_and_usable(client, manager):
    res = client.post(PROVISION, headers=_auth())
    assert res.status_code == 200
    body = res.json()
    assert body["scopes"] == [gev_ai.AI_SCOPE]
    assert 0 < body["expires_in"] <= 3600
    chat = client.post(
        CHAT,
        headers={"Authorization": f"Bearer {body['token']}"},
        json={"messages": _msg()})
    assert chat.status_code == 200
    assert manager.chat_calls


def test_gevs_ai_role_registered():
    assert rbac.has_permission("gevs-ai", Permission.GODS_EYE_AI)
    assert rbac.has_permission("gevs-ai", Permission.CHAT)
    assert not rbac.has_permission("gevs-ai", Permission.ADMIN)



def test_chat_rejects_missing_or_wrong_scope(client):
    assert client.post(
        CHAT, json={"messages": _msg()}).status_code == 401
    res = client.post(
        CHAT, headers=_auth("viewer"), json={"messages": _msg()})
    assert res.status_code == 403


def test_chat_returns_openai_shape(client, manager):
    res = client.post(
        CHAT, headers=_agent(),
        json={"messages": _msg("etat des entites")})
    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "chat.completion"
    choice = data["choices"][0]
    assert choice["message"]["role"] == "assistant"
    assert choice["message"]["content"] == "Nominal."
    assert choice["finish_reason"] == "stop"
    msgs, req = manager.chat_calls[0]
    assert isinstance(msgs[0], ChatMessage)
    assert req.task_type == "chat"


def test_chat_unknown_model_is_404(client):
    res = client.post(
        CHAT, headers=_agent(),
        json={"messages": _msg(), "model": "nope"})
    assert res.status_code == 404


def test_chat_failure_is_sanitized_502(client, manager):
    manager.fail = RuntimeError("upstream api_key sk-SECRET leaked")
    res = client.post(CHAT, headers=_agent(), json={"messages": _msg()})
    assert res.status_code == 502
    assert "sk-SECRET" not in res.text


def test_chat_sse_stream(client):
    res = client.post(
        CHAT, headers=_agent(),
        json={"messages": _msg(), "stream": True})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")
    assert "data: [DONE]" in res.text
    assert "Nominal" in res.text


def test_chat_without_manager_is_503(client):
    gev_ai.set_provider_manager(None)
    res = client.post(CHAT, headers=_agent(), json={"messages": _msg()})
    assert res.status_code == 503


def test_hud_summary_is_five_words_max(client, manager):
    manager.reply = "Nominal feeds stable across every single layer now"
    res = client.post(
        HUD, headers=_agent(),
        json={"labels": ["RADAR"], "feedState": "OK"})
    assert res.status_code == 200
    data = res.json()
    assert data["error"] is None
    assert len(data["summary"].split()) <= 5
    # Prompt system impose au provider (contrat HUD d'origine conserve).
    msgs, _ = manager.chat_calls[0]
    assert msgs[0].role == "system"
    assert msgs[0].content == gev_ai.HUD_SYSTEM_PROMPT


def test_tools_validate_allowlist(client):
    ok = client.post(
        VALIDATE, headers=_agent(),
        json={"name": "fly_to_location", "arguments": {"lat": 48.85}})
    assert ok.status_code == 200
    body = ok.json()
    assert body["ok"] is True
    assert body["requires_explicit_approval"] is True
    denied = client.post(
        VALIDATE, headers=_agent(),
        json={"name": "rm_rf", "arguments": {}})
    assert denied.status_code == 403
    unauth = client.post(
        VALIDATE, json={"name": "fly_to_location", "arguments": {}})
    assert unauth.status_code == 401



# ── Limites de contexte ─────────────────────────────────────────────────


def test_truncate_messages_keeps_system_and_recent():
    msgs = [ChatMessage(role="system", content="SYS-PROMPT")]
    msgs += [
        ChatMessage(role="user", content=f"msg{i:02d}" + "x" * 490)
        for i in range(10)
    ]
    out = gev_ai._truncate_messages(msgs, 1000)
    # Le system est toujours conserve en tete.
    assert out[0].role == "system"
    assert out[0].content == "SYS-PROMPT"
    # Le budget (1000 - 10) autorise 2 messages de 494 chars, pas 3.
    assert len(out) == 3
    # Ce sont les messages les plus recents qui sont gardes.
    assert out[-1].content.startswith("msg09")


def test_truncate_messages_caps_message_count():
    msgs = [ChatMessage(role="user", content=f"m{i}") for i in range(80)]
    out = gev_ai._truncate_messages(msgs, 100000)
    assert len(out) == gev_ai.MAX_MESSAGES
    assert out[-1].content == "m79"


def test_chat_context_limit_truncates_request(client, manager):
    big = [{"role": "user", "content": "y" * 500} for _ in range(10)]
    res = client.post(
        CHAT, headers=_agent(),
        json={"messages": big, "context_limit": 1000})
    assert res.status_code == 200
    sent = manager.chat_calls[0][0]
    # Budget 1000 : au plus 2 messages de 500 chars traversent.
    assert 1 <= len(sent) <= 2
    total = sum(len(m.content or "") for m in sent)
    assert total <= 1000


# ── Non-fuite de secrets ────────────────────────────────────────────────


def test_config_endpoint_never_leaks_secrets(client, manager):
    res = client.get(CONFIG, headers=_auth("viewer"))
    assert res.status_code == 200
    body = res.text.lower()
    assert "api_key" not in body
    assert "secret" not in body
    assert "token" not in body
    # La config plugin ne porte que les 4 cles prevues.
    assert set(res.json()["config"].keys()) == set(_DEFAULT_CONFIG.keys())


def test_provision_returns_only_scoped_token(client):
    res = client.post(PROVISION, headers=_auth())
    assert res.status_code == 200
    assert set(res.json().keys()) == {"token", "expires_in", "scopes"}
    # Le jeton ne porte aucune information provider/clé.
    import base64
    import json as _json
    payload_b64 = res.json()["token"].split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    claims = _json.loads(base64.urlsafe_b64decode(payload_b64))
    blob = _json.dumps(claims).lower()
    assert "api_key" not in blob and "sk-" not in blob
    assert claims["scope"] == [gev_ai.AI_SCOPE]



# ── Modèle local réel (si disponible) ────────────────────────────────────


def _local_models() -> list[str]:
    """Modeles disponibles sur un Ollama local, ou []."""
    import urllib.request
    try:
        with urllib.request.urlopen(
                "http://localhost:11434/api/tags", timeout=2) as resp:
            import json as _json
            data = _json.loads(resp.read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def test_local_model_roundtrip_via_real_manager(manager):
    """Roundtrip reel : vrai ProviderManager + Ollama local (skip sinon).

    Tout le chemin (register + requetes via ASGITransport) tourne dans
    UNE seule boucle asyncio : le client httpx du provider est bindé a la
    boucle qui l'a initialise.
    """
    import asyncio

    from core.llm.provider_manager import ProviderManager
    from httpx import ASGITransport, AsyncClient

    models = _local_models()
    if not models:
        pytest.skip("Ollama local indisponible")

    class _MemStore:
        async def save(self, *args, **kwargs):
            return None

        async def get_all(self):
            return {}

    async def _roundtrip():
        mgr = ProviderManager(store=_MemStore())
        await mgr.register_provider(config={
            "type": "ollama",
            "name": "ollama-local",
            "default_model": models[0],
        })
        gev_ai.set_provider_manager(mgr)
        gev_ai.set_gev_config({"default_model": models[0],
                               "timeout_seconds": 120})
        app = FastAPI()
        app.middleware("http")(auth_middleware)
        app.include_router(gev_ai.router)
        headers = {"Authorization": "Bearer " + create_access_token(
            {"sub": "gevs-ai", "role": "gevs-ai",
             "scope": [gev_ai.AI_SCOPE]})}
        async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://t") as ac:
            res = await ac.post(
                CHAT, headers=headers,
                json={"messages": [{"role": "user",
                                    "content": "Reponds uniquement par OK."}]})
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["object"] == "chat.completion"
            assert data["choices"][0]["message"]["content"].strip()
            # GET /config reflete les modeles locaux (sans embeddings).
            cfg = await ac.get(CONFIG, headers=headers)
            assert cfg.status_code == 200
            ids = [m["id"] for m in cfg.json()["allowed_models"]]
            assert models[0] in ids

    asyncio.run(_roundtrip())



# ── API key (server-to-server) ──────────────────────────────────────────


@pytest.fixture
def api_key_manager_fixture():
    m = APIKeyManager()
    set_api_key_manager(m)
    yield m
    set_api_key_manager(None)


@pytest.fixture
def api_key_value(api_key_manager_fixture):
    import asyncio

    async def _create():
        rec = await api_key_manager_fixture.create_key(
            "gev-server", "gev", scopes=[gev_ai.AI_SCOPE]
        )
        return rec["key"]

    return asyncio.run(_create())


@pytest.fixture
def client_api(manager, api_key_value):
    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(gev_ai.router)
    with TestClient(app) as test_client:
        yield test_client, api_key_value


def test_hud_summary_with_api_key(client_api, manager):
    client, key = client_api
    manager.reply = "Nominal feeds stable across every single layer now"
    res = client.post(
        HUD, headers={"X-API-Key": key},
        json={"labels": ["RADAR"], "feedState": "OK"})
    assert res.status_code == 200
    data = res.json()
    assert data["error"] is None
    assert len(data["summary"].split()) <= 5


def test_hud_summary_invalid_api_key(client_api):
    client, _ = client_api
    res = client.post(
        HUD, headers={"X-API-Key": "ethan_invalid"},
        json={"labels": ["RADAR"]})
    assert res.status_code == 401


def test_hud_summary_missing_credentials(client_api):
    client, _ = client_api
    res = client.post(HUD, json={"labels": ["RADAR"]})
    assert res.status_code == 401
