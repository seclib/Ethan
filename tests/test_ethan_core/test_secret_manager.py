"""Tests pour SecretManager."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from core.config.secrets import SecretManager, SecretNotFoundError


class TestSecretManager:
    """Tests du SecretManager."""

    def test_get_from_env(self, secret_manager: SecretManager):
        """Récupération depuis une variable d'environnement."""
        os.environ["ETHAN_TEST_SECRET"] = "env-value"
        try:
            value = secret_manager.get("test-secret")
            assert value == "env-value"
        finally:
            del os.environ["ETHAN_TEST_SECRET"]

    def test_get_from_direct_env(self, secret_manager: SecretManager):
        """Récupération depuis une variable d'environnement directe."""
        os.environ["MY_SECRET"] = "direct-value"
        try:
            value = secret_manager.get("my-secret")
            assert value == "direct-value"
        finally:
            del os.environ["MY_SECRET"]

    def test_get_not_found(self, secret_manager: SecretManager):
        """Secret non trouvé."""
        with pytest.raises(SecretNotFoundError):
            secret_manager.get("nonexistent-secret")

    def test_get_with_default(self, secret_manager: SecretManager):
        """Secret non trouvé avec valeur par défaut."""
        value = secret_manager.get("nonexistent", default="default-value")
        assert value == "default-value"

    def test_get_or_none(self, secret_manager: SecretManager):
        """get_or_none retourne None si non trouvé."""
        value = secret_manager.get_or_none("nonexistent")
        assert value is None

    def test_cache(self, secret_manager: SecretManager):
        """Le cache évite de re-lire les sources."""
        os.environ["ETHAN_CACHED_SECRET"] = "cached-value"
        try:
            value1 = secret_manager.get("cached-secret")
            assert value1 == "cached-value"

            # Modifier la variable d'environnement
            os.environ["ETHAN_CACHED_SECRET"] = "new-value"

            # Le cache retourne l'ancienne valeur
            value2 = secret_manager.get("cached-secret")
            assert value2 == "cached-value"  # Valeur en cache

            # Après clear_cache, la nouvelle valeur est lue
            secret_manager.clear_cache()
            value3 = secret_manager.get("cached-secret")
            assert value3 == "new-value"
        finally:
            del os.environ["ETHAN_CACHED_SECRET"]

    def test_clear_cache(self, secret_manager: SecretManager):
        """Vidage du cache."""
        os.environ["ETHAN_CLEAR_TEST"] = "value"
        try:
            secret_manager.get("clear-test")
            assert len(secret_manager._cache) == 1

            secret_manager.clear_cache()
            assert len(secret_manager._cache) == 0
        finally:
            del os.environ["ETHAN_CLEAR_TEST"]

    def test_env_name_convention(self, secret_manager: SecretManager):
        """Convention de nommage ETHAN_<NAME>."""
        os.environ["ETHAN_OPENAI_API_KEY"] = "sk-test"
        try:
            value = secret_manager.get("openai-api-key")
            assert value == "sk-test"
        finally:
            del os.environ["ETHAN_OPENAI_API_KEY"]

    def test_repr(self, secret_manager: SecretManager):
        """Représentation du SecretManager."""
        assert "SecretManager" in repr(secret_manager)
        assert "cache_size=0" in repr(secret_manager)