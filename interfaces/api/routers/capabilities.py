"""Capabilities router — expose Core capability managers to HTTP clients.

Core modules live in core/ and stay usable by the CLI or another interface.
This router is a thin HTTP gateway (no business logic): it simply maps REST
verbs onto the Core managers for automations, calendar, TTS, image
generation, evaluations, analytics, channels, notes, Core tools and tool
servers, prompts and SCIM.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.auth import Permission
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["capabilities"])


class CapabilityManagers:
    """Core-owned capability managers exposed through this HTTP gateway."""

    def __init__(
        self,
        *,
        automations: Any | None = None,
        calendar: Any | None = None,
        tts: Any | None = None,
        images: Any | None = None,
        evaluations: Any | None = None,
        analytics: Any | None = None,
        channels: Any | None = None,
        notes: Any | None = None,
        tools: Any | None = None,
        tool_servers: Any | None = None,
        prompts: Any | None = None,
        scim: Any | None = None,
        ldap: Any | None = None,
        oauth: Any | None = None,
        skills: Any | None = None,
    ) -> None:
        self.automations = automations
        self.calendar = calendar
        self.tts = tts
        self.images = images
        self.evaluations = evaluations
        self.analytics = analytics
        self.channels = channels
        self.notes = notes
        self.tools = tools
        self.tool_servers = tool_servers
        self.prompts = prompts
        self.scim = scim
        self.ldap = ldap
        self.oauth = oauth
        self.skills = skills


_managers = CapabilityManagers()


def set_capability_managers(managers: CapabilityManagers) -> None:
    """Inject the Core capability managers during API startup."""
    global _managers
    _managers = managers


def _require(manager: Any, name: str) -> Any:
    if manager is None:
        raise HTTPException(503, f"{name} manager not initialized")
    return manager


# ═══════════════════════════════════════════════════════════════════════════
# AUTOMATIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/automations")
async def list_automations(enabled: bool | None = None):
    manager = _require(_managers.automations, "Automation")
    try:
        return await manager.list(enabled=enabled)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/automations", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def create_automation(data: dict[str, Any]):
    manager = _require(_managers.automations, "Automation")
    try:
        return await manager.create(
            name=data.get("name", ""),
            trigger=data.get("trigger", {}),
            actions=data.get("actions", []),
            description=data.get("description", ""),
            enabled=bool(data.get("enabled", True)),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/automations/{automation_id}")
async def get_automation(automation_id: str):
    manager = _require(_managers.automations, "Automation")
    rule = await manager.get(automation_id)
    if rule is None:
        raise HTTPException(404, f"Automation {automation_id} not found")
    return rule


@router.put("/automations/{automation_id}")
async def update_automation(automation_id: str, data: dict[str, Any]):
    manager = _require(_managers.automations, "Automation")
    rule = await manager.update(automation_id, data)
    if rule is None:
        raise HTTPException(404, f"Automation {automation_id} not found")
    return rule


@router.delete("/automations/{automation_id}")
async def delete_automation(automation_id: str):
    manager = _require(_managers.automations, "Automation")
    if not await manager.delete(automation_id):
        raise HTTPException(404, f"Automation {automation_id} not found")
    return {"status": "deleted"}


@router.post("/automations/{automation_id}/trigger")
async def trigger_automation(automation_id: str):
    manager = _require(_managers.automations, "Automation")
    result = await manager.trigger(automation_id)
    if result is None:
        raise HTTPException(404, f"Automation {automation_id} not found")
    return result


# ═══════════════════════════════════════════════════════════════════════════
# CALENDAR
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/calendar")
async def list_calendar_events():
    manager = _require(_managers.calendar, "Calendar")
    return await manager.list()


@router.post("/calendar", dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_calendar_event(data: dict[str, Any]):
    manager = _require(_managers.calendar, "Calendar")
    try:
        return await manager.create(
            title=data.get("title", ""),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time"),
            description=data.get("description", ""),
            all_day=bool(data.get("all_day", False)),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/calendar/{event_id}")
async def get_calendar_event(event_id: str):
    manager = _require(_managers.calendar, "Calendar")
    event = await manager.get(event_id)
    if event is None:
        raise HTTPException(404, f"Calendar event {event_id} not found")
    return event


@router.put("/calendar/{event_id}")
async def update_calendar_event(event_id: str, data: dict[str, Any]):
    manager = _require(_managers.calendar, "Calendar")
    event = await manager.update(event_id, data)
    if event is None:
        raise HTTPException(404, f"Calendar event {event_id} not found")
    return event


@router.delete("/calendar/{event_id}")
async def delete_calendar_event(event_id: str):
    manager = _require(_managers.calendar, "Calendar")
    if not await manager.delete(event_id):
        raise HTTPException(404, f"Calendar event {event_id} not found")
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════
# AUDIO (TTS)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/audio/config")
async def get_audio_config():
    manager = _require(_managers.tts, "TTS")
    return await manager.get_config() or {}


@router.post("/audio/config", dependencies=[Depends(require_permission(Permission.WRITE))])
async def configure_audio(data: dict[str, Any]):
    manager = _require(_managers.tts, "TTS")
    try:
        return await manager.configure(
            provider=data.get("provider", ""),
            voice=data.get("voice", "default"),
            speed=float(data.get("speed", 1.0)),
            api_key=data.get("api_key"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/audio/synthesize", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def synthesize_audio(data: dict[str, Any]):
    manager = _require(_managers.tts, "TTS")
    text = data.get("text", "")
    if not text:
        raise HTTPException(422, "text is required")
    try:
        audio = await manager.synthesize(text, config=data.get("config"))
    except Exception as exc:
        raise HTTPException(500, f"TTS synthesis failed: {exc}") from exc
    return {
        "format": "wav",
        "content_base64": base64.b64encode(audio).decode("ascii"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# IMAGES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/images/config")
async def get_images_config():
    manager = _require(_managers.images, "ImageGeneration")
    return await manager.get_config() or {}


@router.post("/images/config", dependencies=[Depends(require_permission(Permission.WRITE))])
async def configure_images(data: dict[str, Any]):
    manager = _require(_managers.images, "ImageGeneration")
    try:
        return await manager.configure(
            provider=data.get("provider", ""),
            model=data.get("model", "dall-e-3"),
            api_key=data.get("api_key"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/images/generate", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def generate_image(data: dict[str, Any]):
    manager = _require(_managers.images, "ImageGeneration")
    prompt = data.get("prompt", "")
    if not prompt:
        raise HTTPException(422, "prompt is required")
    try:
        image = await manager.generate(prompt, config=data.get("config"))
    except Exception as exc:
        raise HTTPException(500, f"Image generation failed: {exc}") from exc
    return {
        "format": "png",
        "content_base64": base64.b64encode(image).decode("ascii"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# EVALUATIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/evaluations")
async def list_evaluations():
    manager = _require(_managers.evaluations, "Evaluation")
    return await manager.list()


@router.post("/evaluations", dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_evaluation(data: dict[str, Any]):
    manager = _require(_managers.evaluations, "Evaluation")
    try:
        return await manager.create(
            name=data.get("name", ""),
            criteria=data.get("criteria", []),
            target=data.get("target", ""),
            description=data.get("description", ""),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/evaluations/{eval_id}")
async def get_evaluation(eval_id: str):
    manager = _require(_managers.evaluations, "Evaluation")
    evaluation = await manager.get(eval_id)
    if evaluation is None:
        raise HTTPException(404, f"Evaluation {eval_id} not found")
    return evaluation


@router.post("/evaluations/{eval_id}/results")
async def add_evaluation_result(eval_id: str, data: dict[str, Any]):
    manager = _require(_managers.evaluations, "Evaluation")
    result = await manager.add_result(eval_id, data)
    if result is None:
        raise HTTPException(404, f"Evaluation {eval_id} not found")
    return result


# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/analytics/events", dependencies=[Depends(require_permission(Permission.WRITE))])
async def record_analytics_event(data: dict[str, Any]):
    manager = _require(_managers.analytics, "Analytics")
    try:
        return await manager.record_event(
            event_type=data.get("event_type", ""),
            user_id=data.get("user_id", "anonymous"),
            provider=data.get("provider"),
            model=data.get("model"),
            tokens_in=int(data.get("tokens_in", 0)),
            tokens_out=int(data.get("tokens_out", 0)),
            cost=float(data.get("cost", 0.0)),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/analytics/events")
async def list_analytics_events(
    event_type: str | None = None,
    user_id: str | None = None,
    limit: int = 50,
):
    manager = _require(_managers.analytics, "Analytics")
    return await manager.list_events(event_type=event_type, user_id=user_id, limit=limit)


@router.get("/analytics/summary")
async def get_analytics_summary(user_id: str | None = None):
    manager = _require(_managers.analytics, "Analytics")
    return await manager.get_usage_summary(user_id=user_id)


# ═══════════════════════════════════════════════════════════════════════════
# CHANNELS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/channels")
async def list_channels():
    manager = _require(_managers.channels, "Channel")
    return await manager.list_channels()


@router.post("/channels", dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_channel(data: dict[str, Any]):
    manager = _require(_managers.channels, "Channel")
    try:
        return await manager.create_channel(
            name=data.get("name", ""),
            description=data.get("description", ""),
            user_id=data.get("user_id", "anonymous"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/channels/{channel_id}")
async def get_channel(channel_id: str):
    manager = _require(_managers.channels, "Channel")
    channel = await manager.get_channel(channel_id)
    if channel is None:
        raise HTTPException(404, f"Channel {channel_id} not found")
    return channel


@router.put("/channels/{channel_id}")
async def update_channel(channel_id: str, data: dict[str, Any]):
    manager = _require(_managers.channels, "Channel")
    channel = await manager.update_channel(channel_id, data)
    if channel is None:
        raise HTTPException(404, f"Channel {channel_id} not found")
    return channel


@router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: str):
    manager = _require(_managers.channels, "Channel")
    if not await manager.delete_channel(channel_id):
        raise HTTPException(404, f"Channel {channel_id} not found")
    return {"status": "deleted"}


@router.post("/channels/{channel_id}/messages")
async def add_channel_message(channel_id: str, data: dict[str, Any]):
    manager = _require(_managers.channels, "Channel")
    try:
        return await manager.add_message(
            channel_id,
            data.get("content", ""),
            user_id=data.get("user_id", "anonymous"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/channels/{channel_id}/messages")
async def list_channel_messages(channel_id: str):
    manager = _require(_managers.channels, "Channel")
    return await manager.list_messages(channel_id)


# ═══════════════════════════════════════════════════════════════════════════
# NOTES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/notes")
async def list_notes(user_id: str | None = None, pinned: bool | None = None):
    manager = _require(_managers.notes, "Note")
    return await manager.list(user_id=user_id, pinned=pinned)


@router.post("/notes", dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_note(data: dict[str, Any]):
    manager = _require(_managers.notes, "Note")
    try:
        return await manager.create(
            title=data.get("title", ""),
            content=data.get("content", ""),
            user_id=data.get("user_id", "anonymous"),
            pinned=bool(data.get("pinned", False)),
            tags=data.get("tags"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/notes/search")
async def search_notes(q: str = "", user_id: str | None = None):
    manager = _require(_managers.notes, "Note")
    return await manager.search(q, user_id=user_id)


@router.get("/notes/{note_id}")
async def get_note(note_id: str):
    manager = _require(_managers.notes, "Note")
    note = await manager.get(note_id)
    if note is None:
        raise HTTPException(404, f"Note {note_id} not found")
    return note


@router.put("/notes/{note_id}")
async def update_note(note_id: str, data: dict[str, Any]):
    manager = _require(_managers.notes, "Note")
    note = await manager.update(note_id, data)
    if note is None:
        raise HTTPException(404, f"Note {note_id} not found")
    return note


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    manager = _require(_managers.notes, "Note")
    if not await manager.delete(note_id):
        raise HTTPException(404, f"Note {note_id} not found")
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════
# TOOLS AND TOOL SERVERS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/tools")
async def list_tools():
    """List the Core-owned builtin, custom and discovered MCP tool catalogue."""
    manager = _require(_managers.tools, "Tool")
    return manager.list_tools()


@router.post("/tools", dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_tool(data: dict[str, Any]):
    """Create a persistent custom Tool definition in ETHAN Core."""
    manager = _require(_managers.tools, "Tool")
    try:
        return await manager.create_tool(
            name=data.get("name", ""),
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            code=data.get("code", ""),
            category=data.get("category", "custom"),
            capabilities=data.get("capabilities"),
            tags=data.get("tags"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.delete("/tools/{tool_id}", dependencies=[Depends(require_permission(Permission.WRITE))])
async def delete_tool(tool_id: str):
    manager = _require(_managers.tools, "Tool")
    try:
        deleted = await manager.delete_tool(tool_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not deleted:
        raise HTTPException(404, f"Tool {tool_id} not found")
    return {"status": "deleted"}


@router.get("/tools/pipelines")
async def list_tool_pipelines():
    manager = _require(_managers.tools, "Tool")
    return await manager.list_pipelines()


@router.post("/tools/pipelines", dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_tool_pipeline(data: dict[str, Any]):
    manager = _require(_managers.tools, "Tool")
    try:
        return await manager.create_pipeline(
            name=data.get("name", ""),
            steps=data.get("steps", []),
            description=data.get("description", ""),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/tools/pipelines/{pipeline_id}")
async def get_tool_pipeline(pipeline_id: str):
    manager = _require(_managers.tools, "Tool")
    pipeline = await manager.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(404, f"Tool pipeline {pipeline_id} not found")
    return pipeline


@router.delete("/tools/pipelines/{pipeline_id}")
async def delete_tool_pipeline(pipeline_id: str):
    manager = _require(_managers.tools, "Tool")
    if not await manager.delete_pipeline(pipeline_id):
        raise HTTPException(404, f"Tool pipeline {pipeline_id} not found")
    return {"status": "deleted"}

@router.get("/tools/servers")
async def list_tool_servers(enabled: bool | None = None):
    manager = _require(_managers.tool_servers, "ToolServer")
    return await manager.list(enabled=enabled)


@router.post("/tools/servers", dependencies=[Depends(require_permission(Permission.WRITE))])
async def register_tool_server(data: dict[str, Any]):
    manager = _require(_managers.tool_servers, "ToolServer")
    try:
        return await manager.register(
            name=data.get("name", ""),
            url=data.get("url", ""),
            description=data.get("description", ""),
            auth_type=data.get("auth_type", "none"),
            auth_config=data.get("auth_config"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/tools/servers/{server_id}")
async def get_tool_server(server_id: str):
    manager = _require(_managers.tool_servers, "ToolServer")
    server = await manager.get(server_id)
    if server is None:
        raise HTTPException(404, f"Tool server {server_id} not found")
    return server


@router.put("/tools/servers/{server_id}")
async def update_tool_server(server_id: str, data: dict[str, Any]):
    manager = _require(_managers.tool_servers, "ToolServer")
    server = await manager.update(server_id, data)
    if server is None:
        raise HTTPException(404, f"Tool server {server_id} not found")
    return server


@router.put("/tools/servers/{server_id}/status")
async def set_tool_server_status(server_id: str, data: dict[str, Any]):
    manager = _require(_managers.tool_servers, "ToolServer")
    try:
        server = await manager.set_status(server_id, data.get("status", ""))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if server is None:
        raise HTTPException(404, f"Tool server {server_id} not found")
    return server


@router.post("/tools/servers/{server_id}/sync")
async def sync_tool_server(server_id: str):
    manager = _require(_managers.tool_servers, "ToolServer")
    try:
        if not hasattr(manager, "sync_tools"):
            raise HTTPException(501, "Sync feature not implemented by manager")
        tools = await manager.sync_tools(server_id)
        return {"status": "synced", "tools_discovered": len(tools), "tools": tools}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Sync failed: {exc}") from exc


@router.delete("/tools/servers/{server_id}")
async def delete_tool_server(server_id: str):
    manager = _require(_managers.tool_servers, "ToolServer")
    if not await manager.delete(server_id):
        raise HTTPException(404, f"Tool server {server_id} not found")
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════
# SKILLS EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/skills/{skill_id}/execute", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def execute_skill(skill_id: str, data: dict[str, Any]):
    """Execute a Core skill through the SkillManager (not a stub)."""
    from core.skills.types import SkillContext

    manager = _require(_managers.skills, "Skill")
    skill = manager.get_skill(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} not found")

    context = SkillContext(
        skill_id=skill_id,
        user_id=data.get("user_id", "anonymous"),
        session_id=data.get("session_id", "default"),
        parameters=data.get("parameters", {}),
        constraints=data.get("constraints", {}),
        metadata=data.get("metadata", {}),
        max_cost=data.get("max_cost"),
        max_duration_ms=data.get("max_duration_ms"),
    )
    result = await manager.execute(context)
    return {
        "skill_id": result.skill_id,
        "status": result.status.value,
        "error": result.error,
        "steps_completed": result.steps_completed,
        "steps_total": result.steps_total,
        "duration_ms": result.duration_ms,
        "output": result.output,
        "metadata": result.metadata,
    }


# ═══════════════════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/prompts")
async def list_prompts():
    manager = _require(_managers.prompts, "Prompt")
    return await manager.list()


@router.post("/prompts", dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_prompt(data: dict[str, Any]):
    manager = _require(_managers.prompts, "Prompt")
    try:
        return await manager.create(
            name=data.get("name", ""),
            text=data.get("text", ""),
            description=data.get("description", ""),
            tags=data.get("tags"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    manager = _require(_managers.prompts, "Prompt")
    prompt = await manager.get(prompt_id)
    if prompt is None:
        raise HTTPException(404, f"Prompt {prompt_id} not found")
    return prompt


@router.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, data: dict[str, Any]):
    manager = _require(_managers.prompts, "Prompt")
    prompt = await manager.update(prompt_id, data)
    if prompt is None:
        raise HTTPException(404, f"Prompt {prompt_id} not found")
    return prompt


@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    manager = _require(_managers.prompts, "Prompt")
    if not await manager.delete(prompt_id):
        raise HTTPException(404, f"Prompt {prompt_id} not found")
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════
# SCIM / LDAP / OAuth — fournisseurs d'identité (Core-owned)
# ═══════════════════════════════════════════════════════════════════════════
#
# Politique secrets : AUCUN secret (bearer_token, bind_password, client_secret)
# ne transite dans une réponse GET. La lecture expose uniquement un booléen
# `<champ>_set`. À l'écriture, un champ sensible laissé vide préserve la
# valeur existante (l'admin peut modifier la configuration sans ressaisir le
# secret). Les secrets restent dans le CoreRecordStore du Core.


def _redact(config: dict[str, Any] | None, secret_field: str) -> dict[str, Any]:
    """Return a copy of a provider config with the secret field redacted."""
    if not config:
        return {}
    redacted = dict(config)
    redacted.pop(secret_field, None)
    redacted[f"{secret_field}_set"] = bool(config.get(secret_field))
    return redacted


@router.get("/scim/config")
async def get_scim_config():
    manager = _require(_managers.scim, "SCIM")
    return _redact(await manager.get_config(), "bearer_token")


@router.post("/scim/config", dependencies=[Depends(require_permission(Permission.WRITE))])
async def configure_scim(data: dict[str, Any]):
    manager = _require(_managers.scim, "SCIM")
    existing = await manager.get_config() or {}
    # Secret write-only : vide => on conserve la valeur actuelle du Core.
    bearer_token = data.get("bearer_token") or existing.get("bearer_token", "")
    try:
        config = await manager.configure(
            enabled=bool(data.get("enabled", False)),
            base_url=data.get("base_url", ""),
            bearer_token=bearer_token,
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _redact(config, "bearer_token")


@router.get("/scim/status")
async def get_scim_status():
    manager = _require(_managers.scim, "SCIM")
    return {"enabled": await manager.is_enabled()}


# ── LDAP ─────────────────────────────────────────────────────────────────────

@router.get("/ldap/config")
async def get_ldap_config():
    manager = _require(_managers.ldap, "LDAP")
    return _redact(await manager.get_config(), "bind_password")


@router.post("/ldap/config", dependencies=[Depends(require_permission(Permission.WRITE))])
async def configure_ldap(data: dict[str, Any]):
    manager = _require(_managers.ldap, "LDAP")
    existing = await manager.get_config() or {}
    bind_password = data.get("bind_password") or existing.get("bind_password", "")
    try:
        config = await manager.configure(
            server_url=data.get("server_url", ""),
            bind_dn=data.get("bind_dn", ""),
            bind_password=bind_password,
            user_search_base=data.get("user_search_base", ""),
            user_search_filter=data.get("user_search_filter", "(uid={username})"),
            tls_enabled=bool(data.get("tls_enabled", False)),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _redact(config, "bind_password")


@router.get("/ldap/status")
async def get_ldap_status():
    manager = _require(_managers.ldap, "LDAP")
    return {"enabled": await manager.is_enabled()}


# ── OAuth ────────────────────────────────────────────────────────────────────

@router.get("/oauth/providers")
async def list_oauth_providers():
    manager = _require(_managers.oauth, "OAuth")
    providers = await manager.list_providers()
    return [_redact(p, "client_secret") for p in providers or []]


@router.post("/oauth/providers", dependencies=[Depends(require_permission(Permission.WRITE))])
async def register_oauth_provider(data: dict[str, Any]):
    manager = _require(_managers.oauth, "OAuth")
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(422, "OAuth provider name is required")
    try:
        provider = await manager.register_provider(
            name=name,
            client_id=data.get("client_id", ""),
            client_secret=data.get("client_secret", ""),
            authorize_url=data.get("authorize_url", ""),
            token_url=data.get("token_url", ""),
            userinfo_url=data.get("userinfo_url", ""),
            scopes=data.get("scopes"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _redact(provider, "client_secret")


@router.post("/oauth/providers/{name}/disable", dependencies=[Depends(require_permission(Permission.WRITE))])
async def disable_oauth_provider(name: str):
    manager = _require(_managers.oauth, "OAuth")
    provider = await manager.disable_provider(name)
    if provider is None:
        raise HTTPException(404, f"OAuth provider {name} not found")
    return _redact(provider, "client_secret")
