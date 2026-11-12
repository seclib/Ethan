"""Tests API — routes /v1/web-search.

Valide le contrat HTTP (Core-only : le routeur ne contient aucune logique) :
- 422 si ``max_results`` est manquant, invalide ou > MAX_RESULTS_HARD_CAP (50) ;
- le plafond de 50 est accepte et applique ;
- chaque resultat renvoie le ``domain`` normalise ;
- le catalogue des moteurs est expose.
"""

from __future__ import annotations

import asyncio

import pytest
from core.knowledge.web_search import MAX_RESULTS_HARD_CAP, WebSearchManager
from fastapi import HTTPException
from interfaces.api.routers import web_search as routes

HOST = "https://docs.example.com"


def _seed(manager: WebSearchManager) -> None:
    async def _fake(query, max_results, proxy):
        return [
            {"title": "ETHAN docs", "url": f"{HOST}/", "snippet": "doc"},
            {"title": "Other", "url": "https://other.example.com/x", "snippet": "x"},
        ]

    manager._search_duckduckgo = _fake  # type: ignore[method-assign]


@pytest.fixture
def search_manager():
    manager = WebSearchManager()
    _seed(manager)
    routes.set_web_search_manager(manager)
    yield manager
    routes.set_web_search_manager(None)


def test_engines_route_lists_catalog(search_manager):  # noqa: ARG001
    resp = asyncio.run(routes.list_search_engines())
    assert {"id": "duckduckgo", "label": "DuckDuckGo"} in resp["engines"]


def test_search_returns_domain_and_metadata(search_manager):  # noqa: ARG001
    resp = asyncio.run(
        routes.search_web({"query": "ethan", "engine": "duckduckgo", "max_results": 5})
    )
    assert resp["total_found"] == 2
    first = resp["results"][0]
    assert first["domain"] == "docs.example.com"
    assert first["title"] == "ETHAN docs"
    assert "metadata" in first and "source_engine" in first


def test_search_accepts_limit_50(search_manager):
    async def _many(query, max_results, proxy):
        return [{"title": f"R{i}", "url": f"https://e{i}.example.com"} for i in range(60)]

    search_manager._search_duckduckgo = _many  # type: ignore[method-assign]
    resp = asyncio.run(routes.search_web({"query": "ethan", "max_results": MAX_RESULTS_HARD_CAP}))
    assert resp["total_found"] == MAX_RESULTS_HARD_CAP


def test_search_rejects_max_above_cap_422(search_manager):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.search_web({"query": "ethan", "max_results": MAX_RESULTS_HARD_CAP + 1}))
    assert exc.value.status_code == 422


def test_search_rejects_invalid_max_422(search_manager):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.search_web({"query": "ethan", "max_results": "abc"}))
    assert exc.value.status_code == 422


def test_search_rejects_zero_max_422(search_manager):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.search_web({"query": "ethan", "max_results": 0}))
    assert exc.value.status_code == 422


def test_search_multi_returns_domain(search_manager):  # noqa: ARG001
    resp = asyncio.run(
        routes.search_web_multi(
            {"query": "ethan", "engines": ["duckduckgo"], "max_results_per_engine": 5}
        )
    )
    assert "duckduckgo" in resp["engines"]
    assert resp["engines"]["duckduckgo"]["total_found"] == 2
    assert resp["engines"]["duckduckgo"]["results"][0]["domain"] == "docs.example.com"


def test_search_multi_rejects_over_cap_422(search_manager):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            routes.search_web_multi(
                {"query": "ethan", "max_results_per_engine": MAX_RESULTS_HARD_CAP + 1}
            )
        )
    assert exc.value.status_code == 422
