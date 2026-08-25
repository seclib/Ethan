"""Open WebUI-compatible adapter router (interfaces/api layer — thin gateway).

This router exposes a subset of the Open WebUI backend contract
(`/api/v1/auths/*`, `/api/v1/models/*`, `/openai/*` and the OpenAI-compatible
`/api/chat/completions` streaming endpoint) so that the Open WebUI frontend
(``examples/open-webui``) can run as ETHAN WebUI against the *real* ETHAN
Core/Runtime — it does **not** reimplement any business logic.

All intelligence stays in ``core/`` (AGENTS.md):
- auth   -> ``core/auth`` + JWT via ``interfaces.api.auth``
- models -> ``core/llm/model_store`` + ``core/llm/provider_manager``
- chat   -> ``core/llm/provider_manager.chat_stream`` (echo fallback)
- config -> ``core/llm/provider_manager`` providers

Only request/response *shapes* are adapted to the OWUI contract
(response shaping = interface concern).
"""

from __future__ import annotations

import importlib
import json
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from core.llm.types import ChatMessage, LLMRequirements
from interfaces.api.auth import (
    create_access_token,
    verify_token_string,
)
from interfaces.api.routers.models import get_manager as get_provider_manager
from interfaces.api.routers.models import get_store as get_model_store

logger = logging.getLogger(__name__)

# Mounted at root (``prefix=""``) so Open WebUI paths are absolute:
# ``/api/v1/auths/...``, ``/api/...``, ``/openai/...``.
router = APIRouter(prefix="", tags=["openwebui"])

# Lazy resolver so the router imports cleanly in isolated unit tests even if
# the domains router has not been wired yet.
try:  # UserManager is injected by the lifespan via domains.set_domain_managers
    from interfaces.api.routers.domains import get_user_manager  # type: ignore

    _get_user_manager = get_user_manager  # type: ignore[assignment]
except Exception:  # pragma: no cover - domains router always present at runtime
    _get_user_manager = None  # type: ignore[assignment]


# ── Helpers ────────────────────────────────────────────────────────────


def _bearer_token(request: Request) -> str | None:
    """Extract a JWT bearer token from the request (header or ``token`` cookie)."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer ") :]
    return request.cookies.get("token") or request.cookies.get("ethan_token")


def _now_ts() -> int:
    return int(time.time())


def _ow_session(user: dict[str, Any], token: str, expires_at: int | None = None) -> dict[str, Any]:
    """Build an Open WebUI ``SessionUserResponse`` from an ETHAN user record."""
    return {
        "token": token,
        "token_type": "Bearer",
        "expires_at": expires_at,
        "id": user.get("id"),
        "email": user.get("email"),
        "name": user.get("username") or user.get("email", ""),
        "role": user.get("role", "user"),
        "profile_image_url": f"/api/v1/users/{user.get('id')}/profile/image",
        "permissions": {},
    }


def _resolve_provider_manager():
    try:
        return get_provider_manager()
    except Exception:
        return None


def _resolve_user_manager():
    if _get_user_manager is None:
        return None
    try:
        return _get_user_manager()
    except Exception:
        return None


def _get_chat_pipeline():
    """Lazily resolve the Core ChatPipeline (None if not wired)."""
    try:
        mod = importlib.import_module("interfaces.api.routers.v1")
        return mod.get_chat_pipeline()
    except Exception:
        return None


def _to_chat_messages(messages: list[dict[str, Any]]) -> list[ChatMessage]:
    """Convert OpenAI-style messages into ETHAN Core ``ChatMessage``."""
    out: list[ChatMessage] = []
    for msg in messages or []:
        role = msg.get("role", "user")
        content = msg.get("content")
        if content is None and isinstance(msg.get("parts"), list):
            content = " ".join(str(p) for p in msg["parts"])
        if not isinstance(content, str):
            content = json.dumps(content) if not isinstance(content, str) else content
        out.append(
            ChatMessage(
                role=role,
                content=content,
                name=msg.get("name"),
                tool_calls=msg.get("tool_calls"),
                tool_call_id=msg.get("tool_call_id"),
            )
        )
    return out


def _openai_chunk(request_id: str, created: int, model: str,
                  delta: dict[str, Any], finish_reason: str | None = None) -> str:
    """Serialize one OpenAI-compatible SSE chunk string."""
    payload = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(payload)}\n\n"


async def _echo_stream(content: str, model: str):
    """Fallback OpenAI-compatible SSE emitter used when no provider is wired."""
    request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = _now_ts()
    yield _openai_chunk(request_id, created, model, {"role": "assistant", "content": ""})
    words = content.split(" ") if content else ["[ECHO] no provider configured"]
    for word in words:
        yield _openai_chunk(request_id, created, model, {"content": word + " "})
    yield _openai_chunk(request_id, created, model, {}, finish_reason="stop")
    yield "data: [DONE]\n\n"


def _openai_non_stream_response(model: str, content: str,
                                 request_id: str | None = None) -> JSONResponse:
    request_id = request_id or f"chatcmpl-{uuid.uuid4().hex[:12]}"
    payload = {
        "id": request_id,
        "object": "chat.completion",
        "created": _now_ts(),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    return JSONResponse(content=payload)


def _last_user_message(messages: list[dict[str, Any]]) -> str:
    for msg in reversed(messages or []):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            return content if isinstance(content, str) else str(content)
    return ""


# ── Auth (public) ────────────────────────────────────────────────────────


@router.post("/api/v1/auths/signin")
async def ow_signin(request: Request, response: Response):
    """Open WebUI ``/auths/signin`` → ETHAN JWT (Bearer)."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = (body.get("email") or body.get("username") or "").strip().lower()
    password = body.get("password", "")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    users = _resolve_user_manager()
    if users is None:
        raise HTTPException(status_code=503, detail="User service unavailable")

    user = await users.find_by_email(email)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    from passlib.hash import bcrypt as _bcrypt

    stored = user.get("password_hash") or ""
    if not stored or not _bcrypt.verify(password, stored):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    expires_at = _now_ts() + 3600 * 8
    token = create_access_token(
        data={"sub": email, "id": user.get("id"), "role": user.get("role", "user"), "email": email},
        expires_delta=None,
    )
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=expires_at - _now_ts(),
        path="/",
    )
    return _ow_session(user, token, expires_at)


@router.post("/api/v1/auths/signup")
async def ow_signup(request: Request, response: Response):
    """Open WebUI ``/auths/signup`` → create ETHAN user + JWT."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password", "")
    name = body.get("name") or email
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    users = _resolve_user_manager()
    if users is None:
        raise HTTPException(status_code=503, detail="User service unavailable")

    if await users.find_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered")

    from passlib.hash import bcrypt as _bcrypt

    password_hash = _bcrypt.hash(password)
    user = await users.create(
        username=email,
        email=email,
        role="user",
        password_hash=password_hash,
        profile={"name": name, "profile_image_url": body.get("profile_image_url", "/user.png")},
    )
    expires_at = _now_ts() + 3600 * 8
    token = create_access_token(
        data={"sub": email, "id": user["id"], "role": "user", "email": email},
        expires_delta=None,
    )
    return _ow_session(user, token, expires_at)


@router.get("/api/v1/auths/")
async def ow_get_session_user(request: Request):
    """Open WebUI ``GET /auths/`` → current session (Bearer token)."""
    token = _bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = await verify_token_string(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    users = _resolve_user_manager()
    user = None
    if users is not None and payload.get("id"):
        user = await users.get(payload["id"])
    if user is None:
        user = {
            "id": payload.get("id"),
            "email": payload.get("email"),
            "username": payload.get("sub"),
            "role": payload.get("role", "user"),
        }
    expires_at = payload.get("exp")
    if isinstance(expires_at, (int, float)):
        expires_at = int(expires_at)
    return _ow_session(user, token, expires_at)


@router.get("/api/v1/auths/signout")
async def ow_signout(request: Request, response: Response):
    """Open WebUI ``GET /auths/signout`` → invalidate session."""
    response.delete_cookie(key="token", httponly=True, samesite="lax", path="/")
    return {"status": True, "message": "Logged out successfully"}


# ── Models (protected) ──────────────────────────────────────────────────


@router.get("/api/v1/models/list")
async def ow_list_models(request: Request):
    """Open WebUI ``/models/list`` → aggregated ETHAN model catalogue."""
    provider_manager = _resolve_provider_manager()
    try:
        model_store = get_model_store()
    except Exception:
        model_store = None

    data: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Discovered models from live providers.
    if provider_manager is not None:
        try:
            discovered = await provider_manager.list_models()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("ProviderManager.list_models failed: %s", exc)
            discovered = []
        for info in discovered:
            mid = f"{info.provider}__{info.model or info.id}"
            if mid in seen:
                continue
            seen.add(mid)
            meta = info.metadata if isinstance(info.metadata, dict) else {}
            data.append(
                {
                    "id": mid,
                    "name": info.name or info.model or info.id,
                    "params": {},
                    "meta": {
                        "description": meta.get("description", ""),
                        "tags": list(info.capabilities),
                    },
                    "is_active": info.is_available,
                    "base_model_id": info.model,
                    "access": {"public": True},
                }
            )

    # Custom model cards from the Core ModelStore.
    if model_store is not None:
        try:
            custom = await model_store.list_models()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("ModelStore.list_models failed: %s", exc)
            custom = []
        for card in custom:
            mid = card.get("id") or card.get("name")
            if not mid or mid in seen:
                continue
            seen.add(mid)
            data.append(
                {
                    "id": mid,
                    "name": card.get("name", mid),
                    "params": card.get("params", {}),
                    "meta": card.get("meta", {}),
                    "is_active": bool(card.get("is_active", True)),
                    "base_model_id": card.get("base_model_id", ""),
                    "access": {"public": True},
                }
            )

    page = int(request.query_params.get("page", "1") or "1")
    page_size = int(request.query_params.get("page_size", str(len(data) or 50)) or "50")
    total = len(data)
    start = (page - 1) * page_size
    paged = data[start : start + page_size]
    return {
        "data": paged,
        "total": total,
        "page": page,
        "limit": page_size,
        "page_size": page_size,
        "has_more": False,
    }


@router.get("/api/v1/models/base")
async def ow_get_base_models(request: Request):
    """Open WebUI ``/models/base`` → raw per-provider model lists."""
    provider_manager = _resolve_provider_manager()
    if provider_manager is None:
        return {}
    try:
        providers = await provider_manager.list_providers()
    except Exception:
        providers = []
    base: dict[str, list[str]] = {}
    for prov in providers:
        pid = prov.get("id") or prov.get("name")
        if not pid:
            continue
        try:
            models = await provider_manager.list_models(pid)
            base[pid] = [m.model or m.id for m in models]
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("list_models(%s) failed: %s", pid, exc)
            base[pid] = []
    return base


@router.get("/api/v1/models/tags")
async def ow_get_model_tags(request: Request):
    """Open WebUI ``/models/tags`` → tag catalogue (empty for Phase 1)."""
    return []


@router.get("/api/v1/models/model")
async def ow_get_model_by_id(request: Request):
    """Open WebUI ``/models/model?id=...`` → single model card."""
    model_id = request.query_params.get("id", "")
    if not model_id:
        raise HTTPException(status_code=400, detail="id query param required")

    try:
        model_store = get_model_store()
    except Exception:
        model_store = None
    if model_store is not None:
        card = await model_store.get_model(model_id)
        if card:
            return card

    provider_manager = _resolve_provider_manager()
    if provider_manager is not None:
        try:
            for info in await provider_manager.list_models():
                mid = f"{info.provider}__{info.model or info.id}"
                if mid == model_id or info.id == model_id:
                    return {
                        "id": mid,
                        "name": info.name or info.model or info.id,
                        "provider": info.provider,
                        "model": info.model,
                    }
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("provider list_models failed: %s", exc)
    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


# ── OpenAI-compatible provider config (public read) ──────────────────────


@router.get("/openai/config")
async def ow_get_openai_config(request: Request):
    """Open WebUI ``/openai/config`` → OpenAI-compatible provider surfaces."""
    provider_manager = _resolve_provider_manager()
    urls: list[str] = []
    if provider_manager is not None:
        try:
            for prov in await provider_manager.list_providers():
                ptype = prov.get("type") or prov.get("provider_type")
                base_url = prov.get("base_url")
                if ptype in ("openai", "openai_compatible", "azure") and base_url:
                    urls.append(base_url)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("openai config build failed: %s", exc)
    return {
        "ENABLE_OPENAI_API": len(urls) > 0,
        "OPENAI_API_BASE_URLS": urls,
        "OPENAI_API_KEYS": [],
        "OPENAI_API_CONFIGS": {},
    }


# ── Chat completions (OpenAI-compatible SSE streaming) ──────────────────


@router.post("/api/chat/completions")
async def ow_chat_completions(request: Request, response: Response):
    """OpenAI-compatible ``/chat/completions`` mapped to ETHAN Core.

    Supports ``stream: true`` → SSE chunks in OpenAI format ending with
    ``data: [DONE]``. When no provider is wired the pipeline emits an echo
    stream so the frontend shell stays fully functional offline.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    body = body or {}

    model = body.get("model") or "echo"
    messages = body.get("messages", [])
    stream = bool(body.get("stream", False))
    last_user = _last_user_message(messages)

    provider_manager = _resolve_provider_manager()

    async def _openai_stream():
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = _now_ts()

        if provider_manager is None:
            async for piece in _echo_stream(last_user or "[ECHO] no provider configured", model):
                yield piece
            return

        requirements = LLMRequirements(task_type="chat")
        try:
            yield _openai_chunk(request_id, created, model, {"role": "assistant", "content": ""})
            llm_messages = _to_chat_messages(messages)
            try:
                stream_iter = provider_manager.chat_stream(llm_messages, requirements)
                async for chunk in stream_iter:
                    if chunk:
                        yield _openai_chunk(request_id, created, model, {"content": chunk})
                yield _openai_chunk(request_id, created, model, {}, finish_reason="stop")
            except Exception as exc:
                logger.exception("ProviderManager.chat_stream failed: %s", exc)
                # Degrade gracefully to an echo so the UI stays usable.
                async for piece in _echo_stream(str(exc), model):
                    yield piece
                return
            yield "data: [DONE]\n\n"
        except Exception as exc:
            logger.exception("ow_chat_completions stream failed: %s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            yield "data: [DONE]\n\n"

    if stream:
        return StreamingResponse(_openai_stream(), media_type="text/event-stream")

    # Non-streaming: collect the full response.
    if provider_manager is None:
        full = last_user or "[ECHO] no provider configured"
        return _openai_non_stream_response(model, full)

    try:
        llm_messages = _to_chat_messages(messages)
        try:
            result = await provider_manager.chat(llm_messages, LLMRequirements(task_type="chat"))
            full = result.content if result and getattr(result, "content", None) else last_user
        except Exception as exc:
            logger.exception("ProviderManager.chat failed: %s", exc)
            full = f"[ECHO] provider error: {exc}"
        return _openai_non_stream_response(model, full)
    except Exception as exc:
        logger.exception("ow_chat_completions failed: %s", exc)
        return _openai_non_stream_response(model, f"[ECHO] {exc}")


@router.post("/api/v1/chat/completions")
async def ow_v1_chat_completions(request: Request):
    """Ethan-native ``/v1/chat/completions`` passthrough (delegates to ChatPipeline).

    Kept for ETHAN-native clients mirroring the OpenAI shape but wanting the
    Core chat orchestration (conversation tree, ACL, memory, RAG).
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    body = body or {}

    pipeline = _get_chat_pipeline()
    if pipeline is None:
        last = _last_user_message(body.get("messages", []))
        return _openai_non_stream_response(
            body.get("model") or "echo", f"[ECHO] {last or 'no pipeline configured'}"
        )

    result = await pipeline.run(
        message=body.get("message") or _last_user_message(body.get("messages", [])),
        chat_id=body.get("chat_id"),
        provider_id=body.get("provider") or body.get("provider_id"),
        model=body.get("model"),
        metadata={"model": body.get("model")},
    )
    assistant = result.get("assistant_message", {})
    meta = assistant.get("metadata", {}) if isinstance(assistant.get("metadata"), dict) else {}
    return _openai_non_stream_response(
        meta.get("model") or body.get("model") or "ethan",
        assistant.get("content", ""),
        request_id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
    )
