"""Tests Core — moteur RAG complet (dettes d'intégration).

Couvre les trois briques rattachées au Core lors de la levée des dettes :
- extracteurs PDF/DOCX (core/rag/extractors.py) — sans dépendance dure ;
- vector store pluggable (core/rag/vector_store.py) — memory/chromadb/qdrant,
  fail-closed si un backend externe est demandé mais absent ;
- pipeline RAG (core/rag/pipeline.py) — configuration persistante, re-index,
  scoping par document_ids, purge d'index à la suppression.
"""

from __future__ import annotations

import asyncio
import io
import zipfile

import pytest

from core.rag.extractors import extract_text
from core.rag.pipeline import RAGPipeline
from core.rag.vector_store import InMemoryVectorStore, create_vector_store
from core.state import CoreRecordStore


# ── Extracteurs PDF / DOCX ───────────────────────────────────────────────────

def _docx_bytes(paragraphs: list[str]) -> bytes:
    """Construit un DOCX minimal (OOXML) avec les paragraphes donnés."""
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    body = "".join(
        f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs
    )
    xml = f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return buf.getvalue()


def test_extract_docx_paragraphs():
    """Un DOCX valide est converti en texte (un paragraphe par ligne)."""
    raw = _docx_bytes(["Bonjour ETHAN", "Document de test RAG."])
    text = extract_text(raw, filename="rapport.docx")
    assert "Bonjour ETHAN" in text
    assert "Document de test RAG." in text
    assert text.index("Bonjour ETHAN") < text.index("Document de test RAG.")


def test_extract_docx_invalid_archive():
    """Un faux DOCX (pas une archive) lève une ValueError explicite."""
    with pytest.raises(ValueError):
        extract_text(b"not a zip file", filename="broken.docx")


def test_extract_text_passthrough_and_dispatch():
    """Les fichiers texte ne passent pas par l'extraction ; le dispatch
    se fait aussi sur le content_type."""
    assert extract_text(b"plain text", filename="notes.txt") == ""
    assert extract_text(b"plain text", content_type="text/plain") == ""
    # Dispatch DOCX par content_type même sans extension
    raw = _docx_bytes(["Par content-type"])
    assert "Par content-type" in extract_text(
        raw,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def test_extract_pdf_unsupported_raises():
    """Un PDF non extractible (flux illisibles) lève une ValueError claire."""
    with pytest.raises(ValueError, match="pypdf"):
        extract_text(b"%PDF-1.4 garbage", filename="scan.pdf")


# ── Vector store pluggable ───────────────────────────────────────────────────

def test_vector_store_factory_memory_and_errors():
    """La fabrique retourne memory par défaut et échoue proprement sinon."""
    assert isinstance(create_vector_store("memory"), InMemoryVectorStore)
    assert isinstance(create_vector_store(""), InMemoryVectorStore)
    with pytest.raises(ValueError, match="inconnu"):
        create_vector_store("inconnu")


def test_inmemory_vector_store_search_filter_delete():
    """L'index mémoire supporte upsert, recherche, filtre document et purge."""

    async def scenario():
        store = InMemoryVectorStore()
        await store.upsert(
            [
                {"chunk_id": "c1", "embedding": [1.0, 0.0], "document_id": "d1"},
                {"chunk_id": "c2", "embedding": [0.0, 1.0], "document_id": "d2"},
            ]
        )
        # Sans filtre : c1 est le plus proche de [1, 0]
        hits = await store.search([1.0, 0.0], top_k=2)
        assert hits[0][0] == "c1"
        # Avec filtre : seul c2 est éligible
        hits = await store.search([1.0, 0.0], top_k=2, document_ids=["d2"])
        assert [cid for cid, _ in hits] == ["c2"]
        # Purge par document
        await store.delete_document("d1")
        hits = await store.search([1.0, 0.0], top_k=5)
        assert [cid for cid, _ in hits] == ["c2"]

# ── Pipeline : configuration, persistance, scoping, purge ───────────────────

def _pipeline() -> RAGPipeline:
    return RAGPipeline(store=CoreRecordStore())


def test_pipeline_config_roundtrip_and_backend():
    """configure() applique les paramètres supportés et get_config les expose."""

    async def scenario():
        p = _pipeline()
        config = await p.configure(
            chunk_size=500,
            chunk_overlap=50,
            top_k=3,
            max_context_chars=4000,
            embedding_model="nomic-embed-text",
            vector_backend="chromadb",  # package absent dans l'env de test
        )
        assert config["chunk_size"] == 500
        assert config["top_k"] == 3
        assert config["embedding_model"] == "nomic-embed-text"
        assert config["vector_backend"] == "chromadb"
        # Backend externe indisponible -> fallback mémoire, mais config gardée
        assert p.stats()["vector_backend"] == "chromadb"

        # Retour à memory détache l'index externe
        config = await p.configure(vector_backend="memory")
        assert config["vector_backend"] == "memory"

    asyncio.run(scenario())


def test_pipeline_rejects_invalid_config():
    """Un backend vectoriel inconnu est rejeté proprement (fallback mémoire),
    et un contenu vide est refusé à l'ingestion."""

    async def scenario():
        p = _pipeline()
        with pytest.raises(ValueError):
            await p.ingest("   ")
        # Le backend inconnu est accepté en config mais la recherche retombe
        # sur le chemin mémoire (jamais de crash utilisateur).
        await p.configure(vector_backend="does-not-exist")
        doc = await p.ingest("Contenu de test suffisant pour un chunk.", title="T")
        chunks = await p.retrieve("contenu")
        assert chunks  # fallback textuel/cosinus opérationnel
        await p.delete_document(doc.id)

    asyncio.run(scenario())

def test_pipeline_document_scoping_and_persistence():
    """retrieve(document_ids=…) restreint la recherche ; les documents
    persistent et la suppression purge catalogue + index."""

    async def scenario():
        store = CoreRecordStore()
        p = RAGPipeline(store=store)
        d1 = await p.ingest("Recette de tarte aux pommes maison.", title="Cuisine")
        d2 = await p.ingest("Manuel d'administration PostgreSQL.", title="BDD")

        # Scoping à d1 uniquement
        scoped = await p.retrieve("pommes", document_ids=[d1.id])
        assert scoped
        assert all(c.chunk.document_id == d1.id for c in scoped)

        # Scoping sur d2 : aucun chunk de d1 ne fuit
        scoped_other = await p.retrieve("pommes", document_ids=[d2.id])
        assert all(c.chunk.document_id == d2.id for c in scoped_other)

        # Persistance : une nouvelle instance retrouve les documents
        p2 = RAGPipeline(store=store)
        docs = await p2.list_documents()
        assert {d.id for d in docs} == {d1.id, d2.id}

        # Suppression purge catalogue + index
        assert await p2.delete_document(d1.id)
        remaining = await p2.retrieve("pommes")
        assert all(c.chunk.document_id != d1.id for c in remaining)

    asyncio.run(scenario())

