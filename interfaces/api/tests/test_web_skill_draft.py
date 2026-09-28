"""Tests API — routes /v1/web-skill-draft.

Contrats HTTP (Core-only : le routeur ne contient aucune logique) :
- 503 si le service n'est pas injecté ;
- 422 si topic vide, sources vides ou > 50 (plafond absolu) ;
- 200 : brouillon avec sources, is_active=False (jamais d'activation auto).
"""

from __future__ import annotations

import asyncio

import pytest
from core.skills.web_draft import WebSkillDraftService
from fastapi import HTTPException
from interfaces.api.routers import web_skill_draft as routes


class _FakeIngest:
    async def scan(self, url: str, *, max_depth: int = 0, max_pages: int = 1):
        return {
            "scan_id": "scan-1",
            "pages": [{"page_id": "p1", "url": url, "title": "T", "status": "ok", "text": "x"}],
            "errors": [],
        }


@pytest.fixture
def draft_service():
    service = WebSkillDraftService(web_ingest=_FakeIngest())
    routes.set_web_skill_draft_service(service)
    yield service
    routes.set_web_skill_draft_service(None)


def test_503_sans_service():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.draft_skill({"topic": "x", "sources": ["https://a.example.com"]}))
    assert exc.value.status_code == 503


def test_limits_expose_cap(draft_service):  # noqa: ARG001
    resp = asyncio.run(routes.limits())
    assert resp["max_sources"] == 50


def test_draft_retourne_brouillon_inactif(draft_service):  # noqa: ARG001
    resp = asyncio.run(
        routes.draft_skill({"topic": "OSINT", "sources": [{"url": "https://docs.example.com/a"}]})
    )
    assert resp["is_active"] is False
    assert resp["kind"] == "prompt"
    assert resp["max_sources"] == 50
    assert resp["sources"][0]["url"] == "https://docs.example.com/a"
    assert resp["content"]


def test_draft_rejects_topic_vide_422(draft_service):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.draft_skill({"topic": "  ", "sources": ["https://a.example.com"]}))
    assert exc.value.status_code == 422


def test_draft_rejects_sources_vides_422(draft_service):  # noqa: ARG001
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.draft_skill({"topic": "x", "sources": []}))
    assert exc.value.status_code == 422


def test_draft_rejects_sources_au_dela_du_plafond_422(draft_service):  # noqa: ARG001
    urls = [{"url": f"https://e{i}.example.com"} for i in range(51)]
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.draft_skill({"topic": "x", "sources": urls}))
    assert exc.value.status_code == 422
    assert "plafond" in str(exc.value.detail)


def test_draft_urls_conserves_dans_la_reponse(draft_service):  # noqa: ARG001
    resp = asyncio.run(
        routes.draft_skill(
            {
                "topic": "osint",
                "sources": [
                    {"url": "https://a.example.com", "title": "A"},
                    "https://b.example.com",
                ],
            }
        )
    )
    urls = {s["url"] for s in resp["sources"]}
    assert urls == {"https://a.example.com", "https://b.example.com"}
