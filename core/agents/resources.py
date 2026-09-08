"""Résolution des ressources effectives d'un Agent (Core-owned).

Chaîne de responsabilité :

1. ETHAN possède le **catalogue global** de ressources (knowledge, collections
   RAG, skills, tools/MCP) — chaque manager Core reste propriétaire des siennes ;
2. l'utilisateur **classe** éventuellement ces ressources dans ses propres
   dossiers (``core/folders`` — aucun dossier imposé, relation many-to-many
   sans duplication) ;
3. l'utilisateur **sélectionne explicitement** dossiers et/ou ressources à la
   création/édition d'un Agent ;
4. ce module **résout l'ensemble effectif** : sélectionner un dossier inclut
   les ressources qu'il contient ; une ressource peut être sélectionnée
   individuellement ; une même ressource venue de plusieurs sources n'apparaît
   **qu'une fois** (déduplication par identité, jamais de copie) ;
5. **aucune ressource globale n'est injectée sans décision explicite** : un
   agent sans sélection ne reçoit rien — le résolveur ne consulte jamais les
   catalogues par défaut.

Les ressources disparues (supprimées ailleurs) sont ignorées (jamais de
fantôme) et signalées dans ``ghosts`` pour observabilité.

Le résultat alimente l'exécuteur (le runtime ne reçoit que les ressources
autorisées) et l'API ``GET /agents/{id}/resources`` (vue claire de l'arbre
Agent → Dossiers / Knowledge / RAG Collections / Skills / Tools / MCP).
"""

from __future__ import annotations

import inspect
import logging
from typing import Any

from core.agents.types import Agent

logger = logging.getLogger(__name__)


async def _maybe_await(value: Any) -> Any:
    """Retourne ``await value`` si ``value`` est une coroutine, sinon ``value``.

    Supporte indifféremment des managers à getters sync (ToolManager) ou async
    (KnowledgeManager, SkillStore, KnowledgeCollectionManager).
    """
    if inspect.isawaitable(value):
        return await value
    return value


def _name_of(record: Any, fallback: str) -> str:
    """Extrait un nom affichable d'un record Core (dict ou objet)."""
    if isinstance(record, dict):
        return str(record.get("name") or record.get("label") or fallback)
    for attr in ("name", "label"):
        value = getattr(record, attr, None)
        if value:
            return str(value)
    return fallback


def _record_dict(record: Any) -> dict[str, Any] | None:
    if record is None:
        return None
    if isinstance(record, dict):
        return record
    if hasattr(record, "to_dict"):
        return record.to_dict()
    return None


class _EffectiveSet:
    """Collecte dédupliquée de ressources avec leur source de provenance."""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def add(self, resource_id: str, payload: dict[str, Any], source: str) -> None:
        if resource_id in self._items:
            return  # déduplication : la première source gagne (folder d'abord)
        payload = dict(payload)
        payload["source"] = source
        self._items[resource_id] = payload

    def ids(self) -> list[str]:
        return list(self._items)

    def items(self) -> list[dict[str, Any]]:
        return list(self._items.values())


# ── (SUITE) ──────────────────────────────────────────────────────────────────

async def resolve_agent_resources(
    agent: Agent,
    *,
    folders: Any | None = None,
    knowledge: Any | None = None,
    collections: Any | None = None,
    skills: Any | None = None,
    tools: Any | None = None,
) -> dict[str, Any]:
    """Résout l'ensemble **effectif** de ressources autorisées d'un agent.

    Args:
        agent: Agent dont les sélections (typées) sont résolues.
        folders: FolderManager Core (résolution des contenus de dossiers).
        knowledge: KnowledgeManager Core (nœuds de Knowledge).
        collections: KnowledgeCollectionManager Core (collections RAG).
        skills: SkillStore Core.
        tools: ToolManager Core (tools builtin/custom/MCP).

    Returns:
        Arbre canonique : ``folders`` (avec leur contenu résolu), ``knowledge``,
        ``collections``, ``skills``, ``tools`` — chaque entrée porte sa
        ``source`` (``explicit`` ou ``folder:<id>``). ``ghosts`` liste les ids
        sélectionnés mais disparus du catalogue.
    """
    folder_trees: list[dict[str, Any]] = []
    ghosts: list[dict[str, str]] = []

    eff_knowledge = _EffectiveSet()
    eff_collections = _EffectiveSet()
    eff_skills = _EffectiveSet()
    eff_tools = _EffectiveSet()

    # ── 1. Dossiers : incluent les ressources qu'ils contiennent ────────────
    for folder_id in list(agent.folder_ids or []):
        folder = None
        if folders is not None:
            try:
                folder = await folders.get_folder(folder_id)
            except Exception as exc:
                logger.warning(
                    "Failed to resolve folder %s for agent %s: %s",
                    folder_id, agent.name, exc,
                )
                folder = None
        if folder is None:
            ghosts.append({"resource_type": "folder", "resource_id": folder_id})
            continue

        resources: list[dict[str, Any]] = []
        memberships: list[dict[str, Any]] = []
        try:
            memberships = await folders.list_folder_resources(folder_id)
        except Exception as exc:
            logger.warning(
                "Failed to list resources of folder %s: %s", folder_id, exc
            )
            memberships = []
        source = f"folder:{folder_id}"
        for membership in memberships:
            r_type = membership.get("resource_type")
            r_id = membership.get("resource_id", "")
            record = membership.get("record")
            if record is None:
                ghosts.append({"resource_type": r_type, "resource_id": r_id})
                continue
            name = _name_of(record, r_id)
            resources.append(
                {"resource_type": r_type, "resource_id": r_id, "name": name}
            )
            if r_type == "knowledge":
                eff_knowledge.add(r_id, {"id": r_id, "name": name}, source)
            elif r_type == "collection":
                eff_collections.add(r_id, {"id": r_id, "name": name}, source)
            elif r_type == "skill":
                eff_skills.add(r_id, {"id": r_id, "name": name}, source)
            elif r_type == "tool":
                provider = (
                    record.get("provider", "") if isinstance(record, dict) else ""
                )
                eff_tools.add(
                    r_id, {"id": r_id, "name": name, "provider": provider}, source
                )
        folder_trees.append(
            {
                "id": folder_id,
                "name": folder.get("name", folder_id),
                "resources": resources,
            }
        )

    # ── 2. Sélections explicites (complètent, jamais dupliquées) ────────────
    async def _resolve_catalog(
        manager: Any, getter_name: str, resource_id: str, resource_type: str
    ) -> dict[str, Any] | None:
        if manager is None:
            return None
        getter = getattr(manager, getter_name, None)
        if getter is None:
            return None
        try:
            record = _record_dict(await _maybe_await(getter(resource_id)))
        except Exception as exc:
            logger.warning(
                "Failed to resolve %s %s for agent %s: %s",
                resource_type, resource_id, agent.name, exc,
            )
            return None
        return record

    for kid in list(agent.knowledge_ids or []):
        record = await _resolve_catalog(knowledge, "get", kid, "knowledge")
        if record is None:
            ghosts.append({"resource_type": "knowledge", "resource_id": kid})
            continue
        eff_knowledge.add(kid, {"id": kid, "name": _name_of(record, kid)}, "explicit")

    for cid in list(agent.knowledge_collection_ids or []):
        record = await _resolve_catalog(collections, "get_collection", cid, "collection")
        if record is None:
            ghosts.append({"resource_type": "collection", "resource_id": cid})
            continue
        eff_collections.add(cid, {"id": cid, "name": _name_of(record, cid)}, "explicit")

    for sid in list(agent.skill_ids or []):
        record = await _resolve_catalog(skills, "get_skill", sid, "skill")
        if record is None:
            ghosts.append({"resource_type": "skill", "resource_id": sid})
            continue
        eff_skills.add(sid, {"id": sid, "name": _name_of(record, sid)}, "explicit")

    for tid in list(agent.tool_ids or []):
        record = await _resolve_catalog(tools, "get_tool", tid, "tool")
        if record is None:
            ghosts.append({"resource_type": "tool", "resource_id": tid})
            continue
        eff_tools.add(
            tid,
            {
                "id": tid,
                "name": _name_of(record, tid),
                "provider": record.get("provider", "") if isinstance(record, dict) else "",
            },
            "explicit",
        )

    return {
        "agent_id": agent.id,
        "folders": folder_trees,
        "knowledge": eff_knowledge.items(),
        "collections": eff_collections.items(),
        "skills": eff_skills.items(),
        "tools": eff_tools.items(),
        "ghosts": ghosts,
    }


__all__ = ["resolve_agent_resources"]
