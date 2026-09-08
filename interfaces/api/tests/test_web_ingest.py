"""Tests API — routes /v1/web-ingest (preview → validation → indexation).

Le Core (WebIngestionManager) est réel ; seul le réseau est simulé (fetcher +
résolveur DNS injectés).  Les routes propagent les ValueError en 422 et
n'exposent jamais le texte interne des previews.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from routers import v1
from interfaces.api.routers.folders import set_folder_manager
from interfaces.api.routers import web_ingest as routes
from interfaces.api.routers.web_ingest import (
    get_web_ingest_manager,
    set_web_ingest_manager,
)
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.knowledge.web_ingest import WebIngestionManager
from core.folders import FolderManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore

HOST = "https://docs.example.com"

ROBOTS = f"User-agent: *\nDisallow: /private\nSitemap: {HOST}/sitemap.xml\n"
SITEMAP = (
    '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    f"<url><loc>{HOST}/guide</loc></url></urlset>"
)
HTML_HOME = (
    "<html><head><title>Docs Home</title></head><body><p>Documentation complete.</p>"
    '<a href="/guide">Guide</a></body></html>'
)
HTML_GUIDE = (
    "<html><head><title>Guide</title></head><body><p>Guide d'utilisation.</p></body></html>"
)


class _FakeFetcher:
    def __init__(self) -> None:
        self.pages = {
            f"{HOST}/robots.txt": (200, "text/plain", ROBOTS.encode()),
            f"{HOST}/sitemap.xml": (200, "application/xml", SITEMAP.encode()),
            f"{HOST}/": (200, "text/html", HTML_HOME.encode()),
            f"{HOST}/guide": (200, "text/html", HTML_GUIDE.encode()),
        }

    async def __call__(self, url: str):
        entry = self.pages.get(url)
        if entry is None:
            return {"status": 404, "content_type": "text/html", "body": b"nf"}
        status, content_type, body = entry
        return {"status": status, "content_type": content_type, "body": body}


def _fake_resolver(hostname: str) -> list[str]:
    return ["93.184.216.34"]


@pytest.fixture(autouse=True)
def real_services():
    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    knowledge = KnowledgeManager(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    folders = FolderManager(store=store, knowledge=knowledge, collections=collections)

    v1.set_core_domain_services(v1.CoreDomainServices(
        knowledge=knowledge, rag=rag,
    ))
    v1.set_knowledge_collections(collections)
    set_folder_manager(folders)
    manager = WebIngestionManager(
        rag=rag, knowledge=knowledge, collections=collections, folders=folders,
        fetcher=_FakeFetcher(), resolver=_fake_resolver, request_delay=0.0,
    )
    set_web_ingest_manager(manager)
    yield manager
    set_web_ingest_manager(None)
    v1.set_knowledge_collections(None)
    set_folder_manager(None)


# ── (SUITE) ──────────────────────────────────────────────────────────────────

def test_scan_route_returns_preview_without_internal_text():
    """POST /web-ingest/scan : preview public (titre, extrait) sans `text`."""
    preview = asyncio.run(routes.scan_web({
        "url": f"{HOST}/", "max_pages": 10, "max_depth": 1,
    }))
    assert preview["scan_id"]
    assert preview["robots"]["exists"] is True
    urls = {p["url"]: p for p in preview["pages"]}
    assert urls[f"{HOST}/"]["title"] == "Docs Home"
    assert all("text" not in page for page in preview["pages"])


def test_scan_route_rejects_unsafe_url():
    """URL locale/privée → 422 (garde-fou SSRF du Core)."""
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.scan_web({"url": "http://127.0.0.1/"}))
    assert exc.value.status_code == 422


def test_get_scan_route():
    """GET /web-ingest/scans/{id} : re-affichage ; 404 si inconnu."""
    preview = asyncio.run(routes.scan_web({"url": f"{HOST}/"}))
    again = asyncio.run(routes.get_web_scan(preview["scan_id"]))
    assert again["scan_id"] == preview["scan_id"]
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.get_web_scan("ghost"))
    assert exc.value.status_code == 404


def test_ingest_route_creates_collection_and_folder():
    """POST /web-ingest/ingest : validation utilisateur → dossier + collection."""
    preview = asyncio.run(routes.scan_web({"url": f"{HOST}/", "max_pages": 5}))
    page_ids = [p["page_id"] for p in preview["pages"] if p["status"] == "ok"]

    result = asyncio.run(routes.ingest_web({
        "scan_id": preview["scan_id"],
        "page_ids": page_ids,
        "new_folder_name": "Docs Web",
        "target": "collection",
        "new_collection_name": "Docs Produit",
        "retrieval_strategy": "semantic",
    }))
    assert result["folder"]["name"] == "Docs Web"
    assert result["collection"]["name"] == "Docs Produit"
    assert result["indexed_count"] == 2

    manager = get_web_ingest_manager()
    col = manager._collections.get_collection(result["collection"]["id"])
    col_dict = asyncio.run(col) if asyncio.iscoroutine(col) else col
    assert col_dict["retrieval_strategy"] == "semantic"


def test_ingest_route_validates_payload():
    """Scan inconnu → 422 ; page inconnue → 422."""
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.ingest_web({
            "scan_id": "ghost", "page_ids": [], "target": "knowledge",
        }))
    assert exc.value.status_code == 422

    preview = asyncio.run(routes.scan_web({"url": f"{HOST}/"}))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.ingest_web({
            "scan_id": preview["scan_id"], "page_ids": ["ghost-page"],
            "target": "knowledge",
        }))
    assert exc.value.status_code == 422
