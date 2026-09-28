"""Web Search Router — passerelle HTTP du moteur de recherche web.

ETHAN Core (core/knowledge/web_search.py) possède toute la logique : recherche
multi-moteurs (DuckDuckGo, Bing, Yandex), support proxy/VPN, normalisation des
résultats. Ce router n'expose que des points d'entrée HTTP.
"""

from __future__ import annotations

from typing import Any

from core.auth import Permission
from core.knowledge.web_search import WebSearchManager
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/web-search", tags=["web-search"])

_web_search: WebSearchManager | None = None


def set_web_search_manager(manager: WebSearchManager | None) -> None:
    """Injecte le WebSearchManager Core dans le router (appelé au startup)."""
    global _web_search
    _web_search = manager


def get_web_search_manager() -> WebSearchManager:
    """Retourne le WebSearchManager global (503 si non initialisé)."""
    if _web_search is None:
        raise HTTPException(503, "Web search manager not initialized")
    return _web_search


@router.get("/engines", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def list_search_engines():
    """Liste les moteurs de recherche disponibles."""
    manager = get_web_search_manager()
    return {"engines": manager.list_engines()}


@router.get(
    "/network-profiles",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def list_network_profiles():
    """Profils réseau disponibles (vues publiques — aucun secret).

    Le Core (core/network) possède la logique ; l'API n'expose que des vues
    expurgées pour que les interfaces affichent le sélecteur de profil.
    """
    manager = get_web_search_manager()
    return {"profiles": manager.network_profiles.list_profiles()}


@router.post("/search", dependencies=[Depends(require_permission(Permission.MEMORY))])
@router.post(
    "/search/{provider:path}", dependencies=[Depends(require_permission(Permission.MEMORY))]
)
async def search_web(data: dict[str, Any]):
    """Effectue une recherche web.

    Corps attendu :
    - query (str) : termes de recherche
    - engine (str) : moteur à utiliser (duckduckgo, bing, yandex)
    - max_results (int) : nombre maximum de résultats (défaut: 10)
    - network_profile (str) : identifiant de profil réseau optionnel
      (direct | proxy/VPN enregistré côté Core) — les credentials restent
      dans le Core (variables d'environnement, cf. core/network).
    """
    manager = get_web_search_manager()

    query = data.get("query", "").strip()
    if not query:
        raise HTTPException(422, "Search query is required")

    # Profils réseau : l'API ne transmet qu'un IDENTIFIANT. Les
    # credentials restent dans le Core (variables d'environnement).
    if data.get("proxy") is not None:
        raise HTTPException(
            422,
            "'proxy' (credentials) interdit dans la requête : utilisez 'network_profile'",
        )
    network_profile = data.get("network_profile")
    proxy = str(network_profile).strip() if network_profile else None

    try:
        response = await manager.search(
            query=query,
            engine=data.get("engine", "duckduckgo"),
            max_results=data.get("max_results", 10),
            proxy=proxy,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    # Convert to dict for JSON response
    return {
        "query": response.query,
        "engine": response.engine,
        "total_found": response.total_found,
        "search_time_ms": response.search_time_ms,
        "results": [
            {
                "title": r.title,
                "url": r.url,
                "domain": r.domain,
                "snippet": r.snippet,
                "source_engine": r.source_engine,
                "rank": r.rank,
                "metadata": r.metadata,
            }
            for r in response.results
        ],
        "metadata": response.metadata,
    }


@router.post(
    "/search/multi",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def search_web_multi(data: dict[str, Any]):
    """Effectue une recherche sur plusieurs moteurs en parallèle.

    Corps attendu :
    - query (str) : termes de recherche
    - engines (list[str]) : moteurs à utiliser (défaut: tous)
    - max_results_per_engine (int) : résultats max par moteur (défaut: 5)
    - network_profile (str) : identifiant de profil réseau optionnel
      (credentials Core-only, cf. core/network)
    """
    manager = get_web_search_manager()

    query = data.get("query", "").strip()
    if not query:
        raise HTTPException(422, "Search query is required")

    # Profils réseau : identifiant seul, credentials Core-only.
    if data.get("proxy") is not None:
        raise HTTPException(
            422,
            "'proxy' (credentials) interdit dans la requête : utilisez 'network_profile'",
        )
    network_profile = data.get("network_profile")
    proxy = str(network_profile).strip() if network_profile else None

    try:
        responses = await manager.search_multiple(
            query=query,
            engines=data.get("engines"),
            max_results_per_engine=data.get("max_results_per_engine", 5),
            proxy=proxy,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    return {
        "query": query,
        "engines": {
            engine: {
                "total_found": resp.total_found,
                "search_time_ms": resp.search_time_ms,
                "results": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "domain": r.domain,
                        "snippet": r.snippet,
                        "source_engine": r.source_engine,
                        "rank": r.rank,
                    }
                    for r in resp.results
                ],
                "metadata": resp.metadata,
            }
            for engine, resp in responses.items()
        },
    }
