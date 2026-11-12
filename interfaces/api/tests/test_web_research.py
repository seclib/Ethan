"""Tests API — routes /v1/web-research.

Valide le contrat HTTP (Core-only : le routeur ne contient aucune logique) :
- collect : pages dédupliquées + plafond 50 (422 strict au-delà) ;
- network_profile : identifiant transmis au Core, credentials interdits ;
- preview / import-page / import-selection (création + ajout à une collection).
"""

from __future__ import annotations

import asyncio

import pytest
from core.knowledge.web_research_service import WebResearchService
from core.knowledge.web_search import WebSearchManager
from fastapi import HTTPException
from interfaces.api.routers import web_research as routes

HOST = "https://docs.example.com"


class _FakeIngest:
    """WebIngestionManager minimal (scan + ingest, comportement déterministe)."""

    def __init__(self) -> None:
        self.ingest_calls: list[dict] = []

    async def scan(self, url: str, **_kwargs):
        return {
            "scan_id": "scan-1",
            "pages": [{"page_id": "p1", "url": url, "title": "T", "status": "ok", "text": "x"}],
            "errors": [],
        }

    async def ingest(self, *, scan_id: str, page_ids: list, **kwargs):
        self.ingest_calls.append({"scan_id": scan_id, "page_ids": page_ids, **kwargs})
        collection = None
        if kwargs.get("target") == "collection":
            collection = {
                "id": kwargs.get("collection_id") or "col-1",
                "name": kwargs.get("new_collection_name") or "collection",
            }
        return {
            "indexed": [{"id": f"k-{i}"} for i, _ in enumerate(page_ids)],
            "indexed_count": len(page_ids),
            "collection": collection,
        }


def _service() -> tuple[WebResearchService, WebSearchManager, _FakeIngest]:
    search = WebSearchManager()

    async def _fake(query, max_results, proxy):
        return [
            {"title": "ETHAN docs", "url": f"{HOST}/", "snippet": "doc"},
            {"title": "Other", "url": "https://other.example.com/x", "snippet": "x"},
        ]

    search._search_duckduckgo = _fake  # type: ignore[method-assign]
    ingest = _FakeIngest()
    return WebResearchService(search, ingest), search, ingest


@pytest.fixture
def research_service():
    service, search, ingest = _service()
    routes.set_web_research_service(service)
    yield service
    routes.set_web_research_service(None)


def test_limits_expose_cap(research_service):  # noqa: ARG001
    resp = asyncio.run(routes.limits())
    assert resp["max_pages_per_collection"] == 50


def test_collect_returns_deduped_pages(research_service):  # noqa: ARG001
    resp = asyncio.run(
        routes.collect({"query": "ethan", "engines": ["duckduckgo"], "max_results_per_engine": 10})
    )
    assert resp["max_pages_per_collection"] == 50
    research = resp["research"]
    assert research["total_found"] == 2
    assert {p["domain"] for p in research["results"]} == {
        "docs.example.com",
        "other.example.com",
    }
    assert "metadata" in research["results"][0]


def test_collect_forwards_network_profile(research_service):  # noqa: ARG001
    captured: dict = {}

    from core.network import NetworkProfile

    research_service._web_search.network_profiles.register(
        NetworkProfile(id="corpo-proxy", type="socks5", host="proxy.corp", port=1080)
    )

    async def _spy(query, max_results, proxy):
        captured["proxy"] = proxy
        return []

    research_service._web_search._search_duckduckgo = _spy  # type: ignore[method-assign]
    asyncio.run(routes.collect({"query": "x", "network_profile": "  corpo-proxy  "}))
    # L'identifiant est résolu en ProxyConfig par le Core (credentials hors UI).
    proxy = captured["proxy"]
    from core.knowledge.web_search import ProxyConfig

    assert isinstance(proxy, ProxyConfig)
    assert proxy.url == "socks5://proxy.corp:1080"


def test_collect_rejects_proxy_credentials_422(research_service):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.collect({"query": "x", "proxy": {"url": "socks5://u:p@h:1"}}))
    assert exc.value.status_code == 422
    assert "network_profile" in str(exc.value.detail)


def test_collect_rejects_empty_query_422(research_service):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.collect({"query": "   "}))
    assert exc.value.status_code == 422


def test_collect_rejects_max_above_cap_422(research_service):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.collect({"query": "x", "max_results_per_engine": 51}))
    assert exc.value.status_code == 422


def test_preview_rejects_invalid_url_422(research_service):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.preview({"url": "ftp://example.com"}))
    assert exc.value.status_code == 422


def test_preview_returns_scan(research_service):  # noqa: ARG001
    resp = asyncio.run(routes.preview({"url": f"{HOST}/page"}))
    assert resp["scan_id"] == "scan-1"
    assert resp["pages"][0]["url"] == f"{HOST}/page"


def test_import_page_creates_knowledge(research_service):  # noqa: ARG001
    report = asyncio.run(routes.import_page({"url": f"{HOST}/", "title": "Docs"}))
    assert report["target"] == "knowledge"
    assert report["imported_count"] == 1
    assert report["pages"][0]["status"] == "imported"


def test_import_selection_creates_then_extends_collection(
    research_service,  # noqa: ARG001
):
    report = asyncio.run(
        routes.import_selection(
            {"urls": [f"{HOST}/", "https://other.example.com/x"], "collection_name": "Veille OSINT"}
        )
    )
    assert report["target"] == "collection"
    assert report["imported_count"] == 2
    assert report["collection"]["id"] == "col-1"

    # Ajout ultérieur à la collection existante (collection_id).
    report2 = asyncio.run(
        routes.import_selection({"urls": ["https://third.example.com/"], "collection_id": "col-1"})
    )
    assert report2["collection"]["id"] == "col-1"
    assert report2["imported_count"] == 1


def test_import_selection_rejects_empty_urls_422(research_service):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.import_selection({"urls": []}))
    assert exc.value.status_code == 422


def test_import_selection_rejects_above_cap_422(research_service):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            routes.import_selection({"urls": [f"https://e{i}.example.com" for i in range(51)]})
        )
    assert exc.value.status_code == 422
