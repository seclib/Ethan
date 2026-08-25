"""Email inbox API — thin bindings over core.email.manager. RFC-0001."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from core.mailbox.manager import EmailNotConfigured

router = APIRouter(prefix="/v1/email", tags=["email"])

_manager: Any | None = None


def set_email_manager(manager: Any) -> None:
    global _manager
    _manager = manager


def _require() -> Any:
    if _manager is None:
        raise HTTPException(503, "Email manager not initialized")
    return _manager


@router.get("/messages")
async def list_messages(limit: int = 20):
    try:
        return await _require().list_messages(limit=limit)
    except EmailNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/messages/{uid}")
async def get_message(uid: str):
    try:
        return await _require().get_message(uid)
    except EmailNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc