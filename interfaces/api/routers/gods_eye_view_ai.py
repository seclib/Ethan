"""God's Eye View AI — adaptateur d'inference serveur (ETHAN Core owner).

Expose l'inference reelle d'ETHAN au service God's Eye View :

- ``GET  /ai/capabilities`` : fonctions compatibles + limitations.
- ``GET  /ai/config`` : configuration plugin (modele, limites).
- ``PUT  /ai/config`` : selection agent/modele autorise (PLUGINS).
- ``POST /ai/provision`` : jeton d'agent bref, portee restreinte.
- ``POST /ai/chat`` : chat OpenAI-compatible (non-stream + SSE).
- ``POST /ai/hud-summary`` : resume HUD 5 mots via inference ETHAN.
- ``POST /ai/tools/validate`` : validation serveur d'une action IA.

AGENTS.md : aucune logique metier ici, aucun secret expose,
voix Realtime non portable -> repli texte signale.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import timedelta
from typing import Any

from core.auth import Permission, rbac
from core.llm.types import ChatMessage, LLMRequirements
from core.plugins.gods_eye_view_prompts import (
    HUD_SUMMARY_WORD_COUNT,
    HUD_SYSTEM_PROMPT,
    truncate_to_words,
)
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from interfaces.api.auth import (
    create_access_token,
    require_permission,
    verify_token_string,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/plugins/gods-eye-view/ai",
    tags=["gods-eye-view-ai"],
)

_manager = None  # ProviderManager injecte au startup (pattern providers.py).


def set_provider_manager(manager) -> None:
    """Injecte le ProviderManager (appele au startup)."""
    global _manager
    _manager = manager


def get_manager():
    """Retourne le ProviderManager (503 s'il n'est pas initialise)."""
    if _manager is None:
        raise HTTPException(
            status_code=503, detail="Provider manager not initialized"
        )
    return _manager


AI_SCOPE = "plugins:gods-eye-view-ai"
AI_TOKEN_TTL_SECONDS = 3600
HUD_TIMEOUT_SECONDS = 30.0
MAX_CONTEXT_CHARS = 8000
MAX_MESSAGES = 50

# Le prompt HUD est propriete du Core (core/plugins/gods_eye_view_prompts.py) :
# source unique partagee avec GEV, jamais redefinie ici.

# Etapes 1-2 : cartographie GEV -> ETHAN.
AI_FUNCTIONS_MAP = [
    {"function": "hud_summary", "compatible": True,
     "ethan": "POST ai/hud-summary", "adapter": "chat"},
    {"function": "entity_questions", "compatible": True,
     "ethan": "POST ai/chat", "adapter": "chat"},
    {"function": "voice_commands_text", "compatible": True,
     "ethan": "POST ai/chat", "adapter": "chat"},
    {"function": "context_analysis", "compatible": True,
     "ethan": "POST ai/chat", "adapter": "chat"},
    {"function": "tool_actions", "compatible": True,
     "ethan": "POST ai/tools/validate", "adapter": "validation"},
    {"function": "realtime_voice_audio", "compatible": False,
     "ethan": None, "adapter": "fallback",
     "notes": "WebRTC OpenAI non portable -> repli texte."},
]

ALLOWED_TOOL_NAMES = frozenset({
    "fly_to_location", "select_nearest_aircraft", "adjust_camera_zoom",
    "zoom_to_globe", "set_layer_visibility", "show_data_layers_menu",
    "set_visual_style", "set_post_processing", "set_hud", "set_map_stack",
    "set_panel_open", "set_context_mode", "get_entity_context",
    "get_current_view_state", "track_entity", "stop_tracking",
    "move_camera", "fly_route", "frame_overhead", "annotate_map",
    "clear_annotations", "analyst_query", "control_cctv", "control_radio",
    "control_cockpit", "control_scene", "set_cyber_sonar", "set_detection",
    "next_satellite_pass", "next_iss_pass",
})

_gev_ai_config: dict[str, Any] = {
    "default_model": None,
    "default_provider": None,
    "context_limit": 8000,
    "timeout_seconds": 60,
}


def get_gev_config() -> dict[str, Any]:
    """Retourne la config IA GEV (copie, jamais de secret)."""
    return dict(_gev_ai_config)


def set_gev_config(config: dict[str, Any]) -> None:
    """Met a jour la config IA GEV (sans secret, sans toucher global)."""
    if not isinstance(config, dict):
        return
    for key in ("default_model", "default_provider",
                "context_limit", "timeout_seconds"):
        if config.get(key) is not None:
            _gev_ai_config[key] = config[key]


def _to_chat_messages(messages: list[dict[str, Any]]) -> list[ChatMessage]:
    """Convertit des messages OpenAI-style en ChatMessage ETHAN."""
    out: list[ChatMessage] = []
    for msg in messages or []:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "user")
        content = msg.get("content")
        if content is None and isinstance(msg.get("parts"), list):
            content = " ".join(str(p) for p in msg["parts"])
        if not isinstance(content, str):
            try:
                content = json.dumps(content)
            except (TypeError, ValueError):
                content = str(content)
        out.append(ChatMessage(
            role=role, content=content, name=msg.get("name"),
            tool_calls=msg.get("tool_calls"),
            tool_call_id=msg.get("tool_call_id"),
        ))
    return out


def _truncate_messages(
    messages: list[ChatMessage], limit: int | None
) -> list[ChatMessage]:
    """Tronque le contexte (limite caracteres, garde system + recent)."""
    cap = int(limit or MAX_CONTEXT_CHARS)
    cap = max(256, min(cap, 100000))
    total = sum(len(m.content or "") for m in messages)
    if total <= cap:
        return messages[-MAX_MESSAGES:]
    kept = [m for m in messages if m.role == "system"]
    rest = [m for m in messages if m.role != "system"]
    rest = rest[-MAX_MESSAGES:]
    budget = cap - sum(len(m.content or "") for m in kept)
    out: list[ChatMessage] = []
    for m in reversed(rest):
        size = len(m.content or "")
        if budget - size < 0 and out:
            break
        budget -= size
        out.append(m)
    return kept + list(reversed(out))


def _openai_chunk(cid: str, created: int, model: str,
                  delta: dict, finish: str | None = None) -> str:
    choice = {"index": 0, "delta": delta, "finish_reason": finish}
    payload = {"id": cid, "object": "chat.completion.chunk",
               "created": created, "model": model, "choices": [choice]}
    return f"data: {json.dumps(payload)}\n\n"


def _openai_response(model: str, content: str) -> JSONResponse:
    payload = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0,
                     "message": {"role": "assistant", "content": content},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0,
                  "total_tokens": 0},
    }
    return JSONResponse(payload)


def _sanitize_error(exc: Exception) -> str:
    """Message d'erreur sanitise (jamais de secret ni d'URL interne)."""
    text = str(exc) if str(exc) else "inference failed"
    for token in ("Bearer ", "api_key", "apikey", "sk-"):
        if token in text:
            text = text.split(token)[0] + token + "***"
    return text[:300]


def _five_words(text: str) -> str:
    """Normalise la sortie du modele en cinq mots (source : Core)."""
    return truncate_to_words(text, HUD_SUMMARY_WORD_COUNT)


async def _verify_ai_token(request: Request) -> dict[str, Any]:
    """Verifie JWT ou cle API : scope GEV-AI (provision) ou role autorise."""
    header = request.headers.get("Authorization", "")
    token = None
    if header.startswith("Bearer "):
        token = header[len("Bearer "):].strip()
    if not token:
        token = request.cookies.get("gevs_ai_token")
    api_key = request.headers.get("X-API-Key")
    if token and token.startswith("ethan_"):
        api_key = token
        token = None

    if not token and not api_key:
        raise HTTPException(status_code=401,
                            detail="Authentification AI requise.")

    # Cle API server-to-server (ex. GEV)
    if api_key and not token:
        from interfaces.api.auth import get_api_key_manager

        manager = get_api_key_manager()
        if manager is None:
            raise HTTPException(status_code=503,
                                detail="API key manager not initialized.")
        try:
            key = await manager.validate_key(api_key, require_scopes=[AI_SCOPE])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cle API AI invalide: %s", exc)
            key = None
        if key is None:
            raise HTTPException(status_code=401,
                                detail="Cle API invalide ou portee insuffisante.")
        scopes = list(key.get("scopes") or [])
        return {"sub": key.get("user_id"), "role": "api-key",
                "scope": scopes, "scopes": scopes}

    try:
        payload = await verify_token_string(token)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Token AI invalide: %s", exc)
        raise HTTPException(status_code=401,
                            detail="Token d'agent invalide.") from None
    scopes = payload.get("scope") or payload.get("scopes") or []
    if isinstance(scopes, str):
        scopes = [scopes]
    if AI_SCOPE in scopes:
        return payload
    role = payload.get("role")
    if role and (rbac.has_permission(role, Permission.GODS_EYE_AI)
                 or rbac.has_permission(role, Permission.ADMIN)):
        return payload
    raise HTTPException(status_code=403,
                        detail="Acces refuse : portee AI GEV requise.")


async def _resolve_chat(messages: list[ChatMessage],
                        model: str | None,
                        provider: str | None,
                        context_limit: int | None):
    """Resout (provider, model_id) puis appelle le chat ETHAN."""
    manager = get_manager()
    timeout = float((_gev_ai_config.get("timeout_seconds") or 60) or 60)
    timeout = max(5.0, min(timeout, 300.0))

    async def _with_timeout(coro):
        return await asyncio.wait_for(coro, timeout=timeout)

    if model:
        models = await _with_timeout(manager.list_models())
        match = next((m for m in models if m.id == model), None)
        if match is None:
            raise HTTPException(
                status_code=404,
                detail=f"Modele `{model}` introuvable parmi les "
                       f"modeles ETHAN autorises.")
        req = LLMRequirements(task_type="chat",
                              preferred_providers=[match.provider])
        if context_limit:
            req.context_length = max(int(context_limit), 256)
        try:
            return await _with_timeout(manager.chat(messages, req))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Inference ETHAN indisponible : "
                       + _sanitize_error(exc)) from None
    req = LLMRequirements(task_type="chat")
    if provider:
        req.preferred_providers = [provider]
    if context_limit:
        req.context_length = max(int(context_limit), 256)
    try:
        return await _with_timeout(manager.chat(messages, req))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Inference ETHAN indisponible : "
                   + _sanitize_error(exc)) from None


@router.get("/capabilities")
async def get_capabilities(
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    """Fonctions IA compatibles + limitations (etape 3)."""
    return {
        "functions": AI_FUNCTIONS_MAP,
        "realtime_voice": {
            "compatible": False,
            "fallback": "POST ai/chat (texte)",
            "reason": "WebRTC OpenAI non portable multi-provider.",
        },
    }


@router.get("/config")
async def get_config(
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    """Configuration plugin (jamais de secret)."""
    cfg = get_gev_config()
    models: list[dict[str, Any]] = []
    try:
        listed = await get_manager().list_models()
        models = [{"id": m.id, "provider": m.provider,
                   "name": m.name} for m in listed]
    except Exception as exc:
        logger.warning("List modeles GEV-AI echoue: %s", exc)
    allowed = [m for m in models if "embed" not in m["id"].lower()]
    return {"config": cfg, "allowed_models": allowed,
            "voice_fallback": "texte via ai/chat"}


@router.put("/config",
            dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def update_config(body: dict[str, Any]) -> dict[str, Any]:
    """Selection agent/modele autorise (etape 5)."""
    body = body or {}
    model = body.get("default_model")
    provider = body.get("default_provider")
    manager = get_manager()
    if model:
        models = await manager.list_models()
        if not any(m.id == model for m in models):
            raise HTTPException(
                status_code=404,
                detail=f"Modele `{model}` introuvable.")
    if provider:
        providers = await manager.list_providers()
        ids = {p.get("id") if isinstance(p, dict) else p
               for p in providers}
        if provider not in ids:
            raise HTTPException(
                status_code=404,
                detail=f"Provider `{provider}` introuvable.")
    patch: dict[str, Any] = {}
    if model is not None:
        patch["default_model"] = model
    if provider is not None:
        patch["default_provider"] = provider
    if body.get("context_limit") is not None:
        try:
            patch["context_limit"] = max(
                256, min(int(body["context_limit"]), 100000))
        except (TypeError, ValueError):
            raise HTTPException(status_code=422,
                                detail="context_limit entier requis.")
    if body.get("timeout_seconds") is not None:
        try:
            patch["timeout_seconds"] = max(
                5.0, min(float(body["timeout_seconds"]), 300.0))
        except (TypeError, ValueError):
            raise HTTPException(status_code=422,
                                detail="timeout_seconds nombre requis.")
    set_gev_config(patch)
    return {"config": get_gev_config()}


@router.post("/provision",
             dependencies=[Depends(require_permission(Permission.ADMIN))])
async def provision_ai_token() -> dict[str, Any]:
    """Jeton d'agent bref, portee restreinte (serveur GEV, jamais browser)."""
    now = int(time.time())
    payload = {
        "sub": "gevs-ai",
        "role": "gevs-ai",
        "gevs_plugin_id": "gods-eye-view",
        "purpose": "gods-eye-view:ai",
        "scope": [AI_SCOPE],
        "iat": now,
        "exp": now + AI_TOKEN_TTL_SECONDS,
    }
    token = create_access_token(
        payload, expires_delta=timedelta(seconds=AI_TOKEN_TTL_SECONDS))
    return {"token": token, "expires_in": AI_TOKEN_TTL_SECONDS,
            "scopes": [AI_SCOPE]}


@router.post("/chat")
async def chat(request: Request) -> JSONResponse:
    """Chat OpenAI-compatible non-streaming (et SSE si stream=true)."""
    await _verify_ai_token(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    body = body or {}
    raw = body.get("messages", [])
    if not isinstance(raw, list) or not raw:
        raise HTTPException(status_code=422,
                            detail="messages non vide requis.")
    cfg = get_gev_config()
    model = body.get("model") or cfg.get("default_model")
    provider = body.get("provider") or cfg.get("default_provider")
    limit = body.get("context_limit") or cfg.get("context_limit")
    try:
        limit = int(limit) if limit else None
    except (TypeError, ValueError):
        limit = None
    messages = _truncate_messages(_to_chat_messages(raw), limit)
    if not messages:
        raise HTTPException(status_code=422,
                            detail="messages inexploitables.")
    if body.get("stream"):
        return await _chat_sse(messages, model, provider, limit)
    result = await _resolve_chat(messages, model, provider, limit)
    content = (result.content or "") if result else ""
    return _openai_response(
        model or getattr(result, "model", "") or "ethan", content)

async def _chat_sse(messages: list[ChatMessage],
                    model: str | None,
                    provider: str | None,
                    limit: int | None) -> StreamingResponse:
    """SSE OpenAI-compatible via manager.chat_stream (meme selection)."""
    manager = get_manager()
    cid = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())
    out_model = model or provider or "ethan"
    timeout = float((_gev_ai_config.get("timeout_seconds") or 60) or 60)
    timeout = max(5.0, min(timeout, 300.0))

    async def _gen():
        yield _openai_chunk(cid, created, out_model, {"role": "assistant"})
        try:
            if model:
                models = await manager.list_models()
                match = next((m for m in models if m.id == model), None)
                if match is None:
                    raise HTTPException(status_code=404,
                                        detail=f"Modele `{model}` "
                                               f"introuvable.")
                req = LLMRequirements(task_type="chat",
                                      preferred_providers=[match.provider])
            else:
                req = LLMRequirements(task_type="chat")
                if provider:
                    req.preferred_providers = [provider]
            if limit:
                req.context_length = max(int(limit), 256)
            agen = manager.chat_stream(messages, req)
            while True:
                try:
                    piece = await asyncio.wait_for(
                        agen.__anext__(), timeout=timeout)
                except StopAsyncIteration:
                    break
                if piece:
                    yield _openai_chunk(cid, created, out_model,
                                        {"content": piece})
        except HTTPException as exc:
            yield f"data: {json.dumps({'error': exc.detail})}\n\n"
            yield "data: [DONE]\n\n"
            return
        except Exception as exc:
            logger.exception("SSE GEV-AI echoue: %s", exc)
            yield f"data: {json.dumps({'error': _sanitize_error(exc)})}\n\n"
        yield _openai_chunk(cid, created, out_model, {}, finish="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "Connection": "keep-alive",
                                      "X-Accel-Buffering": "no"})


@router.post("/hud-summary")
async def hud_summary(request: Request) -> dict[str, Any]:
    """Resume HUD 5 mots via inference ETHAN (prompt d'origine conserve)."""
    await _verify_ai_token(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    body = body or {}
    cfg = get_gev_config()
    context_json = json.dumps(body, ensure_ascii=False)[:MAX_CONTEXT_CHARS]
    messages = [ChatMessage(role="system", content=HUD_SYSTEM_PROMPT),
                ChatMessage(role="user", content=context_json)]
    timeout = min(HUD_TIMEOUT_SECONDS,
                  float(cfg.get("timeout_seconds") or HUD_TIMEOUT_SECONDS))
    try:
        result = await asyncio.wait_for(
            _resolve_chat(messages, cfg.get("default_model"),
                          cfg.get("default_provider"),
                          cfg.get("context_limit")),
            timeout=timeout)
    except (asyncio.TimeoutError, HTTPException) as exc:
        detail = getattr(exc, "detail", "delai inference depasse")
        raise HTTPException(status_code=502,
                            detail=f"HUD summary indisponible : "
                                   f"{detail}")
    summary = _five_words(getattr(result, "content", "") or "")
    if not summary:
        raise HTTPException(status_code=502,
                            detail="HUD summary vide de l'inference.")
    return {"summary": summary, "error": None,
            "model": getattr(result, "model", "") or "ethan"}


@router.post("/tools/validate")
async def validate_tool(request: Request) -> dict[str, Any]:
    """Validation serveur d'une action IA (etape 10, jamais auto-exec)."""
    await _verify_ai_token(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    body = body or {}
    name = body.get("name")
    args = body.get("arguments", {})
    if not isinstance(name, str) or name not in ALLOWED_TOOL_NAMES:
        raise HTTPException(status_code=403,
                            detail=f"Outil `{name}` non autorise.")
    if not isinstance(args, dict):
        raise HTTPException(status_code=422,
                            detail="arguments objet requis.")
    if len(json.dumps(args, ensure_ascii=False)) > 8000:
        raise HTTPException(status_code=422,
                            detail="arguments trop volumineux.")
    from datetime import datetime, timezone
    return {"ok": True, "name": name, "arguments": args,
            "requires_explicit_approval": True,
            "validated_at": datetime.now(timezone.utc).isoformat()}


__all__ = [
    "router",
    "set_provider_manager",
    "get_manager",
    "get_gev_config",
    "set_gev_config",
    "ALLOWED_TOOL_NAMES",
    "AI_FUNCTIONS_MAP",
    "AI_SCOPE",
    "HUD_SYSTEM_PROMPT",
    "HUD_SUMMARY_WORD_COUNT",
]

