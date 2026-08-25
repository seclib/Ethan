"""Domain routers — chats, files, users, groups, channels, notes.

These routers expose Core-owned domain managers through HTTP.  They are
thin gateways: all business logic lives in core/state and core/auth.
"""

from __future__ import annotations

import io
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from core.auth import Permission
from interfaces.api.auth import require_permission
from core.auth.groups import GroupManager
from core.auth.users import UserManager
from core.state.chats import ChatStore
from core.state.files import FileStore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["domains"])

# ── Global instances — injected at startup ──────────────────────────────
_chats: ChatStore | None = None
_files: FileStore | None = None
_users: UserManager | None = None
_groups: GroupManager | None = None


def set_domain_managers(
    chats: ChatStore | None = None,
    files: FileStore | None = None,
    users: UserManager | None = None,
    groups: GroupManager | None = None,
) -> None:
    """Inject Core domain managers during API startup."""
    global _chats, _files, _users, _groups
    _chats = chats
    _files = files
    _users = users
    _groups = groups


def _require_chats() -> ChatStore:
    if _chats is None:
        raise HTTPException(503, "Chat store not initialized")
    return _chats


def _require_files() -> FileStore:
    if _files is None:
        raise HTTPException(503, "File store not initialized")
    return _files


def _require_users() -> UserManager:
    if _users is None:
        raise HTTPException(503, "User manager not initialized")
    return _users


def get_user_manager() -> UserManager:
    """Public accessor for the Core UserManager.

    Unlike ``_require_users`` this is exposed so the Open WebUI-compatible
    adapter router (interfaces/api/routers/openwebui.py) can resolve the
    Core user manager without owning any user logic itself (AGENTS.md).
    """
    if _users is None:
        raise HTTPException(503, "User manager not initialized")
    return _users


def _require_groups() -> GroupManager:
    if _groups is None:
        raise HTTPException(503, "Group manager not initialized")
    return _groups


# ═══════════════════════════════════════════════════════════════════════
# CHATS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/chats")
async def list_chats(
    user_id: str | None = None,
    folder_id: str | None = None,
    archived: bool | None = None,
):
    return await _require_chats().list_chats(user_id=user_id, folder_id=folder_id, archived=archived)


@router.post("/chats", dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_chat(data: dict[str, Any]):
    try:
        return await _require_chats().create_chat(
            title=data.get("title", ""),
            user_id=data.get("user_id", "anonymous"),
            folder_id=data.get("folder_id"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/chats/{chat_id}")
async def get_chat(chat_id: str):
    chat = await _require_chats().get_chat(chat_id)
    if chat is None:
        raise HTTPException(404, f"Chat {chat_id} not found")
    return chat


@router.put("/chats/{chat_id}", dependencies=[Depends(require_permission(Permission.WRITE))])
async def update_chat(chat_id: str, data: dict[str, Any]):
    chat = await _require_chats().update_chat(chat_id, data)
    if chat is None:
        raise HTTPException(404, f"Chat {chat_id} not found")
    return chat


@router.delete("/chats/{chat_id}", dependencies=[Depends(require_permission(Permission.WRITE))])
async def delete_chat(chat_id: str):
    if not await _require_chats().delete_chat(chat_id):
        raise HTTPException(404, f"Chat {chat_id} not found")
    return {"status": "deleted"}


@router.get("/chats/{chat_id}/messages")
async def list_chat_messages(chat_id: str):
    return await _require_chats().list_messages(chat_id)


@router.post("/chats/{chat_id}/messages", dependencies=[Depends(require_permission(Permission.WRITE))])
async def add_chat_message(chat_id: str, data: dict[str, Any]):
    try:
        return await _require_chats().add_message(
            chat_id,
            role=data.get("role", "user"),
            content=data.get("content", ""),
            user_id=data.get("user_id", "anonymous"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/chats/{chat_id}/share", dependencies=[Depends(require_permission(Permission.WRITE))])
async def share_chat(chat_id: str):
    chat = await _require_chats().share_chat(chat_id)
    if chat is None:
        raise HTTPException(404, f"Chat {chat_id} not found")
    return chat


# ═══════════════════════════════════════════════════════════════════════
# FILES
# ═══════════════════════════════════════════════════════════════════════

@router.get("/files")
async def list_files(user_id: str | None = None):
    return await _require_files().list(user_id=user_id)


@router.post("/files", dependencies=[Depends(require_permission(Permission.WRITE))])
async def register_file(data: dict[str, Any]):
    try:
        return await _require_files().register(
            filename=data.get("filename", ""),
            content_type=data.get("content_type", "application/octet-stream"),
            size=int(data.get("size", 0)),
            user_id=data.get("user_id", "anonymous"),
            storage_path=data.get("storage_path"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/files/upload", dependencies=[Depends(require_permission(Permission.WRITE))])
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(default="anonymous"),
):
    """Upload a binary file and persist it in Core.

    The bytes are stored in the Core FileStore so they can later be
    downloaded or ingested into RAG by ETHAN Core (not the WebUI).
    """
    content = await file.read()
    try:
        return await _require_files().register(
            filename=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            size=len(content),
            user_id=user_id,
            content=content,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/files/{file_id}")
async def get_file(file_id: str):
    file = await _require_files().get(file_id)
    if file is None:
        raise HTTPException(404, f"File {file_id} not found")
    return file


@router.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """Stream the binary content of a Core-owned file."""
    result = await _require_files().download(file_id)
    if result is None:
        raise HTTPException(404, f"File {file_id} not found")
    content, record = result
    filename = record.get("filename", "download.bin")
    content_type = record.get("content_type", "application/octet-stream")
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/files/{file_id}", dependencies=[Depends(require_permission(Permission.WRITE))])
async def delete_file(file_id: str):
    if not await _require_files().delete(file_id):
        raise HTTPException(404, f"File {file_id} not found")
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/users", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def list_users():
    return await _require_users().list()


@router.post("/users", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def create_user(data: dict[str, Any]):
    try:
        return await _require_users().create(
            username=data.get("username", ""),
            email=data.get("email", ""),
            role=data.get("role", "user"),
            password_hash=data.get("password_hash", ""),
            profile=data.get("profile"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await _require_users().get(user_id)
    if user is None:
        raise HTTPException(404, f"User {user_id} not found")
    return user


@router.put("/users/{user_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def update_user(user_id: str, data: dict[str, Any]):
    user = await _require_users().update(user_id, data)
    if user is None:
        raise HTTPException(404, f"User {user_id} not found")
    return user


@router.delete("/users/{user_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def delete_user(user_id: str):
    if not await _require_users().delete(user_id):
        raise HTTPException(404, f"User {user_id} not found")
    return {"status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════
# GROUPS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/groups", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def list_groups():
    return await _require_groups().list()


@router.post("/groups", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def create_group(data: dict[str, Any]):
    try:
        return await _require_groups().create(
            name=data.get("name", ""),
            description=data.get("description", ""),
            permissions=data.get("permissions"),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/groups/{group_id}")
async def get_group(group_id: str):
    group = await _require_groups().get(group_id)
    if group is None:
        raise HTTPException(404, f"Group {group_id} not found")
    return group


@router.put("/groups/{group_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def update_group(group_id: str, data: dict[str, Any]):
    group = await _require_groups().update(group_id, data)
    if group is None:
        raise HTTPException(404, f"Group {group_id} not found")
    return group


@router.delete("/groups/{group_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def delete_group(group_id: str):
    if not await _require_groups().delete(group_id):
        raise HTTPException(404, f"Group {group_id} not found")
    return {"status": "deleted"}


@router.post("/groups/{group_id}/members/{user_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def add_group_member(group_id: str, user_id: str):
    group = await _require_groups().add_member(group_id, user_id)
    if group is None:
        raise HTTPException(404, f"Group {group_id} not found")
    return group


@router.delete("/groups/{group_id}/members/{user_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def remove_group_member(group_id: str, user_id: str):
    group = await _require_groups().remove_member(group_id, user_id)
    if group is None:
        raise HTTPException(404, f"Group {group_id} not found")
    return group