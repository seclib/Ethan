"""Tests — exécution réelle du builtin web_search via ToolExecutor.

Régression : ``ToolExecutor._run_tool`` était un stub (« MVP: simulation »)
qui ne faisait AUCUNE recherche — ``builtin_web_search`` ne retournait que
``{"status": "ok", "params": ...}`` et DeepResearchEngine ne trouvait jamais
de sources (il lisait en plus ``result.result`` au lieu de ``result.output``).

Invariants :
- ``ToolManager.execute_by_capability('search')`` exécute réellement
  WebSearchManager (Core → Core) et peupl ``ToolResult.output`` ;
- une query manquante → ToolResult.status == 'failed' (ValueError catchée) ;
- un outil builtin sans exécuteur → 'failed' (NotImplementedError catchée) ;
- DeepResearchEngine._search() lit désormais ``result.output`` et retourne
  des sources normalisées.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from core.knowledge.web_search import SearchResponse, SearchResult, WebSearchManager
from core.research.engine import DeepResearchEngine
from core.tools.manager import ToolManager
from core.tools.types import Tool, ToolContext


class _AllowAllEnforcer:
    """Enforcer permissif : ces tests ciblent le pipeline d'exécution des
    builtins, pas la politique security (CTO P0-2 : ``ToolExecutor`` exige
    désormais un enforcer — l'évaluation réelle vit dans tests/security/)."""

    async def check(self, tool, params, context):  # noqa: ARG002
        return None


def _search_response() -> SearchResponse:
    return SearchResponse(
        query="ethan",
        engine="duckduckgo",
        results=[
            SearchResult(
                title="ETHAN docs",
                url="https://docs.example.com",
                snippet="Documentation",
                source_engine="duckduckgo",
                rank=1,
            )
        ],
        total_found=1,
        search_time_ms=42,
    )


@pytest.mark.asyncio
async def test_builtin_web_search_executes_real_pipeline() -> None:
    manager = ToolManager(policy_enforcer=_AllowAllEnforcer())
    context = ToolContext(query="search ethan")
    result = await manager.execute_by_capability("search", {"query": "ethan"}, context)
    # Sans mock : le builtin route vers WebSearchManager — best-effort réseau.
    # On vérifie ici uniquement le contrat de forme (jamais de crash).
    assert result.status in ("success", "failed", "timeout")
    if result.status == "success":
        assert isinstance(result.output, dict)
        assert {"status", "results", "total_found"} <= set(result.output)


@pytest.mark.asyncio
async def test_builtin_web_search_output_populated() -> None:
    """ToolResult.output porte les résultats normalisés (bug régression)."""
    manager = ToolManager(policy_enforcer=_AllowAllEnforcer())
    with patch.object(WebSearchManager, "search", AsyncMock(return_value=_search_response())):
        context = ToolContext(query="search ethan")
        result = await manager.execute_by_capability("search", {"query": "ethan"}, context)
    assert result.status == "success"
    assert result.output is not None
    assert result.output["total_found"] == 1
    assert result.output["results"][0]["url"] == "https://docs.example.com"
    assert result.output["results"][0]["source_engine"] == "duckduckgo"


@pytest.mark.asyncio
async def test_builtin_web_search_missing_query_fails_gracefully() -> None:
    """Query manquante → ValueError → ToolResult.failed (jamais de crash)."""
    manager = ToolManager(policy_enforcer=_AllowAllEnforcer())
    context = ToolContext(query="search")
    result = await manager.execute_by_capability("search", {}, context)
    assert result.status == "failed"
    assert "query" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_builtin_unknown_tool_fails_gracefully() -> None:
    """Un builtin sans exécuteur → NotImplementedError → failed."""
    manager = ToolManager(policy_enforcer=_AllowAllEnforcer())
    ghost = Tool(
        id="builtin_ghost",
        name="ghost_tool",
        description="outil sans implémentation",
        capabilities=["ghost"],
        provider="builtin",
    )
    manager.register_tool(ghost)
    context = ToolContext(query="ghost")
    result = await manager.execute_by_capability("ghost", {"x": 1}, context)
    assert result.status == "failed"
    assert "no executor" in (result.error or "")


@pytest.mark.asyncio
async def test_deep_research_reads_output_and_finds_sources() -> None:
    """Régression : DeepResearchEngine._search() lit ``result.output``."""
    manager = ToolManager(policy_enforcer=_AllowAllEnforcer())
    engine = DeepResearchEngine(provider_manager=object(), tool_manager=manager)
    with patch.object(WebSearchManager, "search", AsyncMock(return_value=_search_response())):
        sources = await engine._search("ethan")
    assert len(sources) == 1
    assert sources[0]["url"] == "https://docs.example.com"
    assert sources[0]["title"] == "ETHAN docs"


@pytest.mark.asyncio
async def test_deep_research_search_failure_is_best_effort() -> None:
    """Un échec réseau ne fait pas échouer la recherche deep research."""
    manager = ToolManager(policy_enforcer=_AllowAllEnforcer())
    engine = DeepResearchEngine(provider_manager=object(), tool_manager=manager)
    with patch.object(
        WebSearchManager,
        "search",
        AsyncMock(side_effect=RuntimeError("network down")),
    ):
        sources = await engine._search("ethan")
    assert sources == []
