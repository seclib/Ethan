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

import logging
import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from core.agents import AgentExecutionUnavailable, AgentManager
from core.auth import Permission
from core.knowledge import KnowledgeManager
from interfaces.api.auth import require_permission
from core.llm.provider_manager import ProviderManager
from core.llm.types import ChatMessage, LLMRequirements
from core.missions import MissionManager
from core.rag import RAGPipeline
from core.state.webui_store import CoreWebUIStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["v1"])

# Instance globale du ProviderManager — injectée au démarrage via set_provider_manager()
_manager: ProviderManager | None = None

# Instance globale du CoreWebUIStore (records persistants goals/facts/skills/
# events/settings/providers/plugins) — injectée au démarrage via set_webui_store().
_webui_store: CoreWebUIStore | None = None


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


def set_core_domain_services(services: CoreDomainServices) -> None:
    """Inject the Core composition root during API startup."""
    global _domains
    _domains = services


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
    return await get_webui_store().list_skills()


@router.post("/skills", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def create_skill(data: dict[str, Any]):
    return await get_webui_store().create_skill(data)


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    skill = await get_webui_store().get_skill(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return skill


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: str, data: dict[str, Any]):
    skill = await get_webui_store().update_skill(skill_id, data)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return skill


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    if not await get_webui_store().delete_skill(skill_id):
        raise HTTPException(404, f"Skill {skill_id} not found")
    return {"status": "deleted"}


@router.post("/skills/{skill_id}/execute")
async def execute_skill(skill_id: str, params: dict[str, Any]):
    skill = await get_webui_store().get_skill(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return {
        "skill_id": skill_id,
        "status": "executed",
        "result": {"message": f"Skill {skill_id} executed with params {params}"},
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

@router.post("/chat")
async def chat(data: dict[str, Any]):
    """Chat completion via le ProviderManager.

    Le frontend envoie le provider_id et le modèle actifs. Le backend
    utilise le ProviderManager pour générer une vraie réponse LLM.
    """
    user_message = data.get("message", "")
    provider_id = data.get("provider_id") or data.get("provider")
    model = data.get("model")

    webui_store = get_webui_store()

    # Enregistrer le message utilisateur
    await webui_store.append_chat_message({"role": "user", "content": user_message})

    # Si le ProviderManager n'est pas initialisé, fallback sur l'écho
    if _manager is None:
        logger.warning("ProviderManager not initialized — falling back to echo")
        response = {
            "id": str(uuid.uuid4()),
            "message": f"[ECHO] {user_message}",
            "role": "assistant",
            "timestamp": _utc_now_rfc3339(),
            "metadata": {"provider": "mock", "model": "echo"},
        }
        await webui_store.append_chat_message(response)
        return response

    try:
        # Construire les messages de conversation
        messages = [ChatMessage(role="user", content=user_message)]

        # Si un provider_id est fourni, utiliser le provider directement
        # pour forcer le modèle demandé par l'utilisateur.
        if provider_id:
            provider = _manager._registry.get_provider(provider_id)
            if provider is None:
                # Tenter d'instancier depuis la config
                config = _manager._providers_config.get(provider_id)
                if config and config.get("enabled", False):
                    from core.llm.provider_factory import create_provider_from_config
                    provider = create_provider_from_config({**config, "name": provider_id})
                    await provider.initialize()
            if provider is not None:
                result = await provider.chat(messages, model=model or None)
                response = {
                    "id": str(uuid.uuid4()),
                    "message": result.content,
                    "role": "assistant",
                    "timestamp": _utc_now_rfc3339(),
                    "metadata": {
                        "provider": provider_id,
                        "model": result.model,
                        "usage": result.usage,
                    },
                }
                await webui_store.append_chat_message(response)
                return response

        # Fallback : sélection automatique via le ProviderManager
        requirements = LLMRequirements(
            task_type="chat",
            preferred_providers=[provider_id] if provider_id else [],
        )

        # Appeler le LLM via le ProviderManager
        result = await _manager.chat(messages, requirements)

        response = {
            "id": str(uuid.uuid4()),
            "message": result.content,
            "role": "assistant",
            "timestamp": _utc_now_rfc3339(),
            "metadata": {
                "provider": result.provider,
                "model": result.model,
                "usage": result.usage,
            },
        }
        await webui_store.append_chat_message(response)
        return response
    except Exception as exc:
        logger.exception("Chat failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}")


@router.get("/chat/history")
async def chat_history(limit: int = 50):
    return await get_webui_store().list_chat_messages(limit=limit)


# ═══════════════════════════════════════════════════════════════════════════
# PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/providers")
async def list_providers():
    return await get_webui_store().list_providers()


@router.get("/providers/{provider_id}")
async def get_provider(provider_id: str):
    provider = await get_webui_store().get_provider(provider_id)
    if provider is None:
        raise HTTPException(404, f"Provider {provider_id} not found")
    return provider


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, data: dict[str, Any]):
    provider = await get_webui_store().update_provider(provider_id, data)
    if provider is None:
        raise HTTPException(404, f"Provider {provider_id} not found")
    return provider


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
