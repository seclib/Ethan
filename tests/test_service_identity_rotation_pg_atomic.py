"""PostgreSQL atomicity tests for SERVICE credential rotation."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tests.test_config_persistence as cfg

_DSN = cfg._dsn()
if _DSN:
    os.environ["DATABASE_URL"] = _DSN

import asyncio

import pytest
import pytest_asyncio

from core.auth.service_identities import ServiceIdentityManager
from core.state.record_store import CoreRecordStore

pytestmark = pytest.mark.skipif(not (_DSN and cfg._pg_available()), reason="PostgreSQL not available")


async def _clean(service_id: str) -> None:
    import asyncpg

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=1)
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM core_domain_records WHERE domain='service-identities' AND record_id=$1", service_id)
            await conn.execute("DELETE FROM core_domain_records WHERE domain='service-admin-operations' AND record_id LIKE 'admin-operation:%'")
    finally:
        await pool.close()


async def _setup(service_id: str):
    import asyncpg

    pool_a = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=2, max_size=3)
    pool_b = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=2, max_size=3)
    store_a = CoreRecordStore(pg_pool=pool_a)
    store_b = CoreRecordStore(pg_pool=pool_b)
    a = ServiceIdentityManager(store=store_a)
    b = ServiceIdentityManager(store=store_b)
    await a.create_service(service_id, "audit", ["audit.events.write"])
    return a, b, pool_a, pool_b


@pytest_asyncio.fixture
async def managers():
    service_id = f"svc-rot-atomic-{uuid.uuid4().hex[:8]}"
    await _clean(service_id)
    a, b, pool_a, pool_b = await _setup(service_id)
    yield service_id, a, b, pool_a, pool_b
    async with pool_a.acquire() as conn:
        await conn.execute("DELETE FROM core_domain_records WHERE domain IN ('service-identities','service-admin-operations') AND record_id IN ($1) OR record_id LIKE 'admin-operation:%'", service_id)
    await pool_a.close()
    await pool_b.close()


@pytest.mark.asyncio
async def test_same_key_concurrency_atomic(managers):
    service_id, a, b, _, _ = managers
    started = asyncio.Barrier(2)

    async def run(manager):
        await started.wait()
        try:
            rec = await manager.rotate_credential(service_id, request_key="same-key")
            return "ok", int(rec["version"]) if isinstance(rec, dict) else 0
        except Exception as exc:  # noqa: BLE001
            return "exc", type(exc).__name__

    (r1), (r2) = await asyncio.gather(run(a), run(b))
    assert sorted([r1[0], r2[0]]) == ["ok", "ok"]  # one physical rotation plus one idempotent winner
    assert r1[1] == r2[1]
    final = await a.service_record(service_id)
    assert isinstance(final, dict)
    assert final["version"] == 2  # exactly one rotation despite two concurrent requests
    assert final["status"] == "active"


@pytest.mark.asyncio
async def test_distinct_keys_two_managers(managers):
    service_id, a, b, _, _ = managers
    r1 = await a.rotate_credential(service_id, request_key="key-one")
    r2 = await b.rotate_credential(service_id, request_key="key-two")
    assert isinstance(r1, dict)
    assert isinstance(r2, dict)
    assert r1["rotation_id"] != r2["rotation_id"]
    assert int(r2["version"]) > int(r1["version"])


@pytest.mark.asyncio
async def test_replay_preserves_original_generation(managers):
    service_id, a, b, _, _ = managers
    first = await a.rotate_credential(service_id, request_key="recover-key")
    await b.rotate_credential(service_id, request_key="other-key")
    replay = await a.rotate_credential(service_id, request_key="recover-key")
    assert replay["credential_id"] == first["credential_id"]
    assert replay["rotation_id"] == first["rotation_id"]


@pytest.mark.asyncio
async def test_replay_preserves_original_after_commit():
    service_id = f"svc-commit-{uuid.uuid4().hex[:8]}"
    await _clean(service_id)
    import asyncpg

    pool_a = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=1)
    try:
        a = ServiceIdentityManager(store=CoreRecordStore(pg_pool=pool_a))
        b = ServiceIdentityManager(store=CoreRecordStore(pg_pool=pool_a))
        await a.create_service(service_id, "audit", ["audit.events.write"])
        key = "commit-key"
        first = await a.rotate_credential(service_id, request_key=key)
        after_first_version = (await a.service_record(service_id))["version"]
        replay = await b.rotate_credential(service_id, request_key=key)
        assert replay["credential_id"] == first["credential_id"]
        assert replay["rotation_id"] == first["rotation_id"]
        assert replay["version"] == first["version"]
        final = await b.service_record(service_id)
        assert final["version"] == after_first_version
        assert final["credential_id"] == first["credential_id"]
    finally:
        await _clean(service_id)
        await pool_a.close()


@pytest.mark.asyncio
async def test_pending_operation_blocks_rotation():
    service_id = f"svc-pending-{uuid.uuid4().hex[:8]}"
    await _clean(service_id)
    import asyncpg

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=1)
    try:
        manager = ServiceIdentityManager(store=CoreRecordStore(pg_pool=pool))
        await manager.create_service(service_id, "audit", ["audit.events.write"])
        service_record = await manager.service_record(service_id)
        original_credential = service_record["credential_id"]
        original_rotation = service_record["rotation_id"]
        original_version = service_record["version"]

        key = "pending-key"
        operation_id = ServiceIdentityManager._admin_operation_id(service_id, "rotate_credential", key)
        pending_record = {
            "operation_id": operation_id,
            "service_id": service_id,
            "operation": "rotate_credential",
            "request_key": key,
            "status": "pending",
            "result": None,
            "version": 1,
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        await pool.execute(
            "INSERT INTO core_domain_records (domain, record_id, record, updated_at) VALUES ($1, $2, $3::jsonb, NOW())",
            "service-admin-operations",
            operation_id,
            __import__("json").dumps(pending_record),
        )

        result = await manager.rotate_credential(service_id, request_key=key)
        assert result is None

        after = await manager.service_record(service_id)
        assert after["credential_id"] == original_credential
        assert after["rotation_id"] == original_rotation
        assert after["version"] == original_version
    finally:
        await _clean(service_id)
        await pool.close()
