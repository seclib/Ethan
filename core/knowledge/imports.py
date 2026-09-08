"""Knowledge Import Manager — import local-first de fichiers/dossiers vers une collection.

ETHAN Core owns file import, extraction, chunking/embedding and collection
membership.  The WebUI only uploads bytes (no parsing, no embeddings, no
Qdrant access) and polls the job state.

Pipeline per file:
  validate (MIME + size + name)  →  FileStore.register (binary, root-local)
  →  extract_text  →  RAGIngestion.ingest  →  Collection.add_document

A short-lived in-memory job keeps real progress (steps + per-file results).
All imported bytes stay inside the ETHAN root directory via FileStore
storage_dir (the WebUI never sends or trusts filesystem paths).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.rag.extractors import extract_text
from core.state.files import FileStore

logger = logging.getLogger(__name__)

#: Formats réellement supportés par le pipeline d'extraction ETHAN.
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
    ".text": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".csv": "text/csv",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

_SUPPORTED_MIME = set(SUPPORTED_EXTENSIONS.values())
#: Les images sont importées (binaire conservé) mais pas indexées en texte.
_IMAGE_MIME = {"image/png", "image/jpeg", "image/webp"}

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MiB — borne unique côté Core

#: ``..``/``~`` interdits (traversée); le ``/`` est permis pour la hiérarchie
#: affichable d'un dossier importé — jamais résolu en chemin filesystem.
_TRAVERSAL = re.compile(r"(^|/)(\.\.|~)(/|$)")


class ImportValidationError(ValueError):
    """Erreur d'import (MIME/taille/chemin) — devient 4xx dans le router."""


def _sanitize_name(filename: str) -> str:
    """Nettoie un nom de fichier fourni par le navigateur.

    Les navigateurs envoient parfois ``C:\fakepath\name`` ou un chemin
    volontairement hostile ; on normalise les antislashs en ``/`` puis on
    rejette toute traversée de dossiers (``..``/``~``).  Un chemin relatif
    (``subdir/file.md``) est conservé comme nom affichable, jamais utilisé
    pour lire/écrire sur disque (le Core ne s'appuie que sur les octets).
    """
    if not filename:
        raise ImportValidationError("Empty filename")
    normalized = filename.replace("\\", "/")
    if _TRAVERSAL.search(normalized):
        raise ImportValidationError(f"Unsafe filename path: {filename!r}")
    return normalized


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeImportManager:
    """Owns file/folder import into a RAG collection, with job progress."""

    def __init__(
        self,
        file_store: FileStore,
        collections: Any,
        ingestion: Any,
    ) -> None:
        self._files = file_store
        self._collections = collections
        self._ingestion = ingestion
        self._jobs: dict[str, dict[str, Any]] = {}

    # ── Jobs ────────────────────────────────────────────────────────────

    def _new_job(self, user_id: str) -> str:
        job_id = str(uuid4())
        self._jobs[job_id] = {
            "id": job_id,
            "user_id": user_id,
            "status": "running",
            "progress": 0.0,
            "step": "receiving",
            "total": 0,
            "done": 0,
            "results": [],
            "errors": [],
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        return job_id

    def get_job(self, job_id: str, user_id: str) -> dict[str, Any] | None:
        """État d'un job (owner-scoped).  Terminé → métadonnées + résultats."""
        job = self._jobs.get(job_id)
        if job is None or job["user_id"] != user_id:
            return None
        return dict(job)

    # ── Validation d'un fichier (avant toute écriture) ──────────────────

    def _validate(self, filename: str, raw: bytes, mime: str) -> str:
        """Retourne le MIME normalisé ; lève ImportValidationError sinon."""
        if not raw:
            raise ImportValidationError("Empty file")
        if len(raw) > _MAX_FILE_SIZE:
            raise ImportValidationError(
                f"File too large ({len(raw)} bytes, max {_MAX_FILE_SIZE})"
            )
        name = _sanitize_name(filename)
        ext = f".{name.rsplit('.', 1)[-1].lower()}" if "." in name else ""
        expected = SUPPORTED_EXTENSIONS.get(ext)
        if expected is None:
            raise ImportValidationError(f"Unsupported file type: {name}")
        # MIME du navigateur ignoré : on fait foi sur l'extension (source sûre).
        return expected

    async def _import_one(
        self,
        user_id: str,
        filename: str,
        raw: bytes,
        collection_id: str,
        *,
        job: dict[str, Any],
    ) -> dict[str, Any]:
        """Importe un fichier : validation → FileStore → extraction → RAG.

        Retourne le record du document RAG.  Un échec d'extraction laisse un
        record ``status="error"`` sans interrompre le lot (erreurs isolées).
        """
        try:
            mime = self._validate(filename, raw, None)
        except ImportValidationError as exc:
            job["errors"].append(
                {"filename": _sanitize_name(filename), "code": 422, "detail": str(exc)}
            )
            job["done"] += 1
            job["progress"] = job["done"] / max(job["total"], 1)
            return {}

        # 1. Binaire → FileStore (root-local) — jamais exposé au WebUI.
        try:
            file_record = await self._files.register(
                filename=filename.rsplit("/", 1)[-1],
                content_type=mime,
                size=len(raw),
                user_id=user_id,
                content=raw,
            )
        except Exception as exc:  # FileStore échoue (disque plein…)
            job["errors"].append(
                {"filename": _sanitize_name(filename), "code": 500, "detail": str(exc)}
            )
            job["done"] += 1
            job["progress"] = job["done"] / max(job["total"], 1)
            return {}

        # 2. Record RAG + ingestion (pipeline Core partagé).
        result: dict[str, Any] = {}
        try:
            text = "" if mime in _IMAGE_MIME else extract_text(raw, filename, mime)
            ingested = await self._ingestion.ingest(
                content=text,
                title=filename.rsplit("/", 1)[-1],
                source=f"import:{collection_id}",
                metadata={
                    "user_id": user_id,
                    "file_id": file_record["id"],
                    "collection_id": collection_id,
                    "filename": filename,
                    "mime_type": mime,
                },
            )
            document_id = ingested.id
            if mime not in _IMAGE_MIME:
                # 3. Attache le document RAG à la collection.
                attached = await self._collections.add_document(
                    collection_id, document_id
                )
                if attached is None:
                    raise RuntimeError("Collection not found")
            result = {
                "filename": _sanitize_name(filename),
                "id": document_id,
                "status": "imported" if mime in _IMAGE_MIME else "ready",
            }
            job["results"].append(result)
        except Exception as exc:  # extraction/embedding/collection
            job["errors"].append(
                {
                    "filename": _sanitize_name(filename),
                    "code": 500,
                    "detail": str(exc)[:300],
                }
            )
        job["done"] += 1
        job["progress"] = round(job["done"] / max(job["total"], 1), 3)
        return result

    # ── API publique ────────────────────────────────────────────────────

    def start_import(
        self,
        user_id: str,
        files: list[tuple[str, bytes]],
        collection_id: str,
    ) -> str:
        """Crée un job et lance l'import en arrière-plan.

        ``files``: liste (filename, raw_bytes) — SANS chemins issus du
        navigateur (le Core ne s'appuie que sur le basename après sanitisation).
        Retourne immédiatement le ``job_id`` ; la progression se consulte via
        :meth:`get_job`.
        """
        import asyncio

        job_id = self._new_job(user_id)
        job = self._jobs[job_id]
        job["total"] = len(files)
        job["step"] = "validating"

        async def _runner() -> None:
            try:
                col = await self._collections.get_collection(collection_id)
                if col is None:
                    job["status"] = "failed"
                    job["step"] = "failed_destination"
                    job["progress"] = 1.0
                    job["errors"].append(
                        {"filename": None, "code": 404, "detail": "Collection not found"}
                    )
                    return
                job["step"] = "importing"
                for filename, raw in files:
                    await self._import_one(
                        user_id, filename, raw, collection_id, job=job
                    )
                job["status"] = "done"
                job["step"] = "done"
                job["progress"] = 1.0
            except Exception as exc:  # erreur globale non attribuable
                logger.warning("Import job %s failed: %s", job_id, exc)
                job["status"] = "failed"
                job["step"] = "failed"
                job["progress"] = 1.0
                job["errors"].append(
                    {"filename": None, "code": 500, "detail": str(exc)[:300]}
                )
            finally:
                job["updated_at"] = _utc_now()

        asyncio.get_event_loop().create_task(_runner())
        return job_id