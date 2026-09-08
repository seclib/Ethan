"""ProjectManager — Core-owned Project / Workspace domain.

Un Projet est un **conteneur de conversation avec portée de connaissance
et contexte d'exécution** :

- conversation container : les conversations y sont rattachées (project_id) ;
- knowledge scope        : collections RAG + agents + skills +
                             outillage admissibles (references, jamais de copie) ;
- execution context      : agent designe et configuration de modele
                             (provider/model) par defaut pour le projet.

Le manager est Core-owned : le WebUI ne fait que projeter l'etat.  La
persistence repose sur CoreRecordStore (PG durable + Redis cache
+ fallback in-memory), exactement comme FolderManager / DomainManager.
Aucune ressource n'est dupliquee : chaque association est un simple identifiant.

La provenance des documents est **centralisée** dans `core/rag/ingestion.py`
(`ingest_documents`).  Un document uploadé depuis le WebUI est traité par
ce pipeline unique — le WebUI ne parse ni n'embed pas ; il deleguë.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_PROJECTS = "projects"
_DOMAIN_DOCS = "documents"  # documents RAG (scope projet)

# Typage des ressources associables a un projet.  Les champs sont optionnels
# et independants : un projet peut n'avoir qu'un nom (zero ressource imposée).
_DEFAULT_FIELDS = (
    "name",
    "description",
    "instructions",
    "folder_ids",
    "knowledge_ids",
    "collection_ids",
    "skill_ids",
    "tool_ids",
    "agent_id",
    "provider_id",
    "model",
    "metadata",
)

# Sentinel interne : distingue "champ non fourni" de "valeur None".
_UNSET = object()


class ProjectManager:
    """Gestion des projets (Core-owned).

    Args:
        store: CoreRecordStore partagé (PG durable + Redis + fallback memoire).
        event_bus: Bus d'evenements optionnel (toutes les mutations publiees).
    """

    def __init__(
        self,
        store: CoreRecordStore,
        event_bus: EventBus | None = None,
        ingestion_service: Any | None = None,
    ) -> None:
        self._store = store
        self._bus = event_bus
        self._ingestion = ingestion_service

    # ── CRUD ───────────────────────────────────────────────────────────

    async def list_projects(
        self, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Liste les projets visibles par l'utilisateur.

        `user_only=True` est imposé en interne quand `user_id` est fourni
        (filtrage par `user_id`), sauf pour le fallback "general".
        """
        projects = await self._store.list(_DOMAIN_PROJECTS)
        if user_id is not None:
            projects = [p for p in projects if p.get("user_id") == user_id]
        return projects

    async def create_project(
        self,
        user_id: str | None,
        name: str,
        description: str = "",
        instructions: str = "",
        folder_ids: list[str] | None = None,
        knowledge_ids: list[str] | None = None,
        collection_ids: list[str] | None = None,
        skill_ids: list[str] | None = None,
        tool_ids: list[str] | None = None,
        agent_id: str | None = None,
        provider_id: str | None = None,
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Cree un projet (persisté via CoreRecordStore.save = upsert)."""
        name = (name or "").strip()
        if not name:
            raise ValueError("Project name is required")
        await self._ensure_unique_name(name)

        project = _new_project(
            user_id=user_id,
            name=name,
            description=description,
            instructions=instructions,
            folder_ids=folder_ids,
            knowledge_ids=knowledge_ids,
            collection_ids=collection_ids,
            skill_ids=skill_ids,
            tool_ids=tool_ids,
            agent_id=agent_id,
            provider_id=provider_id,
            model=model,
            metadata=metadata,
        )
        await self._store.save(_DOMAIN_PROJECTS, project["id"], project)
        await self._publish(
            EventType.PROJECT_CREATED, "project.created", {"project_id": project["id"]}
        )
        return project

    async def get_project(
        self, project_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Retourne un projet ou `None`.

        Le projet virtuel `general` est retourne sans creation en DB.
        """
        if project_id == "general":
            return _general_project(user_id)

        project = await self._store.get(_DOMAIN_PROJECTS, project_id)
        if project is None:
            return None
        if user_id is not None and project.get("user_id") != user_id:
            return None
        return project

    async def update_project(
        self,
        project_id: str,
        user_id: str | None,
        patch: dict[str, Any],
    ) -> dict[str, Any]:
        """Applique un patch partiel aux champs autorises (save = upsert)."""
        project = await self.get_project(project_id, user_id)
        if project is None:
            raise ValueError(f"Project not found: {project_id}")
        if project_id == "general":
            # Le projet "general" est virtuel — on renvoie le snapshot mis a jour.
            if "name" in patch or "description" in patch or "instructions" in patch:
                g = _general_project(user_id)
                for k in ("name", "description", "instructions"):
                    if k in patch:
                        g[k] = patch[k]
                return g
            return project
        allowed = {
            k: v for k, v in patch.items()
            if k in _DEFAULT_FIELDS or k == "is_active"
        }
        if allowed.get("name"):
            await self._ensure_unique_name(allowed["name"], exclude=project_id)
        project.update(allowed)
        project["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_PROJECTS, project_id, project)
        await self._publish(
            EventType.PROJECT_UPDATED,
            "project.updated",
            {"project_id": project_id, "fields": list(allowed)},
        )
        return project

    async def delete_project(
        self, project_id: str, user_id: str | None = None
    ) -> bool:
        """Suppression du projet (delete CoreRecordStore).

        - Le projet "general" est protege (non supprimable).
        - Les conversations ne sont PAS supprimees : elles conservent leur
          `project_id` (orphan-safe).
        """
        if project_id == "general":
            return False
        project = await self.get_project(project_id, user_id)
        if project is None:
            return False
        existed = await self._store.delete(_DOMAIN_PROJECTS, project_id)
        if existed:
            await self._publish(
                EventType.PROJECT_DELETED,
                "project.deleted",
                {"project_id": project_id},
            )
        return existed

    # ── Contexte projet (consomme par le ChatPipeline / API) ───────────

    async def resolve_context(
        self, project_id: str | None
    ) -> dict[str, Any] | None:
        """Resout le contexte d'un projet pour l'execution d'un chat.

        Retourne
        ``{id, name, instructions, agent_id, provider_id, model,
        folder_ids, knowledge_ids, collection_ids, skill_ids, tool_ids}``
        ou ``None`` si aucun projet n'est designe (fail-safe).
        """
        if not project_id:
            return None
        project = await self.get_project(project_id)
        if project is None:
            logger.warning(
                "Project %s not found — ignoring project routing", project_id
            )
            return None
        return {
            "id": project["id"],
            "name": project.get("name", ""),
            "instructions": project.get("instructions", ""),
            "agent_id": project.get("agent_id"),
            "provider_id": project.get("provider_id"),
            "model": project.get("model"),
            "folder_ids": list(project.get("folder_ids") or []),
            "knowledge_ids": list(project.get("knowledge_ids") or []),
            "collection_ids": list(project.get("collection_ids") or []),
            "skill_ids": list(project.get("skill_ids") or []),
            "tool_ids": list(project.get("tool_ids") or []),
        }

    # ── Documents associes au projet (delegation au pipeline Core) ─────

    async def list_project_documents(
        self, project_id: str, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Liste les documents rattaches au projet (scope `project_id`).

        Les documents sont stockés dans `CoreRecordStore` (collection
        `documents`) avec un champ `project_id`.  Le WebUI ne touche jamais
        directement au vector store.
        """
        if project_id == "general":
            return []
        # Securite : verifier l'acces au projet d'abord.
        if (await self.get_project(project_id, user_id)) is None:
            raise ValueError(f"Project not found or access denied: {project_id}")
        all_docs = await self._store.list(_DOMAIN_DOCS)
        return [d for d in all_docs if d.get("project_id") == project_id]

    async def get_project_document(
        self, project_id: str, doc_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Retourne un document du projet ou `None` (404 si hors scope)."""
        if project_id == "general":
            return None
        if (await self.get_project(project_id, user_id)) is None:
            raise ValueError(f"Project not found or access denied: {project_id}")
        doc = await self._store.get(_DOMAIN_DOCS, doc_id)
        if doc is None or doc.get("project_id") != project_id:
            return None
        return doc

    async def record_document_upload(
        self,
        project_id: str,
        file_id: str,
        filename: str,
        mime_type: str,
        size_bytes: int = 0,
        user_id: str | None = None,
        contents: bytes | None = None,
    ) -> dict[str, Any]:
        """Enregistre un document uploade et declenche l'ingestion RAG.

        Le pipeline Core (core/rag) se charge de l'extraction de texte,
        du chunking et de l'embedding. Le WebUI ne parse ni n'embede jamais.

        Args:
            project_id: ID du projet (scope verifie).
            file_id: Chemin ou identifiant du fichier binaire.
            filename: Nom original du fichier.
            mime_type: Type MIME du fichier.
            size_bytes: Taille en octets.
            user_id: Utilisateur courant (scope verifie).
            contents: Contenu binaire du fichier (pour extraction texte).

        Returns:
            Document record cree.
        """
        if project_id != "general":
            if (await self.get_project(project_id, user_id)) is None:
                raise ValueError(f"Project not found or access denied: {project_id}")
        now = _utc_now()
        doc = {
            "id": str(uuid4()),
            "project_id": project_id if project_id != "general" else None,
            "file_id": file_id,
            "filename": filename,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "user_id": user_id,
            "status": "processing",
            "chunk_count": 0,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        await self._store.save(_DOMAIN_DOCS, doc["id"], doc)

        # Ingestion via le pipeline Core (extraction + chunking + embedding)
        if self._ingestion is not None and contents is not None:
            await self._run_ingestion(doc, filename, mime_type, contents)

        return doc

    async def _run_ingestion(
        self,
        doc: dict[str, Any],
        filename: str,
        mime_type: str,
        contents: bytes,
    ) -> None:
        """Execute le pipeline RAG sur un document uploade.

        Met a jour le record avec le statut final (ready/error).
        """
        from core.rag.extractors import extract_text
        try:
            # Extraction de texte (PDF, DOCX) ou decodage UTF-8 (texte brut)
            text = extract_text(contents, filename, mime_type)
            if not text:
                text = contents.decode("utf-8", errors="replace")
            if not text.strip():
                doc["status"] = "error"
                doc["error"] = "No extractable text content"
                doc["updated_at"] = _utc_now()
                await self._store.save(_DOMAIN_DOCS, doc["id"], doc)
                return
            # Ingestion (chunking + embeddings)
            ingested = await self._ingestion.ingest(
                content=text,
                title=filename,
                source=f"project:{doc['project_id']}",
                metadata={
                    "project_id": doc["project_id"],
                    "doc_id": doc["id"],
                    "filename": filename,
                    "mime_type": mime_type,
                },
                document_id=doc["id"],
            )
            doc["status"] = "ready"
            doc["chunk_count"] = len(ingested.chunks)
        except Exception as exc:
            logger.warning("Ingestion failed for %s: %s", filename, exc)
            doc["status"] = "error"
            doc["error"] = str(exc)
        doc["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_DOCS, doc["id"], doc)

    async def update_document_status(
        self,
        doc_id: str,
        status: str,
        *,
        chunk_count: int | None = None,
        error: str | None = None,
    ) -> None:
        """Met à jour le statut d'un document (appelé par le pipeline RAG)."""
        doc = await self._store.get(_DOMAIN_DOCS, doc_id)
        if doc is None:
            return
        doc["status"] = status
        doc["updated_at"] = _utc_now()
        if chunk_count is not None:
            doc["chunk_count"] = chunk_count
        if error is not None:
            doc["error"] = error
        await self._store.save(_DOMAIN_DOCS, doc_id, doc)

    async def delete_project_document(
        self, project_id: str, doc_id: str, user_id: str | None = None
    ) -> bool:
        """Supprime un document du projet (scope vérifié, 403 si hors scope)."""
        try:
            doc = await self.get_project_document(project_id, doc_id, user_id)
        except ValueError:
            # Hors scope → refus silencieux (False, pas d'exception).
            return False
        if doc is None:
            return False
        # Supprimer du vector store si indexé.
        if self._ingestion is not None:
            try:
                await self._ingestion.delete_document(doc_id)
            except Exception:
                logger.warning("Failed to delete document %s from vector store", doc_id)
        return await self._store.delete(_DOMAIN_DOCS, doc_id)

    # ── Internals ───────────────────────────────────────────────────────

    async def _ensure_unique_name(self, name: str, exclude: str | None = None) -> None:
        for project in await self._store.list(_DOMAIN_PROJECTS):
            if project.get("id") == exclude:
                continue
            if project.get("name", "").strip().lower() == name.strip().lower():
                raise ValueError(f"Project name already exists: {name}")

    async def _publish(
        self, event_type: EventType, subject: str, payload: dict[str, Any]
    ) -> None:
        if self._bus is None:
            return
        await self._bus.publish(
            Event(type=event_type, source="projects", payload=payload),
        )


# ── Entite virtuelle : projet "general" (fallback, non persise) ──────────

def _general_project(user_id: str | None = None) -> dict[str, Any]:
    """Snapshot du projet General (Default) — jamais ecrit en DB.

    Represente la conversation sans portee de connaissance.
    """
    now = _utc_now()
    return {
        "id": "general",
        "name": "General (Default)",
        "description": "Conversation scope without Knowledge or specific context.",
        "instructions": "",
        "user_id": user_id or "anonymous",
        "folder_ids": [],
        "knowledge_ids": [],
        "collection_ids": [],
        "skill_ids": [],
        "tool_ids": [],
        "agent_id": None,
        "provider_id": None,
        "model": None,
        "metadata": {},
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


def _new_project(**kw: Any) -> dict[str, Any]:
    now = _utc_now()
    return {
        "id": str(uuid4()),
        "name": kw.get("name", ""),
        "description": kw.get("description", ""),
        "instructions": kw.get("instructions", ""),
        "user_id": kw.get("user_id", "anonymous"),
        "folder_ids": list(kw.get("folder_ids") or []),
        "knowledge_ids": list(kw.get("knowledge_ids") or []),
        "collection_ids": list(kw.get("collection_ids") or []),
        "skill_ids": list(kw.get("skill_ids") or []),
        "tool_ids": list(kw.get("tool_ids") or []),
        "agent_id": kw.get("agent_id"),
        "provider_id": kw.get("provider_id"),
        "model": kw.get("model"),
        "metadata": dict(kw.get("metadata") or {}),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "ProjectManager",
    "_general_project",
]
