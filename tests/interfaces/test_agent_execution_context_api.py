import interfaces.api.auth as auth
import pytest
from fastapi.testclient import TestClient
from interfaces.api.main import app
from interfaces.api.routers import v1
from core.state.record_store import CoreRecordStore
from core.agents.manager import AgentManager


@pytest.fixture
def in_memory_domains(monkeypatch):
    from interfaces.api.routers.v1 import CoreDomainServices

    manager = AgentManager(store=CoreRecordStore())
    services = CoreDomainServices(agents=manager)
    monkeypatch.setattr(v1, "_domains", services)
    return services, manager


@pytest.fixture
def captured_executor(in_memory_domains):
    services, manager = in_memory_domains
    captured = {}

    async def executor(*, agent, task, context, skill_id, execution_context):
        captured["execution_context"] = execution_context
        captured["skill_id"] = skill_id
        captured["context"] = context
        return "done"

    import asyncio

    asyncio.run(manager.set_executor(executor))
    return captured


@pytest.fixture
def admin_token(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["admin"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)

    async def _verify(token):
        return {"sub": "alice", "role": "admin", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    return auth.create_access_token({"sub": "alice", "role": "admin"})


async def _create_agent(manager):
    return await manager.create(name="agent-ctx")


def test_agent_execution_context_propagates(admin_token, captured_executor, in_memory_domains):
    client = TestClient(app)
    services, manager = in_memory_domains

    import asyncio

    agent = asyncio.run(_create_agent(manager))
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(
        f"/v1/agents/{agent.id}/execute",
        json={"task": "hello", "context": {"x": 1}, "skill_id": None},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    captured = captured_executor
    assert captured["execution_context"] is not None
    assert captured["execution_context"].principal.subject_id == "alice"


def test_agent_execution_forbidden_for_unauthorized_user(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["user"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)

    async def _verify(token):
        return {"sub": "bob", "role": "user", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    token = auth.create_access_token({"sub": "bob", "role": "user"})
    client = TestClient(app)
    response = client.post("/v1/agents/any/execute", json={"task": "hello"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (403, 404)
