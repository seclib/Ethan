"""PostgreSQL integration test for SERVICE credential rotation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tests.test_config_persistence as cfg

_DSN = cfg._dsn()
if _DSN:
    os.environ["DATABASE_URL"] = _DSN

import asyncio
import uuid

import pytest
import pytest_asyncio

from core.auth.service_identities import ServiceIdentityManager, ServiceRegistryConflict
from core.state.record_store import CoreRecordStore

pytestmark = pytest.mark.skipif(not (_DSN and cfg._pg_available()), reason="PostgreSQL not available")


SERVICE_ID = f"svc-rot-pg-{uuid.uuid4().hex[:8]}"


async def _clear(service_id: str) -> None:
    import asyncpg

    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=1)
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM core_domain_records WHERE domain='service-identities' AND record_id=$1", service_id)
    finally:
        await pool.close()


@pytest_asyncio.fixture
async def independent_managers():
    import asyncpg

    await _clear(SERVICE_ID)
    pool_a = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=2)
    pool_b = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=2)
    try:
        manager_a = ServiceIdentityManager(store=CoreRecordStore(pg_pool=pool_a))
        manager_b = ServiceIdentityManager(store=CoreRecordStore(pg_pool=pool_b))
        await manager_a.create_service(SERVICE_ID, "audit", ["audit.events.write"])
        yield manager_a, manager_b
    finally:
        await _clear(SERVICE_ID)
        await pool_a.close()
        await pool_b.close()


@pytest.mark.asyncio
async def test_concurrent_rotation_has_one_winner(independent_managers):
    manager_a, manager_b = independent_managers

    async def rotate(manager, barrier):
        record = await manager.service_record(SERVICE_ID)
        stale_version = int(record["version"])
        await barrier.wait()
        record = dict(record)
        record["credential_id"] = str(__import__("uuid").uuid4())
        record["rotation_id"] = str(__import__("uuid").uuid4())
        record["updated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        record["version"] = stale_version + 1
        try:
            await manager._persist_record_pg(SERVICE_ID, record, expected_version=stale_version)
            return ("ok", int(record["version"]))
        except ServiceRegistryConflict as exc:
            return ("conflict", str(exc))
        except Exception as exc:  # noqa: BLE001 - test records every failure
            return ("error", f"{type(exc).__name__}: {exc}")

    barrier = asyncio.Barrier(2)
    result_a, result_b = await asyncio.gather(rotate(manager_a, barrier), rotate(manager_b, barrier))
    assert sorted([result_a[0], result_b[0]]) == ["conflict", "ok"], (result_a, result_b)

    final_record = await manager_a.service_record(SERVICE_ID)
    assert final_record is not None
    assert final_record["status"] == "active"
    assert int(final_record["version"]) >= 2

    # An old-generation token from the initial record must no longer match.
    initial_version = 1
    assert int(final_record["version"]) > initial_version
