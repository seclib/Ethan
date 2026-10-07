from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from core.cti import CTIError, CTIManager
from core.state import CoreRecordStore


class RecordingBus:
    def __init__(self):
        self.published = []

    async def publish(self, subject, event):
        self.published.append((subject, event))


def _stix_id(object_type: str) -> str:
    return f"{object_type}--{uuid4()}"


def test_manifest_declares_tools_route_and_stix_version():
    manifest = CTIManager.manifest()

    assert manifest["id"] == "ethan-cti"
    assert manifest["route"] == "/tools/cti"
    assert manifest["model"] == "STIX 2.1"


def test_create_and_list_stix_object_is_persisted_and_emits_core_event():
    bus = RecordingBus()
    manager = CTIManager(CoreRecordStore(), event_bus=bus)
    indicator_id = _stix_id("indicator")

    record = asyncio.run(
        manager.create_object(
            "alice",
            {
                "type": "indicator",
                "id": indicator_id,
                "spec_version": "2.1",
                "name": "Example indicator",
            },
        )
    )

    assert record["owner_id"] == "alice"
    assert record["stix_object"]["spec_version"] == "2.1"
    assert asyncio.run(manager.get_object("alice", indicator_id)) == record
    assert asyncio.run(manager.get_object("bob", indicator_id)) is None
    assert bus.published[0][0] == "ethan.cti.object.created"
    assert bus.published[0][1].payload["object_id"] == indicator_id


def test_create_generates_id_and_rejects_duplicate_for_same_owner():
    manager = CTIManager(CoreRecordStore())
    record = asyncio.run(manager.create_object("alice", {"type": "malware", "name": "Sample"}))

    assert record["stix_object"]["id"].startswith("malware--")
    with pytest.raises(CTIError, match="already exists"):
        asyncio.run(manager.create_object("alice", record["stix_object"]))


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "indicator", "id": "malware--not-a-uuid"},
        {"type": "indicator", "id": f"indicator--{uuid4()}", "spec_version": "2.0"},
        {"type": "relationship", "relationship_type": "uses"},
    ],
)
def test_invalid_stix_object_is_rejected(payload):
    manager = CTIManager(CoreRecordStore())
    with pytest.raises(CTIError):
        asyncio.run(manager.create_object("alice", payload))


def test_relationship_requires_references_owned_by_same_user():
    manager = CTIManager(CoreRecordStore())
    with pytest.raises(CTIError, match="not available"):
        asyncio.run(
            manager.create_object(
                "alice",
                {
                    "type": "relationship",
                    "relationship_type": "uses",
                    "source_ref": _stix_id("threat-actor"),
                    "target_ref": _stix_id("malware"),
                },
            )
        )


def test_list_is_user_scoped():
    manager = CTIManager(CoreRecordStore())
    asyncio.run(manager.create_object("alice", {"type": "malware", "name": "A"}))
    asyncio.run(manager.create_object("bob", {"type": "malware", "name": "B"}))

    assert [item["owner_id"] for item in asyncio.run(manager.list_objects("alice"))] == ["alice"]
