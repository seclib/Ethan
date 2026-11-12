"""Router API - Model Router (routing LLM).

Expose les regles de selection de modeles pour les interfaces.

Routes:
  GET    /model-routers            -> liste des categories de routing
  POST   /model-routers/route      -> route un modele pour une tache donnee

Le Model Router est gere par Core (core/llm/router.py) et est la source de
verite unique pour les regles de selection. Les interfaces ne dupliquent
jamais ces regles.
"""

from __future__ import annotations

import logging
from dataclasses import fields
from typing import Any

from core.llm.router import LLMRouter
from core.llm.types import ModelInfo
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/model-routers", tags=["model-routers"])

_router_instance = LLMRouter()


def get_router() -> LLMRouter:
    return _router_instance


def _to_model_info(raw: dict[str, Any]) -> ModelInfo:
    """Désérialise un modèle JSON en `ModelInfo` (type du routeur Core).

    Les champs absents ou de type inattendu retombent sur les valeurs par
    défaut du dataclass : le routeur ne doit jamais échouer sur une charge
    utile partielle.
    """
    known = {f.name for f in fields(ModelInfo)}

    def _int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _bool(value: Any, default: bool) -> bool:
        return value if isinstance(value, bool) else default

    payload: dict[str, Any] = {key: value for key, value in raw.items() if key in known}
    payload["id"] = str(raw.get("id") or raw.get("model") or raw.get("name") or "")
    payload["provider"] = str(raw.get("provider") or "")
    payload["name"] = str(raw.get("name") or raw.get("model") or raw.get("id") or "")
    payload["model"] = str(raw.get("model") or raw.get("id") or payload["name"])
    payload["context_length"] = _int(raw.get("context_length"), 4096)
    payload["quality_score"] = _float(raw.get("quality_score"), 0.8)
    payload["avg_latency_ms"] = _float(raw.get("avg_latency_ms"), 1000.0)
    payload["is_local"] = _bool(raw.get("is_local"), False)
    payload["is_private"] = _bool(raw.get("is_private"), False)
    payload["is_available"] = _bool(raw.get("is_available"), True)
    capabilities = raw.get("capabilities")
    payload["capabilities"] = (
        [str(item) for item in capabilities] if isinstance(capabilities, list) else []
    )
    pricing = raw.get("pricing")
    payload["pricing"] = pricing if isinstance(pricing, dict) else None
    metadata = raw.get("metadata")
    payload["metadata"] = metadata if isinstance(metadata, dict) else {}
    return ModelInfo(**payload)


@router.get("")
async def list_model_router_categories():
    """Liste les categories de routing disponibles."""
    return {
        "categories": sorted(get_router().list_categories()),
        "description": "Categories de taches prises en charge par le router",
    }


@router.post("/route")
async def route_model_for_task(payload: dict[str, Any]):
    """Route un modele pour une tache donnee."""
    task = payload.get("task")
    available_models = payload.get("available_models", [])

    if not task:
        raise HTTPException(status_code=400, detail="field 'task' is required")

    if not available_models:
        return {
            "task": task,
            "selected_model_id": None,
            "selected_model_name": None,
            "score": None,
            "fallback_used": False,
            "reasoning": "No available models",
        }

    # Les modèles arrivent en JSON (dicts) : on les désérialise en ModelInfo,
    # le type que le routeur du Core attend. Sans cette conversion, tout
    # appelant HTTP de cette route échouait sur un AttributeError.
    models = [_to_model_info(item) for item in available_models if isinstance(item, dict)]
    if not models:
        return {
            "task": task,
            "selected_model_id": None,
            "selected_model_name": None,
            "score": None,
            "fallback_used": False,
            "reasoning": "No available models",
        }

    try:
        first_attempt = get_router().route(task=task, available_models=models)
        fallback_used = first_attempt == "unknown"

        if fallback_used and task != "fast":
            fallback_result = get_router().route(task="fast", available_models=models)
            selected_model = fallback_result if fallback_result != "unknown" else None
        else:
            selected_model = first_attempt

        return {
            "task": task,
            "selected_model_name": selected_model if selected_model != "unknown" else None,
            "score": None,
            "fallback_used": fallback_used,
            "reasoning": (
                f"Model selected for '{task}'" if first_attempt != "unknown" else "No model matched"
            ),
        }
    except Exception as exc:
        logger.exception("Model router route failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Routing failed: {exc}")
