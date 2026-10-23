"""Package core.models — Découverte, Registre, Inspection Hugging Face et Téléchargement.

Architecture conceptuelle (Model Hub = point central) :
Source → Model → Artifact / Format → Runtime → Endpoint → Hardware

``ModelHub`` est la façade unique (alias ``ModelManager`` pour lever
l'ambiguïté Hub/Store/Registry : pas de deuxième implémentation).
"""

from __future__ import annotations

from core.models.discovery import (
    CURATED_MODEL_CATALOG,
    discover_catalog_models,
    discover_models_async,
)
from core.models.downloader import ModelDownloader, get_model_downloader
from core.models.hf import inspect_hf_model, search_hf_models
from core.models.hub import ModelHub, ModelManager, get_model_hub
from core.models.registry import ModelEntry, ModelRegistry, get_model_registry
from core.models.storage import (
    ModelStorageLayout,
    PathTraversalError,
    StoragePolicyError,
    cleanup_tmp,
    ensure_models_storage,
    get_model_storage,
    get_models_dir,
    resolve_ethan_root,
    safe_join,
    validate_permissions,
)

__all__ = [
    "CURATED_MODEL_CATALOG",
    "ModelEntry",
    "ModelHub",
    "ModelManager",
    "ModelRegistry",
    "ModelDownloader",
    "ModelStorageLayout",
    "StoragePolicyError",
    "PathTraversalError",
    "cleanup_tmp",
    "discover_catalog_models",
    "discover_models_async",
    "ensure_models_storage",
    "get_model_downloader",
    "get_model_hub",
    "get_model_registry",
    "get_model_storage",
    "get_models_dir",
    "inspect_hf_model",
    "resolve_ethan_root",
    "safe_join",
    "search_hf_models",
    "validate_permissions",
]
