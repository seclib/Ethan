"""Tests Core — WebInspirationEngine (core/knowledge/web_inspiration).

Orchestration de recherche web enrichie.  Déterministe : les dépendances
(WebSearchManager, WebIngestionManager, provider LLM) sont mockées ; aucun
appel réseau réel.

Invariants :
- ``inspire()`` restructure les sources (dédoublonnées par URL), chaque source
  porte son crawl ``pages`` et ``error`` éventuelle ;
- les erreurs de crawl ne font pas échouer le pipeline (best-effort) ;
- la synthèse LLM est optionnelle et best-effort ;
- ``search_only()`` renvoie une vue JSON des moteurs sans crawl ;
- un topic vide lève ValueError.
"""

from __future__ import annotations

import pytest
from core.knowledge.web_inspiration import (
    MAX_SOURCES_HARD_CAP,
    WebInspirationEngine,
)
from core.knowledge.web_search import SearchResponse, SearchResult


class _FakeSearch:
    """Faux WebSearchManager : réponses figées par moteur."""

    def __init__(self, results_by_engine: dict[str, list[SearchResult]]) -> None:
        self._by = results_by_engine

    def list_engines(self):
        return [{"id": e, "label": e} for e in self._by]

    async def search_multiple(self, query, engines=None, max_results_per_engine=5, proxy=None):
        engines = engines or list(self._by)
        out: dict[str, SearchResponse] = {}
        for engine in engines:
            items = []
            for r in self._by.get(engine, []):
                # reflète le vrai pipeline : _normalize étiquette la source
                items.append(
                    SearchResult(
                        title=r.title,
                        url=r.url,
                        snippet=r.snippet,
                        source_engine=engine,
                        rank=r.rank,
                    )
                )
            out[engine] = SearchResponse(
                query=query, engine=engine, results=items, total_found=len(items)
            )
        return out


class _FakeIngest:
    """Faux WebIngestionManager : preview figé, ou exception contrôlée."""

    def __init__(self, pages, fail_urls: set[str] | None = None) -> None:
        self._pages = pages
        self._fail = fail_urls or set()

    async def scan(self, url, max_pages=1, max_depth=1, **kwargs):
        if url in self._fail:
            raise ValueError(f"SSRF refusé pour {url}")
        return {
            "scan_id": "scan-test",
            "target": url,
            "pages": [{**p, "status": "ok", "url": url} for p in self._pages],
        }


def _result(title: str, url: str) -> SearchResult:
    return SearchResult(title=title, url=url, snippet=f"Snippet de {title}", rank=1)


def _make_engine(**kw) -> WebInspirationEngine:
    search = _FakeSearch(
        {
            "duckduckgo": [
                _result("Première source", "https://a.example.com"),
                _result("Seconde source", "https://b.example.com"),
            ],
            "bing": [
                _result("Doublon", "https://a.example.com"),
                _result("Troisième source", "https://c.example.com"),
            ],
        }
    )
    ingest = _FakeIngest(pages=[{"title": "Page extraite", "text": "Contenu de la page."}])
    return WebInspirationEngine(web_search=search, web_ingest=ingest, **kw)


@pytest.mark.asyncio
async def test_inspire_deduplicates_sources_and_crawls() -> None:
    engine = _make_engine(synthesize=False)
    result = await engine.inspire("ethan", engines=["duckduckgo", "bing"])
    assert result["topic"] == "ethan"
    assert result["summary"] == ""
    urls = [s["url"] for s in result["sources"]]
    assert urls == [
        "https://a.example.com",
        "https://b.example.com",
        "https://c.example.com",
    ]
    # Chaque source a un crawl preview attaché.
    for source in result["sources"]:
        assert source["pages"]
        assert source["error"] is None
    assert result["stats"]["sources_found"] == 3


@pytest.mark.asyncio
async def test_inspire_crawl_error_is_best_effort() -> None:
    search = _FakeSearch({"duckduckgo": [_result("Bloquée", "https://private.example.com")]})
    ingest = _FakeIngest(pages=[], fail_urls={"https://private.example.com"})
    engine = WebInspirationEngine(web_search=search, web_ingest=ingest, synthesize=False)
    result = await engine.inspire("test")
    assert result["sources"][0]["error"] is not None
    assert "SSRF" in result["sources"][0]["error"]
    assert result["sources"][0]["pages"] == []
    assert len(result["stats"]["errors"]) == 1


@pytest.mark.asyncio
async def test_inspire_respects_max_sources_cap() -> None:
    many = [_result(f"R{i}", f"https://r{i}.example.com") for i in range(30)]
    search = _FakeSearch({"duckduckgo": many})
    engine = WebInspirationEngine(
        web_search=search, web_ingest=_FakeIngest(pages=[]), synthesize=False
    )
    result = await engine.inspire("web")
    assert len(result["sources"]) <= MAX_SOURCES_HARD_CAP
    assert result["stats"]["sources_found"] <= MAX_SOURCES_HARD_CAP


@pytest.mark.asyncio
async def test_inspire_empty_topic_raises() -> None:
    engine = _make_engine(synthesize=False)
    with pytest.raises(ValueError, match="vide"):
        await engine.inspire("   ")


@pytest.mark.asyncio
async def test_search_only_returns_json_view_without_crawl() -> None:
    engine = _make_engine(synthesize=False)
    result = await engine.search_only("ethan", engines=["duckduckgo"])
    assert set(result["engines"]) == {"duckduckgo"}
    duck = result["engines"]["duckduckgo"]
    assert duck["total_found"] == 2
    assert duck["results"][0]["source_engine"] == "duckduckgo"
    assert "crawl" not in str(result)  # aucune trace de crawl


@pytest.mark.asyncio
async def test_synthesize_with_llm_provider() -> None:
    """Avec un provider LLM faux, la synthèse est produite."""

    class _FakeProvider:
        async def chat(self, messages, model=None, temperature=None):
            return "## Synthèse\nPistes identifiées. [1] [2]"

    class _FakeRegistry:
        def get_provider(self, pid):
            return _FakeProvider()

    class _FakeProviders:
        _registry = _FakeRegistry()

        async def get_default_provider(self):
            return {"provider_id": "ollama"}

        async def get_active_model(self, pid):
            return "test-model"

    engine = _make_engine(provider_manager=_FakeProviders())
    result = await engine.inspire("ethan")
    assert "Synthèse" in result["summary"]


@pytest.mark.asyncio
async def test_synthesize_llm_failure_is_best_effort() -> None:
    class _BoomProviders:
        async def get_default_provider(self):
            raise RuntimeError("provider down")

    engine = _make_engine(provider_manager=_BoomProviders())
    result = await engine.inspire("ethan")
    assert result["summary"] == ""
    # Les sources restent présentes malgré l'échec LLM.
    assert result["stats"]["sources_found"] > 0
