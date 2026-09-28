"""Tests Core — moteur de recherche web multi-moteurs (core/knowledge/web_search).

Déterministes : les backends réseau sont mockés ; aucun appel réseau réel.
Invariants vérifiés :
- le catalogue des moteurs est exposé (id + libellé) ;
- les réponses sont normalisées (title, url, snippet, source_engine, rank) ;
- les plafonds durs sont respectés (MAX_RESULTS_HARD_CAP) ;
- un backend en échec ne fait pas échouer la recherche (best-effort,
  erreur portée dans ``metadata``) ;
- les requêtes invalides (query vide, moteur inconnu) lèvent ValueError ;
- la recherche multi-moteurs agrège les réponses en parallèle.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from core.knowledge.web_search import (
    MAX_RESULTS_HARD_CAP,
    MIN_RESULTS,
    ProxyConfig,
    SearchProvider,
    SearchProviderRegistry,
    SearchResponse,
    SearchResult,
    WebSearchManager,
    validate_max_results,
)


def test_list_engines_returns_catalogue() -> None:
    manager = WebSearchManager()
    engines = manager.list_engines()
    ids = [e["id"] for e in engines]
    assert "duckduckgo" in ids
    assert "bing" in ids
    assert "yandex" in ids
    for entry in engines:
        assert {"id", "label"} <= set(entry)


def test_search_result_to_dict_shape() -> None:
    result = SearchResult(
        title="Titre",
        url="https://example.com/",
        snippet="Extrait",
        source_engine="duckduckgo",
        rank=1,
    )
    data = result.to_dict()
    assert data["title"] == "Titre"
    assert data["url"] == "https://example.com/"
    assert data["snippet"] == "Extrait"
    assert data["source_engine"] == "duckduckgo"
    assert data["rank"] == 1
    assert result.hostname == "example.com"


def test_search_response_to_dict_shape() -> None:
    response = SearchResponse(
        query="test",
        engine="duckduckgo",
        results=[SearchResult(title="A", url="https://a.example.com")],
        total_found=1,
        search_time_ms=12,
    )
    data = response.to_dict()
    assert data["query"] == "test"
    assert data["engine"] == "duckduckgo"
    assert data["total_found"] == 1
    assert data["search_time_ms"] == 12
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "A"


def test_search_result_truncation_bounds() -> None:
    """Les champs title/snippet/url sont bornés (pas de réponse démesurée)."""
    result = SearchResult(
        title="x" * 1000,
        url="https://example.com/" + "p" * 3000,
        snippet="y" * 2000,
    )
    assert len(result.title) <= 300
    assert len(result.url) <= 2000
    assert len(result.snippet) <= 600


@pytest.mark.asyncio
async def test_search_empty_query_raises() -> None:
    manager = WebSearchManager()
    with pytest.raises(ValueError, match="vide"):
        await manager.search("   ")


@pytest.mark.asyncio
async def test_search_unknown_engine_raises() -> None:
    manager = WebSearchManager()
    with pytest.raises(ValueError, match="Moteur inconnu"):
        await manager.search("query", engine="google")


@pytest.mark.asyncio
async def test_search_normalizes_backend_items() -> None:
    """Les items bruts du backend sont normalisés : dédup + rang + moteur."""
    manager = WebSearchManager()
    raw = [
        {"title": "Premier", "url": "https://a.example.com", "snippet": "Extrait A"},
        {"title": "Doublon", "url": "https://a.example.com", "snippet": "Extrait A-2"},
        {"title": "Ignoré (pas http)", "url": "mailto:x@y.z", "snippet": "s"},
        {"title": "", "url": "https://fallback.example.com", "snippet": ""},
    ]

    async def _fake_duckduckgo(*_args, **_kwargs):
        return raw

    with patch.object(manager, "_search_duckduckgo", _fake_duckduckgo):
        resp = await manager.search("query")
    assert resp.total_found == 2
    assert resp.results[0].url == "https://a.example.com"
    assert resp.results[0].rank == 1
    assert resp.results[0].source_engine == "duckduckgo"
    assert resp.results[1].url == "https://fallback.example.com"
    assert not resp.metadata  # aucune erreur


@pytest.mark.asyncio
async def test_search_backend_error_is_best_effort() -> None:
    """Un backend qui lève ne fait pas échouer la recherche : l'erreur est
    portée dans ``metadata`` et la réponse reste valide."""
    manager = WebSearchManager()

    async def _boom(*_args, **_kwargs):
        raise RuntimeError("network down")

    with patch.object(manager, "_search_duckduckgo", _boom):
        resp = await manager.search("query")
    assert resp.total_found == 0
    assert resp.results == []
    assert "network down" in resp.metadata.get("error", "")


@pytest.mark.asyncio
async def test_search_max_results_capped() -> None:
    """Le plafond dur est appliqué même si le backend retourne plus d'items."""
    manager = WebSearchManager(max_results=5)
    raw = [
        {"title": f"Résultat {i}", "url": f"https://a.example{i}.com", "snippet": "s"}
        for i in range(100)
    ]

    async def _fake_duckduckgo(*_args, **_kwargs):
        return raw

    with patch.object(manager, "_search_duckduckgo", _fake_duckduckgo):
        resp = await manager.search("query")
    assert resp.total_found <= MAX_RESULTS_HARD_CAP
    assert resp.total_found == 5


@pytest.mark.asyncio
async def test_search_multiple_aggregates() -> None:
    manager = WebSearchManager()

    async def _fake(query: str, engine: str, max_results: int, proxy):
        return SearchResponse(query=query, engine=engine, results=[], total_found=0)

    with patch.object(manager, "search", _fake):
        responses = await manager.search_multiple("query", engines=["duckduckgo", "bing"])
    assert set(responses) == {"duckduckgo", "bing"}


@pytest.mark.asyncio
async def test_search_multiple_unknown_engine_raises() -> None:
    manager = WebSearchManager()
    with pytest.raises(ValueError, match="Moteurs inconnus"):
        await manager.search_multiple("query", engines=["duckduckgo", "google"])


@pytest.mark.asyncio
async def test_proxy_config_auth_property() -> None:
    proxy = ProxyConfig(url="http://proxy.local:8080", username="user", password="pass")
    assert proxy.auth == ("user", "pass")
    assert ProxyConfig(url="http://proxy.local:8080").auth is None


# ── Invariants Web Research : borne 50 / refus strict / robustesse ──────────


def test_constants_define_fifty_cap() -> None:
    """Le plafond absolu de pages par recherche est de 50."""
    assert MAX_RESULTS_HARD_CAP == 50
    assert MIN_RESULTS == 1


def test_validate_max_results_accepts_boundaries() -> None:
    assert validate_max_results(1) == 1
    assert validate_max_results(50) == 50
    assert validate_max_results("50") == 50


def test_validate_max_results_rejects_above_cap() -> None:
    with pytest.raises(ValueError, match="50"):
        validate_max_results(51)
    with pytest.raises(ValueError, match="50"):
        validate_max_results("51")


@pytest.mark.parametrize(
    "invalid",
    ["abc", "", "51", 0, -1, 1.5, True, None, [5], {"n": 5}],
)
def test_validate_max_results_rejects_invalid(invalid: object) -> None:
    """Valeur invalide (type, nulle, negative ou >50) -> refus strict."""
    with pytest.raises(ValueError):
        validate_max_results(invalid)  # type: ignore[arg-type]


def test_manager_ctor_rejects_over_cap() -> None:
    """Le constructeur refuse strictement au-dela du plafond (jamais de clamp)."""
    with pytest.raises(ValueError, match="50"):
        WebSearchManager(max_results=51)


# ── Fournisseur factice (deterministe, aucun reseau) ─────────────────────────


class _FakeProvider(SearchProvider):
    """Provider de test injectable via le registre (extensibilite Core)."""

    id = "fake"
    label = "Fake"

    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        *,
        available: bool = True,
        exc: Exception | None = None,
    ) -> None:
        self._items = list(items or [])
        self._available = available
        self._exc = exc
        self.calls: list[tuple[str, int]] = []

    def is_available(self) -> bool:
        return self._available

    async def fetch(
        self,
        manager: WebSearchManager,
        query: str,
        max_results: int,
        proxy: ProxyConfig | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append((query, max_results))
        if self._exc is not None:
            raise self._exc
        return list(self._items)


def _manager_with(registry: SearchProviderRegistry) -> WebSearchManager:
    return WebSearchManager(registry=registry)


@pytest.mark.asyncio
async def test_search_rejects_limit_above_50_at_call() -> None:
    """Une requete demandant > 50 résultats est refusee (422 en amont)."""
    mgr = WebSearchManager()
    with pytest.raises(ValueError, match="50"):
        await mgr.search("query", engine="duckduckgo", max_results=51)


@pytest.mark.asyncio
async def test_search_accepts_limit_50() -> None:
    """La limite de 50 est acceptee et appliquee comme plafond dur."""
    items = [{"title": f"T{i}", "url": f"https://e{i}.example.com"} for i in range(60)]
    reg = SearchProviderRegistry()
    reg.register(_FakeProvider(items=items))
    mgr = _manager_with(reg)
    resp = await mgr.search("query", engine="fake", max_results=50)
    assert resp.total_found == 50
    assert len(resp.results) == 50


@pytest.mark.asyncio
async def test_search_dedup_normalizes_urls() -> None:
    """Déduplication robuste : www / slash final / fragment / casse."""
    reg = SearchProviderRegistry()
    reg.register(
        _FakeProvider(
            items=[
                {"title": "A", "url": "HTTPS://Example.COM/page/"},
                {"title": "B", "url": "http://example.com/page"},
                {"title": "C", "url": "https://example.com/page#section"},
                {"title": "D", "url": "https://www.example.com/page"},
                {"title": "E", "url": "https://other.example.com/page"},
            ]
        )
    )
    mgr = _manager_with(reg)
    resp = await mgr.search("query", engine="fake", max_results=50)
    assert resp.total_found == 2
    assert len([r for r in resp.results if r.domain == "example.com"]) == 1
    assert resp.results[0].source_engine == "fake"
    assert resp.results[0].rank == 1


@pytest.mark.asyncio
async def test_search_provider_unavailable_is_best_effort() -> None:
    """Provider indisponible : reponse valide mais vide, metadata signale l'absence."""
    reg = SearchProviderRegistry()
    reg.register(_FakeProvider(available=False))
    mgr = _manager_with(reg)
    resp = await mgr.search("query", engine="fake", max_results=5)
    assert resp.results == []
    assert resp.total_found == 0
    assert resp.metadata.get("provider_unavailable") is True
    assert "indisponible" in resp.metadata.get("error", "").lower()


@pytest.mark.asyncio
async def test_search_provider_fetch_error_carried_in_metadata() -> None:
    """Un backend qui lève : best-effort, erreur portee dans metadata."""
    reg = SearchProviderRegistry()
    reg.register(_FakeProvider(exc=RuntimeError("timeout")))
    mgr = _manager_with(reg)
    resp = await mgr.search("query", engine="fake", max_results=5)
    assert resp.total_found == 0
    assert resp.results == []
    assert "timeout" in resp.metadata.get("error", "")


@pytest.mark.asyncio
async def test_search_empty_response_is_clean() -> None:
    """Réponse vide du backend : reponse totalement propre."""
    reg = SearchProviderRegistry()
    reg.register(_FakeProvider(items=[]))
    mgr = _manager_with(reg)
    resp = await mgr.search("query", engine="fake", max_results=5)
    assert resp.total_found == 0
    assert resp.results == []
    assert resp.metadata == {}


@pytest.mark.asyncio
async def test_search_result_exposes_domain_and_metadata() -> None:
    """Chaque résultat expose : titre, url, domaine, snippet, métadonnées."""
    reg = SearchProviderRegistry()
    reg.register(
        _FakeProvider(
            items=[
                {
                    "title": "Guide",
                    "url": "https://docs.example.com/guide",
                    "snippet": "extrait",
                    "rank": 7,
                    "category": "documentation",
                    "score": 0.9,
                }
            ]
        )
    )
    mgr = _manager_with(reg)
    resp = await mgr.search("query", engine="fake", max_results=5)
    data = resp.results[0].to_dict()
    assert data["domain"] == "docs.example.com"
    assert data["title"] == "Guide"
    assert data["url"] == "https://docs.example.com/guide"
    assert data["snippet"] == "extrait"
    assert data["source_engine"] == "fake"
    assert data["rank"] == 1
    assert data["metadata"] == {"category": "documentation", "score": 0.9}


def test_register_custom_provider_extends_catalog() -> None:
    """Extensibilité : un nouveau moteur s'ajoute sans modifier le Core."""
    reg = SearchProviderRegistry()
    reg.register(_FakeProvider())
    assert "fake" in reg
    assert {"id": "fake", "label": "Fake"} in reg.catalog()
    mgr = _manager_with(reg)
    assert {"id": "fake", "label": "Fake"} in mgr.list_engines()
    assert "duckduckgo" not in reg
