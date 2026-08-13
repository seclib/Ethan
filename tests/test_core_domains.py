"""Contract tests for the Core-owned agent, mission, knowledge and RAG domains."""

from __future__ import annotations

import asyncio

from core.agents import AgentManager, AgentStatus
from core.knowledge import KnowledgeManager
from core.missions import MissionManager, MissionStatus, StepStatus
from core.rag import RAGPipeline
from core.state import CoreRecordStore


def test_agent_definition_lifecycle_and_execution_are_core_owned():
    async def executor(**kwargs):
        return {"handled": kwargs["task"], "memory_scope": kwargs["agent"].memory_scope}

    async def scenario():
        manager = AgentManager(executor=executor)
        agent = await manager.create(
            "researcher",
            capabilities=["research"],
            memory_scope="project:ethan",
            skill_ids=["web-search"],
        )
        assert agent.status == AgentStatus.IDLE

        execution = await manager.execute(agent.id, "find the domain boundary", skill_id="web-search")
        assert execution.status.value == "completed"
        assert execution.result["memory_scope"] == "project:ethan"
        assert (await manager.get(agent.id)).status == AgentStatus.IDLE
        assert [item.id for item in await manager.list_executions(agent.id)] == [execution.id]

    asyncio.run(scenario())


def test_mission_verification_requires_approval_and_persists_progress():
    async def scenario():
        manager = MissionManager()
        mission = await manager.create("Refactor API", steps=[{"title": "Move CRUD"}])
        step = mission.steps[0]

        await manager.verify_step(mission.id, step.id)
        awaiting_approval = await manager.get(mission.id)
        assert awaiting_approval.steps[0].status == StepStatus.WAITING_APPROVAL
        assert awaiting_approval.steps_completed == 0

        await manager.approve_step(mission.id, step.id)
        completed = await manager.get(mission.id)
        assert completed.status == MissionStatus.COMPLETED
        assert completed.steps_completed == 1
        assert completed.to_dict()["steps"][0]["completed_at"] is not None

    asyncio.run(scenario())


def test_knowledge_relations_and_rag_access_share_core_contracts():
    async def scenario():
        knowledge = KnowledgeManager()
        first = await knowledge.create("ETHAN", content="ETHAN is a headless intelligent runtime.")
        second = await knowledge.create("Interfaces", content="Interfaces reveal ETHAN capabilities.")
        connected = await knowledge.connect(first.id, second.id, "revealed_by", strength=0.9)
        assert connected.connections[0].to_node_id == second.id
        assert (await knowledge.search("headless"))[0].id == first.id

        rag = RAGPipeline()
        document_id = await knowledge.ingest_into_rag(first.id, rag)
        document = await rag.get_document(document_id)
        assert document is not None
        assert document.metadata["knowledge_id"] == first.id

    asyncio.run(scenario())


def test_rag_pipeline_restores_documents_from_its_core_store():
    async def scenario():
        store = CoreRecordStore()
        first_pipeline = RAGPipeline(store=store)
        document = await first_pipeline.ingest(
            "The Core owns RAG retrieval and builds context for the LLM.",
            title="Architecture",
        )

        restarted_pipeline = RAGPipeline(store=store)
        restored = await restarted_pipeline.get_document(document.id)
        assert restored is not None
        context = await restarted_pipeline.build_context("RAG context")
        assert "Architecture" in context

    asyncio.run(scenario())
