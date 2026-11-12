"""Tests API — routes /v1/web-inspiration (recherche → crawl → synthèse).

Le Core (WebInspirationEngine, WebSearchManager, WebIngestionManager) est
réel ; seul le réseau est simulé (backends de recherche mockés + fetcher
DNS/RAG/Knowledge injectés).  Invariants :
- 503 si le moteur n'est pas initialisé ;
- 422 si le topic est vide ;
- 200 avec sources dédoublonnées, crawls best-effort attachés ;
- synthesize=false → summary vide (pas de LLM requis).
"""

from __future__ import annotations

import asyncio

import pytest
from core.folders import FolderManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.knowledge.web_ingest import WebIngestionManager
from core.knowledge.web_inspiration import WebInspirationEngine
from core.knowledge.web_search import WebSearchManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore
from fastapi import HTTPException
from interfaces.api.routers import web_inspiration as routes
from interfaces.api.routers.web_inspiration import set_web_inspiration_engine

HOST = "https://docs.example.com"
ROBOTS = "User-agent: *\n"
HTML_HOME = (
    "<html><head><title>Docs Home</title></head><body>"
    "<p>Documentation complete du produit ETHAN.</p></body></html>"
)


class _FakeFetcher:
    def __init__(self) -> None:
        self.pages = {
            f"{HOST}/robots.txt": (200, "text/plain", ROBOTS.encode()),
            f"{HOST}/": (200, "text/html", HTML_HOME.encode()),
        }

    async def __call__(self, url: str):
        entry = self.pages.get(url)
        if entry is None:
            return {"status": 404, "content_type": "text/html", "body": b"nf"}
        status, content_type, body = entry
        return {"status": status, "content_type": content_type, "body": body}


def _fake_resolver(hostname: str) -> list[str]:
    return ["93.184.216.34"]  # IP publique fictive (aucun réseau)


def _seed_search_backend(manager: WebSearchManager) -> None:
    """Mocke le backend DuckDuckGo du WebSearchManager (aucun réseau)."""

    async def _fake_duckduckgo(query, max_results, proxy):
        return [
            {
                "title": f"Source pour {query}",
                "url": f"{HOST}/",
                "snippet": "Documentation complete du produit.",
            }
        ]

    manager._search_duckduckgo = _fake_duckduckgo  # type: ignore[method-assign]


@pytest.fixture(autouse=True)
def inspiration_services():
    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    knowledge = KnowledgeManager(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    folders = FolderManager(store=store, knowledge=knowledge, collections=collections)

    web_ingest_manager = WebIngestionManager(
        rag=rag,
        knowledge=knowledge,
        collections=collections,
        folders=folders,
        fetcher=_FakeFetcher(),
        resolver=_fake_resolver,
        request_delay=0.0,
    )
    web_search_manager = WebSearchManager()
    _seed_search_backend(web_search_manager)

    engine = WebInspirationEngine(
        web_search=web_search_manager,
        web_ingest=web_ingest_manager,
        max_sources=3,
        synthesize=False,
    )
    set_web_inspiration_engine(engine)
    yield engine
    set_web_inspiration_engine(None)


# ── (SUITE) ──────────────────────────────────────────────────────────────────


def test_status_route_reports_availability():
    status = asyncio.run(routes.status())
    assert status["available"] is True
    assert "duckduckgo" in status["engines_required"]


def test_routes_503_when_engine_not_initialized():
    set_web_inspiration_engine(None)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.inspire({"topic": "ethan"}))
    assert exc.value.status_code == 503
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.search_only({"topic": "ethan"}))
    assert exc.value.status_code == 503


def test_inspire_route_requires_topic():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.inspire({"topic": "   "}))
    assert exc.value.status_code == 422


def test_inspire_route_returns_sources_with_crawl():
    result = asyncio.run(
        routes.inspire(
            {
                "topic": "ethan",
                "engines": ["duckduckgo"],
                "max_sources": 2,
                "synthesize": False,
            }
        )
    )
    assert result["topic"] == "ethan"
    assert result["summary"] == ""
    assert result["sources"], "au moins une source attendue"
    source = result["sources"][0]
    assert source["url"] == f"{HOST}/"
    assert source["error"] is None
    # Le crawl preview a bien été rattaché (titre extrait du HTML fake).
    assert any(p["title"] == "Docs Home" for p in source["pages"])
    stats = result["stats"]
    assert stats["sources_found"] >= 1
    assert stats["engines"] == ["duckduckgo"]


def test_search_only_route_is_fast_and_json():
    result = asyncio.run(
        routes.search_only(
            {
                "topic": "ethan",
                "engines": ["duckduckgo"],
            }
        )
    )
    assert set(result["engines"]) == {"duckduckgo"}
    duck = result["engines"]["duckduckgo"]
    assert duck["total_found"] == 1
    assert duck["results"][0]["url"] == f"{HOST}/"
    assert "crawl" not in str(result)


def test_inspire_route_without_provider_still_works():
    """Sans ProviderManager (LLM), le pipeline reste fonctionnel."""
    result = asyncio.run(routes.inspire({"topic": "ethan", "synthesize": True}))
    # synthesize=True mais aucun LLM injecté → summary vide, pas d'erreur.
    assert result["summary"] == ""
    assert result["sources"]
