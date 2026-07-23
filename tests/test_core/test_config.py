"""Tests du système de configuration."""

import os
import tempfile
from pathlib import Path

import pytest

from core.config.loader import ConfigLoader
from core.config.schema import RuntimeMode, BusConfig, StorageConfig


@pytest.fixture
def loader():
    return ConfigLoader()


@pytest.fixture
def yaml_config(tmp_path):
    """Crée un fichier YAML de config temporaire."""
    config_file = tmp_path / "ethan.yaml"
    config_file.write_text("""
runtime:
  mode: standalone
  bus:
    type: inmemory
  storage:
    redis_url: redis://test:6379
    postgres_url: postgresql://test@localhost:5432/test
  log_level: DEBUG
""")
    return config_file


class TestConfigLoader:
    def test_default_config(self, loader):
        config = loader.load()
        assert config.runtime.mode == RuntimeMode.STANDALONE
        assert config.runtime.bus.type == "auto"
        assert config.runtime.log_level == "INFO"

    def test_yaml_override(self, loader, yaml_config, monkeypatch):
        monkeypatch.chdir(yaml_config.parent)
        config = loader.load()
        assert config.runtime.mode == RuntimeMode.STANDALONE
        assert config.runtime.bus.type == "inmemory"
        assert config.runtime.storage.redis_url == "redis://test:6379"
        assert config.runtime.log_level == "DEBUG"

    def test_env_override(self, loader, monkeypatch):
        monkeypatch.setenv("ETHAN_MODE", "distributed")
        monkeypatch.setenv("ETHAN_LOG_LEVEL", "WARNING")
        monkeypatch.setenv("ETHAN_REDIS_URL", "redis://env:6379")

        config = loader.load()
        assert config.runtime.mode == RuntimeMode.DISTRIBUTED
        assert config.runtime.log_level == "WARNING"
        assert config.runtime.storage.redis_url == "redis://env:6379"

    def test_programmatic_override(self, loader):
        overrides = {
            "runtime": {
                "mode": "distributed",
                "log_level": "ERROR",
            }
        }
        config = loader.load(overrides=overrides)
        assert config.runtime.mode == RuntimeMode.DISTRIBUTED
        assert config.runtime.log_level == "ERROR"

    def test_priority_order(self, loader, yaml_config, monkeypatch):
        """Les overrides programmatiques > env > YAML > défauts."""
        monkeypatch.chdir(yaml_config.parent)
        monkeypatch.setenv("ETHAN_LOG_LEVEL", "ENV")

        overrides = {"runtime": {"log_level": "OVERRIDE"}}
        config = loader.load(overrides=overrides)

        assert config.runtime.log_level == "OVERRIDE"

    def test_bool_env_parsing(self, loader, monkeypatch):
        monkeypatch.setenv("ETHAN_DEBUG", "true")
        config = loader.load()
        assert config.runtime.debug is True

        monkeypatch.setenv("ETHAN_DEBUG", "false")
        config = loader.load()
        assert config.runtime.debug is False


class TestBusConfig:
    def test_default_bus_config(self):
        config = BusConfig()
        assert config.type == "auto"
        assert config.servers == "nats://localhost:4222"
        assert config.record_history is True
        assert config.max_history == 10000

    def test_custom_bus_config(self):
        config = BusConfig(
            type="nats",
            servers="nats://prod:4222",
            record_history=False,
            max_history=5000,
        )
        assert config.type == "nats"
        assert config.servers == "nats://prod:4222"
        assert config.record_history is False
        assert config.max_history == 5000


class TestStorageConfig:
    def test_default_storage_config(self):
        config = StorageConfig()
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.redis_prefix == "ethan:"
        assert config.pgvector_enabled is False
        assert config.pgvector_dimension == 768

    def test_custom_storage_config(self):
        config = StorageConfig(
            redis_url="redis://custom:6379/1",
            redis_prefix="test:",
            pgvector_enabled=True,
            pgvector_dimension=1536,
        )
        assert config.redis_url == "redis://custom:6379/1"
        assert config.redis_prefix == "test:"
        assert config.pgvector_enabled is True
        assert config.pgvector_dimension == 1536