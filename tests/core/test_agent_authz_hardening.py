"""Tests for fail-closed Agent ownership and authorization (AGENT-AUTHZ-2.1)."""

from __future__ import annotations

import pytest
import pytest_asyncio
from core.state import CoreRecordStore
from interfaces.api.routers import v1
from starlette.requests import Request
from fastapi import HTTPException


def _request(user: str, role: str = "standard"):
    req = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "client": ("test", 1),
        }
    )
    req.state.user = user
    req.state.token_payload = {"sub": user, "role": role}
    return req


@pytest_asyncio.fixture
async def fixture():
    from core.folders import FolderManager
    from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
    from core.rag import RAGPipeline
    from core.agents import AgentManager

    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    knowledge = KnowledgeManager(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    folders = FolderManager(store=store, knowledge=knowledge, collections=collections)
    mgr = AgentManager(store=store)
    v1.set_core_domain_services(v1.CoreDomainServices(agents=mgr, knowledge=knowledge))
    v1.set_knowledge_collections(collections)
    from interfaces.api.routers.folders import set_folder_manager

    set_folder_manager(folders)
    return store, mgr


async def _agent(mgr, owner, **kwargs):
    return await mgr.create(name="Test Agent", owner_id=owner, **kwargs)


@pytest.mark.asyncio
async def test_unauthenticated_get_refused(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, "alice", agent_type="user")
    req = _request("nobody")
    req.state.user = None
    req.state.token_payload = {}
    with pytest.raises(HTTPException) as exc:
        await v1.get_agent(agent.id, request=req)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_non_owner_read_denied(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, "alice")
    with pytest.raises(HTTPException) as exc:
        await v1.get_agent(agent.id, request=_request("bob"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_owner_read_allowed(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, "alice")
    result = await v1.get_agent(agent.id, request=_request("alice"))
    assert result["id"] == agent.id
    assert result["owner_id"] == "alice"


@pytest.mark.asyncio
async def test_admin_with_permission_can_read(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, "alice")
    result = await v1.get_agent(agent.id, request=_request("admin", role="admin"))
    assert result["id"] == agent.id


@pytest.mark.asyncio
async def test_owner_less_agent_denied_to_standard_user(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, None)
    with pytest.raises(HTTPException) as exc:
        await v1.get_agent(agent.id, request=_request("alice"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_system_agent_protected_from_ordinary_user(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, None, agent_type="system")
    with pytest.raises(HTTPException) as exc:
        await v1.get_agent(agent.id, request=_request("alice"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_sensitive_update_denied_with_request(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, "alice")
    with pytest.raises(HTTPException) as exc:
        await v1.update_agent(agent.id, {"tool_ids": ["tool"]}, request=_request("alice"))
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_descriptive_update_allowed_with_authenticated_request(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, "alice")
    updated = await v1.update_agent(
        agent.id, {"description": "updated"}, request=_request("alice")
    )
    assert updated["description"] == "updated"


@pytest.mark.asyncio
async def test_deletion_requires_admin(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, "alice")
    with pytest.raises(HTTPException) as exc:
        await v1.delete_agent(agent.id, request=_request("alice"))
    assert exc.value.status_code in (403, 401)
    result = await v1.delete_agent(agent.id, request=_request("admin", role="admin"))
    assert result["status"] == "deleted"


@pytest.mark.asyncio
async def test_create_sets_owner_from_authenticated_principal(fixture):
    store, mgr = fixture
    agent = await v1.create_agent({"name": "Owned"}, request=_request("alice"))
    assert agent["owner_id"] == "alice"
    assert agent["created_by"] == "alice"
    assert agent["agent_type"] == "user"


@pytest.mark.asyncio
async def test_non_admin_cannot_list_resources_of_foreign_agent(fixture):
    store, mgr = fixture
    agent = await _agent(mgr, "alice")
    with pytest.raises(HTTPException) as exc:
        await v1.get_agent_resources(agent.id, request=_request("bob"))
    assert exc.value.status_code == 403
