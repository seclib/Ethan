"""Tests Core « Web Research » : recherche → sélection → Knowledge/RAG.

Core réel (WebResearchService, WebSearchManager, WebIngestionManager) ;
réseau simulé. Invariants : plafond 50 pages/collection strict ; choix
utilisateur (limite de recherche + pages importées) ; page seule →
Knowledge ; sélection → collection ; page inaccessible isolée ;
métadonnées source conservées ; pipeline Knowledge/RAG existant réutilisé.
"""

from __future__ import annotations

from typing import Any

import pytest
from core.folders import FolderManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.knowledge.web_ingest import WebIngestionManager
from core.knowledge.web_research_service import (
    MAX_PAGES_PER_COLLECTION,
    CollectedPage,
    WebResearchService,
    validate_max_pages,
)
from core.knowledge.web_search import (
    SearchProvider,
    SearchProviderRegistry,
    WebSearchManager,
)
from core.rag import RAGPipeline
from core.state import CoreRecordStore

HOST = "https://docs.example.com"
ROBOTS = "User-agent: *\n"
HTML = (
    "<html><head><title>Docs ETHAN</title></head><body>"
    "<main><p>Documentation complete du produit ETHAN.</p></main></body></html>"
)


class _FakeProvider(SearchProvider):
    id = "fake"
    label = "Fake"

    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self._items = list(items or [])

    def is_available(self) -> bool:
        return True

    async def fetch(self, manager, query, max_results, proxy=None):
        return list(self._items)


def _search(items: list[dict[str, Any]]) -> WebSearchManager:
    registry = SearchProviderRegistry()
    registry.register(_FakeProvider(items=items))
    return WebSearchManager(registry=registry)


def _items(count: int = 3) -> list[dict[str, Any]]:
    return [
        {"title": f"R{i}", "url": f"https://site{i}.example.com/page", "snippet": "s"}
        for i in range(count)
    ]


class _FakeIngest:
    """Enregistre scan/ingest sans stockage (orchestration seulement)."""

    def __init__(self, fail_urls: set[str] | None = None) -> None:
        self.scan_calls: list[dict[str, Any]] = []
        self.ingest_calls: list[dict[str, Any]] = []
        self._fail = set(fail_urls or ())
        self._n = 0

    async def scan(self, root_url: str = "", **kw: Any) -> dict[str, Any]:
        self.scan_calls.append({"root_url": root_url, **kw})
        if root_url in self._fail:
            raise RuntimeError(f"unreachable: {root_url}")
        self._n += 1
        return {
            "scan_id": f"scan-{self._n}",
            "root_url": root_url,
            "pages": [
                {
                    "page_id": f"p-{self._n}",
                    "url": root_url,
                    "title": f"Page {self._n}",
                    "status": 200,
                    "content_type": "text/html",
                    "words": 42,
                }
            ],
            "errors": [],
        }

    async def ingest(self, **kw: Any) -> dict[str, Any]:
        self.ingest_calls.append(kw)
        pids = kw.get("page_ids") or []
        return {
            "target": kw.get("target"),
            "indexed": [{"page_id": p} for p in pids],
            "indexed_count": len(pids),
            "skipped_duplicates": 0,
            "collection": {
                "id": kw.get("collection_id") or "col-1",
                "name": kw.get("collection_name") or "",
            },
            "knowledge": {"id": "k-1"} if kw.get("target") == "knowledge" else None,
        }


def _service(items=None, ingest=None):
    ingest = ingest or _FakeIngest()
    svc = WebResearchService(
        web_search=_search(_items() if items is None else items), web_ingest=ingest
    )
    return svc, ingest


# ── Cap de 50 pages ──────────────────────────────────────────────────────────


def test_cap_is_fifty():
    assert MAX_PAGES_PER_COLLECTION == 50
    assert validate_max_pages(1) == 1
    assert validate_max_pages(50) == 50


@pytest.mark.parametrize("bad", [51, 0, -1, "abc", None, 1.5])
def test_validate_max_pages_rejects(bad):
    with pytest.raises(ValueError):
        validate_max_pages(bad)


def test_service_exposes_cap():
    svc, _ = _service()
    cap = svc.max_pages_per_collection
    if callable(cap):
        cap = cap()
    assert cap == 50


# ── collect() ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_collect_dedup_and_domains():
    items = _items(3) + [{"title": "dup", "url": "https://WWW.site0.example.com/page"}]
    svc, _ = _service(items=items)
    rep = await svc.collect("ethan", engines=["fake"], max_results_per_engine=10)
    assert rep.query == "ethan" and rep.engines == ["fake"]
    assert rep.total_found == 3 and rep.errors == {}
    assert rep.results[0].domain.endswith(".example.com")
    assert rep.results[0].source_engine == "fake"


@pytest.mark.asyncio
async def test_collect_user_limit_no_cap_truncation():
    svc, _ = _service(items=_items(5))
    rep = await svc.collect("ethan", engines=["fake"], max_results_per_engine=2)
    assert rep.total_found == 2 and rep.truncated is False


@pytest.mark.asyncio
async def test_collect_truncates_at_cap_fifty():
    # 2 moteurs x 30 resultats dedupliquables -> 60 candidats -> cap 50.
    registry = SearchProviderRegistry()
    for engine, prefix in (("a", "https://a"), ("b", "https://b")):
        provider = _FakeProvider(
            items=[
                {"title": f"{engine}{i}", "url": f"{prefix}{i}.example.com/p"} for i in range(30)
            ]
        )
        provider.id, provider.label = engine, engine.upper()
        registry.register(provider)
    svc = WebResearchService(
        web_search=WebSearchManager(registry=registry), web_ingest=_FakeIngest()
    )
    rep = await svc.collect("ethan", engines=["a", "b"], max_results_per_engine=50)
    assert rep.total_found == 50 and rep.truncated is True


@pytest.mark.asyncio
async def test_collect_rejects_bad_limits():
    svc, _ = _service()
    for bad in (0, 51):
        with pytest.raises(ValueError):
            await svc.collect("ethan", engines=["fake"], max_results_per_engine=bad)


@pytest.mark.asyncio
async def test_collect_requires_query():
    svc, _ = _service()
    with pytest.raises(ValueError):
        await svc.collect("   ")


# ── Page seule → Knowledge / Sélection → collection ─────────────────────────


@pytest.mark.asyncio
async def test_import_page_single_knowledge():
    svc, ingest = _service()
    await svc.import_page(
        url=f"{HOST}/guide", title="Guide", domain="docs.example.com", collection_name="Solo"
    )
    assert len(ingest.ingest_calls) == 1
    call = ingest.ingest_calls[0]
    assert call["target"] == "knowledge" and call["scan_id"] and call["page_ids"]


def _pages(n):
    return [
        CollectedPage(
            title=f"P{i}",
            url=f"https://site{i}.example.com/page",
            domain=f"site{i}.example.com",
            snippet="s",
            source_engine="fake",
            rank=i + 1,
            metadata={},
        )
        for i in range(n)
    ]


@pytest.mark.asyncio
async def test_import_selection_same_collection():
    svc, ingest = _service()
    await svc.import_selection(_pages(3), collection_name="Web Research", collection_id=None)
    assert len(ingest.ingest_calls) == 3
    # 1re ingestion : creation (collection_id None) ; suivantes : meme id reutilise.
    assert ingest.ingest_calls[0].get("collection_id") is None
    rest = [c.get("collection_id") for c in ingest.ingest_calls[1:]]
    assert rest and len(set(rest)) == 1 and rest[0]
    assert all(c["target"] == "collection" for c in ingest.ingest_calls)


@pytest.mark.asyncio
async def test_import_selection_rejects_over_fifty():
    svc, ingest = _service()
    with pytest.raises(ValueError, match="50"):
        await svc.import_selection(_pages(51), collection_name="Trop", collection_id=None)
    assert ingest.ingest_calls == []


@pytest.mark.asyncio
async def test_import_selection_accepts_fifty():
    svc, ingest = _service()
    await svc.import_selection(_pages(50), collection_name="Limite", collection_id=None)
    assert len(ingest.ingest_calls) == 50


@pytest.mark.asyncio
async def test_unreachable_page_isolated():
    svc, ingest = _service()
    pages = _pages(3)
    pages[1].url = "https://dead.example.com/page"
    ingest._fail = {pages[1].url}
    await svc.import_selection(pages, collection_name="Mixte", collection_id=None)
    assert len(ingest.ingest_calls) == 2


# ── Workflow complet ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_collect_and_import_user_selection():
    items = _items(4)
    svc, ingest = _service(items=items)
    selected = [items[0]["url"], items[2]["url"]]
    await svc.collect_and_import(
        "ethan",
        selected_urls=selected,
        engines=["fake"],
        max_results_per_engine=10,
        proxy=None,
        target="collection",
        collection_name="Sel",
    )
    assert len(ingest.ingest_calls) == 2
    assert {c["root_url"] for c in ingest.scan_calls} == set(selected)


@pytest.mark.asyncio
async def test_collect_and_import_single_knowledge():
    items = _items(2)
    svc, ingest = _service(items=items)
    await svc.collect_and_import(
        "ethan",
        selected_urls=[items[1]["url"]],
        engines=["fake"],
        max_results_per_engine=10,
        proxy=None,
        target="knowledge",
        collection_name="Solo",
    )
    assert len(ingest.ingest_calls) == 1
    assert ingest.ingest_calls[0]["target"] == "knowledge"


@pytest.mark.asyncio
async def test_collect_and_import_unknown_selection_imports_nothing():
    svc, ingest = _service(items=_items(2))
    rep = await svc.collect_and_import(
        "ethan",
        selected_urls=["https://nope.example.com"],
        engines=["fake"],
        max_results_per_engine=10,
        proxy=None,
        target="collection",
        collection_name="X",
    )
    assert ingest.ingest_calls == []
    assert rep["import"]["imported_count"] == 0


@pytest.mark.asyncio
async def test_collect_and_import_never_exceeds_cap():
    # 60 candidats (2 moteurs x 30) : collect() plafonne deja a 50, donc meme
    # en demandant 60 URLs, jamais plus de 50 pages ne sont importees.
    registry = SearchProviderRegistry()
    urls: list[str] = []
    for engine, prefix in (("a", "https://a"), ("b", "https://b")):
        items = [{"title": f"{engine}{i}", "url": f"{prefix}{i}.example.com/p"} for i in range(30)]
        urls.extend(it["url"] for it in items)
        provider = _FakeProvider(items=items)
        provider.id, provider.label = engine, engine.upper()
        registry.register(provider)
    ingest = _FakeIngest()
    svc = WebResearchService(web_search=WebSearchManager(registry=registry), web_ingest=ingest)
    rep = await svc.collect_and_import(
        "ethan",
        selected_urls=urls,
        engines=["a", "b"],
        max_results_per_engine=50,
        proxy=None,
        target="collection",
        collection_name="X",
    )
    assert rep["import"]["imported_count"] == 50
    assert len(ingest.ingest_calls) == 50


# ── Bout-en-bout : Knowledge/RAG réel, réseau simulé ────────────────────────


class _FakeFetcher:
    def __init__(self):
        self.pages = {
            f"{HOST}/robots.txt": (200, "text/plain", ROBOTS.encode()),
            f"{HOST}/": (200, "text/html", HTML.encode()),
        }

    async def __call__(self, url):
        entry = self.pages.get(url)
        if entry is None:
            return {"status": 404, "content_type": "text/html", "body": b"nf"}
        status, ctype, body = entry
        return {"status": status, "content_type": ctype, "body": body}


def _resolver(hostname):
    return ["93.184.216.34"]


@pytest.fixture
def real_ingest():
    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    knowledge = KnowledgeManager(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    folders = FolderManager(store=store, knowledge=knowledge, collections=collections)
    return WebIngestionManager(
        rag=rag,
        knowledge=knowledge,
        collections=collections,
        folders=folders,
        fetcher=_FakeFetcher(),
        resolver=_resolver,
        request_delay=0.0,
    )


@pytest.mark.asyncio
async def test_end_to_end_metadata_preserved(real_ingest):
    svc = WebResearchService(
        web_search=_search([{"title": "Docs ETHAN", "url": f"{HOST}/", "snippet": "doc"}]),
        web_ingest=real_ingest,
    )
    rep = await svc.collect_and_import(
        "ethan",
        selected_urls=[f"{HOST}/"],
        engines=["fake"],
        max_results_per_engine=5,
        proxy=None,
        target="collection",
        collection_name="E2E",
    )
    imp = rep["import"]
    assert imp["collection"]["name"] == "E2E"
    assert imp["imported_count"] == 1 and imp["indexed_count"] == 1
    page = imp["pages"][0]
    assert page["status"] == "imported" and page["error"] is None
    assert page["url"] == f"{HOST}/"
    assert page["title"] == "Docs ETHAN"
    assert page["domain"] == "docs.example.com"
    assert page["collected_at"], "date de collecte conservée"


# ── Destination "project" (Web Import fusionné : destination explicite) ────


@pytest.mark.asyncio
async def test_import_selection_project_passes_target_and_id():
    svc, ingest = _service()
    rep = await svc.import_selection(_pages(2), target="project", project_id="proj-1")
    assert rep["target"] == "project"
    assert rep["imported_count"] == 2
    assert ingest.ingest_calls[0]["target"] == "project"
    assert ingest.ingest_calls[0]["project_id"] == "proj-1"


@pytest.mark.asyncio
async def test_import_selection_project_requires_id():
    svc, _ = _service()
    with pytest.raises(ValueError, match="project_id"):
        await svc.import_selection(_pages(1), target="project")


@pytest.mark.asyncio
async def test_web_ingest_project_uses_project_document_pipeline(real_ingest):
    """target="project" réutilise le pipeline documentaire du projet (Core)."""
    calls: list[dict[str, Any]] = []

    class _FakePM:
        async def record_document_upload(self, **kw: Any) -> dict[str, Any]:
            calls.append(kw)
            return {"id": f"doc-{len(calls)}", "status": "ready", "error": None}

    real_ingest.set_projects(_FakePM())
    scan = await real_ingest.scan(HOST + "/", max_depth=0, max_pages=1)
    pids = [p["page_id"] for p in scan["pages"] if p.get("page_id")]
    res = await real_ingest.ingest(
        scan["scan_id"], pids, target="project", project_id="proj-1", user_id="u1"
    )
    assert res["target"] == "project"
    assert res["project"] == {"id": "proj-1"}
    assert res["indexed_count"] == 1
    assert calls[0]["project_id"] == "proj-1"
    assert calls[0]["user_id"] == "u1"


@pytest.mark.asyncio
async def test_web_ingest_project_requires_project_id(real_ingest):
    scan = await real_ingest.scan(HOST + "/", max_depth=0, max_pages=1)
    pids = [p["page_id"] for p in scan["pages"] if p.get("page_id")]
    with pytest.raises(ValueError, match="project_id"):
        await real_ingest.ingest(scan["scan_id"], pids, target="project")


@pytest.mark.asyncio
async def test_import_selection_threads_user_id_to_ingest():
    """L'identité JWT transite jusqu'au pipeline d'ingestion (accès projet)."""
    svc, ingest = _service()
    await svc.import_selection(_pages(1), target="project", project_id="proj-9", user_id="alice")
    assert ingest.ingest_calls[0]["user_id"] == "alice"
