"""Web Inspiration Router — passerelle HTTP du moteur d'inspiration web.

ETHAN Core (core/knowledge/web_inspiration.py) possède toute la logique :
recherche multi-moteurs, crawl contrôlé, synthèse LLM. Ce router n'expose
que des points d'entrée HTTP.
"""

from __future__ import annotations

import asyncio
from typing import Any

from core.auth import Permission
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/web-inspiration", tags=["web-inspiration"])

_engine: Any | None = None


def set_web_inspiration_engine(engine: Any | None) -> None:
    """Injecte le WebInspirationEngine Core dans le router (appelé au startup)."""
    global _engine
    _engine = engine


def get_web_inspiration_engine() -> Any:
    """Retourne le moteur global (503 si non initialisé)."""
    if _engine is None:
        raise HTTPException(503, "Web inspiration engine not initialized")
    return _engine


@router.get("/status", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def status():
    return {
        "available": _engine is not None,
        "engines_required": ["duckduckgo", "bing"],
        "llm_optional": True,
    }


@router.post("/search", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def search_only(data: dict[str, Any]):
    """Recherche seule (rapide, sans crawl ni synthèse).

    Corps attendu :
    - topic (str) : thème de recherche
    - engines (list[str]) : moteurs (défaut: duckduckgo, bing)
    """
    engine = get_web_inspiration_engine()
    topic = str(data.get("topic", "")).strip()
    if not topic:
        raise HTTPException(422, "'topic' is required")
    engines = data.get("engines") or None
    try:
        return await asyncio.wait_for(engine.search_only(topic, engines=engines), timeout=60)
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Recherche trop longue (>60s)") from exc


@router.post("/inspire", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def inspire(data: dict[str, Any]):
    """Pipeline complet : recherche → crawl → synthèse LLM optionnelle.

    Corps attendu :
    - topic (str) : thème de recherche
    - engines (list[str]) : moteurs (défaut: duckduckgo, bing)
    - max_sources (int) : nombre maximal de sources crawlées (défaut: 6)
    - synthesize (bool) : activer la synthèse LLM (défaut: true si LLM dispo)
    """
    engine = get_web_inspiration_engine()
    topic = str(data.get("topic", "")).strip()
    if not topic:
        raise HTTPException(422, "'topic' is required")
    engines = data.get("engines") or None
    max_sources = int(data.get("max_sources", 6))
    synthesize = bool(data.get("synthesize", True))
    try:
        # Le pipeline (recherche + crawls + LLM) peut être long : garde-fou 180 s.
        return await asyncio.wait_for(
            engine.inspire(
                topic,
                engines=engines,
                max_sources=max_sources,
                synthesize=synthesize,
            ),
            timeout=180,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Inspiration trop longue (>180s)") from exc
