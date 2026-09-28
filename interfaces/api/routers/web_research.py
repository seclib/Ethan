"""Web Research Router — passerelle HTTP du workflow Recherche -> Knowledge.

ETHAN Core (core/knowledge/web_research_service.py) possède toute la logique :
collecte multi-moteurs, sélection bornée (plafond absolu 50 pages), aperçu
transient, import Knowledge/Collection. Ce router n'expose que des points
d'entrée HTTP.

Sécurité (cf. core/network) : aucune credential ne transite par les payloads —
uniquement des identifiants de profils réseau (`network_profile`).
"""

from __future__ import annotations

import asyncio
from typing import Any

from core.auth import Permission
from fastapi import APIRouter, Depends, HTTPException, Request
from interfaces.api.auth import current_user_id, require_permission

router = APIRouter(prefix="/v1/web-research", tags=["web-research"])

_service: Any | None = None


def set_web_research_service(service: Any | None) -> None:
    """Injecte le WebResearchService Core dans le router (appelé au startup)."""
    global _service
    _service = service


def get_web_research_service() -> Any:
    """Retourne le service global (503 si non initialisé)."""
    if _service is None:
        raise HTTPException(503, "Web research service not initialized")
    return _service


def _reject_proxy_credentials(data: dict[str, Any]) -> None:
    """Les credentials ne transitent JAMAIS par les payloads (core/network)."""
    if data.get("proxy") is not None:
        raise HTTPException(
            422,
            "'proxy' (credentials) interdit dans la requête : utilisez 'network_profile'",
        )


def _network_profile_proxy(data: dict[str, Any]) -> str | None:
    """Identifiant de profil réseau -> argument proxy du Core (str)."""
    network_profile = data.get("network_profile")
    return str(network_profile).strip() if network_profile else None


@router.get("/limits", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def limits():
    """Bornes du workflow (plafond absolu de pages par collection)."""
    service = get_web_research_service()
    return {"max_pages_per_collection": service.max_pages_per_collection}


@router.post("/collect", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def collect(data: dict[str, Any]):
    """Recherche un sujet et retourne les pages candidates dédupliquées.

    Corps attendu :
    - query (str) : sujet/requête (requis) ;
    - engines (list[str]) : moteurs à interroger (défaut : tous) ;
    - max_results_per_engine (int) : 1..50 (refus strict au-delà) ;
    - network_profile (str) : identifiant de profil réseau optionnel.
    """
    service = get_web_research_service()
    _reject_proxy_credentials(data)
    query = str(data.get("query", "")).strip()
    if not query:
        raise HTTPException(422, "'query' is required")
    engines = data.get("engines") or None
    max_results = data.get("max_results_per_engine")
    try:
        research = await asyncio.wait_for(
            service.collect(
                query,
                engines=engines,
                max_results_per_engine=max_results,
                proxy=_network_profile_proxy(data),
            ),
            timeout=90,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Recherche trop longue (>90s)") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {
        "research": research.to_dict(),
        "max_pages_per_collection": service.max_pages_per_collection,
    }


@router.post("/preview", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def preview(data: dict[str, Any]):
    """Aperçu transient d'une page candidate (scan contrôlé, non persisté).

    Corps attendu : url (str, http/https).
    """
    service = get_web_research_service()
    url = str(data.get("url", "")).strip()
    if not url:
        raise HTTPException(422, "'url' is required")
    try:
        return await asyncio.wait_for(service.preview_page(url), timeout=60)
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Aperçu trop long (>60s)") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/import-page", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def import_page(data: dict[str, Any], request: Request = None):
    """Importe **une** page comme ressource Knowledge.

    Corps attendu :
    - url (str, requis) ; title/domain/collection_name optionnels ;
    - target ("knowledge"|"collection"|"project") ; project_id si project.
    """
    service = get_web_research_service()
    url = str(data.get("url", "")).strip()
    if not url:
        raise HTTPException(422, "'url' is required")
    try:
        return await asyncio.wait_for(
            service.import_page(
                url,
                title=data.get("title"),
                domain=data.get("domain"),
                collection_name=data.get("collection_name"),
                target=data.get("target", "knowledge"),
                project_id=data.get("project_id"),
                user_id=current_user_id(request),
            ),
            timeout=120,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Import trop long (>120s)") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post(
    "/import-selection",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def import_selection(data: dict[str, Any], request: Request = None):
    """Importe une selection de pages vers la destination choisie.

    Corps attendu :
    - urls (list[str], requis, <= 50) ;
    - target (str) : "collection" (defaut) | "knowledge" | "project" ;
    - collection_name (str) : crée la collection au premier import ;
    - collection_id (str) : ajoute à une collection existante ;
    - project_id (str) : requis si target="project" (documents du projet).
    """
    service = get_web_research_service()
    urls = data.get("urls")
    if not isinstance(urls, list) or not urls:
        raise HTTPException(422, "'urls' (liste non vide) is required")
    try:
        return await asyncio.wait_for(
            service.import_selection(
                [str(u) for u in urls],
                target=data.get("target", "collection"),
                collection_name=data.get("collection_name"),
                collection_id=data.get("collection_id"),
                project_id=data.get("project_id"),
                user_id=current_user_id(request),
            ),
            timeout=300,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(504, "Import trop long (>300s)") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
