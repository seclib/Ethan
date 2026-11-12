"""Router API — Import/Export de skills (délégation Core).

Ce router expose les endpoints d'import/export de skills.
Toute la logique métier réside dans ``core.skills.store.SkillStore``.

Routes :
    GET    /skills/export   → exporte toutes les skills
    POST   /skills/import   → importe une liste de skills
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from interfaces.api.routers.v1 import get_skill_store, require_permission

router = APIRouter(tags=["skills-import"])


@router.get("/skills/export")
async def export_skills():
    """Exporte toutes les skills (portabilité, pattern Open-WebUI)."""
    store = get_skill_store()
    return await store.export_skills()


@router.post(
    "/skills/import",
    dependencies=[Depends(require_permission("plugins"))],
)
async def import_skills(data: dict[str, Any]):
    """Importe une liste de skills (validation Core, pas de secret)."""
    store = get_skill_store()
    records = data.get("skills") or []
    if not isinstance(records, list):
        raise HTTPException(422, "Le corps doit contenir une liste 'skills'.")
    return await store.import_skills(records)
