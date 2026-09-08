"""Web Ingest Router — passerelle HTTP du pipeline d'ingestion web.

ETHAN Core (core/knowledge/web_ingest.py) possède toute la logique : scan
contrôlé (robots.txt, SSRF, bornes), preview transient, indexation après
validation utilisateur.  Ce router n'expose que des points d'entrée HTTP et
propage les ValueError du Core en 422.
"""

from __future__ import annotations

from typing import Any

from core.auth import Permission
from core.knowledge.web_ingest import WebIngestionManager
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/web-ingest", tags=["web-ingest"])

_web_ingest: WebIngestionManager | None = None


def set_web_ingest_manager(manager: WebIngestionManager | None) -> None:
    """Injecte le WebIngestionManager Core dans le router (appelé au startup)."""
    global _web_ingest
    _web_ingest = manager


def get_web_ingest_manager() -> WebIngestionManager:
    """Retourne le WebIngestionManager global (503 si non initialisé)."""
    if _web_ingest is None:
        raise HTTPException(503, "Web ingestion manager not initialized")
    return _web_ingest


@router.post("/scan", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def scan_web(data: dict[str, Any]):
    """Scan contrôlé d'une URL → preview des pages découvertes.

    Aucune indexation à ce stade : la réponse est un preview transient
    (scan_id + pages : titre, extrait, statut, déduplication).  L'utilisateur
    doit ensuite valider via POST /ingest.
    """
    manager = get_web_ingest_manager()
    try:
        return await manager.scan(
            data.get("url", ""),
            max_pages=data.get("max_pages", 10),
            max_depth=data.get("max_depth", 2),
            use_sitemap=bool(data.get("use_sitemap", True)),
            include_patterns=data.get("include_patterns"),
            exclude_patterns=data.get("exclude_patterns"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/scans/{scan_id}", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def get_web_scan(scan_id: str):
    """Preview d'un scan (re-affichage) ; 404 si inconnu ou expiré."""
    manager = get_web_ingest_manager()
    scan = manager.get_scan(scan_id)
    if scan is None:
        raise HTTPException(404, f"Scan {scan_id} not found or expired")
    return scan


@router.post("/ingest", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def ingest_web(data: dict[str, Any]):
    """Indexe les pages sélectionnées après validation utilisateur.

    Corps attendu : scan_id, page_ids, folder_id OU new_folder_name,
    target ("collection"|"knowledge"), collection_id OU new_collection_name,
    retrieval_strategy (stratégie RAG de la collection), embedding_model.
    """
    manager = get_web_ingest_manager()
    try:
        return await manager.ingest(
            data.get("scan_id", ""),
            list(data.get("page_ids") or []),
            folder_id=data.get("folder_id"),
            new_folder_name=data.get("new_folder_name"),
            target=data.get("target", "collection"),
            collection_id=data.get("collection_id"),
            new_collection_name=data.get("new_collection_name"),
            retrieval_strategy=data.get("retrieval_strategy"),
            embedding_model=data.get("embedding_model"),
            user_id=data.get("user_id", "anonymous"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
