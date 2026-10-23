"""Tests — couche de persistance Core (backends agnostiques de driver).

Couvre :
* mode dégradé sans factory injectée (ETHAN doit survivre sans Redis/PG) ;
* injection de drivers factices → cycle de vie + roundtrip réels ;
* ``Persistence`` : composition, SQL d'insertion, validation des identifiants.
"""

from __future__ import annotations

import pytest

from core.persistence import (
    BackendNotConnected,
    Persistence,
    PersistenceConfig,
    PostgresBackend,
    RedisBackend,
)


class _FakeRedis:
    """Client Redis factice (mémoire)."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}
        self.closed = False

    async def ping(self) -> bool:
        return True

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value
        self.ttls[key] = ex

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def delete(self, key: str) -> int:
        return int(self.store.pop(key, None) is not None)

    async def aclose(self) -> None:
        self.closed = True


class _FakePool:
    """Pool PostgreSQL factice (mémoire) renvoyant des lignes dict-like."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []
        self.rows: list[dict] = []
        self.closed = False

    async def execute(self, sql: str, *args) -> str:
        self.statements.append((sql, args))
        return "INSERT 0 1"

    async def fetch(self, sql: str, *args):
        self.statements.append((sql, args))
        return [dict(row) for row in self.rows]

    def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_degraded_without_factory():
    """Sans factory : backends dégradés, jamais 'connectés', échec explicite."""
    redis = RedisBackend("redis://localhost:6379/0")
    pg = PostgresBackend("postgresql://localhost/ethan")

    assert await redis.connect() is False
    assert await pg.connect() is False
    assert redis.connected is False
    assert pg.connected is False

    with pytest.raises(BackendNotConnected):
        await redis.set("k", "v")
    with pytest.raises(BackendNotConnected):
        await pg.execute("SELECT 1")


@pytest.mark.asyncio
async def test_degraded_persistence_boot_tolerates_missing_drivers():
    """Persistence.connect() ne lève jamais : boot survit sans Redis/PG."""
    persistence = Persistence(
        PersistenceConfig(redis_url="redis://x/0", database_url="postgresql://x/y")
    )
    await persistence.connect()  # pas d'exception
    assert persistence.redis.connected is False
    assert persistence.postgres.connected is False
    await persistence.close()  # close inoffensif


@pytest.mark.asyncio
async def test_redis_backend_roundtrip_with_injected_driver():
    fake = _FakeRedis()
    backend = RedisBackend(
        "redis://localhost:6379/0", lambda url: fake, default_ttl=42
    )
    assert await backend.connect() is True
    assert backend.connected is True

    assert await backend.set("ethan:k", "value") is True
    assert fake.ttls["ethan:k"] == 42  # TTL par défaut appliqué
    assert await backend.get("ethan:k") == "value"
    assert await backend.set("ethan:k2", "v2", ttl=7) is True
    assert fake.ttls["ethan:k2"] == 7
    assert await backend.delete("ethan:k") is True
    assert await backend.get("ethan:k") is None

    await backend.close()
    assert fake.closed is True
    assert backend.connected is False
    with pytest.raises(BackendNotConnected):
        await backend.get("ethan:k2")


@pytest.mark.asyncio
async def test_postgres_backend_roundtrip_with_injected_driver():
    fake = _FakePool()

    async def factory(dsn: str):
        assert dsn == "postgresql://localhost/ethan"
        return fake

    backend = PostgresBackend("postgresql://localhost/ethan", factory)
    assert await backend.connect() is True

    await backend.execute("INSERT INTO t VALUES ($1)", "a")
    assert fake.statements == [("INSERT INTO t VALUES ($1)", ("a",))]

    fake.rows.append({"id": 1, "name": "x"})
    rows = await backend.fetch("SELECT * FROM t")
    assert rows == [{"id": 1, "name": "x"}]

    await backend.close()
    assert fake.closed is True
    assert backend.connected is False
    with pytest.raises(BackendNotConnected):
        await backend.fetch("SELECT 1")


@pytest.mark.asyncio
async def test_postgres_factory_sync_return_supported():
    """La factory peut être synchrone (retour direct du pool)."""
    fake = _FakePool()
    backend = PostgresBackend("postgresql://x/y", lambda dsn: fake)
    assert await backend.connect() is True
    await backend.close()


@pytest.mark.asyncio
async def test_persistence_composes_injected_backends():
    fake_redis, fake_pool = _FakeRedis(), _FakePool()

    async def pool_factory(dsn: str):
        return fake_pool

    persistence = Persistence(
        PersistenceConfig(
            redis_url="redis://localhost:6379/0",
            database_url="postgresql://localhost/ethan",
            cache_ttl=99,
        ),
        redis_client_factory=lambda url: fake_redis,
        pg_pool_factory=pool_factory,
    )
    await persistence.connect()
    assert persistence.redis.connected and persistence.postgres.connected

    # Chaîne live : set_live/get_live via Redis injecté.
    assert await persistence.set_live("k", "v") is True
    assert fake_redis.ttls["k"] == 99  # cache_ttl du config
    assert await persistence.get_live("k") == "v"

    # Chaîne durable : persist() construit un INSERT, query() lit les lignes.
    assert await persistence.persist("audit_log", {"id": "e1", "category": "test"}) == 1
    sql, args = fake_pool.statements[-1]
    assert sql == (
        "INSERT INTO audit_log (id, category) VALUES ($1, $2) "
        "ON CONFLICT DO NOTHING"
    )
    assert args == ("e1", "test")

    fake_pool.rows.append({"id": "e1"})
    assert await persistence.query("audit_log") == [{"id": "e1"}]

    await persistence.close()
    assert fake_redis.closed and fake_pool.closed


@pytest.mark.asyncio
async def test_persistence_rejects_invalid_identifiers():
    """Injection SQL bloquée : identifiants non alphanumériques rejetés."""
    persistence = Persistence(
        PersistenceConfig(database_url="postgresql://x/y"),
        pg_pool_factory=lambda dsn: _FakePool(),
    )
    await persistence.connect()

    with pytest.raises(ValueError):
        await persistence.persist("audit; DROP TABLE users", {"id": "x"})
    with pytest.raises(ValueError):
        await persistence.persist("audit_log", {"id; --": "x"})
    with pytest.raises(ValueError):
        await persistence.query("bad table name")


@pytest.mark.asyncio
async def test_manager_init_singleton():
    """init_persistence câble le singleton consultable via get_persistence."""
    from core.persistence.manager import (
        get_persistence,
        init_persistence,
        set_persistence_service,
    )

    fake = Persistence(PersistenceConfig())
    set_persistence_service(fake)
    assert await get_persistence() is fake

    result = await init_persistence(
        PersistenceConfig(redis_url="redis://localhost:6379/0")
    )
    assert await get_persistence() is result
    assert result.redis.connected is False  # pas de factory → dégradé, pas d'échec

