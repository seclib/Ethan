"""Router mince pour l'Engineering Memory d'ETHAN."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.engineering_memory.models import (
    ConfidenceLevel,
    MemoryRecord,
    RecordOrigin,
    RecordType,
    SourceOfFactLevel,
)
from core.engineering_memory.service import EngineeringMemoryService
from core.engineering_memory.traceability import (
    AnomalyState,
    TraceabilityService,
    build_intervention_id,
    report_from_payload,
)
from core.engineering_memory.vault import VaultError, VaultService
from core.auth import Permission
from interfaces.api.auth import require_memory_scope, require_permission
from core.engineering_memory.validators import ValidationError

router = APIRouter(prefix="/v1", tags=["engineering-memory"])

memory_read_permission = require_permission(Permission.READ)
memory_record_permission = require_permission(Permission.RECORD)

# P2.8.3 — portee machine pour l'ingestion de tracabilite. Un plugin ou une
# CLI ne porte pas de role RBAC : il porte une portee, portee par le
# principal HROT. La meme dependance accepte une session humaine dispose
# de la permission `record`.
TRACEABILITY_SCOPE = "memory:traceability"
traceability_write_permission = require_memory_scope(TRACEABILITY_SCOPE, permission=Permission.RECORD)
traceability_read_permission = require_memory_scope(TRACEABILITY_SCOPE, permission=Permission.READ)

_traceability_service: TraceabilityService | None = None


def set_traceability_service(service: TraceabilityService | None) -> None:
    """Branche le service Core de tracabilite sur le router.

    Args:
        service: Service Core (cree par `main.py`).
    """
    global _traceability_service
    _traceability_service = service


def get_traceability_service() -> TraceabilityService:
    """Retourne le service Core de tracabilite.

    Returns:
        Service de tracabilite.

    Raises:
        HTTPException: 503 si le service n'a pas ete branche.
    """
    if _traceability_service is None:
        raise HTTPException(
            status_code=503,
            detail="Traceability service not initialized.",
        )
    return _traceability_service


def _root() -> Path:
    raw = os.environ.get("ETHAN_ENGINEERING_MEMORY_ROOT")
    if raw:
        return Path(raw)
    return Path("/home/fatsio/AI/Ethan/daena")


def _service() -> EngineeringMemoryService:
    return EngineeringMemoryService(root=_root())


def _vault() -> VaultService:
    return VaultService(root=_root())


@router.get("/memory/health", dependencies=[Depends(memory_read_permission)])
async def memory_health() -> dict[str, Any]:
    service = _service()
    return service.verify_integrity()


@router.post("/memory/events", dependencies=[Depends(memory_record_permission)])
async def record_event(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        record = MemoryRecord(**payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    service = _service()
    try:
        stored = service.record(record)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _record_to_dict(stored)


@router.post("/memory/events/validate", dependencies=[Depends(memory_record_permission)])
async def validate_event(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        record = MemoryRecord(**payload)
        validated = _service().validate(record)
        return {"valid": True, "record": _record_to_dict(validated)}
    except Exception as exc:
        return {"valid": False, "error": str(exc)}


@router.get("/memory/events/{record_id}", dependencies=[Depends(memory_read_permission)])
async def get_event(record_id: str) -> dict[str, Any]:
    service = _service()
    record = service.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"unknown record: {record_id}")
    return _record_to_dict(record)


@router.get("/memory/events", dependencies=[Depends(memory_read_permission)])
async def search_events(
    component: str | None = Query(default=None),
    record_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    service = _service()
    results = service.search(component=component, record_type=record_type, status=status)
    return {"results": [_record_to_dict(record) for record in results]}


@router.get("/memory/components/{component}/history", dependencies=[Depends(memory_read_permission)])
async def component_history(component: str) -> dict[str, Any]:
    service = _service()
    history = service.component_history(component)
    return {"component": component, "history": [_record_to_dict(record) for record in history]}


# ── Records listing (unique path, unlike /v1/memory/events which v1 owns) ──

@router.get("/memory/records", dependencies=[Depends(memory_read_permission)])
async def list_records(
    record_type: str | None = Query(default=None),
    component: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, Any]:
    """List Engineering Memory records with optional filters."""
    service = _service()
    results = service.search(
        component=component,
        record_type=record_type,
        status=status,
    )
    if limit:
        results = results[:limit]
    return {"results": [_record_to_dict(record) for record in results]}


# ── Observatory vault (read-only) ─────────────────────────────────────
# These routes are unique to this router (no collision with the v1 memory
# routes) and never write anything: the canonical Obsidian vault is the
# documentary source of truth and stays immutable from the WebUI side.

@router.get("/memory/vault/tree", dependencies=[Depends(memory_read_permission)])
async def vault_tree() -> dict[str, Any]:
    try:
        return _vault().tree()
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/memory/vault/file", dependencies=[Depends(memory_read_permission)])
async def vault_file(path: str = Query(..., min_length=1)) -> dict[str, Any]:
    try:
        return _vault().read(path)
    except VaultError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/memory/vault/search", dependencies=[Depends(memory_read_permission)])
async def vault_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=30, ge=1, le=100),
    extensions: str | None = Query(default=None),
) -> dict[str, Any]:
    try:
        hits = _vault().search(q, limit=limit, extensions=extensions)
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"query": q, "hits": hits}


@router.get("/memory/vault/backlinks", dependencies=[Depends(memory_read_permission)])
async def vault_backlinks(path: str = Query(..., min_length=1)) -> dict[str, Any]:
    try:
        return {"path": path, "backlinks": _vault().backlinks(path)}
    except VaultError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/memory/vault/graph", dependencies=[Depends(memory_read_permission)])
async def vault_graph(limit_nodes: int = Query(default=150, ge=1, le=500)) -> dict[str, Any]:
    try:
        return _vault().graph(limit_nodes=limit_nodes)
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/memory/vault/resolve", dependencies=[Depends(memory_read_permission)])
async def vault_resolve(wikilink: str = Query(..., min_length=1)) -> dict[str, Any]:
    try:
        return _vault().resolve_wikilink(wikilink)
    except VaultError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/memory/vault/file", dependencies=[Depends(memory_record_permission)])
async def vault_write(payload: dict[str, Any]) -> dict[str, Any]:
    """Write a managed document. Raw archives stay immutable."""
    path = payload.get("path")
    content = payload.get("content")
    if not isinstance(path, str) or not isinstance(content, str):
        raise HTTPException(status_code=422, detail="path and content must be strings")
    try:
        return _vault().write(path, content)
    except VaultError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _record_to_dict(record: MemoryRecord) -> dict[str, Any]:
    return record.to_dict()


# ── Tracabilite des interventions (P2.8.3) ────────────────────────────────
# Ces routes sont une **projection HTTP** du service Core
# (`core.engineering_memory.traceability`). Aucune logique metier, aucune
# ecriture documentaire et aucun stockage ne resident ici : la source
# documentaire unique reste le vault DAENA, via l'Engineering Memory.
#
# Le contrat est commun a toutes les interfaces (OpenCode, CLI, WebUI,
# agents) : un rapport structure A->J, des anomalies, des dettes et un
# controle de fin d'intervention.


@router.post("/memory/traceability/interventions", dependencies=[Depends(traceability_write_permission)])
async def record_intervention(payload: dict[str, Any]) -> dict[str, Any]:
    """Enregistre un rapport d'intervention structure dans DAENA.

    Le document est immuable : un identifiant deja utilise avec un contenu
    different n'est jamais ecrase, la divergence etant signalee et conservee
    comme evenement correle.

    Args:
        payload: Rapport d'intervention (rubriques A a J).

    Returns:
        Decriptif de l'operation : `recorded`, `conflict` ou `failed`.
    """
    body = dict(payload)
    if not str(body.get("intervention_id") or "").strip():
        body["intervention_id"] = build_intervention_id(str(body.get("agent") or "opencode"))
    try:
        report = report_from_payload(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    outcome = await get_traceability_service().record_intervention(report)
    status_code = 201
    if outcome.get("conflict"):
        status_code = 409
    elif outcome.get("status") == "failed":
        status_code = 503
    return JSONResponse(status_code=status_code, content=outcome)


@router.get("/memory/traceability/interventions", dependencies=[Depends(traceability_read_permission)])
async def list_interventions(
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    """Liste les rapports d'intervention enregistres, du plus recent au plus ancien."""
    return {"results": get_traceability_service().list_interventions(limit=limit)}


@router.get(
    "/memory/traceability/interventions/{intervention_id}",
    dependencies=[Depends(traceability_read_permission)],
)
async def get_intervention(intervention_id: str) -> dict[str, Any]:
    """Retourne un rapport d'intervention et son historique correle.

    Args:
        intervention_id: Identifiant de l'intervention.

    Returns:
        Rapport, structure portee et evenements correles.
    """
    service = get_traceability_service()
    record = service.get(intervention_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"unknown intervention: {intervention_id}")
    related = service.related_events(intervention_id)
    return {
        "id": record.id,
        "title": record.title,
        "status": record.status,
        "created_at": record.created_at,
        "path": str(getattr(record, "repository_path", "") or ""),
        "structure": record.metadata or {},
        "related_events": [_record_to_dict(item) for item in related],
    }


@router.post(
    "/memory/traceability/interventions/{intervention_id}/complete",
    dependencies=[Depends(traceability_write_permission)],
)
async def complete_intervention(intervention_id: str) -> dict[str, Any]:
    """Controle de fin d'intervention : verifie les huit conditions exigees.

    Une intervention dont le rapport n'est pas persiste ne peut pas etre
    declaree documentee : la reponse indique explicitement ce qui manque.

    Args:
        intervention_id: Identifiant de l'intervention.

    Returns:
        Rapport de controle (jamais un succesDeclare a la place d'un echec).
    """
    result = get_traceability_service().complete(intervention_id)
    return JSONResponse(status_code=200 if result.get("complete") else 409, content=result)


@router.post("/memory/traceability/anomalies", dependencies=[Depends(traceability_write_permission)])
async def record_anomaly(payload: dict[str, Any]) -> dict[str, Any]:
    """Enregistre une anomalie decouverte (document immuable).

    Args:
        payload: Description de l'anomalie.

    Returns:
        Decriptif de l'operation effectuee.
    """
    anomaly_id = str(payload.get("anomaly_id") or payload.get("id") or "").strip()
    if not anomaly_id:
        raise HTTPException(status_code=422, detail="anomaly_id is required")
    outcome = await get_traceability_service().record_anomaly(
        anomaly_id,
        str(payload.get("description") or ""),
        component=str(payload.get("component") or ""),
        severity=str(payload.get("severity") or "MEDIUM"),
        impact=str(payload.get("impact") or ""),
        cause=str(payload.get("cause") or ""),
        project_id=(str(payload["project_id"]) if payload.get("project_id") else None),
        actor=str(payload.get("actor") or ""),
        reference=str(payload.get("reference") or ""),
    )
    status_code = 201
    if outcome.get("conflict"):
        status_code = 409
    elif outcome.get("status") == "failed":
        status_code = 503
    return JSONResponse(status_code=status_code, content=outcome)


@router.post(
    "/memory/traceability/anomalies/{anomaly_id}/transition",
    dependencies=[Depends(traceability_write_permission)],
)
async def transition_anomaly(anomaly_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Enregistre un changement d'etat d'anomalie sans ecraser le document.

    L'historique est porte par des evenements correles : le document
    d'origine reste intact et la chronologie reste reconstituable.

    Args:
        anomaly_id: Identifiant de l'anomalie.
        payload: Nouvel etat, note, auteur et intervention de reference.

    Returns:
        Decriptif de l'evenement enregistre.
    """
    raw_state = str(payload.get("state") or "").strip().upper()
    try:
        state = AnomalyState(raw_state)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"invalid state: {raw_state} (expected one of {[s.value for s in AnomalyState]})",
        ) from exc
    outcome = await get_traceability_service().transition_anomaly(
        anomaly_id,
        state,
        note=str(payload.get("note") or ""),
        actor=str(payload.get("actor") or ""),
        reference=str(payload.get("reference") or ""),
    )
    status_code = 201
    if outcome.get("conflict"):
        status_code = 409
    elif outcome.get("status") == "failed":
        status_code = 503
    return JSONResponse(status_code=status_code, content=outcome)


@router.post("/memory/traceability/debts", dependencies=[Depends(traceability_write_permission)])
async def record_debt(payload: dict[str, Any]) -> dict[str, Any]:
    """Enregistre une dette technique identifiee et conservee.

    Args:
        payload: Description de la dette.

    Returns:
        Decriptif de l'operation effectuee.
    """
    debt_id = str(payload.get("debt_id") or payload.get("id") or "").strip()
    if not debt_id:
        raise HTTPException(status_code=422, detail="debt_id is required")
    outcome = await get_traceability_service().record_debt(
        debt_id,
        str(payload.get("description") or ""),
        origin=str(payload.get("origin") or ""),
        justification=str(payload.get("justification") or ""),
        risk=str(payload.get("risk") or ""),
        priority=str(payload.get("priority") or "MEDIUM"),
        components=list(payload.get("components") or []),
        recommended_action=str(payload.get("recommended_action") or ""),
        dependencies=list(payload.get("dependencies") or []),
        project_id=(str(payload["project_id"]) if payload.get("project_id") else None),
        actor=str(payload.get("actor") or ""),
        reference=str(payload.get("reference") or ""),
    )
    status_code = 201
    if outcome.get("conflict"):
        status_code = 409
    elif outcome.get("status") == "failed":
        status_code = 503
    return JSONResponse(status_code=status_code, content=outcome)
