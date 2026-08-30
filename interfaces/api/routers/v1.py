"""V1 API Router — Endpoints attendus par le frontend WebUI.

Expose les capacités Core aux clients WebUI et CLI :
- /v1/agents
- /v1/goals
- /v1/missions
- /v1/memory/*
- /v1/skills
- /v1/knowledge
- /v1/flux
- /v1/settings
- /v1/chat

Les domaines agents, missions, knowledge et RAG sont délégués aux managers du
Core. Les routes restent des passerelles HTTP sans logique métier propre.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from core.agents import AgentExecutionUnavailable, AgentManager
from core.auth import Permission
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from interfaces.api.auth import require_permission
from core.chat import ChatPipeline
from core.llm.provider_manager import ProviderManager
from core.llm.types import ChatMessage, LLMRequirements
from core.llm.types import ChatMessage as LLMChatMessage
from core.missions import MissionManager
from core.rag import RAGPipeline
from core.skills.store import SkillStore
from core.state.chats import ChatStore
from core.state.webui_store import CoreWebUIStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["v1"])

# Format d'appel d'outil émis par le LLM lorsque des outils sont sélectionnés
# dans le chat :  <tool name="nom">{"param": "valeur"}</tool>
# Le parsing/exécution restent côté Core (ChatPipeline.execute_tool_call).
_TOOL_CALL_RE = re.compile(
    r'<tool\s+name=["\']([^"\']+)["\']\s*>\s*(.*?)\s*</tool>',
    re.DOTALL,
)


def _parse_tool_calls(content: str) -> list[dict[str, Any]]:
    """Extrait les appels d'outils balisés d'une réponse LLM."""
    calls: list[dict[str, Any]] = []
    for match in _TOOL_CALL_RE.finditer(content):
        raw = (match.group(2) or "{}").strip() or "{}"
        try:
            params = json.loads(raw)
            if not isinstance(params, dict):
                params = {"value": params}
        except Exception:
            params = {"raw": raw}
        calls.append({"name": match.group(1), "params": params})
    return calls


def _strip_tool_blocks(content: str, note_by_name: dict[str, str] | None = None) -> str:
    """Retire les blocs <tool> du contenu affiché, avec une note par appel."""
    def _repl(match: re.Match[str]) -> str:
        name = match.group(1)
        note = (note_by_name or {}).get(name, f"_[Outil « {name} » exécuté]_")
        return f"\n\n{note}\n\n"

    return _TOOL_CALL_RE.sub(_repl, content)

# Instance globale du ProviderManager — injectée au démarrage via set_provider_manager()
_manager: ProviderManager | None = None

# Instance globale du CoreWebUIStore (records persistants goals/facts/skills/
# events/settings/providers/plugins) — injectée au démarrage via set_webui_store().
_webui_store: CoreWebUIStore | None = None

# Instance globale du SkillStore Core (records persistants skills) — injectée
# au démarrage via set_skill_store().
_skill_store: SkillStore | None = None

# Instance globale du ChatStore Core (conversations persistantes) — injectée
# au démarrage via set_chat_store().
_chat_store: ChatStore | None = None

# Instance globale du ChatPipeline Core (orchestration du chat) — injectée
# au démarrage via set_chat_pipeline().
_chat_pipeline: ChatPipeline | None = None

# Instance globale du KnowledgeCollectionManager Core (collections de
# documents RAG) — injectée au démarrage via set_knowledge_collections().
_knowledge_collections: KnowledgeCollectionManager | None = None


def set_webui_store(store: CoreWebUIStore) -> None:
    """Injecte le CoreWebUIStore dans le router (appelé au startup)."""
    global _webui_store
    _webui_store = store


def get_webui_store() -> CoreWebUIStore:
    """Retourne le CoreWebUIStore global.

    Raises:
        HTTPException 503 si le store n'est pas initialisé.
    """
    if _webui_store is None:
        raise HTTPException(status_code=503, detail="WebUI store not initialized")
    return _webui_store


def set_skill_store(store: SkillStore) -> None:
    """Injecte le SkillStore Core dans le router (appelé au startup)."""
    global _skill_store
    _skill_store = store


def get_skill_store() -> SkillStore:
    """Retourne le SkillStore Core global.

    Raises:
        HTTPException 503 si le store n'est pas initialisé.
    """
    if _skill_store is None:
        raise HTTPException(status_code=503, detail="Skill store not initialized")
    return _skill_store


def set_chat_store(store: ChatStore) -> None:
    """Injecte le ChatStore Core dans le router (appelé au startup)."""
    global _chat_store
    _chat_store = store


def get_chat_store() -> ChatStore:
    """Retourne le ChatStore Core global.

    Raises:
        HTTPException 503 si le store n'est pas initialisé.
    """
    if _chat_store is None:
        raise HTTPException(status_code=503, detail="Chat store not initialized")
    return _chat_store


def set_chat_pipeline(pipeline: ChatPipeline) -> None:
    """Injecte le ChatPipeline Core dans le router (appelé au startup)."""
    global _chat_pipeline
    _chat_pipeline = pipeline


def get_chat_pipeline() -> ChatPipeline:
    """Retourne le ChatPipeline Core global.

    Raises:
        HTTPException 503 si le pipeline n'est pas initialisé.
    """
    if _chat_pipeline is None:
        raise HTTPException(status_code=503, detail="Chat pipeline not initialized")
    return _chat_pipeline


def set_knowledge_collections(manager: KnowledgeCollectionManager) -> None:
    """Injecte le KnowledgeCollectionManager Core dans le router (startup)."""
    global _knowledge_collections
    _knowledge_collections = manager


def get_knowledge_collections() -> KnowledgeCollectionManager:
    """Retourne le KnowledgeCollectionManager Core global.

    Raises:
        HTTPException 503 si le manager n'est pas initialisé.
    """
    if _knowledge_collections is None:
        raise HTTPException(status_code=503, detail="Knowledge collections not initialized")
    return _knowledge_collections


class CoreDomainServices:
    """Core-owned domain managers exposed through this HTTP gateway."""

    def __init__(
        self,
        *,
        agents: AgentManager | None = None,
        missions: MissionManager | None = None,
        knowledge: KnowledgeManager | None = None,
        rag: RAGPipeline | None = None,
    ) -> None:
        self.agents = agents or AgentManager()
        self.missions = missions or MissionManager()
        self.knowledge = knowledge or KnowledgeManager()
        self.rag = rag or RAGPipeline()


_domains = CoreDomainServices()


# Instance globale du ToolManager Core (catalogue builtin/custom/MCP) —
# injectée au démarrage via set_tool_manager().
_tool_manager: Any | None = None


def set_core_domain_services(services: CoreDomainServices) -> None:
    """Inject the Core composition root during API startup."""
    global _domains
    _domains = services


def set_tool_manager(manager: Any) -> None:
    """Injecte le ToolManager Core dans le router (appelé au startup)."""
    global _tool_manager
    _tool_manager = manager


def set_provider_manager(manager: ProviderManager) -> None:
    """Injecte le ProviderManager dans le router (appelé au startup)."""
    global _manager
    _manager = manager


def get_manager() -> ProviderManager:
    """Retourne le ProviderManager global.

    Raises:
        HTTPException 503 si le manager n'est pas initialisé.
    """
    if _manager is None:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")
    return _manager


def _utc_now_rfc3339() -> str:
    """Timestamp UTC au format RFC3339 (compatible frontend)."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Les records goals/facts/skills/events/settings/providers/plugins vivent dans
# le CoreWebUIStore (Core, persistant), pas dans ce router — voir get_webui_store().


# ═══════════════════════════════════════════════════════════════════════════
# AGENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/agents")
async def list_agents():
    return [agent.to_dict() for agent in await _domains.agents.list()]


@router.post("/agents", dependencies=[Depends(require_permission(Permission.AGENTS))])
async def create_agent(data: dict[str, Any]):
    try:
        agent = await _domains.agents.create(
            name=data.get("name", ""),
            description=data.get("description", ""),
            capabilities=data.get("capabilities"),
            model=data.get("model"),
            provider=data.get("provider"),
            memory_scope=data.get("memory_scope", "default"),
            skill_ids=data.get("skill_ids", data.get("skills")),
            metadata=data.get("metadata"),
        )
        return agent.to_dict()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = await _domains.agents.get(agent_id)
    if agent is None:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return agent.to_dict()


@router.get("/tools")
async def list_tools():
    """Liste le catalogue d'outils Core (builtin, custom, MCP découverts).

    Lecture seule : les tools sont possédés par le ToolManager Core.
    Utilisé par le WebUI pour associer des outils à un agent ou un chat.
    """
    if _tool_manager is None:
        raise HTTPException(503, "ToolManager not initialized")
    return [tool.to_dict() if hasattr(tool, "to_dict") else {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
        "category": tool.category,
        "capabilities": tool.capabilities,
        "provider": tool.provider,
        "is_available": tool.is_available,
        "risk_level": getattr(tool.risk_level, "value", str(tool.risk_level)),
        "tags": tool.tags,
    } for tool in _tool_manager.list_tools()]


@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, data: dict[str, Any]):
    try:
        agent = await _domains.agents.update(agent_id, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if agent is None:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return agent.to_dict()


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    if not await _domains.agents.delete(agent_id):
        raise HTTPException(404, f"Agent {agent_id} not found")
    return {"status": "deleted"}


@router.post("/agents/{agent_id}/execute", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def execute_agent(agent_id: str, data: dict[str, Any]):
    """Request agent work through the Core execution adapter."""
    try:
        execution = await _domains.agents.execute(
            agent_id,
            data.get("task", ""),
            context=data.get("context"),
            skill_id=data.get("skill_id"),
        )
        return execution.to_dict()
    except AgentExecutionUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(404 if message.endswith("not found") else 422, message) from exc


@router.get("/agents/{agent_id}/executions")
async def list_agent_executions(agent_id: str):
    if await _domains.agents.get(agent_id) is None:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return [execution.to_dict() for execution in await _domains.agents.list_executions(agent_id)]


# ═══════════════════════════════════════════════════════════════════════════
# GOALS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/goals")
async def list_goals():
    return await get_webui_store().list_goals()


@router.post("/goals")
async def create_goal(data: dict[str, Any]):
    try:
        return await get_webui_store().create_goal(
            title=data.get("title", "untitled"),
            description=data.get("description", ""),
            priority=data.get("priority", "normal"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    goal = await get_webui_store().get_goal(goal_id)
    if goal is None:
        raise HTTPException(404, f"Goal {goal_id} not found")
    return goal


@router.put("/goals/{goal_id}")
async def update_goal(goal_id: str, data: dict[str, Any]):
    goal = await get_webui_store().update_goal(goal_id, data)
    if goal is None:
        raise HTTPException(404, f"Goal {goal_id} not found")
    return goal


@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str):
    if not await get_webui_store().delete_goal(goal_id):
        raise HTTPException(404, f"Goal {goal_id} not found")
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════
# MISSIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/missions")
async def list_missions(status: str | None = None):
    try:
        return [mission.to_dict() for mission in await _domains.missions.list(status)]
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/missions", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def create_mission(data: dict[str, Any]):
    try:
        mission = await _domains.missions.create(
            title=data.get("title", ""),
            description=data.get("description", ""),
            steps=data.get("steps"),
            workspace_path=data.get("workspace_path", ""),
            metadata=data.get("metadata"),
        )
        return mission.to_dict()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/missions/{mission_id}")
async def get_mission(mission_id: str):
    mission = await _domains.missions.get(mission_id)
    if mission is None:
        raise HTTPException(404, f"Mission {mission_id} not found")
    return mission.to_dict()


@router.put("/missions/{mission_id}")
async def update_mission(mission_id: str, data: dict[str, Any]):
    try:
        mission = await _domains.missions.update(mission_id, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if mission is None:
        raise HTTPException(404, f"Mission {mission_id} not found")
    return mission.to_dict()


@router.delete("/missions/{mission_id}")
async def delete_mission(mission_id: str):
    if not await _domains.missions.delete(mission_id):
        raise HTTPException(404, f"Mission {mission_id} not found")
    return {"status": "deleted"}


@router.post("/missions/{mission_id}/steps/{step_id}/verify")
async def verify_mission_step(mission_id: str, step_id: str):
    try:
        return await _domains.missions.verify_step(mission_id, step_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/missions/{mission_id}/steps/{step_id}/approve")
async def approve_mission_step(mission_id: str, step_id: str):
    try:
        return await _domains.missions.approve_step(mission_id, step_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY / FACTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/memory/facts")
async def list_facts(limit: int = 20, category: str | None = None):
    facts = await get_webui_store().list_facts(category=category)
    return facts[: limit]


@router.get("/memory/facts/search")
async def search_facts(q: str = ""):
    return await get_webui_store().search_facts(q)


@router.get("/memory/facts/{fact_id}")
async def get_fact(fact_id: str):
    fact = await get_webui_store().get_fact(fact_id)
    if fact is None:
        raise HTTPException(404, f"Fact {fact_id} not found")
    return fact


@router.post("/memory/facts")
async def create_fact(data: dict[str, Any]):
    return await get_webui_store().create_fact(data)


@router.get("/memory/events")
async def list_memory_events():
    return await get_webui_store().list_events(limit=100)


@router.post("/memory/ingest")
async def ingest_memory(entry: dict[str, Any]):
    return await get_webui_store().append_event(entry)


@router.get("/memory/search")
async def search_memory(q: str = "", filters: dict[str, Any] | None = None):
    return await get_webui_store().search_memory(q)


@router.get("/memory/{memory_id}")
async def get_memory_entry(memory_id: str):
    entry = await get_webui_store().get_memory_entry(memory_id)
    if entry is None:
        raise HTTPException(404, f"Memory entry {memory_id} not found")
    return entry


# ═══════════════════════════════════════════════════════════════════════════
# SKILLS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/skills")
async def list_skills():
    return await get_skill_store().list_skills()


@router.post("/skills", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def create_skill(data: dict[str, Any]):
    try:
        return await get_skill_store().create_skill(data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/skills/search")
async def search_skills(q: str = ""):
    return await get_skill_store().search_skills(q)


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    skill = await get_skill_store().get_skill(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return skill


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: str, data: dict[str, Any]):
    skill = await get_skill_store().update_skill(skill_id, data)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return skill


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    if not await get_skill_store().delete_skill(skill_id):
        raise HTTPException(404, f"Skill {skill_id} not found")
    return {"status": "deleted"}


@router.post("/skills/{skill_id}/toggle")
async def toggle_skill(skill_id: str):
    skill = await get_skill_store().toggle_skill(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return skill


@router.post("/skills/{skill_id}/run", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def run_skill(skill_id: str, data: dict[str, Any]):
    """Exécute une skill du catalogue via le ChatPipeline Core (moteur réel).

    Contrairement à ``/skills/{id}/execute`` (moteur à étapes des builtins,
    registre mémoire), */run* traite les skills persistées du ``SkillStore`` :
    le ``content`` de la skill est injecté dans le prompt comme instructions
    (via le même chemin ``_build_llm_messages`` qu'une conversation) puis la
    réponse est générée par le ProviderManager Core. Aucun second moteur.
    """
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
            user_id=data.get("user_id", "anonymous"),
            provider_id=data.get("provider_id"),
            model=data.get("model"),
            skill_ids=[skill_id],
            metadata={"skill_id": skill_id, "skill_name": skill.get("name", "")},
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    assistant = result["assistant_message"]
    return {
        "skill_id": skill_id,
        "status": assistant.get("status", "done"),
        "chat_id": result["chat_id"],
        "output": assistant["content"],
        "metadata": assistant.get("metadata") or {},
    }


# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/knowledge")
async def list_knowledge():
    return [node.to_dict() for node in await _domains.knowledge.list()]


@router.get("/knowledge/search")
async def search_knowledge(q: str = ""):
    return [node.to_dict() for node in await _domains.knowledge.search(q)]


@router.get("/knowledge/collections")
async def list_collections(user_id: str | None = None):
    return await get_knowledge_collections().list_collections(user_id=user_id)


@router.post("/knowledge/collections")
async def create_collection(data: dict[str, Any]):
    try:
        return await get_knowledge_collections().create_collection(
            name=data.get("name", ""),
            description=data.get("description", ""),
            user_id=data.get("user_id", "anonymous"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/knowledge/collections/{collection_id}")
async def get_collection(collection_id: str):
    collection = await get_knowledge_collections().get_collection(collection_id)
    if collection is None:
        raise HTTPException(404, f"Collection {collection_id} not found")
    return collection


@router.put("/knowledge/collections/{collection_id}")
async def update_collection(collection_id: str, data: dict[str, Any]):
    collection = await get_knowledge_collections().update_collection(collection_id, data)
    if collection is None:
        raise HTTPException(404, f"Collection {collection_id} not found")
    return collection


@router.delete("/knowledge/collections/{collection_id}")
async def delete_collection(collection_id: str):
    if not await get_knowledge_collections().delete_collection(collection_id):
        raise HTTPException(404, f"Collection {collection_id} not found")
    return {"status": "deleted"}


@router.get("/knowledge/collections/{collection_id}/documents")
async def list_collection_documents(collection_id: str):
    documents = await get_knowledge_collections().list_documents(collection_id)
    return documents


@router.post("/knowledge/collections/{collection_id}/documents")
async def add_collection_document(collection_id: str, data: dict[str, Any]):
    try:
        collection = await get_knowledge_collections().add_document(
            collection_id, data.get("document_id", "")
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if collection is None:
        raise HTTPException(404, f"Collection {collection_id} not found")
    return collection


@router.delete("/knowledge/collections/{collection_id}/documents/{document_id}")
async def remove_collection_document(collection_id: str, document_id: str):
    collection = await get_knowledge_collections().remove_document(collection_id, document_id)
    if collection is None:
        raise HTTPException(404, f"Collection {collection_id} not found")
    return collection


@router.post("/knowledge/collections/{collection_id}/retrieve")
async def retrieve_collection(data: dict[str, Any], collection_id: str):
    """Retrieval RAG restreint à une collection."""
    query = data.get("query", "")
    try:
        top_k = int(data["top_k"]) if data.get("top_k") is not None else None
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, "top_k must be an integer") from exc
    try:
        return await get_knowledge_collections().retrieve(query, collection_id, top_k=top_k)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/knowledge/{knowledge_id}")
async def get_knowledge(knowledge_id: str):
    node = await _domains.knowledge.get(knowledge_id)
    if node is None:
        raise HTTPException(404, f"Knowledge {knowledge_id} not found")
    return node.to_dict()


@router.post("/knowledge")
async def create_knowledge(data: dict[str, Any]):
    try:
        node = await _domains.knowledge.create(
            label=data.get("label", ""),
            node_type=data.get("node_type", data.get("type", "concept")),
            content=data.get("content", ""),
            source=data.get("source", ""),
            connections=data.get("connections"),
            metadata=data.get("metadata"),
        )
        return node.to_dict()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.put("/knowledge/{knowledge_id}")
async def update_knowledge(knowledge_id: str, data: dict[str, Any]):
    try:
        node = await _domains.knowledge.update(knowledge_id, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if node is None:
        raise HTTPException(404, f"Knowledge {knowledge_id} not found")
    return node.to_dict()


@router.delete("/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: str):
    if not await _domains.knowledge.delete(knowledge_id):
        raise HTTPException(404, f"Knowledge {knowledge_id} not found")
    return {"status": "deleted"}


@router.post("/knowledge/{knowledge_id}/connections")
async def connect_knowledge(knowledge_id: str, data: dict[str, Any]):
    try:
        node = await _domains.knowledge.connect(
            knowledge_id,
            data.get("to_node_id", ""),
            relation_type=data.get("relation_type", "related_to"),
            strength=float(data.get("strength", 1.0)),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if node is None:
        raise HTTPException(404, f"Knowledge {knowledge_id} not found")
    return node.to_dict()


@router.post("/knowledge/{knowledge_id}/rag")
async def ingest_knowledge_into_rag(knowledge_id: str):
    try:
        document_id = await _domains.knowledge.ingest_into_rag(knowledge_id, _domains.rag)
        return {"knowledge_id": knowledge_id, "document_id": document_id}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


# ═══════════════════════════════════════════════════════════════════════════
# RAG / DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/rag/documents")
async def list_rag_documents():
    return [document.to_dict() for document in await _domains.rag.list_documents()]


@router.get("/rag/config")
async def get_rag_config():
    """Configuration et statut du moteur RAG (paramètres réellement supportés)."""
    await _domains.rag.list_documents()  # force le chargement de l'index
    return {"config": _domains.rag.get_config(), "stats": _domains.rag.stats()}


@router.put(
    "/rag/config",
    dependencies=[Depends(require_permission(Permission.ADMIN))],
)
async def update_rag_config(data: dict[str, Any]):
    """Applique et persiste la configuration du moteur RAG.

    Champs supportés par le moteur Core : chunk_size, chunk_overlap, top_k,
    max_context_chars, embedding_model. Tout autre champ est ignoré.
    """
    allowed = (
        "chunk_size",
        "chunk_overlap",
        "top_k",
        "max_context_chars",
        "embedding_model",
    )
    payload: dict[str, Any] = {}
    for key in allowed:
        if key not in data or data[key] is None:
            continue
        if key == "embedding_model":
            payload[key] = str(data[key]).strip()
        else:
            try:
                payload[key] = int(data[key])
            except (TypeError, ValueError) as exc:
                raise HTTPException(422, f"{key} doit être un entier") from exc

    try:
        config = _domains.rag.configure(**payload)
        await _domains.rag.persist_config()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await _domains.rag.list_documents()  # force le chargement pour un stats à jour
    return {"config": config, "stats": _domains.rag.stats()}


@router.get("/rag/status")
async def get_rag_status():
    """Statut d'indexation : volumes, mode d'embedding, modèle."""
    await _domains.rag.list_documents()
    return _domains.rag.stats()


@router.post("/rag/documents", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def ingest_rag_document(data: dict[str, Any]):
    try:
        document = await _domains.rag.ingest(
            data.get("content", ""),
            title=data.get("title", ""),
            source=data.get("source", ""),
            metadata=data.get("metadata"),
        )
        return document.to_dict()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post(
    "/rag/documents/from-file/{file_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def ingest_rag_document_from_file(file_id: str, data: dict[str, Any] | None = None):
    """Ingeste le contenu texte d'un fichier déjà uploadé (FileStore Core).

    Le fichier binaire reste la source de vérité (aucun second système de
    fichiers) : son contenu est décodé puis indexé dans le RAG. Un
    ``collection_id`` optionnel attache immédiatement le document créé à une
    collection Knowledge.
    """
    from interfaces.api.routers.domains import _require_files

    body = data or {}
    result = await _require_files().download(file_id)
    if result is None:
        raise HTTPException(404, f"File {file_id} not found")
    raw, record = result

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        if not body.get("force"):
            raise HTTPException(
                422,
                "Le fichier n'est pas du texte UTF-8 (force=true pour forcer l'ingestion)",
            ) from exc
        text = raw.decode("latin-1", errors="replace")

    try:
        document = await _domains.rag.ingest(
            text,
            title=body.get("title") or record.get("filename", file_id),
            source=f"file:{file_id}",
            metadata={
                "file_id": file_id,
                "content_type": record.get("content_type", ""),
                **(body.get("metadata") or {}),
            },
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    attached_collection_id: str | None = None
    collection_id = body.get("collection_id")
    if collection_id:
        try:
            collection = await get_knowledge_collections().add_document(
                collection_id, document.id
            )
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        if collection is None:
            raise HTTPException(404, f"Collection {collection_id} not found")
        attached_collection_id = collection_id

    payload = document.to_dict()
    payload["attached_collection_id"] = attached_collection_id
    return payload


@router.get("/rag/documents/{document_id}")
async def get_rag_document(document_id: str):
    document = await _domains.rag.get_document(document_id)
    if document is None:
        raise HTTPException(404, f"RAG document {document_id} not found")
    return document.to_dict()


@router.delete("/rag/documents/{document_id}")
async def delete_rag_document(document_id: str):
    if not await _domains.rag.delete_document(document_id):
        raise HTTPException(404, f"RAG document {document_id} not found")
    return {"status": "deleted"}


@router.post("/rag/retrieve")
async def retrieve_rag_context(data: dict[str, Any]):
    query = data.get("query", "")
    try:
        top_k = int(data["top_k"]) if data.get("top_k") is not None else None
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, "top_k must be an integer") from exc
    chunks = await _domains.rag.retrieve(query, top_k=top_k)
    return [
        {
            "chunk": item.chunk.to_dict(),
            "score": item.score,
            "document_title": item.document_title,
            "document_source": item.document_source,
        }
        for item in chunks
    ]


@router.post("/rag/context")
async def build_rag_context(data: dict[str, Any]):
    query = data.get("query", "")
    try:
        top_k = int(data["top_k"]) if data.get("top_k") is not None else None
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, "top_k must be an integer") from exc
    return {"context": await _domains.rag.build_context(query, top_k=top_k)}


# ═══════════════════════════════════════════════════════════════════════════
# FLUX / EVENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/flux")
async def list_flux_events(limit: int = 50, type: str | None = None):
    return await get_webui_store().list_events(type=type, limit=limit)


@router.get("/flux/{event_id}")
async def get_flux_event(event_id: str):
    event = await get_webui_store().get_event(event_id)
    if event is None:
        raise HTTPException(404, f"Event {event_id} not found")
    return event


# ═══════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/settings")
async def get_settings():
    return await get_webui_store().get_settings()


@router.put("/settings")
async def update_settings(data: dict[str, Any]):
    return await get_webui_store().update_settings(data)


# ═══════════════════════════════════════════════════════════════════════════
# CHAT
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/chat/completions/stream")
async def chat_completions_stream(data: dict[str, Any]):
    """Chat completion streaming via le ChatPipeline Core (SSE).

    Le frontend envoie le provider_id, le modèle et le message. Le backend
    orchestre la génération via le ChatPipeline Core et renvoie les tokens
    un par un au format Server-Sent Events.

    La conversation est persistée dans le ChatStore Core (``/chats``) avec
    l'arbre de messages (parent_id / children_ids).
    """
    from fastapi.responses import StreamingResponse

    pipeline = get_chat_pipeline()

    user_message = data.get("message", "")
    provider_id = data.get("provider_id") or data.get("provider")
    model = data.get("model")
    chat_id: str | None = data.get("chat_id")
    user_id = data.get("user_id", "anonymous")
    skill_ids = data.get("skill_ids") or None
    tool_ids = data.get("tool_ids") or None
    knowledge_ids = data.get("knowledge_ids") or data.get("collection_ids") or None
    file_ids = data.get("file_ids") or None
    request_metadata = data.get("metadata") or {}
    agent_id = data.get("agent_id") or request_metadata.get("agent_id")

    async def event_stream():
        nonlocal provider_id, model, skill_ids, knowledge_ids, tool_ids
        try:
            # 1. Créer ou réutiliser la conversation.
            cid = chat_id
            if cid:
                chat_record = await pipeline._chats.get_chat(cid)
                if chat_record is None:
                    raise HTTPException(404, f"Chat {cid} not found")
            else:
                chat_record = await pipeline._chats.create_chat(
                    title=user_message[:60] or "New Chat",
                    user_id=user_id,
                    metadata=request_metadata,
                )
                cid = chat_record["id"]
            assert cid is not None

            # 1bis. Routage Chat → Agent : le provider/model/skills de
            # l'agent complètent la requête (logique Core, pas API).
            agent_info = await pipeline._resolve_agent(agent_id)
            if agent_info is not None:
                provider_id = provider_id or agent_info["provider"]
                model = model or agent_info["model"]
                merged_skills = list(skill_ids or [])
                for sid in agent_info["skill_ids"]:
                    if sid not in merged_skills:
                        merged_skills.append(sid)
                skill_ids = merged_skills
                # Knowledge / Tools configurés sur l'agent : fusionnés avec
                # la sélection explicite de l'utilisateur (qui garde la
                # priorité). Logique Core, pas API.
                merged_knowledge = list(knowledge_ids or [])
                for kid in agent_info.get("knowledge_ids") or []:
                    if kid not in merged_knowledge:
                        merged_knowledge.append(kid)
                knowledge_ids = merged_knowledge
                merged_tools = list(tool_ids or [])
                for tid in agent_info.get("tool_ids") or []:
                    if tid not in merged_tools:
                        merged_tools.append(tid)
                tool_ids = merged_tools

            # 2. Persister le message utilisateur.
            user_msg = await pipeline._chats.add_message(
                cid,
                role="user",
                content=user_message,
                user_id=user_id,
                metadata={
                    "provider_id": provider_id,
                    "model": model,
                    "skill_ids": skill_ids or [],
                    "tool_ids": tool_ids or [],
                    "knowledge_ids": knowledge_ids or [],
                    "file_ids": file_ids or [],
                    "agent_id": agent_id,
                },
            )

            # 3. Construire le contexte LLM (skills, RAG scoping, fichiers,
            # mémoire, catalogue d'outils, persona agent).
            llm_messages = await pipeline._build_llm_messages(
                chat_id=cid,
                user_message=user_message,
                user_id=user_id,
                skill_ids=skill_ids,
                knowledge_ids=knowledge_ids,
                file_ids=file_ids,
                tool_ids=tool_ids,
                agent_info=agent_info,
            )

            # 4. Générer en streaming.
            if pipeline._manager is None:
                # Fallback écho.
                content = f"[ECHO] {user_message}"
                yield f"data: {json.dumps({'type': 'content', 'chat_id': cid, 'content': content})}\n\n"
                await pipeline._chats.add_message(
                    cid, role="assistant", content=content, user_id=user_id,
                    parent_id=user_msg["id"], metadata={"provider": "mock", "model": "echo"},
                )
                yield f"data: {json.dumps({'type': 'done', 'chat_id': cid})}\n\n"
                return

            async def open_stream():
                """Ouvre un flux LLM (provider direct ou sélection auto).

                Réévaluée à chaque tour de la boucle d'outils car
                ``llm_messages`` s'enrichit des résultats d'outils.
                """
                if provider_id:
                    provider = pipeline._manager._registry.get_provider(provider_id)
                    if provider is None:
                        config = pipeline._manager._providers_config.get(provider_id)
                        if config and config.get("enabled", False):
                            from core.llm.provider_factory import create_provider_from_config
                            provider = create_provider_from_config({**config, "name": provider_id})
                            await provider.initialize()
                    if provider is not None:
                        # chat_stream est un async generator : pas d'await.
                        return provider.chat_stream(llm_messages, model=model or None)
                    raise HTTPException(502, f"Provider {provider_id} unavailable")
                requirements = LLMRequirements(task_type="chat")
                return pipeline._manager.chat_stream(llm_messages, requirements)

            # 5. Persister le message assistant (vide, on le met à jour en streaming).
            assistant_msg = await pipeline._chats.add_message(
                cid,
                role="assistant",
                content="",
                user_id=user_id,
                parent_id=user_msg["id"],
                model=model,
                status="pending",
                done=False,
            )

            full_content = ""
            try:
                # Boucle génération → détection <tool> → exécution Core →
                # continuation (bornée à MAX_TOOL_ROUNDS).
                MAX_TOOL_ROUNDS = 3
                for round_index in range(MAX_TOOL_ROUNDS + 1):
                    round_content = ""
                    stream = await open_stream()
                    async for chunk in stream:
                        if chunk:
                            round_content += chunk
                            full_content += chunk
                            yield f"data: {json.dumps({'type': 'content', 'chat_id': cid, 'content': chunk})}\n\n"

                    calls = _parse_tool_calls(round_content)
                    if not calls or round_index == MAX_TOOL_ROUNDS:
                        break

                    # Exécution réelle via le ToolManager Core (builtin,
                    # custom ou MCP selon le provider du tool).
                    notes: dict[str, str] = {}
                    result_lines: list[str] = []
                    for call in calls:
                        name = call["name"]
                        yield f"data: {json.dumps({'type': 'tool_call', 'chat_id': cid, 'tool': name, 'params': call['params']})}\n\n"
                        outcome = await pipeline.execute_tool_call(
                            name, call["params"], user_id=user_id,
                        )
                        summary = (
                            outcome.get("output")
                            or outcome.get("error")
                            or outcome.get("status", "failed")
                        )
                        result_lines.append(
                            f"[Résultat outil « {name} » ({outcome.get('status')})]\n{summary}"
                        )
                        notes[name] = f"_[Outil « {name} » exécuté ({outcome.get('status')})]_"
                        yield f"data: {json.dumps({'type': 'tool_result', 'chat_id': cid, 'tool': name, 'status': outcome.get('status'), 'output': str(summary)[:2000]})}\n\n"

                    # Les blocs bruts sont remplacés par une note lisible
                    # dans le contenu affiché puis persisté.
                    full_content = _strip_tool_blocks(full_content, notes)
                    yield f"data: {json.dumps({'type': 'content_replace', 'chat_id': cid, 'content': full_content})}\n\n"

                    # Continuation : réponse intermédiaire + résultats
                    # d'outils injectés dans le contexte du tour suivant.
                    llm_messages.append(LLMChatMessage(role="assistant", content=round_content))
                    llm_messages.append(
                        LLMChatMessage(
                            role="user",
                            content=(
                                "[Résultats d'outils]\n"
                                + "\n\n".join(result_lines)
                                + "\n\nContinue ta réponse en t'appuyant sur ces résultats."
                            ),
                        )
                    )

            except asyncio.CancelledError:
                # Client interrompu (stop generation) : la tâche ASGI est déjà
                # annulée — un await direct ici serait lui-même annulé et la
                # persistance échouerait silencieusement (message resté
                # « pending » constaté en test). La sauvegarde du contenu
                # partiel est donc déléguée à une tâche détachée qui survit à
                # l'annulation : pas de trou dans l'historique après refresh.
                persisted = _strip_tool_blocks(full_content) if tool_ids else full_content

                async def _persist_stopped() -> None:
                    try:
                        await pipeline._chats.update_message(
                            cid, assistant_msg["id"],
                            {"content": persisted, "status": "stopped", "done": True},
                        )
                    except Exception:
                        logger.exception(
                            "Failed to persist partial chat message (chat %s)", cid,
                        )

                asyncio.get_running_loop().create_task(_persist_stopped())
                raise
            else:
                # Fin normale : réponse complète persistée + événement done.
                persisted = (
                    _strip_tool_blocks(full_content) if tool_ids else full_content
                )
                await pipeline._chats.update_message(
                    cid, assistant_msg["id"],
                    {"content": persisted, "status": "done", "done": True},
                )
                done_payload = json.dumps(
                    {
                        "type": "done",
                        "chat_id": cid,
                        "message_id": assistant_msg["id"],
                    },
                )
                yield f"data: {done_payload}\n\n"

        except asyncio.CancelledError:
            logger.info("Chat stream cancelled by client (chat %s)", data.get("chat_id"))
            raise
        except Exception as exc:
            logger.exception("Chat stream failed: %s", exc)
            yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat/completions")
async def chat_completions(data: dict[str, Any]):
    """Chat completion non-streaming via le ChatPipeline Core.

    Le frontend envoie le provider_id, le modèle et le message. Le backend
    orchestre la génération via le ChatPipeline Core et renvoie la réponse
    complète.

    La conversation est persistée dans le ChatStore Core (``/chats``) avec
    l'arbre de messages (parent_id / children_ids).
    """
    pipeline = get_chat_pipeline()

    result = await pipeline.run(
        message=data.get("message", ""),
        chat_id=data.get("chat_id"),
        user_id=data.get("user_id", "anonymous"),
        provider_id=data.get("provider_id") or data.get("provider"),
        model=data.get("model"),
        parent_id=data.get("parent_id"),
        skill_ids=data.get("skill_ids"),
        tool_ids=data.get("tool_ids"),
        knowledge_ids=data.get("knowledge_ids") or data.get("collection_ids"),
        file_ids=data.get("file_ids"),
        agent_id=(data.get("metadata") or {}).get("agent_id") or data.get("agent_id"),
        metadata=data.get("metadata"),
    )

    return {
        "id": str(uuid.uuid4()),
        "chat_id": result["chat_id"],
        "message": result["assistant_message"]["content"],
        "role": "assistant",
        "timestamp": _utc_now_rfc3339(),
        "metadata": {
            "provider": result["assistant_message"]["metadata"].get("provider"),
            "model": result["assistant_message"]["metadata"].get("model"),
            "usage": result["assistant_message"]["metadata"].get("usage"),
        },
    }


@router.get("/chat/history")
async def chat_history(limit: int = 50):
    """Historique des conversations Core (ChatStore), plus le store WebUI.

    Retourne les messages de toutes les conversations du ChatStore Core.
    """
    chat_store = get_chat_store()
    chats = await chat_store.list_chats()
    messages: list[dict[str, Any]] = []
    for chat_record in chats:
        messages.extend(await chat_store.list_messages(chat_record["id"]))
    messages.sort(key=lambda m: m.get("created_at", ""))
    return messages[-limit:]


# ═══════════════════════════════════════════════════════════════════════════
# PLUGINS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/plugins")
async def list_plugins():
    return await get_webui_store().list_plugins()

@router.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    plugin = await get_webui_store().get_plugin(plugin_id)
    if plugin is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return plugin

@router.post("/plugins/install")
async def install_plugin(data: dict[str, Any]):
    return await get_webui_store().install_plugin(data)

@router.put("/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str):
    plugin = await get_webui_store().toggle_plugin(plugin_id)
    if plugin is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return plugin
