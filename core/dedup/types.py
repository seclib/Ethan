"""Duplicate detection types — Core-owned domain.

Unified vocabulary for the duplicate detector across Library (FileStore),
Projects (ProjectManager), Knowledge (KnowledgeManager + collections) and
the RAG pipeline.  The WebUI only renders :class:`DuplicateReport` and sends
intents through the API — all classification logic lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class DuplicateCategory(str, Enum):
    """How two (or more) scanned items relate to each other.

    Values are stable strings so reports serialize cleanly to JSON.
    """

    EXACT_DUPLICATE = "exact_duplicate"          # same hash + same name
    PROBABLE_DUPLICATE = "probable_duplicate"    # same hash, different name
    SAME_NAME_DIFFERENT_CONTENT = "same_name_different_content"
    DIFFERENT_VERSION = "different_version"      # same name/location lineage
    SAME_CONTENT_DIFFERENT_LOCATION = "same_content_different_location"
    ALREADY_INDEXED = "already_indexed"          # file present + RAG doc exists
    ORPHAN_DOCUMENT = "orphan_document"          # RAG doc without source file
    BROKEN_REFERENCE = "broken_reference"        # points to a missing source


class DuplicateAction(str, Enum):
    """Resolution intent the user may request on a duplicate group."""

    KEEP_BOTH = "keep_both"
    REPLACE_WITH_NEWEST = "replace_with_newest"
    KEEP_PRIMARY = "keep_primary"
    MOVE_TO_ARCHIVE = "move_to_archive"
    DELETE_AFTER_CONFIRM = "delete_after_confirm"
    REPAIR_REFERENCE = "repair_reference"
    MERGE_ASSOCIATIONS = "merge_associations"


class ItemDomain(str, Enum):
    """Origin domain of a scanned item."""

    FILE = "file"
    PROJECT_DOCUMENT = "project_document"
    KNOWLEDGE_NODE = "knowledge_node"
    RAG_DOCUMENT = "rag_document"


@dataclass
class ScannedItem:
    """A single item normalised from any source domain for comparison."""

    id: str
    domain: ItemDomain
    name: str
    size: int = 0
    content_type: str = ""
    content_hash: str = ""                       # SHA-256 (empty if unreadable)
    created_at: str = ""
    updated_at: str = ""
    locations: list[str] = field(default_factory=list)  # storage paths / uris
    project_ids: list[str] = field(default_factory=list)
    collection_ids: list[str] = field(default_factory=list)
    folder_ids: list[str] = field(default_factory=list)
    rag_document_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "domain": self.domain.value,
            "name": self.name,
            "size": self.size,
            "content_type": self.content_type,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "locations": self.locations,
            "project_ids": self.project_ids,
            "collection_ids": self.collection_ids,
            "folder_ids": self.folder_ids,
            "rag_document_id": self.rag_document_id,
            "metadata": self.metadata,
        }


@dataclass
class DuplicateGroup:
    """Two or more :class:`ScannedItem` considered related."""

    group_id: str
    category: DuplicateCategory
    items: list[ScannedItem]
    confidence: float = 1.0                       # 0.0 – 1.0
    recommended_action: DuplicateAction = DuplicateAction.KEEP_BOTH

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "category": self.category.value,
            "items": [item.to_dict() for item in self.items],
            "confidence": self.confidence,
            "recommended_action": self.recommended_action.value,
        }


@dataclass
class DuplicateReport:
    """Full result of a scan — the value returned by the API."""

    scan_id: str
    timestamp: str
    total_scanned: int = 0
    total_files: int = 0
    total_project_documents: int = 0
    total_knowledge_nodes: int = 0
    total_rag_documents: int = 0
    groups: list[DuplicateGroup] = field(default_factory=list)
    orphans: list[ScannedItem] = field(default_factory=list)
    broken_references: list[ScannedItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "timestamp": self.timestamp,
            "total_scanned": self.total_scanned,
            "total_files": self.total_files,
            "total_project_documents": self.total_project_documents,
            "total_knowledge_nodes": self.total_knowledge_nodes,
            "total_rag_documents": self.total_rag_documents,
            "groups": [g.to_dict() for g in self.groups],
            "orphans": [o.to_dict() for o in self.orphans],
            "broken_references": [b.to_dict() for b in self.broken_references],
        }


def _new_scan_id() -> str:
    return str(uuid4())


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()
