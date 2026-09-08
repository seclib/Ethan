"""Tests API — phases Skills (P0→P3) : filtres, validation tools 422,
gate is_active sur /run, export/import, valves, lab 503 sans Docker.

Les routes v1 sont appelées directement (pattern du repo) ; le SkillStore
et le ToolManager sont réels/injectés.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from routers import v1
from core.skills.lab import SkillLab
from core.skills.store import SkillStore


class _FakeTool:
    def __init__(self, tool_id: str) -> None:
        self.tool_id = tool_id


class _FakeToolManager:
    def list_tools(self):
        return [_FakeTool("web_search"), _FakeTool("writer")]


def test_create_skill_unknown_tool_422():
    async def scenario():
        v1.set_skill_store(SkillStore())
        v1.set_tool_manager(_FakeToolManager())
        try:
            with pytest.raises(HTTPException) as exc:
                await v1.create_skill(
                    {
                        "name": "bad",
                        "kind": "pipeline",
                        "required_tools": ["web_search", "ghost"],
                    }
                )
            assert exc.value.status_code == 422
            assert "ghost" in exc.value.detail
        finally:
            v1.set_tool_manager(None)

    asyncio.run(scenario())


def test_create_skill_valid_tools_ok():
    async def scenario():
        store = SkillStore()
        v1.set_skill_store(store)
        v1.set_tool_manager(_FakeToolManager())
        try:
            skill = await v1.create_skill(
                {
                    "name": "good",
                    "kind": "pipeline",
                    "steps": [{"id": "s1", "name": "S", "tool_id": "writer"}],
                    "required_tools": ["writer"],
                }
            )
            assert skill["kind"] == "pipeline"
            assert skill["required_tools"] == ["writer"]
        finally:
            v1.set_tool_manager(None)

    asyncio.run(scenario())


def test_create_skill_invalid_kind_422():
    async def scenario():
        v1.set_skill_store(SkillStore())
        with pytest.raises(HTTPException) as exc:
            await v1.create_skill({"name": "x", "kind": "magic"})
        assert exc.value.status_code == 422

    asyncio.run(scenario())


def test_update_skill_validates_tools():
    async def scenario():
        store = SkillStore()
        v1.set_skill_store(store)
        v1.set_tool_manager(_FakeToolManager())
        try:
            skill = await store.create_skill({"name": "u", "kind": "prompt"})
            with pytest.raises(HTTPException) as exc:
                await v1.update_skill(skill["id"], {"required_tools": ["unknown_tool"]})
            assert exc.value.status_code == 422
        finally:
            v1.set_tool_manager(None)

    asyncio.run(scenario())


def test_run_inactive_skill_409():
    async def scenario():
        v1.set_skill_store(SkillStore())
        skill = await v1.create_skill({"name": "off", "content": "instructions"})
        await v1.toggle_skill(skill["id"])
        with pytest.raises(HTTPException) as exc:
            await v1.run_skill(skill["id"], {"input": "go"})
        assert exc.value.status_code == 409

    asyncio.run(scenario())

def test_list_filters():
    async def scenario():
        v1.set_skill_store(SkillStore())
        await v1.create_skill({"name": "prompt-skill", "kind": "prompt", "content": "c"})
        pipeline = await v1.create_skill(
            {
                "name": "pipe-skill",
                "kind": "pipeline",
                "steps": [{"id": "s", "name": "S", "tool_id": "t"}],
            }
        )
        await v1.toggle_skill(pipeline["id"])  # → inactive

        assert {s["name"] for s in await v1.list_skills()} == {"prompt-skill", "pipe-skill"}
        assert [s["name"] for s in await v1.list_skills(kind="prompt")] == ["prompt-skill"]
        assert [s["name"] for s in await v1.list_skills(kind="pipeline", active=False)] == [
            "pipe-skill"
        ]

    asyncio.run(scenario())


def test_export_import_roundtrip():
    async def scenario():
        v1.set_skill_store(SkillStore())
        await v1.create_skill({"name": "exp-a", "content": "A"})
        await v1.create_skill({"name": "exp-b", "content": "B", "tags": ["t"]})

        exported = await v1.export_skills()
        assert len(exported) == 2

        fresh = SkillStore()
        v1.set_skill_store(fresh)
        summary = await v1.import_skills({"skills": exported})
        assert summary == {"imported": 2, "skipped": 0}
        assert {s["name"] for s in await fresh.list_skills()} == {"exp-a", "exp-b"}

        with pytest.raises(HTTPException) as exc:
            await v1.import_skills({"skills": "not-a-list"})
        assert exc.value.status_code == 422

    asyncio.run(scenario())


def test_valves_get_put():
    async def scenario():
        v1.set_skill_store(SkillStore())
        skill = await v1.create_skill({"name": "valved", "content": "x"})
        valves = await v1.update_skill_valves(skill["id"], {"valves": {"depth": 3}})
        assert valves == {"depth": 3}
        assert await v1.get_skill_valves(skill["id"]) == {"depth": 3}
        with pytest.raises(HTTPException) as exc:
            await v1.update_skill_valves(skill["id"], {"valves": ["nope"]})
        assert exc.value.status_code == 422
        with pytest.raises(HTTPException) as exc:
            await v1.get_skill_valves("missing-id")
        assert exc.value.status_code == 404

    asyncio.run(scenario())


def test_lab_test_503_without_docker():
    async def scenario():
        v1.set_skill_store(SkillStore())
        v1._skill_lab = SkillLab(docker_client=None)
        with pytest.raises(HTTPException) as exc:
            await v1.skill_lab_test({"code": "print('x')"})
        assert exc.value.status_code == 503
        v1._skill_lab = None

    asyncio.run(scenario())


def test_lab_test_422_without_code():
    async def scenario():
        v1.set_skill_store(SkillStore())
        # client factice (non-None) → sandbox "disponible" → validation du corps
        v1._skill_lab = SkillLab(docker_client=object())
        with pytest.raises(HTTPException) as exc:
            await v1.skill_lab_test({"name": "no-code"})
        assert exc.value.status_code == 422
        v1._skill_lab = None

    asyncio.run(scenario())

