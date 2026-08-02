"""V1 API Router — Endpoints attendus par le frontend WebUI.

Fournit des implémentations minimales mais fonctionnelles pour :
- /v1/agents
- /v1/goals
- /v1/missions
- /v1/memory/*
- /v1/skills
- /v1/knowledge
- /v1/flux
- /v1/settings
- /v1/chat

Le stockage est en mémoire (pour l'instant). Les données sont perdues au
redémarrage du conteneur API. Pour la persistence, remplacer par PostgreSQL.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any
import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.auth import Permission
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["v1"])


# ── In-memory stores ──────────────────────────────────────────────────────

class MemoryStore:
    def __init__(self) -> None:
        self.agents: dict[str, dict[str, Any]] = {}
        self.goals: dict[str, dict[str, Any]] = {}
        self.missions: dict[str, dict[str, Any]] = {}
        self.facts: dict[str, dict[str, Any]] = {}
        self.skills: dict[str, dict[str, Any]] = {}
        self.knowledge: dict[str, dict[str, Any]] = {}
        self.events: list[dict[str, Any]] = []
        self.chat_messages: list[dict[str, Any]] = []

    def _now(self) -> str:
        return datetime.datetime.utcnow().isoformat() + "Z"


_store = MemoryStore()


# ═══════════════════════════════════════════════════════════════════════════
# AGENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/agents")
async def list_agents():
    return list(_store.agents.values())


@router.post("/agents", dependencies=[Depends(require_permission(Permission.AGENTS))])
async def create_agent(data: dict[str, Any]):
    agent_id = str(uuid.uuid4())
    agent = {
        "id": agent_id,
        "name": data.get("name", "unnamed"),
        "capabilities": data.get("capabilities", []),
        "status": "idle",
        "created_at": _store._now(),
    }
    _store.agents[agent_id] = agent
    return agent


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    if agent_id not in _store.agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return _store.agents[agent_id]


@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, data: dict[str, Any]):
    if agent_id not in _store.agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    _store.agents[agent_id].update(data)
    return _store.agents[agent_id]


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    if agent_id not in _store.agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    del _store.agents[agent_id]
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════
# GOALS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/goals")
async def list_goals():
    return list(_store.goals.values())


@router.post("/goals")
async def create_goal(data: dict[str, Any]):
    goal_id = str(uuid.uuid4())
    goal = {
        "id": goal_id,
        "title": data.get("title", "untitled"),
        "description": data.get("description", ""),
        "priority": data.get("priority", "normal"),
        "status": "pending",
        "created_at": _store._now(),
    }
    _store.goals[goal_id] = goal
    return goal


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    if goal_id not in _store.goals:
        raise HTTPException(404, f"Goal {goal_id} not found")
    return _store.goals[goal_id]


@router.put("/goals/{goal_id}")
async def update_goal(goal_id: str, data: dict[str, Any]):
    if goal_id not in _store.goals:
        raise HTTPException(404, f"Goal {goal_id} not found")
    _store.goals[goal_id].update(data)
    return _store.goals[goal_id]


@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str):
    if goal_id not in _store.goals:
        raise HTTPException(404, f"Goal {goal_id} not found")
    del _store.goals[goal_id]
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════
# MISSIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/missions")
async def list_missions():
    return list(_store.missions.values())


@router.post("/missions", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def create_mission(data: dict[str, Any]):
    mission_id = str(uuid.uuid4())
    mission = {
        "id": mission_id,
        "title": data.get("title", "untitled"),
        "description": data.get("description", ""),
        "status": "pending",
        "progress": 0,
        "steps": data.get("steps", []),
        "created_at": _store._now(),
    }
    _store.missions[mission_id] = mission
    return mission


@router.get("/missions/{mission_id}")
async def get_mission(mission_id: str):
    if mission_id not in _store.missions:
        raise HTTPException(404, f"Mission {mission_id} not found")
    return _store.missions[mission_id]


@router.put("/missions/{mission_id}")
async def update_mission(mission_id: str, data: dict[str, Any]):
    if mission_id not in _store.missions:
        raise HTTPException(404, f"Mission {mission_id} not found")
    _store.missions[mission_id].update(data)
    return _store.missions[mission_id]


@router.delete("/missions/{mission_id}")
async def delete_mission(mission_id: str):
    if mission_id not in _store.missions:
        raise HTTPException(404, f"Mission {mission_id} not found")
    del _store.missions[mission_id]
    return {"status": "deleted"}


@router.post("/missions/{mission_id}/steps/{step_id}/verify")
async def verify_mission_step(mission_id: str, step_id: str):
    if mission_id not in _store.missions:
        raise HTTPException(404, f"Mission {mission_id} not found")
    return {"verified": True}


@router.post("/missions/{mission_id}/steps/{step_id}/approve")
async def approve_mission_step(mission_id: str, step_id: str):
    if mission_id not in _store.missions:
        raise HTTPException(404, f"Mission {mission_id} not found")
    return {"status": "approved"}


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY / FACTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/memory/facts")
async def list_facts(limit: int = 20, category: str | None = None):
    facts = list(_store.facts.values())
    if category:
        facts = [f for f in facts if f.get("category") == category]
    return facts[: limit]


@router.get("/memory/facts/search")
async def search_facts(q: str = ""):
    q_lower = q.lower()
    results = [
        f for f in _store.facts.values()
        if q_lower in f.get("subject", "").lower()
        or q_lower in f.get("predicate", "").lower()
        or q_lower in f.get("object", "").lower()
    ]
    return results


@router.get("/memory/facts/{fact_id}")
async def get_fact(fact_id: str):
    if fact_id not in _store.facts:
        raise HTTPException(404, f"Fact {fact_id} not found")
    return _store.facts[fact_id]


@router.post("/memory/facts")
async def create_fact(data: dict[str, Any]):
    fact_id = str(uuid.uuid4())
    fact = {
        "id": fact_id,
        "subject": data.get("subject", ""),
        "predicate": data.get("predicate", ""),
        "object": data.get("object", ""),
        "category": data.get("category", "knowledge"),
        "confidence": data.get("confidence", 0.5),
        "created_at": _store._now(),
    }
    _store.facts[fact_id] = fact
    return fact


@router.get("/memory/events")
async def list_memory_events():
    return list(reversed(_store.events[-100:]))


@router.post("/memory/ingest")
async def ingest_memory(entry: dict[str, Any]):
    event = {
        "id": str(uuid.uuid4()),
        "type": entry.get("type", "event"),
        "content": entry.get("content", ""),
        "metadata": entry.get("metadata", {}),
        "timestamp": _store._now(),
    }
    _store.events.append(event)
    return event


@router.get("/memory/search")
async def search_memory(q: str = "", filters: dict[str, Any] | None = None):
    q_lower = q.lower()
    results = []
    for ev in _store.events:
        text = str(ev).lower()
        if q_lower in text:
            results.append(ev)
    for f in _store.facts.values():
        text = str(f).lower()
        if q_lower in text:
            results.append(f)
    return results[:50]


@router.get("/memory/{memory_id}")
async def get_memory_entry(memory_id: str):
    for ev in _store.events:
        if ev.get("id") == memory_id:
            return ev
    raise HTTPException(404, f"Memory entry {memory_id} not found")


# ═══════════════════════════════════════════════════════════════════════════
# SKILLS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/skills")
async def list_skills():
    return list(_store.skills.values())


@router.post("/skills", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def create_skill(data: dict[str, Any]):
    skill_id = str(uuid.uuid4())
    skill = {
        "id": skill_id,
        "name": data.get("name", "unnamed"),
        "description": data.get("description", ""),
        "version": "1.0.0",
        "status": "active",
        "created_at": _store._now(),
    }
    _store.skills[skill_id] = skill
    return skill


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    if skill_id not in _store.skills:
        raise HTTPException(404, f"Skill {skill_id} not found")
    return _store.skills[skill_id]


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: str, data: dict[str, Any]):
    if skill_id not in _store.skills:
        raise HTTPException(404, f"Skill {skill_id} not found")
    _store.skills[skill_id].update(data)
    return _store.skills[skill_id]


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    if skill_id not in _store.skills:
        raise HTTPException(404, f"Skill {skill_id} not found")
    del _store.skills[skill_id]
    return {"status": "deleted"}


@router.post("/skills/{skill_id}/execute")
async def execute_skill(skill_id: str, params: dict[str, Any]):
    if skill_id not in _store.skills:
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
    return list(_store.knowledge.values())


@router.get("/knowledge/search")
async def search_knowledge(q: str = ""):
    q_lower = q.lower()
    return [
        k for k in _store.knowledge.values()
        if q_lower in k.get("label", "").lower()
    ]


@router.get("/knowledge/{knowledge_id}")
async def get_knowledge(knowledge_id: str):
    if knowledge_id not in _store.knowledge:
        raise HTTPException(404, f"Knowledge {knowledge_id} not found")
    return _store.knowledge[knowledge_id]


@router.post("/knowledge")
async def create_knowledge(data: dict[str, Any]):
    kid = str(uuid.uuid4())
    node = {
        "id": kid,
        "label": data.get("label", ""),
        "type": data.get("type", "concept"),
        "connections": data.get("connections", []),
        "created_at": _store._now(),
    }
    _store.knowledge[kid] = node
    return node


# ═══════════════════════════════════════════════════════════════════════════
# FLUX / EVENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/flux")
async def list_flux_events(limit: int = 50, type: str | None = None):
    events = _store.events
    if type:
        events = [e for e in events if e.get("type") == type]
    return list(reversed(events[-limit:]))


@router.get("/flux/{event_id}")
async def get_flux_event(event_id: str):
    for ev in _store.events:
        if ev.get("id") == event_id:
            return ev
    raise HTTPException(404, f"Event {event_id} not found")


# ═══════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

_default_settings = {
    "llm": {"provider": "openai", "model": "gpt-4", "temperature": 0.7},
    "permissions": {"allow_autonomy": False, "allow_network": True},
    "budget": {"daily_limit_usd": 10.0, "alert_threshold": 0.8},
    "system": {"log_level": "INFO", "max_workers": 4},
}


@router.get("/settings")
async def get_settings():
    return _default_settings


@router.put("/settings")
async def update_settings(data: dict[str, Any]):
    _default_settings.update(data)
    return _default_settings


# ═══════════════════════════════════════════════════════════════════════════
# CHAT
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/chat")
async def chat(data: dict[str, Any]):
    user_message = data.get("message", "")
    response = {
        "id": str(uuid.uuid4()),
        "message": f"[ECHO] {user_message}",
        "role": "assistant",
        "timestamp": _store._now(),
        "metadata": {"provider": "mock", "model": "echo"},
    }
    _store.chat_messages.append(
        {"role": "user", "content": user_message, "timestamp": _store._now()}
    )
    _store.chat_messages.append(response)
    return response


@router.get("/chat/history")
async def chat_history(limit: int = 50):
    return list(reversed(_store.chat_messages[-limit:]))


# ═══════════════════════════════════════════════════════════════════════════
# PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════

_default_providers = [
    {"id": "openai", "name": "OpenAI", "type": "LLM", "status": "connected", "configured": True},
    {"id": "anthropic", "name": "Anthropic", "type": "LLM", "status": "connected", "configured": True},
    {"id": "huggingface", "name": "HuggingFace", "type": "LLM", "status": "disconnected", "configured": False},
    {"id": "pinecone", "name": "Pinecone", "type": "VectorDB", "status": "connected", "configured": True},
]


@router.get("/providers")
async def list_providers():
    return _default_providers


@router.get("/providers/{provider_id}")
async def get_provider(provider_id: str):
    for p in _default_providers:
        if p["id"] == provider_id:
            return p
    raise HTTPException(404, f"Provider {provider_id} not found")


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, data: dict[str, Any]):
    for p in _default_providers:
        if p["id"] == provider_id:
            p.update(data)
            return p
    raise HTTPException(404, f"Provider {provider_id} not found")


# ═══════════════════════════════════════════════════════════════════════════
# PLUGINS
# ═══════════════════════════════════════════════════════════════════════════

_default_plugins = [
    {"id": "github", "name": "GitHub Integration", "status": "active", "version": "1.0.0"},
    {"id": "slack", "name": "Slack Notifier", "status": "inactive", "version": "1.2.0"},
]

@router.get("/plugins")
async def list_plugins():
    return _default_plugins

@router.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    for p in _default_plugins:
        if p["id"] == plugin_id:
            return p
    raise HTTPException(404, f"Plugin {plugin_id} not found")

@router.post("/plugins/install")
async def install_plugin(data: dict[str, Any]):
    new_plugin = {
        "id": data.get("id", str(uuid.uuid4())),
        "name": data.get("name", "Unknown Plugin"),
        "status": "inactive",
        "version": "0.1.0"
    }
    _default_plugins.append(new_plugin)
    return new_plugin

@router.put("/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str):
    for p in _default_plugins:
        if p["id"] == plugin_id:
            p["status"] = "active" if p["status"] == "inactive" else "inactive"
            return p
    raise HTTPException(404, f"Plugin {plugin_id} not found")
