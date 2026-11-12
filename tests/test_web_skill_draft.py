"""Tests — Brouillon de Skill depuis des sources Web (core/skills/web_draft).

Contrats clés :
- plafond strict de 50 sources, déduplication d'URLs, erreurs isolées ;
- le LLM ne produit qu'un TEXTE de brouillon (jamais de persistance, jamais
  d'activation) ; repli déterministe garanti sans LLM ;
- les URLs des sources sont conservées dans le brouillon.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from core.skills.web_draft import (
    SKILL_DRAFT_MAX_SOURCES,
    SkillDraft,
    WebSkillDraftService,
)


class _FakeIngest:
    """WebIngestionManager minimal (scan contrôlé simulé)."""

    def __init__(self, fail_urls: set[str] | None = None) -> None:
        self.fail_urls = fail_urls or set()
        self.scanned: list[str] = []

    async def scan(self, url: str, *, max_depth: int = 0, max_pages: int = 1):
        self.scanned.append(url)
        if url in self.fail_urls:
            raise RuntimeError("network down")
        return {
            "scan_id": "scan-1",
            "pages": [
                {
                    "page_id": "p1",
                    "url": url,
                    "title": f"Page {url}",
                    "status": "ok",
                    "text": f"Contenu de {url} — " + "x" * 300,
                }
            ],
            "errors": [],
        }


class _FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    async def chat(self, messages, model=None, temperature=None):
        self.calls += 1
        return self.response


class _FakeProviders:
    """ProviderManager minimal (pattern web_inspiration)."""

    def __init__(self, response: str) -> None:
        self.provider = _FakeLLMProvider(response)

        class _Registry:
            def get_provider(self, _pid):
                return None  # remplacé ci-dessous

        self._registry = _Registry()
        self._registry.get_provider = lambda _pid: self.provider  # type: ignore[method-assign]

    async def get_default_provider(self):
        return {"provider_id": "fake"}

    async def get_active_model(self, _pid):
        return "fake-model"


URL_A = "https://docs.example.com/a"
URL_B = "https://blog.example.com/b"


def _service(**kwargs) -> tuple[WebSkillDraftService, _FakeIngest]:
    ingest = _FakeIngest()
    return WebSkillDraftService(web_ingest=ingest, **kwargs), ingest


def test_plafond_50_sources():
    svc, _ = _service()
    assert svc.max_sources == SKILL_DRAFT_MAX_SOURCES == 50
    urls = [{"url": f"https://e{i}.example.com"} for i in range(51)]
    with pytest.raises(ValueError, match="plafond"):
        asyncio.run(svc.draft("osint", urls))


def test_50_sources_acceptees():
    svc, _ = _service()
    urls = [{"url": f"https://e{i}.example.com"} for i in range(50)]
    draft = asyncio.run(svc.draft("osint", urls, use_llm=False))
    assert len(draft.sources) == 50


def test_selection_vide_et_topic_vide_refuses():
    svc, _ = _service()
    with pytest.raises(ValueError, match="topic"):
        asyncio.run(svc.draft("  ", [{"url": URL_A}]))
    with pytest.raises(ValueError, match="source"):
        asyncio.run(svc.draft("osint", []))


def test_dedup_urls_et_scheme_non_http_refuse():
    svc, _ = _service()
    draft = asyncio.run(
        svc.draft(
            "osint",
            [
                {"url": URL_A, "title": "A"},
                {"url": URL_A.rstrip("/") + "/", "title": "A dup"},
                "ftp://bad.example.com",
                URL_B,
            ],
            use_llm=False,
        )
    )
    assert [s.url for s in draft.sources] == [URL_A, URL_B]


def test_recuperation_et_analyse_par_source():
    svc, ingest = _service()
    draft = asyncio.run(svc.draft("osint", [URL_A, URL_B], use_llm=False))
    assert ingest.scanned == [URL_A, URL_B]
    assert all(s.status == "ok" for s in draft.sources)
    assert all("Contenu de" in s.excerpt for s in draft.sources)
    assert len(draft.sources[0].excerpt) <= 1200


def test_erreur_isolee_par_source():
    svc, _ = _service()
    svc._web_ingest = _FakeIngest(fail_urls={URL_B})  # type: ignore[assignment]
    draft = asyncio.run(svc.draft("osint", [URL_A, URL_B], use_llm=False))
    statuses = {s.url: s.status for s in draft.sources}
    assert statuses == {URL_A: "ok", URL_B: "unreachable"}


def test_fallback_sans_llm_contient_urls_et_actif_false():
    svc, _ = _service()
    draft = asyncio.run(svc.draft("OSINT, CVE", [URL_A, URL_B], use_llm=False))
    assert isinstance(draft, SkillDraft)
    assert draft.llm_used is False
    assert draft.fallback_used is True
    assert draft.is_active is False
    assert draft.name.startswith("Skill —")
    assert URL_A in draft.content and URL_B in draft.content
    assert "web-inspiration" in draft.tags


def test_llm_json_valide_retenu():
    payload = json.dumps(
        {
            "name": "OSINT Analyst",
            "description": "Analyse OSINT guidée",
            "content": "# Rôle\nAnalyse les sources [1] [2] avec rigueur.",
        }
    )
    svc, _ = _service(provider_manager=_FakeProviders(payload))
    draft = asyncio.run(svc.draft("osint", [URL_A], use_llm=True))
    assert draft.llm_used is True
    assert draft.fallback_used is False
    assert draft.name == "OSINT Analyst"
    assert "[1]" in draft.content
    assert draft.is_active is False


def test_llm_reponse_invalide_repli_deterministe():
    svc, _ = _service(provider_manager=_FakeProviders("pas du JSON du tout"))
    draft = asyncio.run(svc.draft("osint", [URL_A], use_llm=True))
    assert draft.llm_used is False
    assert draft.fallback_used is True
    assert URL_A in draft.content


def test_use_llm_false_ignore_le_provider():
    providers = _FakeProviders(json.dumps({"name": "x", "content": "y"}))
    svc, _ = _service(provider_manager=providers)
    draft = asyncio.run(svc.draft("osint", [URL_A], use_llm=False))
    assert providers.provider.calls == 0
    assert draft.fallback_used is True


def test_brouillon_jamais_persiste_par_le_service():
    """Le service ne possède AUCUN accès d'écriture au SkillStore."""
    svc, _ = _service()
    for forbidden in ("create", "save", "persist", "activate", "skill_store"):
        assert not hasattr(svc, forbidden)
    public_methods = [name for name in dir(WebSkillDraftService) if not name.startswith("_")]
    assert set(public_methods) <= {
        "draft",
        "set_provider_manager",
        "max_sources",
    }  # aucune méthode de persistance/activation exposée
    draft = asyncio.run(svc.draft("osint", [URL_A], use_llm=False))
    assert not hasattr(draft, "skill_id")  # pas d'id : jamais persisté tel quel


def test_urls_conservees_dans_le_brouillon():
    svc, _ = _service()
    draft = asyncio.run(
        svc.draft(
            "osint",
            [{"url": URL_A, "title": "Docs", "domain": "docs.example.com"}],
            use_llm=False,
        )
    )
    payload = draft.to_dict()
    assert payload["sources"][0]["url"] == URL_A
    assert payload["sources"][0]["title"] == "Docs"
    assert payload["is_active"] is False
