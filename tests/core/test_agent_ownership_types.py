"""Tests for Agent ownership fields introduced by AGENT-AUTHZ-1."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.agents.types import Agent, AgentStatus, AgentType

pytest.importorskip("pytest")


def test_new_agent_defaults_to_user_ownership():
    agent = Agent(id="a-1", name="Agent")
    assert agent.owner_id is None
    assert agent.created_by is None
    assert agent.agent_type == AgentType.USER


def test_old_record_without_ownership_loads_proportionately():
    data = {
        "id": "legacy-1",
        "name": "Legacy",
        "status": "idle",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    agent = Agent.from_dict(data)

    assert agent.owner_id is None
    assert agent.created_by is None
    assert agent.agent_type == AgentType.USER
    assert agent.id == "legacy-1"


@pytest.mark.parametrize(
    "agent_type,expected",
    [
        ("system", AgentType.SYSTEM),
        ("internal", AgentType.INTERNAL),
        ("user", AgentType.USER),
    ],
)
def test_agent_type_is_deserialized(agent_type, expected):
    data = {
        "id": f"agent-{agent_type}",
        "name": f"Agent {agent_type}",
        "agent_type": agent_type,
    }
    agent = Agent.from_dict(data)
    assert agent.agent_type == expected
    assert Agent.from_dict(agent.to_dict()).agent_type == expected


def test_roundtrip_preserves_existing_and_new_fields():
    agent = Agent(
        id="agent-1",
        name="Ownership",
        capabilities=["read"],
        tool_ids=["tool-1"],
        owner_id="user-alice",
        created_by="user-bob",
        agent_type=AgentType.SYSTEM,
        metadata={"source": "existing"},
    )

    restored = Agent.from_dict(agent.to_dict())

    assert restored.id == agent.id
    assert restored.name == agent.name
    assert restored.owner_id == agent.owner_id
    assert restored.created_by == agent.created_by
    assert restored.agent_type == agent.agent_type
    assert restored.capabilities == agent.capabilities
    assert restored.tool_ids == agent.tool_ids
    assert restored.metadata == agent.metadata


def test_missing_fields_are_deterministic():
    agent = Agent.from_dict({"id": "minimal", "name": "Minimal"})
    assert agent.owner_id is None
    assert agent.created_by is None
    assert agent.agent_type == AgentType.USER
    assert agent.created_at is not None
    assert agent.updated_at is not None


def test_system_agent_preserves_type():
    agent = Agent(id="sys-1", name="System", agent_type=AgentType.SYSTEM)
    restored = Agent.from_dict(agent.to_dict())
    assert restored.agent_type == AgentType.SYSTEM
    assert restored.owner_id is None


def test_invalid_agent_type_raises_deterministic_error():
    data = {"id": "bad", "name": "Bad", "agent_type": "invalid"}
    with pytest.raises(ValueError):
        Agent.from_dict(data)


def test_to_dict_includes_ownership_fields():
    agent = Agent(id="x", name="x", owner_id="u", created_by="c")
    serialized = agent.to_dict()
    assert serialized["owner_id"] == "u"
    assert serialized["created_by"] == "c"
    assert serialized["agent_type"] == "user"
    assert "status" in serialized
