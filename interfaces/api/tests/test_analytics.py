"""Tests réels Analytics — GET /v1/analytics/summary et GET /v1/evaluations.

Utilise les VRAIS managers du Core (AnalyticsManager, EvaluationManager,
core/metrics/analytics.py + core/learning/evaluations.py) sur un
CoreRecordStore en mémoire : aucune donnée factice, les routes sont appelées
directement (pattern test_groups.py / test_plugins.py) après injection via
set_capability_managers.
"""

import pytest

from core.learning.evaluations import EvaluationManager
from core.metrics.analytics import AnalyticsManager
from core.state.record_store import CoreRecordStore
from routers.capabilities import (
    CapabilityManagers,
    get_analytics_summary,
    list_evaluations,
    set_capability_managers,
)


@pytest.fixture()
def core_managers():
    """Managers Core réels sur store mémoire + injection dans le router."""
    store = CoreRecordStore()
    managers = CapabilityManagers(
        analytics=AnalyticsManager(store=store),
        evaluations=EvaluationManager(store=store),
    )
    set_capability_managers(managers)
    return managers


@pytest.mark.asyncio
async def test_summary_empty(core_managers):
    """Résumé sur un store vide : zéros du Core, pas d'invention frontend."""
    summary = await get_analytics_summary()
    assert summary == {"total_tokens": 0, "total_cost": 0.0, "event_count": 0}


@pytest.mark.asyncio
async def test_summary_with_real_events(core_managers):
    """Événements réels enregistrés via AnalyticsManager → totaux exacts."""
    await core_managers.analytics.record_event(
        "chat_completion", tokens_in=100, tokens_out=50, cost=0.0025,
    )
    await core_managers.analytics.record_event(
        "chat_completion", tokens_in=10, tokens_out=20, cost=0.0005,
    )

    summary = await get_analytics_summary()
    assert summary["total_tokens"] == 180
    assert summary["total_cost"] == pytest.approx(0.003)
    assert summary["event_count"] == 2


@pytest.mark.asyncio
async def test_summary_requires_manager():
    """Sans manager injecté → 503 (HTTPException), pas un crash 500."""
    set_capability_managers(CapabilityManagers())
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await get_analytics_summary()
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_evaluations_empty(core_managers):
    assert await list_evaluations() == []


@pytest.mark.asyncio
async def test_evaluations_list_with_results(core_managers):
    """Évaluation réelle créée par EvaluationManager + résultat ajouté."""
    created = await core_managers.evaluations.create(
        name="Retrieval quality",
        criteria=[{"name": "relevance", "threshold": 0.8}],
        target="rag.retriever",
        description="Évalue la pertinence du RAG",
    )
    await core_managers.evaluations.add_result(
        created["id"], {"score": 0.87, "passed": True},
    )

    evaluations = await list_evaluations()
    assert len(evaluations) == 1
    evaluation = evaluations[0]
    assert evaluation["name"] == "Retrieval quality"
    assert evaluation["target"] == "rag.retriever"
    assert evaluation["criteria"] == [{"name": "relevance", "threshold": 0.8}]
    assert len(evaluation["results"]) == 1
    assert evaluation["results"][0]["score"] == 0.87
    assert "timestamp" in evaluation["results"][0]