"""Web Skill Draft Router — passerelle HTTP des brouillons de Skill (web).

ETHAN Core (core/skills/web_draft.py) possède toute la logique : récupération
contrôlée des sources (scan Core), synthèse LLM best-effort, brouillon
structuré. Ce router n'expose que des points d'entrée HTTP.

Sécurité : ce router n'écrit JAMAIS dans le SkillStore. La création de la
Skill passe par le système existant (``POST /v1/skills``) sur validation
humaine, avec ``is_active=False`` et les URLs conservées dans ``meta``.
"""

from __future__ import annotations

import asyncio
from typing import Any

from core.auth import Permission
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/web-skill-draft", tags=["web-skill-draft"])

_service: Any | None = None


def set_web_skill_draft_service(service: Any | None) -> None:
    """Injecte le WebSkillDraftService Core dans le router (startup)."""
    global _service
    _service = service


def get_web_skill_draft_service() -> Any:
    """Retourne le service global (503 si non initialisé)."""
    if _service is None:
        raise HTTPException(503, "Web skill draft service not initialized")
    return _service


@router.get("/limits", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def limits():
    """Bornes du workflow (plafond absolu de sources par brouillon)."""
    service = get_web_skill_draft_service()
    return {"max_sources": service.max_sources}


@router.post("/draft", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def draft_skill(data: dict[str, Any]):
    """Génère un **brouillon** de Skill depuis des sources web sélectionnées.

    Corps attendu :
    - topic (str) : sujet de la recherche (requis) ;
    - sources (list) : 1..50 entrées ``{url, title?, snippet?, domain?}``
      (ou URLs brutes) — plafond absolu 50 ;
    - use_llm (bool) : tenter la synthèse LLM (défaut : true ; repli
      déterministe sinon).

    La réponse est un brouillon (``is_active=False``) avec les sources
    utilisées : la création effective relève de la validation humaine via
    ``POST /v1/skills`` (système de Skills existant).
    """
    service = get_web_skill_draft_service()
    topic = str(data.get("topic", "")).strip()
    if not topic:
        raise HTTPException(422, "'topic' is required")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise HTTPException(422, "'sources' (liste non vide) is required")
    use_llm = bool(data.get("use_llm", True))
    try:
        draft = await asyncio.wait_for(
            service.draft(topic, sources, use_llm=use_llm),
            timeout=240,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Génération trop longue (>240s)") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return draft.to_dict()
