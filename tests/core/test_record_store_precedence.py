"""Hiérarchie des sources de vérité de `CoreRecordStore` (audit §2).

PostgreSQL est la source durable ; la mémoire du process est le cache chaud ;
Redis n'est qu'un cache de lecture. Lire Redis avant PostgreSQL rendait
l'état persistant invisible pendant toute la durée du cache (300 s) : après un
redémarrage de l'API, une capability restait figée sur un état périmé.

Ces tests n'utilisent aucun service réel.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from core.state.record_store import CoreRecordStore


class FakePG:
    """Pool asyncpg minimaliste sur `core_domain_records`."""

    def __init__(self, rows: dict[tuple[str, str], str] | None = None) -> None:
        self.rows = rows or {}
        self.fail = False

    async def execute(self, query: str, *args: Any) -> str:
        sql = " ".join(query.split())
        if self.fail:
            raise RuntimeError("postgres indisponible")
        if "INSERT INTO core_domain_records" in sql:
            self.rows[(args[0], args[1])] = args[2]
            return "INSERT 0 1"
        if "DELETE FROM core_domain_records" in sql:
            return "DELETE 1" if self.rows.pop((args[0], args[1]), None) is not None else "DELETE 0"
        raise AssertionError("requête SQL inattendue: " + sql)

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        sql = " ".join(query.split())
        if "SELECT record FROM core_domain_records" in sql:
            payload = self.rows.get((args[0], args[1]))
            return None if payload is None else {"record": payload}
        raise AssertionError("requête SQL inattendue: " + sql)

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        sql = " ".join(query.split())
        if "SELECT record_id, record" in sql:
            return [
                {"record_id": rid, "record": payload}
                for (domain, rid), payload in list(self.rows.items())
                if domain == args[0]
            ]
        raise AssertionError("requête SQL inattendue: " + sql)


class FakeRedis:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self.values = values or {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)


class TestRecordStorePrecedence:
    pytestmark = pytest.mark.asyncio

    async def test_postgres_prime_sur_un_cache_redis_perime(self) -> None:
        """La base gagne : c'est elle qui fait foi après un redémarrage."""
        key = "ethan:core-records:capability_manager:qdrant"
        pg = FakePG(
            {("capability_manager", "qdrant"): json.dumps({"id": "qdrant", "state": "INSTALLING"})}
        )
        # Cache Redis antérieur, décrivant un état qui n'est plus le bon.
        redis = FakeRedis({key: json.dumps({"id": "qdrant", "state": "SUPPORTED"})})
        store = CoreRecordStore(pg_pool=pg, redis_client=redis)

        record = await store.get("capability_manager", "qdrant")
        assert record is not None
        assert record["state"] == "INSTALLING"

    async def test_redis_sert_de_repli_quand_postgres_echoue(self) -> None:
        """PostgreSQL indisponible : le cache permet encore de lire."""
        key = "ethan:core-records:capability_manager:qdrant"
        pg = FakePG()
        pg.fail = True
        redis = FakeRedis({key: json.dumps({"id": "qdrant", "state": "READY"})})
        store = CoreRecordStore(pg_pool=pg, redis_client=redis)

        record = await store.get("capability_manager", "qdrant")
        assert record is not None
        assert record["state"] == "READY"

    async def test_memoire_du_process_reste_le_cache_chaud(self) -> None:
        """Une lecture répétée ne relit ni PostgreSQL ni Redis."""
        pg = FakePG()
        store = CoreRecordStore(pg_pool=pg)
        await store.save("d", "r", {"v": 1})
        calls_before = len(pg.rows)
        first = await store.get("d", "r")
        second = await store.get("d", "r")
        assert first == second == {"v": 1}
        assert len(pg.rows) == calls_before
