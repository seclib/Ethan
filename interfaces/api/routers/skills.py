"""Router API — Skills (dédié, extrait de v1.py).

Toute la logique métier réside dans ``core.skills.store.SkillStore`` et
``core.skills.lab.SkillLab``. Ce router est une passerelle HTTP mince.

Routes (préfixe /v1) :
    GET     /v1/skills                          → liste avec filtres
    POST    /v1/skills                          → créer
    GET     /v1/skills/search                   → recherche
    GET     /v1/skills/export                   → export
    POST    /v1/skills/import                   → import
    GET     /v1/skills/{id}                     → détail
    PUT     /v1/skills/{id}                     → mise à jour
    DELETE  /v1/skills/{id}                     → suppression
    POST    /v1/skills/{id}/toggle              → activer/désactiver
    GET     /v1/skills/{id}/valves              → valves config
    PUT     /v1/skills/{id}/valves              → mise à jour valves
    POST    /v1/skills/{id}/run                 → exécution via ChatPipeline
    POST    /v1/skills/lab/test                 → test sandbox Docker
    GET     /v1/skills/lab/results              → résultats lab
"""

from __future__ import annotations

import json

from typing import Any

from core.auth import Permission
from core.chat import ChatPipeline
from core.security.types import ActionType
from core.skills.import_manager import SkillImportManager
from core.skills.lab import SkillLab
from core.skills.store import SkillStore
from core.skills.validation import collect_unknown_tools
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from interfaces.api.auth import current_user_id, resolve_user_scope, require_permission
from interfaces.api.gateway_guard import gateway_guard

router = APIRouter(prefix="/v1", tags=["skills"])

# ── Dépendances (injection au démarrage via main.py) ──────────────────────

_skill_store: SkillStore | None = None
_chat_pipeline: ChatPipeline | None = None
_tool_manager: Any | None = None
_skill_lab: SkillLab | None = None


def set_skill_store(store: SkillStore) -> None:
    global _skill_store
    _skill_store = store


def get_skill_store() -> SkillStore:
    if _skill_store is None:
        raise HTTPException(status_code=503, detail="Skill store not initialized")
    return _skill_store


def set_chat_pipeline(pipeline: ChatPipeline) -> None:
    global _chat_pipeline
    _chat_pipeline = pipeline


def get_chat_pipeline() -> ChatPipeline:
    if _chat_pipeline is None:
        raise HTTPException(status_code=503, detail="Chat pipeline not initialized")
    return _chat_pipeline


def set_tool_manager(manager: Any) -> None:
    global _tool_manager
    _tool_manager = manager


def _get_tool_manager() -> Any:
    return _tool_manager


# ── Helpers ───────────────────────────────────────────────────────────────


def _validate_skill_tools(data: dict[str, Any]) -> None:
    """Refuse (422) toute skill référençant un outil inconnu du ToolManager."""
    manager = _get_tool_manager()
    unknown = collect_unknown_tools(
        data.get("required_tools") or [],
        data.get("steps") or [],
        manager,
    )
    if unknown:
        raise HTTPException(
            422,
            "Outils inconnus (absents du ToolManager) : " + ", ".join(unknown),
        )


# ── Skill Lab (sandbox Docker) ───────────────────────────────────────────


def get_skill_lab() -> SkillLab:
    """SkillLab paresseux : client Docker réel si le daemon répond, sinon None."""
    global _skill_lab
    if _skill_lab is None:
        try:
            import docker as _docker_sdk

            _docker_client = _docker_sdk.from_env()
            _docker_client.ping()
            _skill_lab = SkillLab(docker_client=_docker_client)
        except Exception:
            _skill_lab = SkillLab(docker_client=None)
    return _skill_lab


# ── Routes ────────────────────────────────────────────────────────────────

@router.get("/skills")
async def list_skills(
    active: bool | None = None,
    kind: str | None = None,
    tag: str | None = None,
):
    """Liste les skills (modèle unifié) avec filtres optionnels."""
    return await get_skill_store().list_skills(active=active, kind=kind, tag=tag)


@router.post("/skills", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def create_skill(data: dict[str, Any]):
    _validate_skill_tools(data)
    try:
        return await get_skill_store().create_skill(data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/skills/search")
async def search_skills(q: str = ""):
    return await get_skill_store().search_skills(q)


@router.get("/skills/export")
async def export_skills():
    """Exporte toutes les skills (portabilité, pattern Open-WebUI)."""
    return await get_skill_store().export_skills()


@router.post(
    "/skills/import",
    dependencies=[
        Depends(require_permission(Permission.PLUGINS)),
        Depends(gateway_guard(ActionType.PLUGIN_INSTALL)),
    ],
)
async def import_skills(data: dict[str, Any]):
    records = data.get("skills") or []
    if not isinstance(records, list):
        raise HTTPException(422, "Le corps doit contenir une liste 'skills'.")
    return await get_skill_store().import_skills(records)


@router.post("/skills/lab/test", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def skill_lab_test(data: dict[str, Any]):
    """Teste un code Python de skill candidat dans le sandbox Docker."""
    lab = get_skill_lab()
    if not lab.docker_available:
        raise HTTPException(
            503,
            "Skill Lab indisponible : Docker est requis (sandbox obligatoire, "
            "aucune exécution locale du code candidat).",
        )
    code = str(data.get("code") or "").strip()
    if not code:
        raise HTTPException(422, "Le champ 'code' (Python) est requis.")
    result = await lab.test_skill(
        skill_code=code,
        skill_name=str(data.get("name") or "test_skill"),
        test_input=str(data.get("input") or ""),
        requirements=list(data.get("requirements") or []),
    )
    return result.to_dict()


@router.get("/skills/lab/results")
async def skill_lab_results(skill_name: str | None = None):
    return get_skill_lab().list_results(skill_name=skill_name)


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    skill = await get_skill_store().get_skill(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return skill


@router.put(
    "/skills/{skill_id}", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def update_skill(skill_id: str, data: dict[str, Any]):
    _validate_skill_tools(data)
    try:
        skill = await get_skill_store().update_skill(skill_id, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return skill


@router.delete(
    "/skills/{skill_id}", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def delete_skill(skill_id: str):
    if not await get_skill_store().delete_skill(skill_id):
        raise HTTPException(404, f"Skill {skill_id} not found")
    return {"status": "deleted"}


@router.post(
    "/skills/{skill_id}/toggle",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def toggle_skill(skill_id: str):
    skill = await get_skill_store().toggle_skill(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return skill


@router.get("/skills/{skill_id}/valves")
async def get_skill_valves(skill_id: str):
    """Valves (configuration réelle) d'une skill."""
    valves = await get_skill_store().get_valves(skill_id)
    if valves is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return valves


@router.put(
    "/skills/{skill_id}/valves",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def update_skill_valves(skill_id: str, data: dict[str, Any]):
    try:
        valves = await get_skill_store().update_valves(skill_id, data.get("valves", {}))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if valves is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return valves


@router.post(
    "/skills/{skill_id}/run",
    dependencies=[Depends(require_permission(Permission.EXECUTE))],
)
async def run_skill(skill_id: str, data: dict[str, Any], request: Request = None):
    """Exécute une skill du catalogue via le ChatPipeline Core (moteur réel)."""
    skill = await get_skill_store().get_skill(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    if not (skill.get("content") or "").strip():
        raise HTTPException(422, "Cette skill n'a pas de contenu exécutable (content vide).")
    if not skill.get("is_active", True):
        raise HTTPException(409, "Cette skill est désactivée — activez-la avant de l'exécuter.")

    input_text = (data.get("input") or "").strip()
    if not input_text:
        raise HTTPException(422, "Un message d'entrée (input) est requis pour exécuter la skill.")

    pipeline = get_chat_pipeline()
    try:
        result = await pipeline.run(
            message=input_text,
            chat_id=data.get("chat_id"),
            user_id=resolve_user_scope(request, data.get("user_id")),
            provider_id=data.get("provider_id"),
            model=data.get("model"),
            skill_ids=[skill_id],
            metadata={"skill_id": skill_id, "skill_name": skill.get("name", "")},
        )
    except ValueError as exc:
        await get_skill_store().record_execution(skill_id, False)
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        await get_skill_store().record_execution(skill_id, False)
        raise
    await get_skill_store().record_execution(skill_id, True)

    assistant = result["assistant_message"]
    return {
        "skill_id": skill_id,
        "status": assistant.get("status", "done"),
        "chat_id": result["chat_id"],
        "output": assistant["content"],
        "metadata": assistant.get("metadata") or {},
    }

# ── Skill package import (Core manager) ───────────────────────────────────

_skill_import_manager: SkillImportManager | None = None


def get_skill_import_manager() -> SkillImportManager:
    global _skill_import_manager
    if _skill_import_manager is None:
        _skill_import_manager = SkillImportManager(store=get_skill_store())
    return _skill_import_manager


async def _read_uploads(files: list[UploadFile]) -> list[tuple[str, bytes]]:
    pairs = []
    for upload in files:
        raw = await upload.read()
        pairs.append((upload.filename or "unnamed", raw))
    return pairs


@router.post(
    "/skills/import/scan",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def scan_skills_import(files: list[UploadFile] = File(...)):
    """Preview a Skill bundle without installing anything."""
    manager = get_skill_import_manager()
    pairs = await _read_uploads(files)
    return await manager.scan(pairs)


@router.post(
    "/skills/import-files",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def import_skills_files(
    files: list[UploadFile] = File(...),
    selected: str | None = Form(None),
):
    """Import selected or all valid skills from uploaded files/folders/archives."""
    manager = get_skill_import_manager()
    pairs = await _read_uploads(files)
    selected_ids = None
    if selected:
        try:
            parsed = json.loads(selected)
            selected_ids = [str(v) for v in parsed] if isinstance(parsed, list) else None
        except (json.JSONDecodeError, TypeError):
            selected_ids = [x for x in selected.split(",") if x.strip()] or None
    return await manager.import_files(pairs, selected=selected_ids)


# Aliases for client/back-compat discovery.
@router.post(
    "/skills/import-batch",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def import_skills_batch_alias(files: list[UploadFile] = File(...), selected: str | None = Form(None)):
    manager = get_skill_import_manager()
    pairs = await _read_uploads(files)
    selected_ids = None
    if selected:
        try:
            parsed = json.loads(selected)
            selected_ids = [str(v) for v in parsed] if isinstance(parsed, list) else None
        except (json.JSONDecodeError, TypeError):
            selected_ids = [x for x in selected.split(",") if x.strip()] or None
    return await manager.import_files(pairs, selected=selected_ids)


@router.post(
    "/skills/import-package",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def import_skills_package_alias(files: list[UploadFile] = File(...), selected: str | None = Form(None)):
    manager = get_skill_import_manager()
    pairs = await _read_uploads(files)
    selected_ids = None
    if selected:
        try:
            parsed = json.loads(selected)
            selected_ids = [str(v) for v in parsed] if isinstance(parsed, list) else None
        except (json.JSONDecodeError, TypeError):
            selected_ids = [x for x in selected.split(",") if x.strip()] or None
    return await manager.import_files(pairs, selected=selected_ids)
