from __future__ import annotations

import asyncio
from unittest.mock import MagicMock
from uuid import uuid4

from core.knowledge.manager import KnowledgeManager
from core.skills.store import SkillStore
from core.state.record_store import CoreRecordStore


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_knowledge_manager_records_create_update_delete() -> None:
    integration = MagicMock()
    store = CoreRecordStore()
    manager = KnowledgeManager(store=store, engineering_memory_integration=integration)

    node = _run(manager.create("test node", source="unit"))
    _run(manager.update(node.id, {"content": "changed"}))
    _run(manager.delete(node.id))

    assert integration.record_knowledge_operation.call_count >= 1


def test_skill_store_records_create_and_delete() -> None:
    integration = MagicMock()
    store = CoreRecordStore()
    skills = SkillStore(store=store, engineering_memory_integration=integration)

    created = _run(skills.create_skill({"name": "test-skill"}))
    _run(skills.delete_skill(created["id"]))

    assert integration.record_skill_lifecycle.call_count >= 1
