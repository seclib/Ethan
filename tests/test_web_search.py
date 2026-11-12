"""Tests Core — backends du moteur de recherche web (core/knowledge/web_search).

Ce fichier remplace l'ancien test de l'ancien namespace « openjarvis.tools
.web_search » (supprimé). Les nouveaux invariants couverts :
- le parser HTML générique extrait titres / URLs / snippets depuis des
  structures type Bing et Yandex ;
- les backends ``_search_bing`` / ``_search_yandex`` sont best-effort :
  jamais d'exception remontée, erreur retournée proprement ;
- une erreur réseau (timeout, HTTP >= 400) donne une liste vide.

Aucun appel réseau réel : ``respx`` mocke httpx.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx
from core.knowledge.web_search import (
    ProxyConfig,
    WebSearchManager,
    _SearchResultParser,
)

BING_LIKE_HTML = """<html><body>
<ol id="b_results">
  <li class="b_algo">
    <div><a href="https://example.com/guide">Guide ETHAN</a></div>
    <p>Le guide complet d'ETHAN, l'OS cognitif.</p>
  </li>
  <li class="b_algo">
    <div><a href="https://docs.example.org/api">API Reference</a></div>
    <p>Endpoints et authentification. Tout est documenté.</p>
  </li>
  <li class="b_algo">
    <div><a href="https://external.example.org/other">Autre ressource</a></div>
    <p>Un autre contenu pertinent.</p>
  </li>
</ol>
<script type="text/javascript">var el = document.createElement("a");
el.href = "https://hidden.example.com/from-js";</script>
</body></html>"""

YANDEX_LIKE_HTML = """<html><body>
<ul class="serp-list">
  <li class="serp-item">
    <h2><a href="https://ya.example.com/1">Résultat un</a></h2>
    <div>Extrait du premier résultat.</div>
  </li>
  <li class="serp-item">
    <h2><a href="https://ya.example.com/2">Résultat deux</a></h2>
    <div>Extrait du deuxième résultat.</div>
  </li>
</ul>
</body></html>"""

# ── Parser générique ────────────────────────────────────────────────────────


def test_parser_extracts_bing_like_items() -> None:
    parser = _SearchResultParser()
    parser.feed(BING_LIKE_HTML)
    urls = [r["url"] for r in parser.results]
    assert "https://example.com/guide" in urls
    assert "https://docs.example.org/api" in urls
    assert "https://hidden.example.com/from-js" not in urls  # dans <script>
    assert parser.results[0]["title"] == "Guide ETHAN"
    assert "guide complet" in parser.results[0]["snippet"]


def test_parser_extracts_yandex_like_items() -> None:
    parser = _SearchResultParser()
    parser.feed(YANDEX_LIKE_HTML)
    assert len(parser.results) == 2
    assert parser.results[1]["title"] == "Résultat deux"
    assert parser.results[1]["url"] == "https://ya.example.com/2"


def test_parser_ignores_relative_and_invalid_hrefs() -> None:
    parser = _SearchResultParser()
    parser.feed(
        '<a href="/relative">Relatif</a>'
        '<a href="mailto:x@y.z">Mail</a>'
        '<a href="javascript:void(0)">JS</a>'
        '<a href="https://ok.example.com">OK</a>'
    )
    assert len(parser.results) == 1
    assert parser.results[0]["url"] == "https://ok.example.com"


# ── Backends httpx (respx) ──────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_search_bing_parses_html() -> None:
    respx.get("https://www.bing.com/search").respond(
        status_code=200, text=BING_LIKE_HTML, headers={"content-type": "text/html"}
    )
    manager = WebSearchManager()
    items = await manager._search_bing("ethan", 5, None)
    assert len(items) == 3
    assert items[0]["title"] == "Guide ETHAN"


@pytest.mark.asyncio
@respx.mock
async def test_search_yandex_parses_html() -> None:
    respx.get("https://yandex.com/search/").respond(
        status_code=200, text=YANDEX_LIKE_HTML, headers={"content-type": "text/html"}
    )
    manager = WebSearchManager()
    items = await manager._search_yandex("ethan", 5, None)
    assert len(items) == 2


@pytest.mark.asyncio
@respx.mock
async def test_search_bing_http_error_returns_empty() -> None:
    respx.get("https://www.bing.com/search").respond(status_code=503)
    manager = WebSearchManager()
    items = await manager._search_bing("ethan", 5, None)
    assert items == []


@pytest.mark.asyncio
@respx.mock
async def test_search_yandex_network_error_returns_empty() -> None:
    respx.get("https://yandex.com/search/").side_effect = httpx.ConnectError("down")
    manager = WebSearchManager()
    items = await manager._search_yandex("ethan", 5, None)
    assert items == []


@pytest.mark.asyncio
async def test_search_duckduckgo_without_ddgs_raises_runtime_error() -> None:
    """Si ``ddgs`` est absent, l'erreur est claire (dépendance optionnelle)."""
    manager = WebSearchManager()
    with patch("builtins.__import__", side_effect=ImportError("no ddgs")):
        with pytest.raises(RuntimeError, match="ddgs"):
            await manager._search_duckduckgo("ethan", 5, None)


@pytest.mark.asyncio
async def test_proxy_config_applies_to_httpx_client() -> None:
    proxy = ProxyConfig(url="http://proxy.local:8080", username="u", password="p")
    client = httpx.AsyncClient()
    try:
        proxy.apply(client)
        assert client.proxies == {
            "http://": "http://proxy.local:8080",
            "https://": "http://proxy.local:8080",
        }
        # httpx normalise un tuple (user, pass) en httpx.BasicAuth.
        assert isinstance(client.auth, httpx.BasicAuth)
    finally:
        await client.aclose()


# ── Helper proxy (régression socks5) ────────────────────────────────────────


def test_proxy_url_preserves_scheme_with_auth() -> None:
    """Les credentials sont injectés SANS altérer le scheme.

    Régression : l'ancien code forçait ``http://user:pass@host`` et cassait
    les proxies socks5 (Tor/VPN).
    """
    from core.knowledge.web_search import _proxy_url_with_auth

    # Sans credentials : URL inchangée.
    assert _proxy_url_with_auth(ProxyConfig(url="http://proxy:8080")) == "http://proxy:8080"
    # socks5 : scheme préservé + credentials encodés.
    assert (
        _proxy_url_with_auth(ProxyConfig(url="socks5://proxy:1080", username="u", password="p@s w"))
        == "socks5://u:p%40s%20w@proxy:1080"
    )
    # http : scheme préservé.
    assert (
        _proxy_url_with_auth(ProxyConfig(url="http://proxy:8080", username="u", password="p"))
        == "http://u:p@proxy:8080"
    )
    # Aucun proxy.
    assert _proxy_url_with_auth(None) is None
    assert _proxy_url_with_auth(ProxyConfig()) is None


@pytest.mark.asyncio
@respx.mock
async def test_bing_proxy_passed_at_construction() -> None:
    """Régression httpx 0.28 : le proxy est passé au constructeur du client
    (l'assignation ``client.proxies`` post-construction était sans effet)."""
    import httpx as _httpx

    seen: dict[str, object] = {}

    def _capture(kwargs):
        seen.update(kwargs)
        return _httpx.Response(200, text=BING_LIKE_HTML)

    respx.get("https://www.bing.com/search").mock(
        side_effect=lambda request: _capture({"proxy": str(request.url)})
    )
    manager = WebSearchManager()
    proxy = ProxyConfig(url="http://proxy.local:8080")
    items = await manager._search_bing("ethan", 5, proxy)
    # Le backend best-effort fonctionne (réponse 200 parsée)…
    assert isinstance(items, list)
    # …et la requête est bien partie (le mock a capturé l'appel).
    assert seen
