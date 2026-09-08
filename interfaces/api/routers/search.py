"""Search Router — unified search across ETHAN domains.

The Core owns search logic. This router only delegates to SearchManager.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import Permission
from core.search import SearchManager
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

_search_manager: SearchManager | None = None


def set_search_manager(manager: SearchManager) -> None:
    global _search_manager
    _search_manager = manager


def get_search_manager() -> SearchManager:
    if _search_manager is None:
        raise HTTPException(503, "Search manager not initialized")
    return _search_manager


@router.get("", dependencies=[Depends(require_permission(Permission.READ))])
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str = Query("knowledge", description="Search type: web, knowledge, library, conversation"),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Run a search across the specified domain."""
    manager = get_search_manager()
    return await manager.search(q, search_type=type, limit=limit)


@router.get("/types", dependencies=[Depends(require_permission(Permission.READ))])
async def list_search_types() -> dict[str, Any]:
    """List available search types."""
    from core.search import SEARCH_TYPES
    return {"types": list(SEARCH_TYPES)}
