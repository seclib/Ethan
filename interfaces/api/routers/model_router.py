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
from typing import Any

from core.llm.router import LLMRouter
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/model-routers", tags=["model-routers"])

_router_instance = LLMRouter()


def get_router() -> LLMRouter:
    return _router_instance


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

    try:
        first_attempt = get_router().route(task=task, available_models=available_models)
        fallback_used = first_attempt == "unknown"

        if fallback_used and task != "fast":
            fallback_result = get_router().route(task="fast", available_models=available_models)
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
