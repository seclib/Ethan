"""Tests Core — Skills unifiées (P0→P3 : fusion modèle, gate is_active,
validation tools, lab Docker obligatoire, valves, stats, import/export).

Le SkillStore est réel (CoreRecordStore en mémoire) ; aucun mock.
Pattern asyncio du repo : scénarios async exécutés via asyncio.run().
"""

from __future__ import annotations

import asyncio

import pytest

from core.skills.lab import LabStatus, SkillLab
from core.skills.store import SkillStore
from core.skills.validation import collect_unknown_tools


def test_create_pipeline_skill_persists_kind_steps_tools():
    async def scenario():
        store = SkillStore()
        skill = await store.create_skill(
            {
                "name": "recon-bundle",
                "description": "Pipeline de recon",
                "kind": "pipeline",
                "steps": [
                    {"id": "s1", "name": "Scan", "tool_id": "web_search", "parameters": {"q": "x"}},
                    {"id": "s2", "name": "Report", "tool_id": "writer", "depends_on": ["s1"]},
                ],
                "required_tools": ["web_search", "writer"],
            }
        )
        fetched = await store.get_skill(skill["id"])
        assert fetched["kind"] == "pipeline"
        assert [s["id"] for s in fetched["steps"]] == ["s1", "s2"]
        assert fetched["required_tools"] == ["web_search", "writer"]
        assert fetched["is_active"] is True

    asyncio.run(scenario())


def test_prompt_kind_defaults():
    async def scenario():
        store = SkillStore()
        skill = await store.create_skill({"name": "simple-prompt", "content": "Fais X."})
        assert skill["kind"] == "prompt"
        assert skill["steps"] == []
        assert skill["required_tools"] == []
        assert skill["total_executions"] == 0
        assert skill["is_active"] is True

    asyncio.run(scenario())


def test_create_invalid_kind_rejected():
    async def scenario():
        store = SkillStore()
        with pytest.raises(ValueError):
            await store.create_skill({"name": "x", "kind": "magic"})

    asyncio.run(scenario())


def test_toggle_and_list_filters():
    async def scenario():
        store = SkillStore()
        prompt = await store.create_skill({"name": "p1", "kind": "prompt"})
        await store.create_skill(
            {"name": "p2", "kind": "pipeline", "steps": [{"id": "s", "name": "S", "tool_id": "t"}]}
        )

        await store.toggle_skill(prompt["id"])  # → inactive

        assert {s["name"] for s in await store.list_skills()} == {"p1", "p2"}
        assert [s["name"] for s in await store.list_skills(active=True)] == ["p2"]
        assert [s["name"] for s in await store.list_skills(active=False)] == ["p1"]
        assert [s["name"] for s in await store.list_skills(kind="pipeline")] == ["p2"]
        assert [s["name"] for s in await store.list_skills(kind="prompt", active=False)] == ["p1"]

    asyncio.run(scenario())

def test_sync_builtin_skills_idempotent_preserves_active():
    async def scenario():
        from core.skills.builtin import iter_builtin_skill_specs

        store = SkillStore()
        specs = iter_builtin_skill_specs()
        assert len(specs) == 5

        first = await store.sync_builtin_skills(specs)
        assert first == 5

        email = await store.get_skill("email_reader")
        assert email["kind"] == "pipeline"
        assert email["is_builtin"] is True
        assert email["steps"], "steps doivent être sérialisés depuis le code"
        assert email["required_tools"], "required_tools dérivés des steps"

        # L'utilisateur désactive la builtin → un re-sync préserve son choix
        await store.toggle_skill("email_reader")
        await store.sync_builtin_skills(specs)
        again = await store.get_skill("email_reader")
        assert again["is_active"] is False
        # mais la définition technique reste à jour
        assert again["steps"] == email["steps"]

    asyncio.run(scenario())


def test_record_execution_stats():
    async def scenario():
        store = SkillStore()
        skill = await store.create_skill({"name": "s", "content": "x"})
        await store.record_execution(skill["id"], True)
        await store.record_execution(skill["id"], True)
        await store.record_execution(skill["id"], False)
        final = await store.get_skill(skill["id"])
        assert final["total_executions"] == 3
        assert final["success_count"] == 2
        assert final["last_run_at"] is not None

    asyncio.run(scenario())


def test_import_export_roundtrip():
    async def scenario():
        store = SkillStore()
        await store.create_skill({"name": "a", "content": "A", "kind": "prompt"})
        await store.create_skill(
            {
                "name": "b",
                "kind": "pipeline",
                "steps": [{"id": "s", "name": "S", "tool_id": "t"}],
                "required_tools": ["t"],
                "valves": {"depth": 2},
            }
        )
        exported = await store.export_skills()
        assert len(exported) == 2

        fresh = SkillStore()
        summary = await fresh.import_skills({"skills": exported})
        assert summary == {"imported": 2, "skipped": 0}

        imported = await fresh.list_skills()
        assert {s["name"] for s in imported} == {"a", "b"}
        # nouvelles ids (jamais d'écrasement silencieux)
        assert {s["id"] for s in imported}.isdisjoint({s["id"] for s in exported})
        b = next(s for s in imported if s["name"] == "b")
        assert b["valves"] == {"depth": 2}
        assert b["required_tools"] == ["t"]

    asyncio.run(scenario())


def test_import_skips_invalid_records():
    async def scenario():
        store = SkillStore()
        summary = await store.import_skills(
            {"skills": [{"description": "sans nom"}, "junk"]}
        )
        assert summary == {"imported": 0, "skipped": 2}

    asyncio.run(scenario())


def test_valves_update():
    async def scenario():
        store = SkillStore()
        skill = await store.create_skill({"name": "v", "content": "x"})
        await store.update_valves(skill["id"], {"temperature": 0.2})
        assert await store.get_valves(skill["id"]) == {"temperature": 0.2}
        with pytest.raises(ValueError):
            await store.update_valves(skill["id"], ["pas-un-dict"])

    asyncio.run(scenario())


def test_collect_unknown_tools():
    class _FakeTool:
        def __init__(self, tool_id: str) -> None:
            self.tool_id = tool_id

    class _FakeManager:
        def list_tools(self):
            return [_FakeTool("web_search"), _FakeTool("writer")]

    unknown = collect_unknown_tools(
        ["web_search", "ghost"], [{"tool_id": "phantom"}], _FakeManager()
    )
    assert unknown == ["ghost", "phantom"]
    # ToolManager non câblé → validation neutralisée (fail-open)
    assert collect_unknown_tools(["ghost"], [], None) == []


def test_lab_requires_docker_no_local_execution():
    async def scenario():
        lab = SkillLab(docker_client=None)
        result = await lab.test_skill("result = 'EXECUTED LOCALLY'", skill_name="pwn")
        assert result.status == LabStatus.ERROR
        assert result.passed is False
        assert "Docker" in result.error
        assert result.output == ""  # rien n'a été exécuté
        assert lab.docker_available is False
        assert len(lab.list_results()) == 1

    asyncio.run(scenario())

