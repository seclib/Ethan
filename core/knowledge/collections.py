"""Knowledge collections — Core-owned grouping of RAG documents.

ETHAN Core owns knowledge collections.  A collection groups RAG documents so
the WebUI can offer Open-WebUI-style selection ("use this collection in the
chat") without owning any data or logic.

The collection itself is a lightweight record; the documents live in the
RAGPipeline catalogue.  Retrieval is delegated to the RAG pipeline with a
collection filter.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.rag.pipeline import RAGPipeline
from core.rag.strategies import normalize_strategy, validate_strategy
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_COLLECTIONS = "knowledge-collections"

# Permissions de partage possibles sur une collection (pattern Open-WebUI :
# grants par utilisateur ou par groupe, read ou write).
_GRANT_PERMISSIONS = ("read", "write")


def _grant_covers(grant: dict[str, Any], permission: str) -> bool:
    """True si un grant couvre la permission demandée (write ⊇ read)."""
    granted = grant.get("permission", "read")
    if permission == "write":
        return granted == "write"
    return granted in ("read", "write")


class KnowledgeCollectionManager:
    """Own knowledge collections and their document membership."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
        rag: RAGPipeline | None = None,
        groups: Any | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()
        self._rag = rag or RAGPipeline()
        # GroupManager Core (optionnel) — nécessaire pour résoudre les
        # access_grants de type groupe lors du contrôle d'accès.
        self._groups = groups

    # ── CRUD collections ────────────────────────────────────────────────

    async def create_collection(
        self,
        name: str,
        description: str = "",
        user_id: str = "anonymous",
        metadata: dict[str, Any] | None = None,
        parent_id: str | None = None,
        icon: str | None = None,
        order: int = 0,
        retrieval_strategy: str | None = None,
    ) -> dict[str, Any]:
        """Create a knowledge collection (optionally nested under a parent).

        ``parent_id`` lets users organize collections as a free-form tree of
        folders: no default hierarchy is seeded, roots are collections without
        a parent.

        ``retrieval_strategy`` (``auto``, ``keyword``, ``semantic``,
        ``hybrid``) surcharge la stratégie RAG globale pour cette collection.
        ``None`` → stratégie globale (``rag-config.strategy``, défaut ``auto``).
        """
        normalized = name.strip()
        if not normalized:
            raise ValueError("Collection name must not be empty")
        if parent_id is not None:
            await self._require_collection(parent_id)
        strategy = (
            validate_strategy(retrieval_strategy)
            if retrieval_strategy is not None
            else None
        )
        collection = {
            "id": str(uuid4()),
            "name": normalized,
            "description": description,
            "user_id": user_id,
            "parent_id": parent_id,
            "icon": icon,
            "order": order,
            "document_ids": [],
            "access_grants": [],
            "metadata": dict(metadata or {}),
            "retrieval_strategy": strategy,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        await self._store.save(_DOMAIN_COLLECTIONS, collection["id"], collection)
        await self._publish(EventType.KNOWLEDGE_CREATED, "knowledge.collection.created", {"collection": collection})
        return collection

    async def get_collection(self, collection_id: str) -> dict[str, Any] | None:
        """Retrieve a collection by id."""
        return await self._store.get(_DOMAIN_COLLECTIONS, collection_id)

    async def list_collections(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List collections, optionally filtered by owner."""
        collections = await self._store.list(_DOMAIN_COLLECTIONS)
        if user_id is not None:
            collections = [c for c in collections if c.get("user_id") == user_id]
        return collections

    async def update_collection(
        self, collection_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update collection metadata.

        Supports ``parent_id`` (re-parenting with cycle detection), ``icon``,
        ``order``, ``retrieval_strategy`` (validated) in addition to
        name/description/metadata.
        """
        collection = await self.get_collection(collection_id)
        if collection is None:
            return None
        for key in ("name", "description", "metadata", "icon", "order"):
            if key in data:
                collection[key] = data[key]
        if "retrieval_strategy" in data:
            value = data["retrieval_strategy"]
            collection["retrieval_strategy"] = (
                validate_strategy(value) if value is not None else None
            )
        if "parent_id" in data:
            new_parent = data["parent_id"]
            await self._validate_parent(collection_id, new_parent)
            collection["parent_id"] = new_parent
        collection["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_COLLECTIONS, collection_id, collection)
        await self._publish(EventType.KNOWLEDGE_UPDATED, "knowledge.collection.updated", {"collection": collection})
        return collection

    async def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection (documents remain in the RAG catalogue).

        Child collections are re-parented to the deleted collection's own
        parent so the tree never keeps dangling ``parent_id`` references.
        """
        collection = await self.get_collection(collection_id)
        if collection is None:
            return False
        grandparent = collection.get("parent_id")
        for child in await self.list_collections():
            if child.get("parent_id") == collection_id:
                child["parent_id"] = grandparent
                child["updated_at"] = _utc_now()
                await self._store.save(_DOMAIN_COLLECTIONS, child["id"], child)
        await self._store.delete(_DOMAIN_COLLECTIONS, collection_id)
        await self._publish(EventType.KNOWLEDGE_DELETED, "knowledge.collection.deleted", {"collection_id": collection_id})
        return True

    # ── Hierarchy (user-organizable folders) ────────────────────────────

    async def move_collection(self, collection_id: str, new_parent_id: str | None) -> dict[str, Any]:
        """Move a collection under another one (or to the root with ``None``).

        Raises ``ValueError`` for unknown collections and for moves that
        would create a cycle (a collection cannot become its own descendant).
        """
        collection = await self._require_collection(collection_id)
        await self._validate_parent(collection_id, new_parent_id)
        collection["parent_id"] = new_parent_id
        collection["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_COLLECTIONS, collection_id, collection)
        await self._publish(EventType.KNOWLEDGE_UPDATED, "knowledge.collection.moved", {
            "collection_id": collection_id,
            "parent_id": new_parent_id,
        })
        return collection

    async def list_tree(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List collections as an ordered tree (parents before children).

        Roots come first (sorted by ``order`` then ``name``); each node
        carries a ``children`` list built recursively.  Collections whose
        parent is missing or foreign are surfaced at the root so no record
        ever disappears from the listing.
        """
        collections = await self.list_collections(user_id=user_id)
        by_id = {c["id"]: c for c in collections}
        children_map: dict[str | None, list[dict[str, Any]]] = {}
        for c in collections:
            parent = c.get("parent_id")
            if parent is not None and parent not in by_id:
                parent = None  # dangling / cross-owner parent → surface at root
            children_map.setdefault(parent, []).append(c)

        def _sort(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return sorted(nodes, key=lambda c: (c.get("order", 0), c.get("name", "")))

        def _build(parent_key: str | None) -> list[dict[str, Any]]:
            nodes = []
            for child in _sort(children_map.get(parent_key, [])):
                child["children"] = _build(child["id"])
                nodes.append(child)
            return nodes

        return _build(None)

    # ── Access control (access_grants, pattern Open-WebUI) ──────────────

    async def share_collection(
        self, collection_id: str, grants: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Remplace la liste des access_grants d'une collection.

        Chaque grant : ``{"user_id": "..."}`` ou ``{"group_id": "..."}`` avec
        ``permission: "read" | "write"``.  Le owner et les admins gardent
        toujours l'accès complet (non représentés dans les grants).
        """
        collection = await self._require_collection(collection_id)
        validated: list[dict[str, Any]] = []
        for grant in grants or []:
            permission = str(grant.get("permission", "read")).lower()
            if permission not in _GRANT_PERMISSIONS:
                raise ValueError(
                    f"Grant permission invalide : {permission!r} (read ou write attendus)"
                )
            user_id = grant.get("user_id")
            group_id = grant.get("group_id")
            if not user_id and not group_id:
                raise ValueError("Chaque grant requiert user_id ou group_id")
            entry: dict[str, Any] = {"permission": permission}
            if user_id:
                entry["user_id"] = str(user_id)
            if group_id:
                entry["group_id"] = str(group_id)
            validated.append(entry)

        collection["access_grants"] = validated
        collection["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_COLLECTIONS, collection_id, collection)
        await self._publish(EventType.KNOWLEDGE_UPDATED, "knowledge.collection.shared", {
            "collection_id": collection_id,
            "grants_count": len(validated),
        })
        return collection

    async def list_accessible(
        self, user_id: str, *, is_admin: bool = False
    ) -> list[dict[str, Any]]:
        """Liste les collections accessibles par un utilisateur.

        Owner toujours, admin toujours, sinon grant utilisateur ou grant de
        groupe dont l'utilisateur est membre.
        """
        collections = await self.list_collections()
        if is_admin:
            return collections
        user_groups = await self._user_group_ids(user_id)
        return [
            c for c in collections if self._grants_allow(c, user_id, user_groups, "read")
        ]

    def require_read(
        self,
        collection: dict[str, Any],
        user_id: str | None,
        *,
        is_admin: bool = False,
    ) -> None:
        """Vérifie l'accès en lecture (lève ``PermissionError`` sinon).

        ``user_id=None`` = contexte interne (tests, appels in-process) :
        comportement legacy sans enforcement (les routes HTTP sont de toute
        façon derrière auth_middleware).
        """
        if user_id is None:
            return
        self._require_access(collection, user_id, is_admin, "read")

    def require_write(
        self,
        collection: dict[str, Any],
        user_id: str | None,
        *,
        is_admin: bool = False,
    ) -> None:
        """Vérifie l'accès en écriture (lève ``PermissionError`` sinon)."""
        if user_id is None:
            return
        self._require_access(collection, user_id, is_admin, "write")

    def _require_access(
        self,
        collection: dict[str, Any],
        user_id: str,
        is_admin: bool,
        permission: str,
    ) -> None:
        if is_admin:
            return
        if collection.get("user_id") == user_id:
            return
        grants = collection.get("access_grants", [])
        if not grants:
            raise PermissionError(
                f"Accès refusé : la collection {collection.get('name', collection.get('id'))} "
                "n'est pas partagée avec cet utilisateur"
            )
        # Résolution des groupes nécessaire seulement s'il existe des
        # grants de groupe — la résolution est async et gérée par l'appelant
        # via check_access ; ici on accepte si un grant utilisateur suffit.
        for grant in grants:
            if grant.get("user_id") == user_id and _grant_covers(grant, permission):
                return
        raise PermissionError(
            f"Accès {permission} refusé sur la collection "
            f"{collection.get('name', collection.get('id'))}"
        )

    async def check_access(
        self,
        collection: dict[str, Any],
        user_id: str,
        *,
        is_admin: bool = False,
        permission: str = "read",
    ) -> bool:
        """Contrôle d'accès complet (owner, admin, grants user et groupes)."""
        if is_admin or collection.get("user_id") == user_id:
            return True
        user_groups = await self._user_group_ids(user_id)
        return self._grants_allow(collection, user_id, user_groups, permission)

    def _grants_allow(
        self,
        collection: dict[str, Any],
        user_id: str,
        user_groups: set[str],
        permission: str,
    ) -> bool:
        """True si un grant (utilisateur ou groupe) accorde ``permission``.

        Un grant ``write`` accorde aussi la lecture.
        """
        for grant in collection.get("access_grants", []):
            granted = grant.get("permission", "read")
            if permission == "write" and granted != "write":
                continue  # write exige un grant write
            if grant.get("user_id") and grant["user_id"] == user_id:
                return True
            if grant.get("group_id") and grant["group_id"] in user_groups:
                return True
        return False

    async def _user_group_ids(self, user_id: str) -> set[str]:
        """Groupes dont l'utilisateur est membre (via le GroupManager Core)."""
        if self._groups is None:
            return set()
        group_ids: set[str] = set()
        try:
            for group in await self._groups.list():
                members = await self._groups.list_members(group["id"])
                if user_id in members:
                    group_ids.add(group["id"])
        except Exception as exc:
            logger.warning("Impossible de résoudre les groupes de %s : %s", user_id, exc)
        return group_ids


    # ── Document membership ─────────────────────────────────────────────

    async def add_document(self, collection_id: str, document_id: str) -> dict[str, Any] | None:
        """Attach an existing RAG document to a collection."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            return None
        document = await self._rag.get_document(document_id)
        if document is None:
            raise ValueError(f"RAG document {document_id} not found")
        if document_id not in collection["document_ids"]:
            collection["document_ids"].append(document_id)
            collection["updated_at"] = _utc_now()
            await self._store.save(_DOMAIN_COLLECTIONS, collection_id, collection)
        return collection

    async def remove_document(self, collection_id: str, document_id: str) -> dict[str, Any] | None:
        """Detach a document from a collection."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            return None
        if document_id in collection["document_ids"]:
            collection["document_ids"].remove(document_id)
            collection["updated_at"] = _utc_now()
            await self._store.save(_DOMAIN_COLLECTIONS, collection_id, collection)
        return collection

    async def list_documents(self, collection_id: str) -> list[dict[str, Any]]:
        """List the RAG documents attached to a collection."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            return []
        documents = []
        for document_id in collection.get("document_ids", []):
            document = await self._rag.get_document(document_id)
            if document is not None:
                documents.append(document.to_dict())
        return documents

    # ── Retrieval scoped to a collection ────────────────────────────────

    def _global_strategy(self) -> str:
        """Stratégie RAG globale (config persistée du moteur)."""
        global_cfg = self._rag.get_config().get("strategy")
        return normalize_strategy(global_cfg)

    async def get_effective_strategy(self, collection_id: str) -> str:
        """Stratégie effective d'une collection.

        Résolution : ``retrieval_strategy`` de la collection si définie,
        sinon stratégie globale du moteur RAG (``rag-config``), sinon ``auto``.
        """
        collection = await self.get_collection(collection_id)
        if collection is None:
            raise ValueError(f"Collection {collection_id} not found")
        per_collection = collection.get("retrieval_strategy")
        if per_collection:
            return normalize_strategy(per_collection)
        return self._global_strategy()

    async def retrieve(
        self,
        query: str,
        collection_id: str,
        *,
        top_k: int | None = None,
        strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve chunks restricted to one collection's documents.

        ``strategy`` (``auto``, ``keyword``, ``semantic``, ``hybrid``)
        surcharge explicitement la stratégie de la collection pour cet appel.
        ``None`` → stratégie de la collection (ou globale si non définie).
        """
        collection = await self.get_collection(collection_id)
        if collection is None:
            raise ValueError(f"Collection {collection_id} not found")
        effective = strategy or await self.get_effective_strategy(collection_id)
        return await self.retrieve_multi(
            query, [collection_id], top_k=top_k, strategy=effective
        )

    async def retrieve_multi(
        self,
        query: str,
        collection_ids: list[str],
        *,
        top_k: int | None = None,
        strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve chunks scoped to several collections in a single RAG pass.

        Every requested collection must exist.  The allowed document set is
        the union of the collections' ``document_ids`` so the retrieval runs
        once (instead of N retrieves + post-filtering).

        ``strategy`` s'applique à l'ensemble du passage multi-collections (la
        stratégie par collection n'est pas consultée ici : le passage est un
        seul appel moteur). ``None`` → stratégie globale du moteur.
        """
        if not collection_ids:
            return []
        allowed: set[str] = set()
        for collection_id in collection_ids:
            collection = await self.get_collection(collection_id)
            if collection is None:
                raise ValueError(f"Collection {collection_id} not found")
            allowed.update(collection.get("document_ids", []))
        effective = strategy or self._global_strategy()
        # Passe document_ids à la source : évite un retrieve global + post-filtre.
        chunks = await self._rag.retrieve(
            query,
            top_k=top_k,
            document_ids=list(allowed) or None,
            strategy=effective,
        )
        return [
            {
                "chunk": item.chunk.to_dict(),
                "score": item.score,
                "document_title": item.document_title,
                "document_source": item.document_source,
            }
            for item in chunks
        ]

    async def build_context_multi(
        self,
        query: str,
        collection_ids: list[str],
        *,
        top_k: int | None = None,
        strategy: str | None = None,
    ) -> str:
        """Build a bounded RAG context scoped to several collections."""
        results = await self.retrieve_multi(
            query, collection_ids, top_k=top_k, strategy=strategy
        )
        if not results:
            return ""
        parts = []
        for i, item in enumerate(results, start=1):
            title = item.get("document_title") or "Document"
            source = item.get("document_source") or ""
            chunk = item.get("chunk", {})
            content = chunk.get("content", "")
            parts.append(f"[{i}] {title} ({source})\n{content}")
        return "\n\n".join(parts)

    async def reindex_collection(self, collection_id: str) -> dict[str, Any]:
        """Ré-indexe les documents d'une collection (rechunk + ré-embed).

        Utile quand le modèle d'embedding change : les documents source (dont
        le ``content`` est persisté) sont re-découpés et re-embeddés via le
        pipeline Core, puis réattachés à la même collection.

        Returns:
            ``{"collection_id", "reindexed", "documents"}``.
        """
        collection = await self._require_collection(collection_id)
        docs = await self.list_documents(collection_id)
        reindexed = 0
        errors: list[dict[str, str]] = []
        for document in docs:
            try:
                title = document.get("title") or document.get("source") or "Document"
                source = document.get("source", "")
                content = document.get("content", "") or ""
                metadata = document.get("metadata", {})
                if not content.strip():
                    continue
                await self._rag.delete_document(document["id"])
                new_doc = await self._rag.ingest(
                    content, title=title, source=source, metadata=metadata
                )
                # Remplace l'id dans la collection (leaf document).
                ids = list(collection.get("document_ids", []))
                if document["id"] in ids:
                    ids[ids.index(document["id"])] = new_doc.id
                    collection["document_ids"] = ids
                reindexed += 1
            except Exception as exc:  # noqa: BLE001 - une panne ne bloque pas la collection
                logger.warning("Reindex failed for %s: %s", document.get("id"), exc)
                errors.append({"document_id": document.get("id", ""), "error": str(exc)})
        if collection.get("document_ids") is not None:
            await self._persist_collection(collection)
        return {
            "collection_id": collection_id,
            "reindexed": reindexed,
            "documents": len(docs),
            "errors": errors,
        }

    async def _persist_collection(self, collection: dict[str, Any]) -> None:
        """Persiste une collection modifiée en place (core store partagé)."""
        collection["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_COLLECTIONS, collection["id"], collection)

    async def build_context(
        self,
        query: str,
        collection_id: str,
        *,
        top_k: int | None = None,
        strategy: str | None = None,
    ) -> str:
        """Build a bounded RAG context scoped to several collections."""
        results = await self.retrieve(
            query, collection_id, top_k=top_k, strategy=strategy
        )
        if not results:
            return ""
        parts = []
        for i, item in enumerate(results, start=1):
            title = item.get("document_title") or "Document"
            source = item.get("document_source") or ""
            chunk = item.get("chunk", {})
            content = chunk.get("content", "")
            parts.append(f"[{i}] {title} ({source})\n{content}")
        return "\n\n".join(parts)

    async def _require_collection(self, collection_id: str) -> dict[str, Any]:
        """Return the collection or raise ``ValueError`` if unknown."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            raise ValueError(f"Collection {collection_id} not found")
        return collection

    async def _validate_parent(self, collection_id: str, parent_id: str | None) -> None:
        """Validate a re-parenting target (existence, no self, no cycle)."""
        if parent_id is None:
            return
        if parent_id == collection_id:
            raise ValueError("A collection cannot be its own parent")
        await self._require_collection(parent_id)
        descendants = await self._descendant_ids(collection_id)
        if parent_id in descendants:
            raise ValueError(
                f"Cannot move collection {collection_id} under its own descendant {parent_id}"
            )

    async def _descendant_ids(self, collection_id: str) -> set[str]:
        """Return every collection id below ``collection_id`` in the tree."""
        by_parent: dict[str | None, list[str]] = {}
        for c in await self.list_collections():
            by_parent.setdefault(c.get("parent_id"), []).append(c["id"])
        descendants: set[str] = set()
        frontier = list(by_parent.get(collection_id, []))
        while frontier:
            current = frontier.pop()
            if current in descendants:
                continue  # defensive: corrupted store must not loop forever
            descendants.add(current)
            frontier.extend(by_parent.get(current, []))
        return descendants

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="knowledge-collections", payload=payload))


def _utc_now() -> str:
    from datetime import timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["KnowledgeCollectionManager"]
