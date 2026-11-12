"""Gestionnaire de téléchargement résilient pour les modèles d'IA.

Prend en charge :
- Le téléchargement depuis Hugging Face Hub
- La reprise automatique sur fichiers partiels / blobs incomplets
- Les tentatives avec backoff exponentiel (jusqu'à 5 retries)
- L'injection sécurisée du HF_TOKEN
- Le suivi de progression sans bloquer la boucle d'événements
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable

from core.models.storage import ensure_models_storage

logger = logging.getLogger(__name__)


@dataclass
class DownloadProgress:
    """État d'avancement d'un téléchargement."""

    repo_id: str
    status: str  # "starting" | "downloading" | "completed" | "failed"
    downloaded_bytes: int = 0
    total_bytes: int = 0
    percent: float = 0.0
    error: str | None = None


class ModelDownloader:
    """Service de téléchargement asynchrone avec retry et reprise."""

    def __init__(self, cache_dir: str | None = None) -> None:
        # Initialiser et valider la disposition sous Ethan/models/
        self.layout = ensure_models_storage(cache_dir)
        self.cache_dir = str(self.layout.downloads_dir)
        self.artifacts_dir = str(self.layout.artifacts_dir)
        self._tasks: dict[str, dict[str, Any]] = {}

    def record_task(
        self,
        task_id: str,
        repo_id: str,
        runtime: str = "ollama",
        status: str = "starting",
        percent: float = 0.0,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Enregistre ou met à jour l'état d'un téléchargement."""
        entry = self._tasks.get(task_id, {
            "id": task_id,
            "repo_id": repo_id,
            "runtime": runtime,
            "created_at": time.time(),
        })
        entry.update({
            "status": status,
            "percent": percent,
            "error": error,
            "updated_at": time.time(),
        })
        self._tasks[task_id] = entry
        return entry

    def list_downloads(self) -> list[dict[str, Any]]:
        """Retourne la liste des téléchargements ordonnés par date décroissante."""
        return sorted(
            self._tasks.values(),
            key=lambda x: x.get("created_at", 0),
            reverse=True,
        )

    async def download_hf_model(
        self,
        repo_id: str,
        filename: str | None = None,
        hf_token: str | None = None,
        max_retries: int = 4,
        on_progress: Callable[[DownloadProgress], None] | None = None,
    ) -> dict[str, Any]:
        """Télécharge un modèle Hugging Face avec reprise et retry automatique.

        Args:
            repo_id: Dépôt Hugging Face (ex: "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")
            filename: Fichier spécifique optionnel (ex: "*q4_k_m.gguf")
            hf_token: Token Hugging Face optionnel
            max_retries: Nombre de tentatives avant abandon
            on_progress: Callback optionnel de progression

        Returns:
            Dict avec le statut et le chemin local des poids téléchargés.
        """
        token = hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")

        def _do_download() -> str:
            # Tenter d'utiliser huggingface_hub si installé
            try:
                from huggingface_hub import hf_hub_download, snapshot_download

                if filename:
                    return hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        token=token,
                        cache_dir=self.cache_dir,
                    )
                return snapshot_download(
                    repo_id=repo_id,
                    token=token,
                    cache_dir=self.cache_dir,
                )
            except ImportError:
                # Si huggingface_hub n'est pas installé, lever une erreur explicite
                raise RuntimeError(
                    "Le paquet 'huggingface_hub' est requis pour les téléchargements directs. "
                    "Installez-le avec : pip install huggingface-hub"
                )

        delay = 2.0
        last_error = None

        if on_progress:
            on_progress(DownloadProgress(repo_id=repo_id, status="starting"))

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "Téléchargement de %s (tentative %d/%d)...", repo_id, attempt, max_retries
                )
                if on_progress:
                    on_progress(DownloadProgress(repo_id=repo_id, status="downloading"))

                # Exécuter le téléchargement dans un thread dédié pour ne pas bloquer l'event loop
                local_path = await asyncio.to_thread(_do_download)

                logger.info("Téléchargement réussi pour %s -> %s", repo_id, local_path)
                if on_progress:
                    on_progress(
                        DownloadProgress(repo_id=repo_id, status="completed", percent=100.0)
                    )

                return {
                    "success": True,
                    "repo_id": repo_id,
                    "local_path": local_path,
                    "attempts": attempt,
                }

            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Échec de la tentative %d pour %s : %s", attempt, repo_id, last_error
                )
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2.0  # Backoff exponentiel

        if on_progress:
            on_progress(
                DownloadProgress(repo_id=repo_id, status="failed", error=last_error or "Unknown")
            )

        return {
            "success": False,
            "repo_id": repo_id,
            "error": last_error,
            "attempts": max_retries,
        }


# Singleton downloader — instanciation paresseuse.
# La construction de ModelDownloader() crée l'arborescence de stockage sur
# disque (ensure_models_storage) : faire cela au niveau module rendait tout
# import de core.models impossible dans un environnement en lecture seule
# (ex. /app dans l'image API, non-root) et faisait crasher uvicorn au
# démarrage. Même motif lazy que get_model_storage() et get_model_hub().
_global_downloader: ModelDownloader | None = None


def get_model_downloader() -> ModelDownloader:
    """Retourne l'instance unique du ModelDownloader."""
    global _global_downloader
    if _global_downloader is None:
        _global_downloader = ModelDownloader()
    return _global_downloader
