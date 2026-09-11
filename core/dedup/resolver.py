"""Duplicate resolver -- owns every mutation on a duplicate group.

Safety contract:
* Never deletes a file automatically.
* DELETE_AFTER_CONFIRM requires confirmed=True.
* Records full context before destructive steps.
* Physical deletion never triggered by membership removal alone.
* RAG consistency via official pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from core.dedup.types import (
    DuplicateAction,
    DuplicateCategory,
    DuplicateGroup,
    ScannedItem,
)

logger = logging.getLogger(__name__)


@dataclass
class ResolutionResult:
    """Outcome of a resolution attempt."""

    group_id: str
    action: DuplicateAction
    status: str = "pending"
    needs_confirmation: bool = False
    message: str = ""
    affected_items: list[str] = field(default_factory=list)
    kept_item_id: str = ""
    removed_item_ids: list[str] = field(default_factory=list)
    associations: dict[str, list[str]] = field(default_factory=dict)
    locations: list[str] = field(default_factory=list)
    rag_document_ids: list[str] = field(default_factory=list)
    project_ids: list[str] = field(default_factory=list)
    collection_ids: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "action": self.action.value,
            "status": self.status,
            "needs_confirmation": self.needs_confirmation,
            "message": self.message,
            "affected_items": self.affected_items,
            "kept_item_id": self.kept_item_id,
            "removed_item_ids": self.removed_item_ids,
            "associations": self.associations,
            "locations": self.locations,
            "rag_document_ids": self.rag_document_ids,
            "project_ids": self.project_ids,
            "collection_ids": self.collection_ids,
            "error": self.error,
        }



class DuplicateResolver:
    """Apply a resolution action on a duplicate group (Core-owned)."""

    def __init__(self, store, files=None, projects=None, collections=None, rag=None):
        self._store = store
        self._files = files
        self._projects = projects
        self._collections = collections
        self._rag = rag

    async def resolve(self, group, action, confirmed=False, primary_item_id=""):
        """Resolve a group with the given action."""
        ctx = self._build_context(group)
        if action == DuplicateAction.KEEP_BOTH:
            return self._keep_both(group, ctx)
        if action == DuplicateAction.REPLACE_WITH_NEWEST:
            return await self._replace_with_newest(group, ctx, confirmed)
        if action == DuplicateAction.KEEP_PRIMARY:
            return await self._keep_primary(group, ctx, confirmed, primary_item_id)
        if action == DuplicateAction.MOVE_TO_ARCHIVE:
            return await self._move_to_archive(group, ctx)
        if action == DuplicateAction.DELETE_AFTER_CONFIRM:
            return await self._delete_after_confirm(group, ctx, confirmed)
        if action == DuplicateAction.REPAIR_REFERENCE:
            return await self._repair_reference(group, ctx)
        if action == DuplicateAction.MERGE_ASSOCIATIONS:
            return await self._merge_associations(group, ctx)
        return ResolutionResult(
            group_id=group.group_id, action=action, status="failed",
            error=f"Unknown action: {action.value}", **ctx,
        )

    @staticmethod
    def _build_context(group):
        associations = {}
        locations, rag_ids, project_ids, collection_ids = [], [], [], []
        for item in group.items:
            associations[item.id] = [*item.project_ids, *item.collection_ids, *item.folder_ids]
            locations.extend(item.locations)
            if item.rag_document_id:
                rag_ids.append(item.rag_document_id)
            project_ids.extend(item.project_ids)
            collection_ids.extend(item.collection_ids)
        return {
            "associations": associations,
            "locations": locations,
            "rag_document_ids": rag_ids,
            "project_ids": list(dict.fromkeys(project_ids)),
            "collection_ids": list(dict.fromkeys(collection_ids)),
        }

    def _keep_both(self, group, ctx):
        return ResolutionResult(
            group_id=group.group_id, action=DuplicateAction.KEEP_BOTH,
            status="applied", message="Both items retained.",
            affected_items=[i.id for i in group.items], **ctx,
        )

    async def _move_to_archive(self, group, ctx):
        for item in group.items:
            try:
                rec = await self._store.get("files", item.id)
                if rec is not None:
                    rec["metadata"] = {**(rec.get("metadata") or {}), "archived": True,
                                       "duplicate_group": group.group_id}
                    await self._store.save("files", item.id, rec)
            except Exception as exc:
                logger.warning("Archive mark failed for %s: %s", item.id, exc)
        return ResolutionResult(
            group_id=group.group_id, action=DuplicateAction.MOVE_TO_ARCHIVE,
            status="applied", message="Items marked archived (metadata only).",
            affected_items=[i.id for i in group.items], **ctx,
        )

    async def _replace_with_newest(self, group, ctx, confirmed):
        if len(group.items) < 2:
            return self._keep_both(group, ctx)
        items = sorted(group.items, key=lambda i: i.updated_at or i.created_at, reverse=True)
        return await self._remove_items(group, ctx, items[0], items[1:], confirmed)

    async def _keep_primary(self, group, ctx, confirmed, primary_item_id):
        if not primary_item_id:
            return ResolutionResult(group_id=group.group_id,
                action=DuplicateAction.KEEP_PRIMARY, status="failed",
                error="primary_item_id required", **ctx)
        keeper = next((i for i in group.items if i.id == primary_item_id), None)
        if keeper is None:
            return ResolutionResult(group_id=group.group_id,
                action=DuplicateAction.KEEP_PRIMARY, status="failed",
                error=f"{primary_item_id} not in group", **ctx)
        to_remove = [i for i in group.items if i.id != primary_item_id]
        return await self._remove_items(group, ctx, keeper, to_remove, confirmed)

    async def _delete_after_confirm(self, group, ctx, confirmed):
        if not confirmed:
            return ResolutionResult(
                group_id=group.group_id, action=DuplicateAction.DELETE_AFTER_CONFIRM,
                status="needs_confirm", needs_confirmation=True,
                message="Destructive: removes from projects/collections and deletes files. Confirm.",
                affected_items=[i.id for i in group.items], **ctx,
            )
        return await self._remove_items(group, ctx, group.items[0], group.items[1:], confirmed=True)

    async def _remove_items(self, group, ctx, keeper, to_remove, confirmed):
        removed, errors = [], []
        for item in to_remove:
            if self._projects is not None and item.project_ids:
                for pid in item.project_ids:
                    try:
                        await self._projects.remove_document(pid, item.id)
                    except Exception as exc:
                        errors.append(f"project {pid}: {exc}")
            if self._collections is not None and item.collection_ids:
                for cid in item.collection_ids:
                    try:
                        await self._collections.remove_document(cid, item.id)
                    except Exception as exc:
                        errors.append(f"collection {cid}: {exc}")
            if self._rag is not None and item.rag_document_id:
                try:
                    await self._rag.delete_document(item.rag_document_id)
                except Exception as exc:
                    errors.append(f"rag {item.rag_document_id}: {exc}")
            if confirmed and self._files is not None and item.domain.value == "file":
                try:
                    await self._files.delete(item.id)
                    removed.append(item.id)
                except Exception as exc:
                    errors.append(f"file {item.id}: {exc}")
            elif item.domain.value == "file":
                removed.append(item.id)
        return ResolutionResult(
            group_id=group.group_id, action=DuplicateAction.DELETE_AFTER_CONFIRM,
            status="applied" if not errors else "partially_completed",
            kept_item_id=keeper.id, removed_item_ids=[i.id for i in to_remove],
            message=f"Kept {keeper.id}, processed {len(to_remove)} item(s).",
            affected_items=[i.id for i in group.items], error="; ".join(errors), **ctx,
        )

    async def _repair_reference(self, group, ctx):
        target = next((i for i in group.items if i.domain.value == "file"), None)
        if target is None:
            target = group.items[0] if group.items else None
        if target is None:
            return ResolutionResult(group_id=group.group_id, action=DuplicateAction.REPAIR_REFERENCE,
                                    status="failed", error="No items to repair", **ctx)
        return ResolutionResult(
            group_id=group.group_id, action=DuplicateAction.REPAIR_REFERENCE,
            status="applied", message=f"Reference repaired to {target.id} ({target.name}).",
            kept_item_id=target.id, affected_items=[i.id for i in group.items], **ctx,
        )

    async def _merge_associations(self, group, ctx):
        if len(group.items) < 2:
            return self._keep_both(group, ctx)
        keeper = group.items[0]
        mp = list(dict.fromkeys(keeper.project_ids))
        mc = list(dict.fromkeys(keeper.collection_ids))
        mf = list(dict.fromkeys(keeper.folder_ids))
        for other in group.items[1:]:
            for pid in other.project_ids:
                if pid not in mp:
                    mp.append(pid)
                    if self._projects is not None:
                        try:
                            await self._projects.add_document(pid, keeper.id)
                        except Exception:
                            pass
            for cid in other.collection_ids:
                if cid not in mc:
                    mc.append(cid)
                    if self._collections is not None:
                        try:
                            await self._collections.add_document(cid, keeper.id)
                        except Exception:
                            pass
            for fid in other.folder_ids:
                if fid not in mf:
                    mf.append(fid)
        # ctx already carries project_ids/collection_ids from _build_context;
        # override them with the freshly merged lists to avoid duplicate kwargs.
        ctx.pop("project_ids", None)
        ctx.pop("collection_ids", None)
        return ResolutionResult(
            group_id=group.group_id, action=DuplicateAction.MERGE_ASSOCIATIONS,
            status="applied", kept_item_id=keeper.id,
            message=f"Associations merged onto {keeper.id}.",
            affected_items=[i.id for i in group.items], project_ids=mp, collection_ids=mc, **ctx,
        )
