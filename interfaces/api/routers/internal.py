"""Internal API Router — endpoints internes des modules (Audit, Budget,
Approval, Facts, SkillLab).

Accessible via /internal/* pour le dashboard web et les clients.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
from pathlib import Path
import threading
from datetime import datetime, timedelta
from typing import Any

from core.approval import ApprovalEngine
from core.audit import AuditCategory, AuditDecision, AuditStore
from core.auth import Permission, rbac
from core.hrot.durable import DurableHrotStore
from core.auth.service_identities import ServiceIdentityManager, ServiceRegistryUnavailable
from core.auth.principal import PrincipalType
from core.cost import BudgetGuard, BudgetScope, CostTracker
from core.facts import Fact, FactCategory, FactStatus, FactStore
from core.skills.lab import SkillLab
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from interfaces.api.auth import current_user_id, get_service_identity_manager, require_permission, require_service_operation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])

_service_audit_pg_pools = {}
_service_audit_pg_error = False

# ── Service audit event idempotence (process-local, guarded) ───────────
_service_audit_lock = threading.Lock()
_service_audit_events: dict[str, dict[str, Any]] = {}


# ── Instances globales (initialisées au démarrage) ──────────────────

_audit: AuditStore | None = None
_budget_guard: BudgetGuard | None = None
_cost_tracker: CostTracker | None = None
_fact_store: FactStore | None = None
_approval_engine: ApprovalEngine | None = None
_human_root: Any | None = None
_skill_lab: SkillLab | None = None


def init_modules(
    pg_conn: Any = None,
    publish_fn: Any = None,
    audit_log_fn: Any = None,
) -> None:
    """Initialise tous les nouveaux modules (appelé au startup)."""
    global _audit, _budget_guard, _cost_tracker, _fact_store, _approval_engine, _human_root, _skill_lab

    _audit = AuditStore(pg_conn=pg_conn, publish_fn=publish_fn)
    _cost_tracker = CostTracker(pg_conn=pg_conn)
    _budget_guard = BudgetGuard(tracker=_cost_tracker, publish_fn=audit_log_fn)
    _fact_store = FactStore(pg_conn=pg_conn, publish_fn=publish_fn)
    _approval_engine = ApprovalEngine(publish_fn=publish_fn, audit_log_fn=audit_log_fn)

    try:
        from core.human_root import HumanRoot
        _human_root = HumanRoot(approval_engine=_approval_engine)
        _approval_engine.set_human_root(_human_root)
        logger.info("Human Root of Trust (HROT) connected to ApprovalEngine")
    except Exception as exc:
        _human_root = None
        logger.warning("Failed to initialize HumanRoot: %s", exc)

    _skill_lab = None
    global _hrot_store
    _hrot_store = DurableHrotStore()
    try:
        import docker as _docker_sdk

        _docker_client = _docker_sdk.from_env()
        _docker_client.ping()  # échoue si le daemon est injoignable
        _skill_lab = SkillLab(docker_client=_docker_client, publish_fn=publish_fn)
        logger.info("SkillLab ready (Docker sandbox available)")
    except Exception as exc:
        # Sandbox obligatoire : sans Docker le lab reste inutilisable
        # (les endpoints renvoient 503) — aucun fallback local.
        _skill_lab = SkillLab(docker_client=None, publish_fn=publish_fn)
        logger.warning("SkillLab initialized WITHOUT Docker (%s) — endpoints will return 503", exc)

    logger.info("Internal modules initialized: audit, budget, facts, approval, human_root, skilllab")


def get_audit_store() -> AuditStore | None:
    """Expose l'AuditStore aux autres routers (lecture de l'instance, journal append-only)."""
    return _audit


def get_approval_engine() -> ApprovalEngine | None:
    """Expose the Core approval engine to other thin API routers."""
    return _approval_engine


def get_human_root() -> Any | None:
    """Expose le Human Root of Trust comme autorité racine."""
    return _human_root


# ═══════════════════════════════════════════════════════════════════════
# AUDIT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════


@router.get("/audit", dependencies=[Depends(require_permission(Permission.ADMIN))])
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


@router.get("/audit/summary", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def get_audit_summary(since: str | None = None):
    """Résumé des entrées d'audit."""
    if _audit is None:
        return {"error": "Audit module not initialized"}, 503
    since_dt = datetime.fromisoformat(since) if since else None
    return _audit.summary(since=since_dt)


@router.get("/audit/search", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def search_audit(q: str = Query("", min_length=1)):
    """Recherche dans l'audit."""
    if _audit is None:
        # Fix : un tuple (dict, 503) est sérialisé comme corps JSON par
        # FastAPI (statut 200) — il faut une vraie HTTPException.
        raise HTTPException(status_code=503, detail="Audit module not initialized")
    entries = _audit.search(q)
    return [e.to_dict() for e in entries]


@router.post("/audit/log", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def log_audit_entry(entry: dict[str, Any]):
    """Crée une entrée d'audit manuellement."""
    if _audit is None:
        raise HTTPException(status_code=503, detail="Audit module not initialized")
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


@router.get("/budget/status", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def get_budget_status():
    """Statut budgétaire complet."""
    if _budget_guard is None:
        return {"error": "Budget module not initialized"}, 503
    return _budget_guard.status()


@router.post("/budget/reserve", dependencies=[Depends(require_permission(Permission.WRITE))])
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
    return {
        "allowed": allowed,
        "remaining": _budget_guard.remaining(scope, data.get("scope_id", "")),
    }


@router.post("/budget/record", dependencies=[Depends(require_permission(Permission.WRITE))])
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


@router.get("/budget/alerts", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def get_budget_alerts():
    """Alertes budgétaires (limitées, depuis l'audit)."""
    if _audit is None:
        return [], 200
    entries = _audit.recent(limit=20, category=AuditCategory("budget"))
    return [e.to_dict() for e in entries]


@router.get("/budget/daily", dependencies=[Depends(require_permission(Permission.ADMIN))])
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


@router.get("/facts", dependencies=[Depends(require_permission(Permission.ADMIN))])
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


@router.get("/facts/search", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def search_facts(q: str = Query("", min_length=1)):
    """Recherche plein texte dans les faits."""
    if _fact_store is None:
        return {"error": "Facts module not initialized"}, 503
    results = _fact_store.search(q)
    return [{"fact": r.fact.to_dict(), "score": r.score} for r in results]


@router.get("/facts/{fact_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def get_fact(fact_id: str):
    """Récupère un fait par son ID."""
    if _fact_store is None:
        return {"error": "Facts module not initialized"}, 503
    fact = _fact_store.get(fact_id)
    if fact is None:
        raise HTTPException(404, f"Fact {fact_id} not found")
    return fact.to_dict()


@router.get(
    "/facts/{fact_id}/relations", dependencies=[Depends(require_permission(Permission.ADMIN))]
)
async def get_fact_relations(fact_id: str):
    """Relations d'un fait."""
    if _fact_store is None:
        return {"error": "Facts module not initialized"}, 503
    return [r.to_dict() for r in _fact_store.list_relations(fact_id)]


@router.post("/facts", dependencies=[Depends(require_permission(Permission.ADMIN))])
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


@router.get("/approval/pending", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def list_pending_approvals():
    """Liste les approbations en attente."""
    if _approval_engine is None:
        return {"error": "Approval module not initialized"}, 503
    return _approval_engine.list_pending()


@router.post("/approval/resolve", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def resolve_approval(data: dict[str, Any], request: Request):
    """Résout une approbation."""
    if _approval_engine is None:
        return {"error": "Approval module not initialized"}, 503
    from core.approval.types import ApprovalAuthority
    user = getattr(request.state, "user", "human")
    authority = ApprovalAuthority(
        principal_id=str(user),
        principal_type="HUMAN",
        authenticated=True,
        permissions=("ADMIN",) if rbac.has_permission(str(getattr(request.state, "token_payload", {}).get("role", "")), Permission.ADMIN) else (),
        human=True,
        trusted=True,
    )
    resolved = _approval_engine.resolve(
        request_id=data.get("request_id", ""),
        approved=bool(data.get("approved", False)),
        reason=data.get("reason", ""),
        responder=user,
        authority=authority,
    )
    return {"resolved": resolved}


# ═══════════════════════════════════════════════════════════════════════
# SKILLLAB ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════


@router.post("/skilllab/test", dependencies=[Depends(require_permission(Permission.EXECUTE))])
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


@router.post("/skilllab/validate", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def validate_plugin(data: dict[str, Any]):
    """Valide un dossier de plugin."""
    if _skill_lab is None:
        return {"error": "SkillLab module not initialized"}, 503
    result = await _skill_lab.validate_plugin(data.get("path", ""))
    return result.to_dict()


@router.get("/skilllab/results", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def list_skilllab_results(skill_name: str | None = None):
    """Liste les résultats SkillLab."""
    if _skill_lab is None:
        return [], 200
    results = _skill_lab.list_results(skill_name=skill_name)
    return [r.to_dict() for r in results]


# ═══════════════════════════════════════════════════════════════════════
# SERVICE AUDIT EVENTS
# ═══════════════════════════════════════════════════════════════════════


class ServiceAuditEvent(BaseModel):
    """Strict event payload accepted from SERVICE identities only."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=1, max_length=64)
    occurred_at: datetime
    resource_type: str = Field(min_length=1, max_length=64)
    resource_id: str | None = Field(default=None, max_length=256)
    severity: str = Field(default="info", pattern="^(debug|info|warning|error|critical)$")
    details: dict[str, Any] = Field(default_factory=dict)


def _service_audit_content_hash(event: ServiceAuditEvent, principal) -> str:
    payload = {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "occurred_at": event.occurred_at.isoformat(),
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
        "severity": event.severity,
        "details": event.details,
        "service_id": principal.subject_id,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()





async def _get_service_audit_pg_pool():
    global _service_audit_pg_error
    import asyncio

    loop = asyncio.get_running_loop()
    pool = _service_audit_pg_pools.get(id(loop))
    if pool is not None:
        return pool
    if _service_audit_pg_error:
        return None
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        import asyncpg

        _service_audit_pg_pools[id(loop)] = await asyncpg.create_pool(dsn, min_size=1, max_size=2)
        return _service_audit_pg_pools[id(loop)]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Service audit PostgreSQL pool unavailable: %s", exc)
        _service_audit_pg_error = True
        return None

async def _ensure_service_audit_pg_tables(pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS service_audit_events (
                event_id TEXT PRIMARY KEY,
                service_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                audit_entry_id TEXT NOT NULL,
                received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                category TEXT NOT NULL,
                decision TEXT NOT NULL DEFAULT 'auto',
                action TEXT NOT NULL DEFAULT '',
                actor TEXT NOT NULL DEFAULT 'system',
                source TEXT NOT NULL DEFAULT 'system',
                details JSONB NOT NULL DEFAULT '{}',
                correlation_id TEXT NOT NULL DEFAULT '',
                tags TEXT[] NOT NULL DEFAULT '{}'
            )
            """
        )


async def _record_service_audit_event_postgres(event, content_hash, service_id, service_component, request_id):
    backend = os.getenv("AUDIT_STORAGE_BACKEND", "auto").strip().lower()
    if backend == "jsonl":
        return None
    if backend in ("postgres", "postgresql", "pg"):
        pool = await _get_service_audit_pg_pool()
        if pool is None:
            raise HTTPException(status_code=503, detail="Audit storage unavailable")
    else:
        pool = await _get_service_audit_pg_pool()
        if pool is None:
            if os.getenv("DATABASE_URL"):
                raise HTTPException(status_code=503, detail="Audit storage unavailable")
            return None
    await _ensure_service_audit_pg_tables(pool)
    entry_id = f"aud_{__import__('uuid').uuid4().hex[:12]}"
    from datetime import datetime, timezone

    async with pool.acquire() as conn:
        async with conn.transaction():
            inserted = await conn.fetchval(
                """
                INSERT INTO service_audit_events (event_id, service_id, content_hash, audit_entry_id)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (event_id) DO NOTHING
                RETURNING event_id
                """,
                event.event_id,
                service_id,
                content_hash,
                entry_id,
            )
            if inserted is not None:
                await conn.execute(
                    """
                    INSERT INTO audit_log (id, timestamp, category, decision, action, actor, source, details, correlation_id, tags)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10)
                    """,
                    entry_id,
                    datetime.now(timezone.utc),
                    "security",
                    "auto",
                    event.event_type,
                    f"service:{service_id}",
                    str(service_component or "service"),
                    __import__("json").dumps({
                        "service_event": True,
                        "event_id": event.event_id,
                        "occurred_at": event.occurred_at.isoformat(),
                        "resource_type": event.resource_type,
                        "resource_id": event.resource_id,
                        "severity": event.severity,
                        "details": event.details,
                    }),
                    request_id,
                    ["service", service_id],
                )
                return {"status": "created", "event_id": event.event_id, "audit_entry_id": entry_id}

            row = await conn.fetchrow(
                "SELECT content_hash, audit_entry_id FROM service_audit_events WHERE event_id = $1",
                event.event_id,
            )
            if row is None:
                raise HTTPException(status_code=503, detail="Audit storage unavailable")
            if row["content_hash"] != content_hash:
                raise HTTPException(status_code=409, detail="Audit event idempotency conflict")
            return {"status": "duplicate", "event_id": event.event_id, "audit_entry_id": row["audit_entry_id"]}


@router.post(
    "/services/audit-events",
    dependencies=[Depends(require_service_operation("audit.events.write"))],
)
async def submit_service_audit_event(data: dict[str, Any], request: Request):
    """Accept an auditable event from a verified SERVICE principal only."""
    if _audit is None:
        raise HTTPException(status_code=503, detail="Audit module not initialized")

    principal = getattr(request.state, "principal", None)
    if principal is None or getattr(principal, "principal_type", None) != PrincipalType.SERVICE:
        raise HTTPException(status_code=401, detail="Service authentication required")

    service_id = str(getattr(principal, "subject_id", "")).strip()
    service_component = None
    service_record = getattr(request.state, "service_identity_record", None)
    if isinstance(service_record, dict):
        service_component = service_record.get("component")

    # Parse after identity/permission checks so an unauthenticated request
    # cannot force payload parsing as a privileged operation.
    try:
        event = ServiceAuditEvent.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    content_hash = _service_audit_content_hash(event, principal)

    pg_result = await _record_service_audit_event_postgres(
        event=event,
        content_hash=content_hash,
        service_id=service_id,
        service_component=service_component,
        request_id=str(getattr(request.state, "request_id", "") or ""),
    )
    if pg_result is not None:
        return pg_result

    # Local fallback for environments without a configured PostgreSQL pool.
    registry_path = Path.home() / ".ethan" / "audit" / "service_audit_events.jsonl"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = registry_path.with_suffix(".lock")
    lock_path.touch(exist_ok=True)

    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        existing_row = None
        if registry_path.exists():
            for line in registry_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    candidate = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if candidate.get("event_id") == event.event_id:
                    existing_row = candidate
                    break

        if existing_row is not None:
            if existing_row.get("content_hash") != content_hash:
                raise HTTPException(status_code=409, detail="Audit event idempotency conflict")
            return {"status": "duplicate", "event_id": event.event_id, "audit_entry_id": existing_row.get("audit_entry_id")}

        try:
            entry = _audit.log(
                category=AuditCategory.SECURITY,
                decision=AuditDecision.AUTO,
                action=event.event_type,
                actor=f"service:{service_id}",
                source=str(service_component or "service"),
                details={
                    "service_event": True,
                    "event_id": event.event_id,
                    "occurred_at": event.occurred_at.isoformat(),
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id,
                    "severity": event.severity,
                    "details": event.details,
                },
                correlation_id=str(getattr(request.state, "request_id", "") or ""),
                tags=["service", service_id],
            )
        except Exception as exc:  # noqa: BLE001 - keep failure opaque and fail closed
            logger.warning("Service audit event persistence failed: %s", exc)
            raise HTTPException(status_code=503, detail="Audit storage unavailable") from exc

        registry_line = {
            "event_id": event.event_id,
            "content_hash": content_hash,
            "audit_entry_id": entry.id,
            "service_id": service_id,
        }
        with registry_path.open("a", encoding="utf-8") as registry_file:
            registry_file.write(json.dumps(registry_line, sort_keys=True) + "\n")
            registry_file.flush()
            os.fsync(registry_file.fileno())

    return {"status": "created", "event_id": event.event_id, "audit_entry_id": entry.id}



# ═══════════════════════════════════════════════════════════════════════
# SERVICE IDENTITY PROVISIONING (HUMAN ADMIN)
# ═══════════════════════════════════════════════════════════════════════


class CreateServiceIdentityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: str = Field(min_length=1, max_length=128)
    component: str = Field(min_length=1, max_length=128)
    allowed_operations: list[str] = Field(min_length=1)
    status: str = Field(default="active", pattern="^(active|disabled)$")


def _service_manager(request: Request) -> ServiceIdentityManager | None:
    manager = getattr(request.app.state, "service_identity_manager", None)
    if manager is None:
        manager = get_service_identity_manager()
    return manager



@router.post("/services", status_code=201, dependencies=[Depends(require_permission(Permission.ADMIN))])
async def create_service_identity(data: CreateServiceIdentityRequest, request: Request):
    manager = _service_manager(request)
    if manager is None:
        raise HTTPException(status_code=503, detail="Service identity manager not initialized")

    principal = getattr(request.state, "principal", None)
    token_payload = getattr(request.state, "token_payload", {}) or {}
    if getattr(principal, "principal_type", None) != PrincipalType.HUMAN:
        raise HTTPException(status_code=403, detail="Human administrator required")
    if token_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator permission required")

    admin = current_user_id(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")

    await _require_hrot_approval(
        request,
        data.service_id,
        "service.provision",
        {"service_id": data.service_id, "component": data.component, "allowed_operations": data.allowed_operations, "status": data.status},
    )
    try:
        record = await manager.create_service(
            data.service_id,
            data.component,
            data.allowed_operations,
            created_by=admin,
            status=data.status,
        )
    except ValueError as exc:
        msg = str(exc)
        if "already exists" in msg:
            raise HTTPException(status_code=409, detail=msg) from exc
        raise HTTPException(status_code=422, detail=msg) from exc
    except ServiceRegistryUnavailable as exc:
        raise HTTPException(status_code=503, detail="Service identity registry unavailable") from exc

    if _audit is None:
        raise HTTPException(status_code=503, detail="Audit storage unavailable")
    try:
        _audit.log(
            category=AuditCategory.SECURITY,
            decision=AuditDecision.AUTO,
            action="service.identity.create",
            actor=admin,
            source="internal",
            details={
                "service_id": record["service_id"],
                "component": record["component"],
                "allowed_operations": record["allowed_operations"],
                "status": record["status"],
            },
            correlation_id=str(getattr(request.state, "request_id", "") or ""),
            tags=["service", "provisioning", record["service_id"]],
        )
    except Exception as exc:  # noqa: BLE001 - audit failure is reported, persistence already done
        logger.warning("Service identity create audit failed: %s", exc)
        raise HTTPException(status_code=503, detail="Audit storage unavailable") from exc

    return {
        "service_id": record["service_id"],
        "component": record["component"],
        "allowed_operations": record["allowed_operations"],
        "status": record["status"],
        "created_by": record["created_by"],
        "version": record["version"],
    }


@router.get("/services", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def list_service_identities(request: Request):
    manager = _service_manager(request)
    if manager is None:
        raise HTTPException(status_code=503, detail="Service identity manager not initialized")
    principal = getattr(request.state, "principal", None)
    token_payload = getattr(request.state, "token_payload", {}) or {}
    if getattr(principal, "principal_type", None) != PrincipalType.HUMAN or token_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Human administrator required")

    records = await manager.list_services()
    return [
        {
            "service_id": rec["service_id"],
            "component": rec["component"],
            "allowed_operations": rec.get("allowed_operations", []),
            "status": rec.get("status"),
            "created_by": rec.get("created_by"),
            "version": rec.get("version"),
        }
        for rec in records
        if isinstance(rec, dict)
    ]


@router.get("/services/{service_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def get_service_identity(service_id: str, request: Request):
    manager = _service_manager(request)
    if manager is None:
        raise HTTPException(status_code=503, detail="Service identity manager not initialized")
    principal = getattr(request.state, "principal", None)
    token_payload = getattr(request.state, "token_payload", {}) or {}
    if getattr(principal, "principal_type", None) != PrincipalType.HUMAN or token_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Human administrator required")
    record = await manager.service_record(service_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Service identity not found")
    try:
        import core.auth.service_identities as _service_module
        if isinstance(record, str):
            raise HTTPException(status_code=404, detail="Service identity not found")
    except Exception:
        pass
    return {
        "service_id": record["service_id"],
        "component": record["component"],
        "allowed_operations": record.get("allowed_operations", []),
        "status": record.get("status"),
        "created_by": record.get("created_by"),
        "version": record.get("version"),
    }


# ═══════════════════════════════════════════════════════════════════════
# SERVICE TOKEN ISSUE / RENEWAL (HUMAN ADMIN + SERVICE SELF)
# ═══════════════════════════════════════════════════════════════════════


@router.post("/services/{service_id}/issue-token", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def issue_service_token(service_id: str, request: Request):
    manager = _service_manager(request)
    if manager is None:
        raise HTTPException(status_code=503, detail="Service identity manager not initialized")
    principal = getattr(request.state, "principal", None)
    token_payload = getattr(request.state, "token_payload", {}) or {}
    if getattr(principal, "principal_type", None) != PrincipalType.HUMAN or token_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Human administrator required")

    await _require_hrot_approval(request, service_id, "service.issue", {"service_id": service_id})
    try:
        token = await manager.issue_token(service_id)
    except ServiceRegistryUnavailable as exc:
        raise HTTPException(status_code=503, detail="Service identity registry unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if _audit is not None:
        _audit.log(
            category=AuditCategory.SECURITY,
            decision=AuditDecision.AUTO,
            action="service.token.issue",
            actor=current_user_id(request) or "admin",
            source="internal",
            details={"service_id": service_id},
            correlation_id=str(getattr(request.state, "request_id", "") or ""),
            tags=["service", "token-issue", service_id],
        )
    return {"token": token, "token_type": "bearer"}


@router.post("/services/renew", dependencies=[])
async def renew_service_token(request: Request):
    principal = getattr(request.state, "principal", None)
    if not isinstance(principal, object) or getattr(principal, "principal_type", None) != PrincipalType.SERVICE:
        raise HTTPException(status_code=403, detail="Service authentication required")

    service_id = str(getattr(principal, "subject_id", "")).strip()
    manager = _service_manager(request)
    if manager is None:
        raise HTTPException(status_code=503, detail="Service identity manager not initialized")

    token_payload = getattr(request.state, "token_payload", {}) or {}
    try:
        record = await manager.service_record(service_id)
    except ServiceRegistryUnavailable as exc:
        raise HTTPException(status_code=503, detail="Service identity registry unavailable") from exc
    if not isinstance(record, dict) or record.get("status") != "active":
        raise HTTPException(status_code=401, detail="Service authentication required")

    token_operations = {
        str(operation).strip()
        for operation in (token_payload.get("allowed_operations") or [])
        if str(operation).strip()
    }
    registry_operations = {
        str(operation).strip()
        for operation in (record.get("allowed_operations") or [])
        if str(operation).strip()
    }
    effective_operations = (token_operations or registry_operations) & registry_operations
    if not effective_operations:
        raise HTTPException(status_code=403, detail="Service operation not authorized")

    try:
        new_token = await manager.issue_token(service_id, allowed_operations=sorted(effective_operations))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    old_rotation = str(token_payload.get("rotation_id") or "")
    old_credential = str(token_payload.get("credential_id") or "")
    if old_rotation and old_rotation != record.get("rotation_id"):
        raise HTTPException(status_code=401, detail="Service credential is no longer valid")
    if old_credential and old_credential != record.get("credential_id"):
        raise HTTPException(status_code=401, detail="Service credential is no longer valid")

    if _audit is not None:
        _audit.log(
            category=AuditCategory.SECURITY,
            decision=AuditDecision.AUTO,
            action="service.token.renew",
            actor=f"service:{service_id}",
            source=str(record.get("component") or "service"),
            details={"service_id": service_id},
            correlation_id=str(getattr(request.state, "request_id", "") or ""),
            tags=["service", "token-renew", service_id],
        )

    return {"token": new_token, "token_type": "bearer", "expires_in": 900}


@router.post("/services/{service_id}/rotate", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def rotate_service_identity(service_id: str, request: Request):
    manager = _service_manager(request)
    if manager is None:
        raise HTTPException(status_code=503, detail="Service identity manager not initialized")
    principal = getattr(request.state, "principal", None)
    token_payload = getattr(request.state, "token_payload", {}) or {}
    if getattr(principal, "principal_type", None) != PrincipalType.HUMAN or token_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Human administrator required")

    await _require_hrot_approval(request, service_id, "service.rotate", {"service_id": service_id})
    record = await manager.service_record(service_id)
    if not isinstance(record, dict):
        raise HTTPException(status_code=404, detail="Service identity not found")
    if record.get("status") != "active":
        raise HTTPException(status_code=409, detail="Service identity is not active")

    idempotency_key = (
        request.headers.get("Idempotency-Key")
        or request.headers.get("X-Idempotency-Key")
    )
    rotated = await manager.rotate_credential(service_id, request_key=idempotency_key)
    if not isinstance(rotated, dict):
        raise HTTPException(status_code=503, detail="Service identity rotation failed")

    if _audit is None:
        raise HTTPException(status_code=503, detail="Audit storage unavailable")
    try:
        _audit.log(
            category=AuditCategory.SECURITY,
            decision=AuditDecision.AUTO,
            action="service.identity.rotate",
            actor=current_user_id(request) or "admin",
            source="internal",
            details={
                "service_id": rotated["service_id"],
                "rotation_id": rotated["rotation_id"],
                "version": rotated["version"],
            },
            correlation_id=str(getattr(request.state, "request_id", "") or ""),
            tags=["service", "rotation", service_id],
        )
    except Exception as exc:  # noqa: BLE001 - audit failure is reported, persistence already done
        logger.warning("Service identity rotation audit failed: %s", exc)
        raise HTTPException(status_code=503, detail="Audit storage unavailable") from exc

    return {
        "service_id": rotated["service_id"],
        "status": rotated["status"],
        "credential_id": rotated["credential_id"],
        "rotation_id": rotated["rotation_id"],
        "version": rotated["version"],
    }


# ═══════════════════════════════════════════════════════════════════════
# DURABLE HROT APPROVALS
# ═══════════════════════════════════════════════════════════════════════


class HrotApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: str = Field(min_length=1, max_length=128)
    operation: str = Field(min_length=1, max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int = Field(default=300, ge=1, le=3600)


class HrotResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    reason: str = Field(default="", max_length=500)


def _hrot_store_instance() -> DurableHrotStore | None:
    global _hrot_store  # noqa: PLW0602
    if _hrot_store is None:
        _hrot_store = DurableHrotStore()
    return _hrot_store


def _canonical_operation_hash(service_id, operation, parameters):
    import hashlib, json

    payload = {"service_id": service_id, "operation": operation, "parameters": parameters}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


async def _require_hrot_approval(request: Request, service_id: str, operation: str, parameters: dict[str, Any]):
    approval_id = request.headers.get("X-HROT-Approval-Id") or (request.query_params.get("approval_id"))
    if not approval_id:
        raise HTTPException(status_code=403, detail="HROT approval required")
    store = _hrot_store_instance()
    if store is None:
        raise HTTPException(status_code=503, detail="HROT store unavailable")
    record = await store.get(approval_id)
    if record is None:
        raise HTTPException(status_code=403, detail="Unknown HROT approval")
    if record.service_id != service_id or record.operation != operation:
        raise HTTPException(status_code=403, detail="HROT approval scope mismatch")
    expected_hash = hashlib.sha256(
        json.dumps(
            {
                "service_id": service_id,
                "operation": operation,
                "parameters": parameters,
                "requester": record.requester,
                "requester_type": record.requester_type,
            },
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()
    if record.content_hash != expected_hash:
        raise HTTPException(status_code=403, detail="HROT approval content mismatch")
    if record.is_expired():
        raise HTTPException(status_code=403, detail="HROT approval expired")
    principal = getattr(request.state, "principal", None)
    user = getattr(principal, "subject_id", None) or getattr(request.state, "user", None)
    if record.requester != user and user is not None:
        raise HTTPException(status_code=403, detail="HROT approval requester mismatch")
    if record.status != "APPROVED":
        raise HTTPException(status_code=403, detail="HROT approval not approved")
    response = await store.consume(approval_id, user or "unknown", expected_hash)
    if isinstance(response, tuple) and not response[0]:
        raise HTTPException(status_code=409, detail=f"HROT approval cannot be consumed: {response[1]}")
    return record


@router.post("/hrot/requests", status_code=201, dependencies=[Depends(require_permission(Permission.ADMIN))])
async def create_hrot_approval(data: HrotApprovalRequest, request: Request):
    principal = getattr(request.state, "principal", None)
    token_payload = getattr(request.state, "token_payload", {}) or {}
    if getattr(principal, "principal_type", None) != PrincipalType.HUMAN or token_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Human administrator required")
    requester = current_user_id(request) or "unknown"
    operation = data.operation
    store = _hrot_store_instance()
    if store is None:
        raise HTTPException(status_code=503, detail="HROT store unavailable")
    approval = await store.create(
        requester=requester,
        requester_type="HUMAN",
        service_id=data.service_id,
        operation=operation,
        parameters=data.parameters,
        ttl_seconds=data.ttl_seconds,
    )
    return {
        "approval_id": approval.approval_id,
        "request_id": approval.request_id,
        "status": approval.status,
        "expires_at": approval.expires_at,
        "content_hash": approval.content_hash,
    }


@router.get("/hrot/requests/{approval_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def get_hrot_approval(approval_id: str, request: Request):
    store = _hrot_store_instance()
    if store is None:
        raise HTTPException(status_code=503, detail="HROT store unavailable")
    approval = await store.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="HROT approval not found")
    return approval.to_dict()


@router.get("/hrot/pending", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def list_pending_hrot(request: Request):
    store = _hrot_store_instance()
    if store is None:
        raise HTTPException(status_code=503, detail="HROT store unavailable")
    return [approval.to_dict() for approval in await store.list_pending()]


@router.post("/hrot/requests/{approval_id}/resolve", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def resolve_hrot_approval(approval_id: str, data: HrotResolveRequest, request: Request):
    principal = getattr(request.state, "principal", None)
    token_payload = getattr(request.state, "token_payload", {}) or {}
    if getattr(principal, "principal_type", None) != PrincipalType.HUMAN or token_payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Human administrator required")

    store = _hrot_store_instance()
    if store is None:
        raise HTTPException(status_code=503, detail="HROT store unavailable")
    approval = await store.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="HROT approval not found")
    if approval.is_expired():
        raise HTTPException(status_code=403, detail="HROT approval expired")
    if approval.requester == current_user_id(request):
        # Decision by the same principal is still recorded; true separation
        # requires an independent responder and is documented as a residual.
        pass
    if not await store.resolve(approval_id, current_user_id(request) or "unknown", data.approved, data.reason):
        raise HTTPException(status_code=409, detail="HROT approval cannot be resolved")
    return {"approval_id": approval_id, "status": "APPROVED" if data.approved else "DENIED"}


# Gate helper used by service admin endpoints when HROT is enforced.
