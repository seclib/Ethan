"""Tests Core — pipeline d'ingestion web (URL → scan → preview → validation → index).

Managers Core réels (RAG, Knowledge, Collections, Folders) ; seul le réseau
est simulé : fetcher et résolveur DNS injectés.  Invariants :
- le scan ne produzit qu'un preview (aucune indexation automatique) ;
- robots.txt est respecté (jamais de contournement) ;
- profondeur, nombre de pages, patterns d'exclusion/inclusion bornent le scan ;
- la déduplication (URL + contenu) évite tout double indexation ;
- l'indexation n'a lieu qu'après sélection explicite, vers la destination
  choisie (dossier, Knowledge ou RAG Collection).
"""

from __future__ import annotations

import asyncio

import pytest

from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.knowledge.web_ingest import WebIngestionManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore

HOST = "https://docs.example.com"

HTML_HOME = """<html><head><title>Docs Home</title></head><body>
<h1>Bienvenue</h1><p>Documentation complete du produit.</p>
<a href="/guide">Guide</a>
<a href="/api">API</a>
<a href="/faq">FAQ</a>
<a href="/private">Zone privée</a>
<a href="/dup">Duplicate</a>
<a href="/assets/logo.png">Logo</a>
<a href="https://external.example.org/page">Externe</a>
</body></html>"""

HTML_GUIDE = "<html><head><title>Guide</title></head><body><p>Guide d'utilisation : demarrer ici.</p></body></html>"
HTML_API = "<html><head><title>API Reference</title></head><body><p>Endpoints et authentification.</p></body></html>"
HTML_FAQ = "<html><head><title>FAQ</title></head><body><p>Questions frequentes et reponses.</p></body></html>"
HTML_PRIVATE = "<html><head><title>Private</title></head><body><p>Contenu interdit.</p></body></html>"
HTML_DUP = "<html><head><title>Duplicate</title></head><body><p>Guide d'utilisation : demarrer ici.</p></body></html>"

ROBOTS = "User-agent: *\nDisallow: /private\nSitemap: {host}/sitemap.xml\n".format(host=HOST)
SITEMAP = (
    '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    f"<url><loc>{HOST}/guide</loc></url>"
    f"<url><loc>{HOST}/api</loc></url>"
    f"<url><loc>{HOST}/faq</loc></url>"
    "</urlset>"
)


class _FakeFetcher:
    """Serveur web factice : mapping URL → (status, content_type, body)."""

    def __init__(self) -> None:
        self.pages: dict[str, tuple[int, str, bytes]] = {}
        self.requested: list[str] = []

    def add(self, url: str, body: str, content_type: str = "text/html", status: int = 200) -> None:
        self.pages[url] = (status, content_type, body.encode("utf-8"))

    async def __call__(self, url: str):
        self.requested.append(url)
        if url not in self.pages:
            return {"status": 404, "content_type": "text/html", "body": b"not found"}
        status, content_type, body = self.pages[url]
        return {"status": status, "content_type": content_type, "body": body}


def _fake_resolver(hostname: str) -> list[str]:
    return ["93.184.216.34"]  # IP publique fictive (aucun réseau)


def _make_site() -> _FakeFetcher:
    fetcher = _FakeFetcher()
    fetcher.add(f"{HOST}/robots.txt", ROBOTS, "text/plain")
    fetcher.add(f"{HOST}/sitemap.xml", SITEMAP, "application/xml")
    fetcher.add(f"{HOST}/", HTML_HOME)
    fetcher.add(f"{HOST}/guide", HTML_GUIDE)
    fetcher.add(f"{HOST}/api", HTML_API)
    fetcher.add(f"{HOST}/faq", HTML_FAQ)
    fetcher.add(f"{HOST}/private", HTML_PRIVATE)
    fetcher.add(f"{HOST}/dup", HTML_DUP)
    return fetcher


def _manager(fetcher: _FakeFetcher, **kwargs) -> tuple[WebIngestionManager, dict]:
    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    knowledge = KnowledgeManager(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    from core.folders import FolderManager

    folders = FolderManager(store=store, knowledge=knowledge, collections=collections)
    manager = WebIngestionManager(
        rag=rag,
        knowledge=knowledge,
        collections=collections,
        folders=folders,
        fetcher=fetcher,
        resolver=_fake_resolver,
        request_delay=0.0,
        **kwargs,
    )
    return manager, {
        "rag": rag, "knowledge": knowledge,
        "collections": collections, "folders": folders,
    }


# ── (SUITE) ──────────────────────────────────────────────────────────────────

def test_scan_produces_preview_without_indexing():
    """Le scan découvre, extrait, déduplique — mais n'indexe RIEN."""

    async def scenario():
        fetcher = _make_site()
        manager, managers = _manager(fetcher)
        preview = await manager.scan(f"{HOST}/", max_pages=10, max_depth=1)

        urls = {p["url"]: p for p in preview["pages"]}
        assert preview["sitemap_used"] is True
        assert preview["robots"]["exists"] is True

        # Pages ok : titre + extrait + hash, pas de champ interne `text`.
        assert urls[f"{HOST}/"]["title"] == "Docs Home"
        assert "Documentation complete" in urls[f"{HOST}/"]["excerpt"]
        assert all("text" not in page for page in preview["pages"])

        # robots.txt Disallow respecté : /private jamais récupéré.
        assert urls[f"{HOST}/private"]["status"] == "disallowed"
        assert f"{HOST}/private" not in fetcher.requested

        # Dédup contenu : /dup (même texte que /guide) marqué duplicate.
        assert urls[f"{HOST}/dup"]["duplicate_of"] == urls[f"{HOST}/guide"]["page_id"]

        # AUCUNE indexation : le catalogue RAG reste vide après le scan.
        assert await managers["rag"].list_documents() == []

        # Preview re-affichable via get_scan.
        assert manager.get_scan(preview["scan_id"])["scan_id"] == preview["scan_id"]

    asyncio.run(scenario())


def test_scan_bounded_by_max_pages_and_depth():
    """Le nombre de pages et la profondeur bornent strictement le scan."""

    async def scenario():
        fetcher = _make_site()
        manager, _m = _manager(fetcher)

        preview = await manager.scan(f"{HOST}/", max_pages=2, max_depth=1)
        ok_pages = [p for p in preview["pages"] if p["status"] == "ok"]
        assert len(ok_pages) <= 2

        # Profondeur 0 : seule la page racine est explorée.
        fetcher2 = _make_site()
        manager2, _m2 = _manager(fetcher2)
        preview_shallow = await manager2.scan(f"{HOST}/", max_pages=10, max_depth=0)
        ok_shallow = [p for p in preview_shallow["pages"] if p["status"] == "ok"]
        assert [p["url"] for p in ok_shallow] == [f"{HOST}/"]

    asyncio.run(scenario())


def test_scan_include_and_exclude_patterns():
    """Patterns glob d'exclusion et d'inclusion sur l'URL complète."""

    async def scenario():
        fetcher = _make_site()
        manager, _m = _manager(fetcher)
        preview = await manager.scan(
            f"{HOST}/", max_pages=10, max_depth=1,
            exclude_patterns=["*/api*"],
        )
        urls = {p["url"] for p in preview["pages"] if p["status"] == "ok"}
        assert f"{HOST}/api" not in urls
        assert f"{HOST}/guide" in urls

        fetcher2 = _make_site()
        manager2, _m2 = _manager(fetcher2)
        preview2 = await manager2.scan(
            f"{HOST}/", max_pages=10, max_depth=1,
            include_patterns=["*guide*", f"{HOST}/"],
        )
        urls2 = {p["url"] for p in preview2["pages"] if p["status"] == "ok"}
        assert urls2 == {f"{HOST}/", f"{HOST}/guide"}

    asyncio.run(scenario())


def test_scan_rejects_unsafe_urls():
    """Garde-fou SSRF : localhost, IP privées, schéma non-web → ValueError."""

    async def scenario():
        manager, _m = _manager(_make_site())
        for bad_url in (
            "http://localhost:8000/",
            "http://127.0.0.1/",
            "http://192.168.1.10/",
            "http://10.0.0.5/",
            "file:///etc/passwd",
            "https://internal.local/",
        ):
            with pytest.raises(ValueError):
                await manager.scan(bad_url)

    asyncio.run(scenario())


# ── (SUITE 2) ────────────────────────────────────────────────────────────────

def test_ingest_to_new_collection_and_folder():
    """Sélection → création dossier + collection (stratégie choisie) → index."""
    async def scenario():
        fetcher = _make_site()
        manager, m = _manager(fetcher)
        preview = await manager.scan(f"{HOST}/", max_pages=10, max_depth=1)
        pages_by_url = {p["url"]: p for p in preview["pages"]}

        # Sélection explicite : home + guide + duplicate (doit être ignoré).
        page_ids = [
            pages_by_url[f"{HOST}/"]["page_id"],
            pages_by_url[f"{HOST}/guide"]["page_id"],
            pages_by_url[f"{HOST}/dup"]["page_id"],
        ]
        result = await manager.ingest(
            preview["scan_id"], page_ids,
            new_folder_name="Docs Web",
            target="collection",
            new_collection_name="Docs Produit",
            retrieval_strategy="hybrid",
        )

        # Dossier créé à la volée, collection classée dedans.
        assert result["folder"]["name"] == "Docs Web"
        assert result["collection"]["name"] == "Docs Produit"
        folder_contents = await m["folders"].list_folder_resources(result["folder"]["id"])
        assert ("collection", result["collection"]["id"]) in {
            (r["resource_type"], r["resource_id"]) for r in folder_contents
        }

        # Collection : stratégie choisie, documents indexés (dup ignoré).
        col = await m["collections"].get_collection(result["collection"]["id"])
        assert col["retrieval_strategy"] == "hybrid"
        assert result["indexed_count"] == 2
        assert len(result["skipped_duplicates"]) == 1
        col_docs = await m["collections"].list_documents(result["collection"]["id"])
        assert {d["source"] for d in col_docs} == {f"{HOST}/", f"{HOST}/guide"}

        # Les documents RAG portent la provenance web.
        all_docs = await m["rag"].list_documents()
        assert any(d.metadata.get("web_url") == f"{HOST}/guide" for d in all_docs)

    asyncio.run(scenario())


def test_ingest_to_existing_collection_updates_strategy():
    """Collection existante : la stratégie choisie met la collection à jour."""
    async def scenario():
        fetcher = _make_site()
        manager, m = _manager(fetcher)
        preview = await manager.scan(f"{HOST}/", max_pages=10, max_depth=0)
        root_page = next(p for p in preview["pages"] if p["status"] == "ok")

        col = await m["collections"].create_collection("Existant", user_id="alice")
        result = await manager.ingest(
            preview["scan_id"], [root_page["page_id"]],
            target="collection", collection_id=col["id"],
            retrieval_strategy="semantic", embedding_model="nomic-embed-text",
        )
        updated = await m["collections"].get_collection(col["id"])
        assert updated["retrieval_strategy"] == "semantic"
        # Le modèle d'embedding choisi est appliqué au moteur (persisté).
        assert m["rag"].get_config()["embedding_model"] == "nomic-embed-text"
        assert result["indexed_count"] == 1

    asyncio.run(scenario())


def test_ingest_to_knowledge_nodes_classified_in_folder():
    """Cible Knowledge : un nœud par page sélectionnée, classé dans le dossier."""
    async def scenario():
        fetcher = _make_site()
        manager, m = _manager(fetcher)
        preview = await manager.scan(f"{HOST}/", max_pages=10, max_depth=0)
        root_page = next(p for p in preview["pages"] if p["status"] == "ok")

        result = await manager.ingest(
            preview["scan_id"], [root_page["page_id"]],
            new_folder_name="Veille",
            target="knowledge",
        )
        assert result["target"] == "knowledge"
        assert result["indexed_count"] == 1
        node_id = result["indexed"][0]["node_id"]
        node = await m["knowledge"].get(node_id)
        assert node.source == f"{HOST}/"
        assert node.metadata.get("web_url") == f"{HOST}/"
        folder_contents = await m["folders"].list_folder_resources(result["folder"]["id"])
        assert ("knowledge", node_id) in {
            (r["resource_type"], r["resource_id"]) for r in folder_contents
        }
        # Aucun document RAG indexé (cible Knowledge ≠ indexation RAG).
        assert await m["rag"].list_documents() == []

    asyncio.run(scenario())


def test_ingest_validation_errors():
    """Scan inconnu, pages inconnues, cible invalide → ValueError."""
    async def scenario():
        fetcher = _make_site()
        manager, _m = _manager(fetcher)
        preview = await manager.scan(f"{HOST}/", max_pages=1, max_depth=0)
        root_page = next(p for p in preview["pages"] if p["status"] == "ok")

        with pytest.raises(ValueError, match="introuvable"):
            await manager.ingest("ghost-scan", [root_page["page_id"]])
        with pytest.raises(ValueError, match="inconnues"):
            await manager.ingest(preview["scan_id"], ["ghost-page"])
        with pytest.raises(ValueError, match="Cible inconnue"):
            await manager.ingest(
                preview["scan_id"], [root_page["page_id"]],
                target="database", new_collection_name="X",
            )
        with pytest.raises(ValueError, match="collection_id ou new_collection_name"):
            await manager.ingest(preview["scan_id"], [root_page["page_id"]])

        # Sélection d'une page non-ok (disallowed) : rien n'est indexé.
        private_id = None
        for page in preview["pages"]:
            if page["status"] != "ok":
                private_id = page["page_id"]
        if private_id:
            result = await manager.ingest(
                preview["scan_id"], [private_id],
                target="knowledge", new_folder_name="Vide",
            )
            assert result["indexed_count"] == 0

    asyncio.run(scenario())
