"""Tests unitaires pour la politique de stockage du Model Hub d'ETHAN."""

import os
import stat
import tempfile
from pathlib import Path

import pytest
from core.models.hub import get_model_hub
from core.models.storage import (
    ModelStorageLayout,
    PathTraversalError,
    apply_storage_environment,
    cleanup_tmp,
    ensure_models_storage,
    get_model_storage,
    get_models_dir,
    reset_model_storage,
    resolve_ethan_root,
    safe_join,
    validate_permissions,
)


@pytest.fixture(autouse=True)
def clean_storage_state(monkeypatch):
    """Garantit l'isolation de chaque test de stockage."""
    reset_model_storage()
    # Supprimer temporairement tout override d'environnement
    monkeypatch.delenv("ETHAN_ROOT", raising=False)
    monkeypatch.delenv("ETHAN_MODELS_DIR", raising=False)
    yield
    reset_model_storage()


def test_resolve_ethan_root():
    """Vérifie que la racine d'ETHAN est résolue correctement."""
    root = resolve_ethan_root()
    assert root.exists()
    assert (root / "pyproject.toml").exists()
    assert (root / "core").exists()


def test_resolve_ethan_root_with_env(monkeypatch, tmp_path):
    """Vérifie que ETHAN_ROOT est respecté si défini."""
    fake_root = tmp_path / "custom_ethan"
    fake_root.mkdir()
    monkeypatch.setenv("ETHAN_ROOT", str(fake_root))
    assert resolve_ethan_root() == fake_root


def test_get_models_dir_defaults_to_ethan_models():
    """Vérifie que le chemin par défaut est sous la racine ETHAN."""
    models_dir = get_models_dir()
    root = resolve_ethan_root()
    assert models_dir == (root / "models").resolve()


def test_get_models_dir_with_env(monkeypatch, tmp_path):
    """Vérifie que ETHAN_MODELS_DIR surcharge le dossier par défaut."""
    custom_models = tmp_path / "models_override"
    monkeypatch.setenv("ETHAN_MODELS_DIR", str(custom_models))
    assert get_models_dir() == custom_models.resolve()


def test_ensure_models_storage_creates_all_subdirectories(tmp_path):
    """Vérifie la création automatique des 6 sous-répertoires requis."""
    test_models = tmp_path / "test_models_root"
    layout = ensure_models_storage(base_models_dir=test_models)

    assert isinstance(layout, ModelStorageLayout)
    assert layout.models_dir.exists()
    assert layout.registry_dir.exists()
    assert layout.downloads_dir.exists()
    assert layout.artifacts_dir.exists()
    assert layout.installed_dir.exists()
    assert layout.metadata_dir.exists()
    assert layout.tmp_dir.exists()

    # Vérification des noms exacts
    assert layout.registry_dir.name == "registry"
    assert layout.downloads_dir.name == "downloads"
    assert layout.artifacts_dir.name == "artifacts"
    assert layout.installed_dir.name == "installed"
    assert layout.metadata_dir.name == "metadata"
    assert layout.tmp_dir.name == "tmp"


def test_validate_permissions(tmp_path):
    """Vérifie la validation des permissions en lecture, écriture et exécution."""
    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()
    # Doit réussir sur un répertoire accessible
    validate_permissions(valid_dir)

    # Répertoire inexistant
    with pytest.raises(FileNotFoundError):
        validate_permissions(tmp_path / "inexistant")


def test_safe_join_prevents_path_traversal(tmp_path):
    """Vérifie le blocage de toute évasion de répertoire (Path Traversal)."""
    base = tmp_path / "sandbox"
    base.mkdir()

    # Chemins valides à l'intérieur
    valid_path = safe_join(base, "sub", "model.gguf")
    assert valid_path == (base / "sub" / "model.gguf").resolve()

    # Tentative d'évasion via ..
    with pytest.raises(PathTraversalError):
        safe_join(base, "..", "escape.txt")

    with pytest.raises(PathTraversalError):
        safe_join(base, "sub", "../../etc/passwd")

    with pytest.raises(PathTraversalError):
        safe_join(base, "../../../root")


def test_environment_isolation_prevents_cache_dispersion(tmp_path, monkeypatch):
    """Vérifie que l'environnement bloque la dispersion vers ~/.cache."""
    test_models = tmp_path / "isolated_models"
    layout = ensure_models_storage(base_models_dir=test_models)

    apply_storage_environment(layout)

    assert os.environ["HF_HOME"] == str(layout.downloads_dir)
    assert os.environ["HUGGINGFACE_HUB_CACHE"] == str(layout.downloads_dir)
    assert os.environ["TRANSFORMERS_CACHE"] == str(layout.downloads_dir)
    assert os.environ["ETHAN_MODELS_DIR"] == str(layout.models_dir)

    # S'assurer qu'aucun chemin ne contient .cache
    assert ".cache" not in os.environ["HF_HOME"]
    assert ".cache" not in os.environ["HUGGINGFACE_HUB_CACHE"]


def test_cleanup_tmp(tmp_path):
    """Vérifie le nettoyage des fichiers temporaires expirés."""
    test_models = tmp_path / "cleanup_models"
    layout = ensure_models_storage(base_models_dir=test_models)

    old_file = layout.tmp_dir / "old.tmp"
    old_file.write_text("old")
    # Forcer un mtime dans le passé
    past = 1000.0
    os.utime(old_file, (past, past))

    fresh_file = layout.tmp_dir / "fresh.tmp"
    fresh_file.write_text("fresh")

    deleted = cleanup_tmp(layout, older_than_seconds=3600)
    assert deleted == 1
    assert not old_file.exists()
    assert fresh_file.exists()


def test_model_hub_integration_with_storage():
    """Vérifie que ModelHub expose bien la disposition de stockage."""
    hub = get_model_hub()
    storage = hub.get_storage_layout()
    assert isinstance(storage, ModelStorageLayout)
    assert storage.models_dir.exists()
    assert storage.models_dir.name == "models"
