"""Deep Research API — thin binding over core.research.engine. RFC-0002."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/research", tags=["research"])

_engine: Any | None = None


def set_research_engine(engine: Any) -> None:
    global _engine
    _engine = engine


@router.post("")
@router.post("/")
async def run_research(data: dict):
    if _engine is None:
        raise HTTPException(503, "Research engine not initialized")
    query = str(data.get("query", "")).strip()
    if not query:
        raise HTTPException(422, "'query' is required")
    depth = int(data.get("depth", 2))
    try:
        # Le pipeline LLM+recherche peut prendre ~1-2 min : garde-fou à 180 s.
        return await asyncio.wait_for(_engine.run(query, depth=depth), timeout=180)
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Recherche trop longue (>180s), réduisez la profondeur") from exc


@router.get("/status")
async def research_status():
    return {
        "available": _engine is not None,
        "llm_required": True,
        "tool_required": "builtin_web_search",
    }