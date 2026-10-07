"""Persistance de la configuration ETHAN — chaîne UI → API → Core → PostgreSQL.

Couvre la chaîne complète du plan de remise en état :

1. modifier un réglage → la réponse API contient la valeur ;
2. relecture API (refresh navigateur) → même valeur ;
3. nouvel objet ``ConfigurationService`` (redémarrage du process) → même valeur ;
4. nouveau pool PostgreSQL (redémarrage du conteneur API) → même valeur ;
5. connexion fraîche, ligne lue sur disque → présente.

Règles de défaillance également couvertes :

* une écriture échouée lève ``ConfigPersistenceError`` et ne modifie PAS l'état ;
* l'API répond 503 (jamais 200) quand la persistance échoue ;
* les défauts du loader ne remplacent jamais une valeur déjà persistée ;
* ``init.sql`` et la migration 008 déclarent bien ``ethan_config``.

Les tests PostgreSQL tournent dans un schéma sandbox (``ethan_cfg_test``) via
``search_path`` : la configuration réelle de l'instance n'est jamais lue ni
modifiée.  Ils sont ignorés si aucune base n'est joignable (CI sans Docker).
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import re
from pathlib import Path
from typing import Any

import pytest
from core.config import ConfigStore, ConfigurationService
from core.config.store import ConfigPersistenceError

ROOT = Path(__file__).resolve().parent.parent
MIGRATION = ROOT / "deploy" / "postgres" / "migrations" / "008_create_ethan_config.sql"
INIT_SQL = ROOT / "deploy" / "postgres" / "init.sql"
SANDBOX_SCHEMA = "ethan_cfg_test"


# ── Connexion PostgreSQL (ignorée si base absente) ──────────────────────────


def _read_env_file() -> dict[str, str]:
    """Lit ``.env`` sans exposer les secrets dans les logs de test."""
    env: dict[str, str] = {}
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def _dsn() -> str | None:
    """DSN de test, ou ``None`` si PostgreSQL est absent.

    ``ETHAN_TEST_DATABASE_URL`` gagne (CI).  Sinon on reconstruit l'URL depuis
    ``.env`` en remplaçant l'hôte docker ``postgres`` par ``127.0.0.1`` — le
    ``DATABASE_URL`` brut n'est pas résolvable depuis l'hôte.
    """
    explicit = os.environ.get("ETHAN_TEST_DATABASE_URL")
    if explicit:
        return explicit

    env = _read_env_file()
    password = os.environ.get("POSTGRES_PASSWORD") or env.get("POSTGRES_PASSWORD")
    if not password:
        return None

    port = os.environ.get("POSTGRES_PORT") or env.get("POSTGRES_PORT") or "5432"
    user = os.environ.get("POSTGRES_USER") or env.get("POSTGRES_USER") or "ethan"
    dbname = os.environ.get("POSTGRES_DB") or env.get("POSTGRES_DB") or "ethan"
    return f"postgresql://{user}:{password}@127.0.0.1:{port}/{dbname}"


DSN = _dsn()


def _pg_available() -> bool:
    """Vérifie une fois que la base répond (échec → tests ignorés)."""
    if not DSN:
        return False
    try:
        import asyncpg

        async def probe() -> bool:
            try:
                conn = await asyncio.wait_for(asyncpg.connect(DSN), timeout=3)
            except Exception:  # noqa: BLE001 — base absente = skip
                return False
            await conn.close()
            return True

        return asyncio.run(probe())
    except Exception:  # noqa: BLE001
        return False


HAS_PG = _pg_available()
requires_pg = pytest.mark.skipif(
    not HAS_PG,
    reason="PostgreSQL non joignable (lance './ethan up' ou ETHAN_TEST_DATABASE_URL)",
)

# ── Fixtures sandbox ────────────────────────────────────────────────────────


def _migration_sql() -> str:
    """SQL de la migration 008, dépouillé de ses effets de bord psql/réels.

    On retire le ``\\set`` (méta-commande psql), les commentaires, les
    ``BEGIN/COMMIT`` (inutiles statement-par-statement) et l'insertion dans
    ``schema_migrations`` (table de l'instance réelle : ne jamais la toucher).
    """
    text = MIGRATION.read_text(encoding="utf-8")
    text = re.sub(r"^\s*\\set.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*--.*$", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"INSERT INTO schema_migrations.*?DO NOTHING;",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return text


async def _apply_migration(conn: Any) -> None:
    """Applique réellement la migration 008 dans le schéma sandbox."""
    for statement in _migration_sql().split(";"):
        statement = statement.strip()
        if not statement or statement.upper() in {"BEGIN", "COMMIT"}:
            continue
        await conn.execute(statement)


@contextlib.asynccontextmanager
async def _sandbox():
    """Pool + schéma sandbox isolé : la config réelle n'est jamais touchée."""
    import asyncpg

    assert DSN is not None
    bootstrap = await asyncio.wait_for(asyncpg.connect(DSN), timeout=5)
    try:
        await bootstrap.execute(f'DROP SCHEMA IF EXISTS "{SANDBOX_SCHEMA}" CASCADE')
        await bootstrap.execute(f'CREATE SCHEMA "{SANDBOX_SCHEMA}"')
        await bootstrap.execute(f'SET search_path TO "{SANDBOX_SCHEMA}"')
        await _apply_migration(bootstrap)
    finally:
        await bootstrap.close()

    async def _init(conn: Any) -> None:
        await conn.execute(f'SET search_path TO "{SANDBOX_SCHEMA}"')

    # ``server_settings`` porte le search_path au niveau du handshake : chaque
    # connexion du pool (y compris les créées à la demande) part dans le schéma
    # sandbox.  Un simple ``SET`` en ``init`` ne couvrait qu'une connexion et
    # laissait les autres écrire dans ``public``.
    pool = await asyncio.wait_for(
        asyncpg.create_pool(
            DSN,
            min_size=1,
            max_size=3,
            init=_init,
            server_settings={"search_path": SANDBOX_SCHEMA},
        ),
        10,
    )
    try:
        yield pool
    finally:
        await pool.close()
        teardown = await asyncio.wait_for(asyncpg.connect(DSN), timeout=5)
        try:
            await teardown.execute(f'DROP SCHEMA IF EXISTS "{SANDBOX_SCHEMA}" CASCADE')
        finally:
            await teardown.close()


def _fresh_service(pool: Any) -> ConfigurationService:
    """Un service neuf = ce que verrait un process redémarré."""
    service = ConfigurationService(store=ConfigStore(pg_pool=pool))
    asyncio.run(service.load())
    return service


async def _raw_read(domain: str) -> Any:
    """Lit la ligne via une connexion fraîche (bypass mémoire/cache Redis)."""
    import asyncpg

    conn = await asyncpg.connect(DSN)
    try:
        await conn.execute(f'SET search_path TO "{SANDBOX_SCHEMA}"')
        return await conn.fetchval("SELECT config FROM ethan_config WHERE domain_name = $1", domain)
    finally:
        await conn.close()


async def _new_pool() -> Any:
    """Pool neuf = ce que verrait un conteneur API redémarré.

    ``server_settings`` (packet de démarrage) plutôt que ``SET`` en ``init`` :
    asyncpg n'applique pas fiablement un ``SET`` de session à toutes les
    connexions du pool, ce qui faisait fuir des écritures dans ``public``.
    """
    import asyncpg

    return await asyncio.wait_for(
        asyncpg.create_pool(
            DSN,
            min_size=1,
            max_size=2,
            server_settings={"search_path": SANDBOX_SCHEMA},
        ),
        10,
    )


# ── 1. La table existe vraiment (sinon tout échoue silencieusement) ────────


class TestSchemaExists:
    def test_migration_008_creates_ethan_config(self):
        assert MIGRATION.is_file(), "migration 008_create_ethan_config.sql manquante"
        sql = MIGRATION.read_text(encoding="utf-8")
        assert "CREATE TABLE IF NOT EXISTS ethan_config" in sql
        assert "008_create_ethan_config" in sql, "migration non enregistrée dans schema_migrations"

    def test_init_sql_creates_ethan_config(self):
        sql = INIT_SQL.read_text(encoding="utf-8")
        assert "CREATE TABLE IF NOT EXISTS ethan_config" in sql, (
            "init.sql ne crée pas ethan_config : un volume vierge n'aurait aucune "
            "table de configuration"
        )

    def test_config_store_targets_ethan_config(self):
        from core.config import store as store_module

        source = Path(store_module.__file__).read_text(encoding="utf-8")
        assert "ethan_config" in source


# ── 2. Échec de persistance : jamais un succès silencieux ──────────────────


class _FailingPool:
    """Pool qui simule PostgreSQL hors service."""

    async def execute(self, *args: Any, **kwargs: Any) -> str:
        raise RuntimeError("connection refused")

    async def fetch(self, *args: Any, **kwargs: Any) -> list[Any]:
        raise RuntimeError("connection refused")


class TestFailureIsSurfaced:
    def test_store_save_raises_when_pg_fails(self):
        store = ConfigStore(pg_pool=_FailingPool())
        with pytest.raises(ConfigPersistenceError):
            asyncio.run(store.save("rag", {"enabled": False}))

    def test_store_delete_raises_when_pg_fails(self):
        store = ConfigStore(pg_pool=_FailingPool())
        with pytest.raises(ConfigPersistenceError):
            asyncio.run(store.delete("rag"))

    def test_store_reports_durability(self):
        assert ConfigStore(pg_pool=_FailingPool()).durable is True
        assert ConfigStore(pg_pool=_FailingPool()).backend == "postgresql"
        assert ConfigStore().durable is False
        assert ConfigStore().backend == "memory"

    def test_service_does_not_commit_on_failed_write(self):
        service = ConfigurationService(store=ConfigStore(pg_pool=_FailingPool()))
        asyncio.run(service.load())
        before = service.get_domain("rag")

        with pytest.raises(ConfigPersistenceError):
            asyncio.run(service.set_domain("rag", {"enabled": False, "chunk_size": 42}))

        # L'état en mémoire n'a PAS bougé : on ne prétend pas avoir enregistré.
        assert service.get_domain("rag") == before
        assert service.get("rag.chunk_size") != 42

    def test_service_set_propagates_failure(self):
        service = ConfigurationService(store=ConfigStore(pg_pool=_FailingPool()))
        asyncio.run(service.load())
        with pytest.raises(ConfigPersistenceError):
            asyncio.run(service.set("rag.enabled", False))

    def test_status_reports_non_durable_backend(self):
        status = asyncio.run(ConfigurationService(store=ConfigStore()).status())
        assert status["durable"] is False
        assert status["backend"] == "memory"
        assert status["warning"]


# ── Application de test : le VRAI routeur /config ───────────────────────────


def _build_app(service: ConfigurationService) -> Any:
    """Monte le routeur ``/config`` réel dans une app minimale.

    Le gate RBAC est satisfait en injectant un rôle admin (le test porte sur la
    persistance, pas sur l'authentification).
    """
    from fastapi import FastAPI
    from interfaces.api.routers import config as config_router

    app = FastAPI()

    @app.middleware("http")
    async def _grant_role(request: Any, call_next: Any) -> Any:
        request.state.token_payload = {"role": "admin"}
        return await call_next(request)

    app.include_router(config_router.router)
    config_router.set_configuration_service(service)
    return app


@contextlib.asynccontextmanager
async def _generation(pool: Any | None = None):
    """Une « génération » de process API : pool + service + app + client HTTP.

    ``pool is None`` → pool neuf (redémarrage de conteneur) ; sinon on réutilise
    le pool courant (redémarrage de process seul).
    """
    import httpx

    owned = None
    if pool is None:
        owned = await _new_pool()
        pool = owned

    service = ConfigurationService(store=ConfigStore(pg_pool=pool))
    await service.load()
    app = _build_app(service)
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, service
    finally:
        from interfaces.api.routers import config as config_router

        config_router.set_configuration_service(None)
        if owned is not None:
            await owned.close()


# ── 3. L'API ne renvoie JAMAIS 200 sur une écriture non persistée ──────────


class TestApiSurfacesPersistenceFailure:
    def test_patch_returns_503_when_store_fails(self):
        import httpx

        service = ConfigurationService(store=ConfigStore(pg_pool=_FailingPool()))
        asyncio.run(service.load())
        app = _build_app(service)
        transport = httpx.ASGITransport(app=app)

        async def _go() -> Any:
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.patch("/config/rag", json={"enabled": False})

        response = asyncio.run(_go())
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["error"] == "persistence_failed"
        assert "NOT saved" in detail["message"]

    def test_put_returns_503_when_store_fails(self):
        import httpx

        service = ConfigurationService(store=ConfigStore(pg_pool=_FailingPool()))
        asyncio.run(service.load())
        app = _build_app(service)
        transport = httpx.ASGITransport(app=app)

        async def _go() -> Any:
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.put("/config/planner", json={"max_depth": 9})

        response = asyncio.run(_go())
        assert response.status_code == 503

    def test_status_endpoint_is_reachable_and_not_shadowed(self):
        import httpx

        service = ConfigurationService(store=ConfigStore())
        asyncio.run(service.load())
        app = _build_app(service)
        transport = httpx.ASGITransport(app=app)

        async def _go() -> Any:
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.get("/config/status")

        response = asyncio.run(_go())
        assert response.status_code == 200
        assert response.json()["durable"] is False

    @pytest.mark.parametrize("path", ["/config/export", "/config/validate"])
    def test_static_routes_are_not_shadowed_by_domain(self, path: str):
        """``/export`` et ``/validate`` déclarés APRÈS ``/{domain}`` = 404."""
        import httpx

        service = ConfigurationService(store=ConfigStore())
        asyncio.run(service.load())
        app = _build_app(service)
        transport = httpx.ASGITransport(app=app)

        async def _go() -> Any:
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.get(path)

        response = asyncio.run(_go())
        assert response.status_code == 200, response.text


# ── 4. Chaîne complète : UI → API → Core → PostgreSQL → rechargement ────────


@requires_pg
class TestPersistenceChain:
    """Les 5 étapes de survie exigées par le plan de remise en état."""

    def test_setting_survives_all_restarts(self) -> None:
        asyncio.run(self._chain())

    async def _chain(self) -> None:
        import json as _json

        from core.config import ConfigSchema

        async with _sandbox() as pool:
            # ── Étape 1 : modification → la réponse API porte la valeur ──
            async with _generation(pool) as (client, _s1):
                response = await client.patch("/config/rag", json={"enabled": False, "top_k": 13})
                assert response.status_code == 200, response.text
                body = response.json()
                assert body["top_k"] == 13
                assert body["enabled"] is False

                # ── Étape 2 : relecture API (refresh navigateur) ────────
                reread = await client.get("/config/rag")
                assert reread.status_code == 200
                assert reread.json()["top_k"] == 13

            # ── Étape 3 : redémarrage du process (pool + service neufs) ─
            async with _generation() as (client, service):
                reread = await client.get("/config/rag")
                assert reread.status_code == 200, reread.text
                assert reread.json()["top_k"] == 13, "valeur perdue au redémarrage process"
                # La vérité côté Core aussi, pas seulement dans la réponse HTTP.
                assert service.get("rag.top_k") == 13

                update = await client.patch("/config/rag", json={"top_k": 17})
                assert update.status_code == 200, update.text
                assert update.json()["top_k"] == 17

            # ── Étape 4 : conteneur API redémarré (nouveau pool) ────────
            async with _generation() as (client, service):
                reread = await client.get("/config/rag")
                assert reread.status_code == 200, reread.text
                assert reread.json()["top_k"] == 17, "valeur perdue au redémarrage conteneur"
                assert service.get("rag.top_k") == 17
                # Règle « defaults only if nothing persisted » : le défaut du
                # loader n'a PAS remplacé la valeur écrite.
                assert ConfigSchema().to_dict()["rag"]["top_k"] != 17

            # ── Étape 5 : la ligne est réellement sur disque ────────────
            row = await _raw_read("rag")
            assert row is not None, "aucune ligne ethan_config : rien ne survivrait"
            stored = _json.loads(row) if isinstance(row, str) else row
            assert stored["top_k"] == 17
            assert stored["enabled"] is False

    def test_defaults_applied_only_when_nothing_persisted(self) -> None:
        asyncio.run(self._defaults())

    async def _defaults(self) -> None:
        from core.config import ConfigSchema

        async with _sandbox() as pool:
            async with _generation(pool) as (client, _service):
                response = await client.get("/config/rag")
                assert response.status_code == 200
                body = response.json()
                for key, value in ConfigSchema().to_dict()["rag"].items():
                    assert body.get(key) == value, f"default {key} non appliqué"

    def test_write_read_back_is_the_source_of_truth(self) -> None:
        asyncio.run(self._read_back())

    async def _read_back(self) -> None:
        """Ce que l'API renvoie après un PUT est ce que contient la base."""
        async with _sandbox() as pool:
            async with _generation(pool) as (client, _service):
                payload = {"max_depth": 7, "max_steps": 42}
                written = await client.put("/config/planner", json=payload)
                assert written.status_code == 200, written.text
                assert written.json()["max_depth"] == 7

                # Relecture via un service neuf (pas de cache partagé).
                async with _generation() as (client2, _s2):
                    reread = await client2.get("/config/planner")
                    assert reread.json()["max_depth"] == 7
                    assert reread.json()["max_steps"] == 42
