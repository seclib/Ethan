"""Internal API Router — Endpoints pour les nouveaux modules (Audit, Budget, Approval, Facts, SkillLab).

Accessible via /internal/* pour le dashboard web et les clients.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from core.audit import AuditStore, AuditCategory, AuditDecision
from core.cost import BudgetGuard, CostTracker, BudgetScope
from core.facts import FactStore, Fact, FactCategory, FactStatus
from core.approval import ApprovalEngine
from core.skills.lab import SkillLab

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])

# ── Instances globales (initialisées au démarrage) ──────────────────

_audit: AuditStore | None = None
_budget_guard: BudgetGuard | None = None
_cost_tracker: CostTracker | None = None
_fact_store: FactStore | None = None
_approval_engine: ApprovalEngine | None = None
_skill_lab: SkillLab | None = None


def init_modules(
    pg_conn: Any = None,
    publish_fn: Any = None,
    audit_log_fn: Any = None,
) -> None:
    """Initialise tous les nouveaux modules (appelé au startup)."""
    global _audit, _budget_guard, _cost_tracker, _fact_store, _approval_engine, _skill_lab

    _audit = AuditStore(pg_conn=pg_conn, publish_fn=publish_fn)
    _cost_tracker = CostTracker(pg_conn=pg_conn)
    _budget_guard = BudgetGuard(tracker=_cost_tracker, publish_fn=audit_log_fn)
    _fact_store = FactStore(pg_conn=pg_conn, publish_fn=publish_fn)
    _approval_engine = ApprovalEngine(publish_fn=publish_fn, audit_log_fn=audit_log_fn)
    _skill_lab = SkillLab(docker_client=None, publish_fn=publish_fn)

    logger.info("Internal modules initialized: audit, budget, facts, approval, skilllab")


# ═══════════════════════════════════════════════════════════════════════
# AUDIT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════


@router.get("/audit")
async def get_audit_entries(
    limit: int = Query(50, ge=1, le=1000),
    category: str | None = None,
    decision: str | None = None,
    since: str | None = None,
):
    """Récupère les entrées d'audit récentes."""
    if _audit is None:
        return {"error": "Audit module not initialized"}, 503

    since_dt = datetime.fromisoformat(since) if since else None
    cat = AuditCategory(category) if category else None
    dec = AuditDecision(decision) if decision else None

    entries = _audit.recent(limit=limit, category=cat, decision=dec, since=since_dt)
    return [e.to_dict() for e in entries]


@router.get("/audit/summary")
async def get_audit_summary(since: str | None = None):
    """Résumé des entrées d'audit."""
    if _audit is None:
        return {"error": "Audit module not initialized"}, 503
    since_dt = datetime.fromisoformat(since) if since else None
    return _audit.summary(since=since_dt)


@router.get("/audit/search")
async def search_audit(q: str = Query("", min_length=1)):
    """Recherche dans l'audit."""
    if _audit is None:
        return {"error": "Audit module not initialized"}, 503
    entries = _audit.search(q)
    return [e.to_dict() for e in entries]


@router.post("/audit/log")
async def log_audit_entry(entry: dict[str, Any]):
    """Crée une entrée d'audit manuellement."""
    if _audit is None:
        return {"error": "Audit module not initialized"}, 503
    result = _audit.log(
        category=entry.get("category", "system"),
        decision=entry.get("decision", "auto"),
        action=entry.get("action", ""),
        actor=entry.get("actor", "system"),
        details=entry.get("details"),
        correlation_id=entry.get("correlation_id", ""),
    )
    return result.to_dict()


# ═══════════════════════════════════════════════════════════════════════
# BUDGET ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════


@router.get("/budget/status")
async def get_budget_status():
    """Statut budgétaire complet."""
    if _budget_guard is None:
        return {"error": "Budget module not initialized"}, 503
    return _budget_guard.status()


@router.post("/budget/reserve")
async def reserve_budget(data: dict[str, Any]):
    """Réserve un montant sur un scope budgétaire."""
    if _budget_guard is None:
        return {"error": "Budget module not initialized"}, 503
    scope_str = data.get("scope", "global")
    try:
        scope = BudgetScope(scope_str)
    except ValueError:
        raise HTTPException(400, f"Invalid scope: {scope_str}")
    allowed = _budget_guard.reserve_sync(
        estimated_usd=float(data.get("estimated_usd", 0)),
        scope=scope,
        scope_id=data.get("scope_id", ""),
    )
    return {"allowed": allowed, "remaining": _budget_guard.remaining(scope, data.get("scope_id", ""))}


@router.post("/budget/record")
async def record_cost(data: dict[str, Any]):
    """Enregistre une dépense."""
    if _cost_tracker is None:
        return {"error": "Cost module not initialized"}, 503
    _cost_tracker.record(
        cost_usd=float(data.get("cost_usd", 0)),
        provider=data.get("provider", "unknown"),
        model=data.get("model", ""),
        tokens_input=int(data.get("tokens_input", 0)),
        tokens_output=int(data.get("tokens_output", 0)),
        scope=data.get("scope", "global"),
        scope_id=data.get("scope_id", ""),
        context=data.get("context", ""),
    )
    return {"status": "recorded"}


@router.get("/budget/alerts")
async def get_budget_alerts():
    """Alertes budgétaires (limitées, depuis l'audit)."""
    if _audit is None:
        return [], 200
    entries = _audit.recent(limit=20, category=AuditCategory("budget"))
    return [e.to_dict() for e in entries]


@router.get("/budget/daily")
async def get_daily_costs(days: int = Query(30, ge=1, le=365)):
    """Coûts journaliers."""
    if _cost_tracker is None:
        return [], 200
    results = []
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        cost = _cost_tracker.get_daily_cost(day)
        results.append({"date": day.isoformat(), "cost_usd": cost})
    return results


# ═══════════════════════════════════════════════════════════════════════
# FACTS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════


@router.get("/facts")
async def list_facts(
    limit: int = Query(20, ge=1, le=200),
    status: str | None = None,
    category: str | None = None,
):
    """Liste les faits atomiques."""
    if _fact_store is None:
        return {"error": "Facts module not initialized"}, 503
    if status and status != "tous":
        facts = _fact_store.list_by_status(FactStatus(status), limit=limit)
    elif category and category != "toutes":
        facts = _fact_store.list_by_category(FactCategory(category), limit=limit)
    else:
        facts = _fact_store.list_by_status(FactStatus.ACTIVE, limit=limit)
    return [f.to_dict() for f in facts]


@router.get("/facts/search")
async def search_facts(q: str = Query("", min_length=1)):
    """Recherche plein texte dans les faits."""
    if _fact_store is None:
        return {"error": "Facts module not initialized"}, 503
    results = _fact_store.search(q)
    return [{"fact": r.fact.to_dict(), "score": r.score} for r in results]


@router.get("/facts/{fact_id}")
async def get_fact(fact_id: str):
    """Récupère un fait par son ID."""
    if _fact_store is None:
        return {"error": "Facts module not initialized"}, 503
    fact = _fact_store.get(fact_id)
    if fact is None:
        raise HTTPException(404, f"Fact {fact_id} not found")
    return fact.to_dict()


@router.get("/facts/{fact_id}/relations")
async def get_fact_relations(fact_id: str):
    """Relations d'un fait."""
    if _fact_store is None:
        return {"error": "Facts module not initialized"}, 503
    return [r.to_dict() for r in _fact_store.list_relations(fact_id)]


@router.post("/facts")
async def create_fact(data: dict[str, Any]):
    """Crée un nouveau fait."""
    if _fact_store is None:
        return {"error": "Facts module not initialized"}, 503
    fact = Fact(
        subject=data.get("subject", ""),
        predicate=data.get("predicate", ""),
        object=data.get("object", ""),
        category=FactCategory(data.get("category", "knowledge")),
        source=data.get("source", "api"),
        confidence=float(data.get("confidence", 0.5)),
        importance=float(data.get("importance", 0.5)),
        tags=data.get("tags", []),
        metadata=data.get("metadata", {}),
    )
    _fact_store.insert(fact)
    return fact.to_dict()


# ═══════════════════════════════════════════════════════════════════════
# APPROVAL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════


@router.get("/approval/pending")
async def list_pending_approvals():
    """Liste les approbations en attente."""
    if _approval_engine is None:
        return {"error": "Approval module not initialized"}, 503
    return _approval_engine.list_pending()


@router.post("/approval/resolve")
async def resolve_approval(data: dict[str, Any]):
    """Résout une approbation."""
    if _approval_engine is None:
        return {"error": "Approval module not initialized"}, 503
    resolved = _approval_engine.resolve(
        request_id=data.get("request_id", ""),
        approved=bool(data.get("approved", False)),
        reason=data.get("reason", ""),
        responder=data.get("responder", "human"),
    )
    return {"resolved": resolved}


# ═══════════════════════════════════════════════════════════════════════
# SKILLLAB ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════


@router.post("/skilllab/test")
async def test_skill(data: dict[str, Any]):
    """Teste un skill candidat."""
    if _skill_lab is None:
        return {"error": "SkillLab module not initialized"}, 503
    result = await _skill_lab.test_skill(
        skill_code=data.get("code", ""),
        skill_name=data.get("name", "test"),
        test_input=data.get("input", ""),
        requirements=data.get("requirements"),
    )
    return result.to_dict()


@router.post("/skilllab/validate")
async def validate_plugin(data: dict[str, Any]):
    """Valide un dossier de plugin."""
    if _skill_lab is None:
        return {"error": "SkillLab module not initialized"}, 503
    result = await _skill_lab.validate_plugin(data.get("path", ""))
    return result.to_dict()


@router.get("/skilllab/results")
async def list_skilllab_results(skill_name: str | None = None):
    """Liste les résultats SkillLab."""
    if _skill_lab is None:
        return [], 200
    results = _skill_lab.list_results(skill_name=skill_name)
    return [r.to_dict() for r in results]