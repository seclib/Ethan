"""Duplicate detector -- scans all Core domains and classifies candidates.

The detector is deliberately **read-only**: it never mutates state.  It
normalises files, project documents, knowledge nodes and RAG documents into
:class:`~core.dedup.types.ScannedItem`, then buckets them by name and by
content hash to build :class:`~core.dedup.types.DuplicateGroup` entries.

No file is deleted here -- the :class:`DuplicateResolver` owns mutations.
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from typing import Any

from core.dedup.types import (
    DuplicateCategory,
    DuplicateGroup,
    DuplicateReport,
    ItemDomain,
    ScannedItem,
    _new_scan_id,
    _utc_now_iso,
)

logger = logging.getLogger(__name__)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class DuplicateDetector:
    """Scan FileStore, ProjectManager, Knowledge and RAG, then classify.

    Args:
        store: shared CoreRecordStore (in-memory fallback is enough for scans).
        files: optional FileStore instance.
        projects: optional ProjectManager instance.
        knowledge: optional KnowledgeManager instance.
        collections: optional KnowledgeCollectionManager instance.
        rag: optional RAGPipeline instance.
    """

    def __init__(
        self,
        store: Any,
        files: Any | None = None,
        projects: Any | None = None,
        knowledge: Any | None = None,
        collections: Any | None = None,
        rag: Any | None = None,
    ) -> None:
        self._store = store
        self._files = files
        self._projects = projects
        self._knowledge = knowledge
        self._collections = collections
        self._rag = rag

    async def scan(self, user_id: str | None = None) -> DuplicateReport:
        """Build a full duplicate report across every available domain."""
        scan_id = _new_scan_id()
        timestamp = _utc_now_iso()
        files = await self._scan_files(user_id)
        project_docs = await self._scan_project_documents()
        knowledge_nodes = await self._scan_knowledge()
        rag_docs = await self._scan_rag()
        all_items: list[ScannedItem] = [*files, *project_docs, *knowledge_nodes, *rag_docs]
        groups: list[DuplicateGroup] = []
        groups.extend(self._group_by_exact_duplicate(files, rag_docs))
        groups.extend(self._group_by_name(files, rag_docs))
        groups.extend(self._group_same_content_different_location(files))
        groups.extend(self._group_already_indexed(files, rag_docs))
        orphans = self._find_orphans(rag_docs, files)
        broken = await self._find_broken_references()
        return DuplicateReport(
            scan_id=scan_id,
            timestamp=timestamp,
            total_scanned=len(all_items),
            total_files=len(files),
            total_project_documents=len(project_docs),
            total_knowledge_nodes=len(knowledge_nodes),
            total_rag_documents=len(rag_docs),
            groups=groups,
            orphans=orphans,
            broken_references=broken,
        )

    async def _scan_files(self, user_id: str | None) -> list[ScannedItem]:
        if self._files is None:
            return []
        try:
            records = await self._files.list(user_id=user_id)
        except Exception as exc:
            logger.warning("FileStore scan failed: %s", exc)
            return []
        return [self._file_to_item(rec) for rec in records]

    @staticmethod
    def _file_to_item(rec: dict[str, Any]) -> ScannedItem:
        return ScannedItem(
            id=rec.get("id", ""),
            domain=ItemDomain.FILE,
            name=rec.get("filename", "") or rec.get("name", ""),
            size=int(rec.get("size") or 0),
            content_type=rec.get("content_type", ""),
            created_at=rec.get("created_at", ""),
            updated_at=rec.get("updated_at", "") or rec.get("created_at", ""),
            locations=[rec.get("storage_path", "")] if rec.get("storage_path") else [],
            metadata=dict(rec.get("metadata") or {}),
        )

    async def _scan_project_documents(self) -> list[ScannedItem]:
        if self._projects is None:
            return []
        items: list[ScannedItem] = []
        try:
            for project in await self._projects.list_projects():
                pid = project.get("id", "")
                for doc in await self._projects.list_documents(pid):
                    items.append(ScannedItem(
                        id=doc.get("id", ""),
                        domain=ItemDomain.PROJECT_DOCUMENT,
                        name=doc.get("title", "") or doc.get("filename", ""),
                        size=int(doc.get("size") or 0),
                        content_type=doc.get("content_type", ""),
                        created_at=doc.get("created_at", ""),
                        updated_at=doc.get("updated_at", ""),
                        project_ids=[pid],
                        metadata=dict(doc.get("metadata") or {}),
                    ))
        except Exception as exc:
            logger.warning("Project scan failed: %s", exc)
        return items

    async def _scan_knowledge(self) -> list[ScannedItem]:
        if self._knowledge is None:
            return []
        items: list[ScannedItem] = []
        try:
            for node in await self._knowledge.list():
                items.append(ScannedItem(
                    id=node.id,
                    domain=ItemDomain.KNOWLEDGE_NODE,
                    name=node.label,
                    content_type=node.node_type.value,
                    created_at=node.created_at.isoformat(),
                    updated_at=node.updated_at.isoformat(),
                    metadata={"source": node.source, "connections": len(node.connections)},
                ))
        except Exception as exc:
            logger.warning("Knowledge scan failed: %s", exc)
        return items

    async def _scan_rag(self) -> list[ScannedItem]:
        if self._rag is None:
            return []
        items: list[ScannedItem] = []
        try:
            for doc in await self._rag.list_documents():
                items.append(ScannedItem(
                    id=doc.id,
                    domain=ItemDomain.RAG_DOCUMENT,
                    name=doc.title,
                    created_at=doc.metadata.get("created_at", ""),
                    updated_at=doc.metadata.get("updated_at", ""),
                    rag_document_id=doc.id,
                    metadata={"source": doc.source, "chunks": len(doc.chunks)},
                ))
        except Exception as exc:
            logger.warning("RAG scan failed: %s", exc)
        return items

    def _group_by_exact_duplicate(self, files, rag_docs) -> list[DuplicateGroup]:
        groups: list[DuplicateGroup] = []
        by_name: dict[str, list[ScannedItem]] = defaultdict(list)
        for f in files:
            if f.name:
                by_name[f.name].append(f)
        for name, bucket in by_name.items():
            if len(bucket) < 2:
                continue
            by_hash: dict[str, list[ScannedItem]] = defaultdict(list)
            for item in bucket:
                if item.content_hash:
                    by_hash[item.content_hash].append(item)
            for h, hbucket in by_hash.items():
                if len(hbucket) >= 2:
                    groups.append(DuplicateGroup(
                        group_id=f"exact:{name}:{h[:12]}",
                        category=DuplicateCategory.EXACT_DUPLICATE,
                        items=hbucket,
                        confidence=1.0,
                    ))
        return groups

    def _group_by_name(self, files, rag_docs) -> list[DuplicateGroup]:
        groups: list[DuplicateGroup] = []
        by_name: dict[str, list[ScannedItem]] = defaultdict(list)
        for item in files:
            if item.name:
                by_name[item.name].append(item)
        for r in rag_docs:
            if r.name:
                by_name[r.name].append(r)
        for name, bucket in by_name.items():
            if len(bucket) < 2:
                continue
            hashes = {i.content_hash for i in bucket if i.content_hash}
            if len(hashes) > 1:
                groups.append(DuplicateGroup(
                    group_id=f"name:{name}",
                    category=DuplicateCategory.SAME_NAME_DIFFERENT_CONTENT,
                    items=bucket,
                    confidence=0.7,
                ))
        return groups

    def _group_same_content_different_location(self, files) -> list[DuplicateGroup]:
        groups: list[DuplicateGroup] = []
        by_hash: dict[str, list[ScannedItem]] = defaultdict(list)
        for f in files:
            if f.content_hash and f.locations:
                by_hash[f.content_hash].append(f)
        for h, bucket in by_hash.items():
            locations = {loc for item in bucket for loc in item.locations if loc}
            if len(bucket) >= 2 and len(locations) > 1:
                groups.append(DuplicateGroup(
                    group_id=f"loc:{h[:12]}",
                    category=DuplicateCategory.SAME_CONTENT_DIFFERENT_LOCATION,
                    items=bucket,
                    confidence=0.9,
                ))
        return groups

    def _group_already_indexed(self, files, rag_docs) -> list[DuplicateGroup]:
        groups: list[DuplicateGroup] = []
        rag_names = {r.name for r in rag_docs if r.name}
        for f in files:
            if f.name and f.name in rag_names:
                matching = [r for r in rag_docs if r.name == f.name]
                groups.append(DuplicateGroup(
                    group_id=f"indexed:{f.id}",
                    category=DuplicateCategory.ALREADY_INDEXED,
                    items=[f, *matching],
                    confidence=0.8,
                ))
        return groups

    @staticmethod
    def _find_orphans(rag_docs, files) -> list[ScannedItem]:
        file_names = {f.name for f in files if f.name}
        return [r for r in rag_docs
                if r.name and r.name not in file_names
                and r.domain == ItemDomain.RAG_DOCUMENT]

    async def _find_broken_references(self) -> list[ScannedItem]:
        broken: list[ScannedItem] = []
        if self._projects is None:
            return broken
        try:
            for project in await self._projects.list_projects():
                for doc in await self._projects.list_documents(project.get("id", "")):
                    if doc.get("status") == "missing_source" or doc.get("broken"):
                        broken.append(ScannedItem(
                            id=doc.get("id", ""),
                            domain=ItemDomain.PROJECT_DOCUMENT,
                            name=doc.get("title", ""),
                            project_ids=[project.get("id", "")],
                            metadata={"broken": True},
                        ))
        except Exception as exc:
            logger.warning("Broken-reference scan failed: %s", exc)
        return broken

    async def compute_file_hash(self, file_id: str) -> str:
        """SHA-256 of a file\u2019s bytes (in-Core content or storage_path)."""
        if self._files is None:
            return ""
        try:
            downloaded = await self._files.download(file_id)
            if downloaded is not None:
                data, _meta = downloaded
                return _sha256(data)
        except Exception as exc:
            logger.warning("Hash computation failed for %s: %s", file_id, exc)
        return ""
