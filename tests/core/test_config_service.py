"""Tests pour le ConfigurationService centralisé et le schéma de configuration."""

from __future__ import annotations

import asyncio
import pytest

from core.config import (
    ConfigSchema,
    ConfigurationService,
    ConfigStore,
    ConfigLoader,
    RuntimeMode,
    ProviderConfig,
    ProvidersConfig,
    RAGConfig,
    MemoryConfig,
    AgentsConfig,
    PlannerConfig,
    PluginsConfig,
    AuthenticationConfig,
    ModelsConfig,
)


# ── Tests du schéma ─────────────────────────────────────────────────────────

class TestConfigSchema:
    def test_defaults(self):
        cfg = ConfigSchema()
        assert cfg.runtime.mode == RuntimeMode.AUTO
        assert cfg.providers.active == "ollama"
        assert cfg.rag.enabled is True
        assert cfg.memory.enabled is True
        assert cfg.agents.max_concurrent == 4
        assert cfg.planner.max_depth == 5
        assert cfg.plugins.auto_load is True
        assert cfg.authentication.enabled is True

    def test_providers_seeded(self):
        cfg = ConfigSchema()
        assert "ollama" in cfg.providers.providers
        assert "openai" in cfg.providers.providers
        assert "anthropic" in cfg.providers.providers
        assert cfg.providers.providers["ollama"].enabled is True

    def test_to_dict(self):
        cfg = ConfigSchema()
        data = cfg.to_dict()
        assert "providers" in data
        assert "models" in data
        assert "rag" in data
        assert "memory" in data
        assert "agents" in data
        assert "planner" in data
        assert "plugins" in data
        assert "authentication" in data
        assert "runtime" in data

    def test_from_dict(self):
        data = {
            "rag": {"enabled": False, "chunk_size": 500},
            "agents": {"max_concurrent": 8},
        }
        cfg = ConfigSchema.from_dict(data)
        assert cfg.rag.enabled is False
        assert cfg.rag.chunk_size == 500
        assert cfg.agents.max_concurrent == 8
        # Les defaults restent
        assert cfg.rag.top_k == 5
        assert cfg.memory.enabled is True


# ── Tests du ConfigurationService ───────────────────────────────────────────

class TestConfigurationService:
    @pytest.fixture
    def service(self):
        """Service avec store en mémoire."""
        store = ConfigStore()
        loader = ConfigLoader(paths=[])  # Pas de fichiers YAML
        svc = ConfigurationService(loader=loader, store=store)
        return svc

    def test_get_defaults(self, service):
        asyncio.run(service.load())
        assert service.get("rag.enabled") is True
        assert service.get("providers.active") == "ollama"
        assert service.get("nonexistent.key") is None
        assert service.get("nonexistent.key", "fallback") == "fallback"

    def test_get_domain(self, service):
        asyncio.run(service.load())
        rag = service.get_domain("rag")
        assert rag["enabled"] is True
        assert rag["chunk_size"] == 1000

    def test_get_all(self, service):
        asyncio.run(service.load())
        all_config = service.get_all()
        assert "providers" in all_config
        assert "models" in all_config
        assert "rag" in all_config
        assert "memory" in all_config
        assert "agents" in all_config
        assert "planner" in all_config
        assert "plugins" in all_config
        assert "authentication" in all_config
        assert "runtime" in all_config

    def test_set_and_get(self, service):
        asyncio.run(service.load())
        asyncio.run(service.set("rag.enabled", False))
        assert service.get("rag.enabled") is False

    def test_set_domain(self, service):
        asyncio.run(service.load())
        asyncio.run(service.set_domain("rag", {"enabled": False, "chunk_size": 2000}))
        rag = service.get_domain("rag")
        assert rag["enabled"] is False
        assert rag["chunk_size"] == 2000

    def test_delete(self, service):
        asyncio.run(service.load())
        asyncio.run(service.set("rag.enabled", False))
        assert service.get("rag.enabled") is False
        deleted = asyncio.run(service.delete("rag.enabled"))
        assert deleted is True
        # Après suppression, on retombe sur le défaut
        assert service.get("rag.enabled") is True

    def test_validate(self, service):
        asyncio.run(service.load())
        result = service.validate()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_key(self, service):
        asyncio.run(service.load())
        result = service.validate("rag.enabled")
        assert result["valid"] is True

    def test_export_import(self, service):
        asyncio.run(service.load())
        exported = service.export()
        assert "providers" in exported

        # Import
        result = asyncio.run(service.import_({"rag": {"enabled": False}}))
        assert "rag" in result["imported"]
        assert result["errors"] == []
        assert service.get("rag.enabled") is False

    def test_import_unknown_domain(self, service):
        asyncio.run(service.load())
        result = asyncio.run(service.import_({"unknown": {"foo": "bar"}}))
        assert result["imported"] == []
        assert len(result["errors"]) == 1

    def test_get_schema(self, service):
        asyncio.run(service.load())
        schema = service.get_schema()
        assert isinstance(schema, ConfigSchema)


# ── Tests du ConfigStore ────────────────────────────────────────────────────

class TestConfigStore:
    def test_memory_store(self):
        store = ConfigStore()
        asyncio.run(store.save("rag", {"enabled": False}))
        data = asyncio.run(store.get("rag"))
        assert data == {"enabled": False}

    def test_get_all(self):
        store = ConfigStore()
        asyncio.run(store.save("rag", {"enabled": False}))
        asyncio.run(store.save("memory", {"enabled": True}))
        all_data = asyncio.run(store.get_all())
        assert "rag" in all_data
        assert "memory" in all_data

    def test_delete(self):
        store = ConfigStore()
        asyncio.run(store.save("rag", {"enabled": False}))
        deleted = asyncio.run(store.delete("rag"))
        assert deleted is True
        assert asyncio.run(store.get("rag")) is None

    def test_delete_missing(self):
        store = ConfigStore()
        deleted = asyncio.run(store.delete("nonexistent"))
        assert deleted is False