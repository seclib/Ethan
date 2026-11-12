"""Politique de stockage centralisée du Model Hub d'ETHAN.

Tous les modèles et artefacts gérés par ETHAN doivent être stockés sous la
racine du projet ETHAN dans le sous-répertoire `models/`.

Structure imposée :
Ethan/models/
├── registry/    # Enregistrement des modèles, catalogues locaux (JSON/YAML)
├── downloads/   # Téléchargements bruts (blobs en cours, reprises de téléchargement)
├── artifacts/   # Poids et artefacts extraits ou convertis (GGUF, Safetensors, tokenizers, configs)
├── installed/   # Modèles finalisés prêts à l'inférence locale ou liens symboliques
├── metadata/    # Fiches descriptives, adéquation matérielle, manifests, SHA256
└── tmp/         # Fichiers de travail temporaires internes au Model Hub

Règles de sécurité :
- Résolution fiable et déterministe de la racine du projet ETHAN.
- Interdiction stricte de dispersion hors du répertoire autorisé (~/.cache, ~/.ollama, /tmp).
- Protection contre les attaques par traversée de répertoire (Path Traversal / Jail).
- Vérification stricte des permissions en lecture, écriture et exécution.
"""

from __future__ import annotations

import logging
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class StoragePolicyError(Exception):
    """Exception de base pour les violations de politique de stockage."""


class PathTraversalError(StoragePolicyError, ValueError):
    """Tentative de sortie du périmètre de stockage autorisé (Path Traversal)."""


@dataclass(frozen=True)
class ModelStorageLayout:
    """Structure des répertoires de stockage pour le Model Hub ETHAN."""

    root_dir: Path
    models_dir: Path
    registry_dir: Path
    downloads_dir: Path
    artifacts_dir: Path
    installed_dir: Path
    metadata_dir: Path
    tmp_dir: Path

    def to_dict(self) -> dict[str, str]:
        """Convertit les chemins en dictionnaire de chaînes."""
        return {
            "root_dir": str(self.root_dir),
            "models_dir": str(self.models_dir),
            "registry_dir": str(self.registry_dir),
            "downloads_dir": str(self.downloads_dir),
            "artifacts_dir": str(self.artifacts_dir),
            "installed_dir": str(self.installed_dir),
            "metadata_dir": str(self.metadata_dir),
            "tmp_dir": str(self.tmp_dir),
        }


def resolve_ethan_root() -> Path:
    """Résout de manière fiable la racine du projet ETHAN.

    Priorités :
    1. Variable d'environnement ``ETHAN_ROOT`` ou ``ETHAN_HOME`` si définie et valide.
    2. Remontée de l'arborescence depuis ce fichier jusqu'à trouver les marqueurs
       de projet (``pyproject.toml``, dossiers ``core`` et ``interfaces``).
    3. Répertoire de travail actuel si les marqueurs sont présents.
    4. Fallback sur le chemin canonique calculé depuis ``core/models/storage.py``.

    Returns:
        Path absolu et résolu de la racine ETHAN.
    """
    # 1. Variable d'environnement explicite pour la racine du projet
    env_root = os.getenv("ETHAN_ROOT")
    if env_root:
        candidate = Path(env_root).resolve()
        if candidate.exists() and candidate.is_dir():
            return candidate

    # 2. Remontée arborescente depuis ce fichier
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists() and (parent / "core").exists():
            return parent

    # 3. Répertoire courant
    cwd = Path.cwd().resolve()
    if (cwd / "pyproject.toml").exists() and (cwd / "core").exists():
        return cwd

    # 4. Fallback canonique (core/models/storage.py -> 3 niveaux jusqu'à racine)
    return Path(__file__).resolve().parents[2]


def get_models_dir(custom_path: str | Path | None = None) -> Path:
    """Retourne le chemin absolu du dossier models de base.

    Args:
        custom_path: Chemin explicite optionnel (prioritaire).

    Returns:
        Path absolu vers le dossier models.
    """
    if custom_path:
        return Path(custom_path).resolve()

    env_models = os.getenv("ETHAN_MODELS_DIR")
    if env_models:
        return Path(env_models).resolve()

    return (resolve_ethan_root() / "models").resolve()


def safe_join(base_dir: Path, *parts: str | Path) -> Path:
    """Joint un ou plusieurs segments à base_dir en garantissant l'absence d'évasion (Jail).

    Args:
        base_dir: Dossier racine autorisé.
        parts: Segments de chemin relatifs.

    Returns:
        Path résolu et garanti dans base_dir.

    Raises:
        PathTraversalError: Si le chemin résolu tente de sortir de base_dir.
    """
    resolved_base = base_dir.resolve()
    target = resolved_base

    for part in parts:
        clean_part = str(part).strip()
        # Interdire les chemins absolus passés en segment secondaire
        if clean_part.startswith("/") or clean_part.startswith("\\"):
            clean_part = clean_part.lstrip("/\\")
        target = target / clean_part

    resolved_target = target.resolve()

    # Vérification stricte du confinement (is_relative_to)
    try:
        resolved_target.relative_to(resolved_base)
    except ValueError as exc:
        raise PathTraversalError(
            "Tentative de sortie de périmètre détectée : "
            f"chemin '{resolved_target}' hors de '{resolved_base}'"
        ) from exc

    return resolved_target


def validate_permissions(directory: Path) -> None:
    """Valide les permissions en lecture, écriture et exécution d'un répertoire.

    Raises:
        PermissionError: Si les permissions requises sont absentes.
    """
    resolved = directory.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Le répertoire n'existe pas : {resolved}")

    # Vérification des bits d'accès
    if not os.access(resolved, os.R_OK):
        raise PermissionError(f"Permission en lecture manquante sur : {resolved}")
    if not os.access(resolved, os.W_OK):
        raise PermissionError(f"Permission en écriture manquante sur : {resolved}")
    if not os.access(resolved, os.X_OK):
        raise PermissionError(f"Permission en traversée (exécution) manquante sur : {resolved}")

    # Test d'écriture / suppression réel (canary)
    canary = resolved / f".ethan_canary_{os.getpid()}_{int(time.time()*1000)}"
    try:
        canary.touch()
        canary.unlink()
    except Exception as exc:
        raise PermissionError(
            f"Échec du test d'écriture/suppression réel sur : {resolved} ({exc})"
        ) from exc


def ensure_models_storage(base_models_dir: str | Path | None = None) -> ModelStorageLayout:
    """Initialise, crée et valide l'intégralité de l'arborescence Ethan/models/.

    Crée automatiquement :
    - models/registry
    - models/downloads
    - models/artifacts
    - models/installed
    - models/metadata
    - models/tmp

    Configure également les variables d'environnement des bibliothèques externes
    (ex: Hugging Face) pour garantir qu'aucune dispersion n'a lieu vers ~/.cache.

    Returns:
        Instance ModelStorageLayout validée.
    """
    root_dir = resolve_ethan_root()
    models_dir = get_models_dir(base_models_dir)

    layout = ModelStorageLayout(
        root_dir=root_dir,
        models_dir=models_dir,
        registry_dir=models_dir / "registry",
        downloads_dir=models_dir / "downloads",
        artifacts_dir=models_dir / "artifacts",
        installed_dir=models_dir / "installed",
        metadata_dir=models_dir / "metadata",
        tmp_dir=models_dir / "tmp",
    )

    # 1. Création sécurisée des dossiers
    for directory in [
        layout.models_dir,
        layout.registry_dir,
        layout.downloads_dir,
        layout.artifacts_dir,
        layout.installed_dir,
        layout.metadata_dir,
        layout.tmp_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True, mode=0o755)
        validate_permissions(directory)

    # 2. Confinement des bibliothèques externes : interdire ~/.cache
    apply_storage_environment(layout)

    if base_models_dir is None:
        global _global_storage_layout
        _global_storage_layout = layout

    return layout


def apply_storage_environment(layout: ModelStorageLayout) -> None:
    """Configure les variables d'environnement de bas niveau pour éviter toute dispersion.

    Assure que Hugging Face Hub, Transformers, PyTorch ou d'autres sous-systèmes
    écrivent strictement sous Ethan/models/downloads ou Ethan/models/tmp.
    """
    os.environ["ETHAN_MODELS_DIR"] = str(layout.models_dir)
    os.environ["HF_HOME"] = str(layout.downloads_dir)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(layout.downloads_dir)
    os.environ["TRANSFORMERS_CACHE"] = str(layout.downloads_dir)


def cleanup_tmp(layout: ModelStorageLayout | None = None, older_than_seconds: int = 86400) -> int:
    """Nettoie les fichiers temporaires expirés sous Ethan/models/tmp/.

    Args:
        layout: Structure de stockage (utilise la structure par défaut si omise).
        older_than_seconds: Âge minimum des fichiers à supprimer en secondes (défaut: 24h).

    Returns:
        Nombre de fichiers ou dossiers supprimés.
    """
    active_layout = layout or get_model_storage()
    tmp_dir = active_layout.tmp_dir
    if not tmp_dir.exists():
        return 0

    now = time.time()
    deleted_count = 0

    for item in tmp_dir.iterdir():
        try:
            mtime = item.stat().st_mtime
            if now - mtime >= older_than_seconds:
                if item.is_dir() and not item.is_symlink():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
                deleted_count += 1
        except Exception as exc:
            logger.debug("Échec nettoyage temporaire pour %s: %s", item, exc)

    return deleted_count


# Instance singleton globale
_global_storage_layout: ModelStorageLayout | None = None


def get_model_storage() -> ModelStorageLayout:
    """Retourne la disposition de stockage globale initialisée."""
    global _global_storage_layout
    if _global_storage_layout is None:
        _global_storage_layout = ensure_models_storage()
    return _global_storage_layout


def reset_model_storage() -> None:
    """Réinitialise le singleton de stockage (utile pour les tests et la reconfiguration)."""
    global _global_storage_layout
    _global_storage_layout = None
