"""Persistance du provider LLM par défaut (audit §4).

Le défaut était choisi en mémoire puis mis en cache Redis : il repartait du
premier provider actif à chaque refresh de la WebUI et ne survivait ni à un
restart ni à un recreate de l'API. PostgreSQL (`llm_providers.is_default`) est
la source de vérité ; la mémoire et Redis ne sont que des replis.

Ces tests n'utilisent aucun service réel : un pool asyncpg et un client Redis
factices suffisent à prouver la hiérarchie des sources de vérité.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from core.llm.store import ProviderStore


class FakeProviderPG:
    """Pool asyncpg minimaliste sur `llm_providers`.

    Le même objet partagé par deux `ProviderStore` reproduit un redémarrage de
    l'API : le second store repart d'une mémoire vierge et relit la base.
    """

    def __init__(self, fail: bool = False) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.fail = fail
        self.updates = 0
        self._clock = 0

    async def execute(self, query: str, *args: Any) -> str:
        sql = " ".join(query.split())
        if self.fail:
            raise RuntimeError("postgres indisponible")
        self._clock += 1
        if sql.startswith("INSERT INTO llm_providers"):
            provider_id, config = args[0], args[1]
            existing = self.rows.get(provider_id)
            # ON CONFLICT DO UPDATE ne touche que config/updated_at :
            # `is_default` est préservé par PostgreSQL.
            self.rows[provider_id] = {
                "config": config,
                "enabled": existing["enabled"] if existing else True,
                "is_default": existing["is_default"] if existing else False,
                "updated_at": self._clock,
            }
            return "INSERT 0 1"
        if sql.startswith("UPDATE llm_providers"):
            (provider_id,) = args
            self.updates += 1
            affected = 0
            for row_id, row in self.rows.items():
                if row["is_default"] or row_id == provider_id:
                    row["is_default"] = row_id == provider_id
                    row["updated_at"] = self._clock
                    affected += 1
            return f"UPDATE {affected}"
        if sql.startswith("DELETE FROM llm_providers"):
            (provider_id,) = args
            return "DELETE 1" if self.rows.pop(provider_id, None) is not None else "DELETE 0"
        raise AssertionError("requête SQL inattendue: " + sql)

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        sql = " ".join(query.split())
        if sql.startswith("SELECT provider_id, config"):
            return [{"provider_id": pid, "config": row["config"]} for pid, row in self.rows.items()]
        raise AssertionError("requête SQL inattendue: " + sql)

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        sql = " ".join(query.split())
        if sql.startswith("SELECT provider_id FROM llm_providers"):
            for pid, row in self.rows.items():
                if row["is_default"]:
                    return {"provider_id": pid}
            return None
        raise AssertionError("requête SQL inattendue: " + sql)


class FakeRedis:
    """Client Redis minimaliste (cache du provider par défaut)."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def close(self) -> None:
        return None


class TestProviderDefaultPersistence:
    pytestmark = pytest.mark.asyncio

    async def test_defaut_ecrit_en_postgres(self) -> None:
        pg = FakeProviderPG()
        store = ProviderStore(pg_pool=pg)
        await store.save("openai", {"type": "openai", "enabled": True})
        await store.save("ollama", {"type": "ollama", "enabled": True})

        await store.set_default("ollama")

        assert pg.rows["ollama"]["is_default"] is True
        assert pg.rows["openai"]["is_default"] is False
        assert pg.updates == 1

    async def test_un_seul_defaut_a_la_fois(self) -> None:
        pg = FakeProviderPG()
        store = ProviderStore(pg_pool=pg)
        await store.save("openai", {"type": "openai", "enabled": True})
        await store.save("ollama", {"type": "ollama", "enabled": True})
        await store.set_default("openai")
        await store.set_default("ollama")

        defaults = [pid for pid, row in pg.rows.items() if row["is_default"]]
        assert defaults == ["ollama"]

    async def test_defaut_survit_au_rechargement(self) -> None:
        """Restart/recreate de l'API : mémoire vierge, base conservée."""
        pg = FakeProviderPG()
        first = ProviderStore(pg_pool=pg)
        await first.save("openai", {"type": "openai", "enabled": True})
        await first.save("ollama", {"type": "ollama", "enabled": True})
        await first.set_default("ollama")

        # Nouveau process : aucun état mémoire, aucun cache Redis.
        second = ProviderStore(pg_pool=pg)
        assert second._memory_default is None
        assert await second.get_default() == "ollama"

    async def test_postgres_prime_sur_la_memoire_et_redis(self) -> None:
        pg = FakeProviderPG()
        redis = FakeRedis()
        await redis.set("ethan:providers:default", "ollama")
        store = ProviderStore(redis_client=redis, pg_pool=pg)
        await store.save("openai", {"type": "openai", "enabled": True})
        await store.save("ollama", {"type": "ollama", "enabled": True})
        await store.set_default("openai")
        # Mémoire et Redis au secours de « ollama », base à « openai ».
        store._memory_default = "ollama"
        await redis.set("ethan:providers:default", "ollama")

        assert await store.get_default() == "openai"

    async def test_echec_postgres_remonte_jamais_un_faux_succes(self) -> None:
        """Fail-closed : un défaut non durable ne doit pas être annoncé réussi."""
        pg = FakeProviderPG(fail=True)
        store = ProviderStore(pg_pool=pg)
        await store.save("openai", {"type": "openai", "enabled": True})
        with pytest.raises(RuntimeError, match="provider par défaut"):
            await store.set_default("openai")

    async def test_provider_non_persiste_est_publie(self) -> None:
        """Provider jamais écrit en base : le défaut ne peut pas être marqué."""
        pg = FakeProviderPG()
        store = ProviderStore(pg_pool=pg)
        with pytest.raises(RuntimeError, match="introuvable"):
            await store.set_default("fantome")

    async def test_sans_postgres_le_defaut_est_jetable_et_annonce(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        store = ProviderStore(redis_client=FakeRedis())
        await store.save("openai", {"type": "openai", "enabled": True})
        with caplog.at_level("WARNING"):
            await store.set_default("openai")
        assert "non durable" in caplog.text
        assert await store.get_default() == "openai"

    async def test_lecture_bascule_sur_le_premier_actif_sans_defaut(self) -> None:
        """Comportement historique conservé quand rien n'est marqué en base."""
        pg = FakeProviderPG()
        store = ProviderStore(pg_pool=pg)
        await store.save("openai", {"type": "openai", "enabled": False})
        await store.save("ollama", {"type": "ollama", "enabled": True})
        assert await store.get_default() == "ollama"

    async def test_save_ne_reinitialise_pas_le_defaut(self) -> None:
        pg = FakeProviderPG()
        store = ProviderStore(pg_pool=pg)
        await store.save("openai", {"type": "openai", "enabled": True})
        await store.set_default("openai")
        # Activer/désactiver réécrit la config : le marquage doit survivre.
        await store.save("openai", {"type": "openai", "enabled": False})
        assert pg.rows["openai"]["is_default"] is True
        assert await store.get_default() == "openai"

    async def test_cache_redis_invalide(self) -> None:
        pg = FakeProviderPG()
        redis = FakeRedis()
        await redis.set("ethan:providers:default", "ollama")
        await redis.set("ethan:providers:all", json.dumps({"ollama": {"enabled": True}}))
        store = ProviderStore(redis_client=redis, pg_pool=pg)
        await store.save("openai", {"type": "openai", "enabled": True})
        await store.set_default("openai")

        assert "ethan:providers:default" not in redis.values
        assert "ethan:providers:all" not in redis.values
