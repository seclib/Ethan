"""Terminal API — passerelle mince vers le `TerminalService` du Core.

Aucune logique métier ici : création, E/S, signaux et nettoyage appartiennent
à `core/terminal/service.py`. Ce routeur ne fait que

1. exiger l'authentification ETHAN (JWT) et la permission `EXECUTE`,
2. traduire les `TerminalError` du Core en statuts HTTP,
3. pomper le PTY et le relier au WebSocket.

Le WebSocket est authentifié EXPLICITEMENT : `auth_middleware` n'est qu'un
middleware HTTP et ne traverse donc pas les WS. Sans ce contrôle, le terminal
serait un shell non authentifié — le contrôle est fail-closed (on refuse la
connexion avant `accept`).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging

from core.auth import Permission
from core.terminal import (
    TerminalError,
    TerminalNotFound,
    TerminalSecurityError,
    TerminalService,
    TerminalState,
)
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from interfaces.api.auth import current_user_id, rbac, require_permission, verify_token_string
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/terminal", tags=["terminal"])

#: Service injecté au démarrage de l'API (singleton, workers=1).
_service: TerminalService | None = None


def set_terminal_service(service: TerminalService | None) -> None:
    """Injecte le TerminalService Core (tests / lifespan)."""
    global _service
    _service = service


def get_terminal_service() -> TerminalService:
    if _service is None:
        raise HTTPException(503, "Terminal service not initialized")
    return _service


def _http_error(exc: TerminalError) -> HTTPException:
    """Traduit une erreur Core en statut HTTP (sans fuite interne)."""
    if isinstance(exc, TerminalSecurityError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, TerminalNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if exc.code == "TERMINAL-CLOSED":
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Erreur interne du terminal")


# ── Schémas ───────────────────────────────────────────────────────────────────


class CreateSession(BaseModel):
    """Requête de création — cwd borné par le Core, jamais arbitraire."""

    cwd: str | None = Field(default=None, max_length=512)
    cols: int = Field(default=80, ge=1, le=500)
    rows: int = Field(default=24, ge=1, le=500)


class SendInput(BaseModel):
    """stdin : données brutes. Un Ctrl+C est `\x03` (géré par le PTY)."""

    data: str = Field(default="", max_length=8192)


class ResizeSession(BaseModel):
    cols: int = Field(default=80, ge=1, le=500)
    rows: int = Field(default=24, ge=1, le=500)


# ── REST ──────────────────────────────────────────────────────────────────────


@router.post("/sessions", status_code=201)
async def create_session(
    body: CreateSession,
    request: Request,
    _: bool = Depends(require_permission(Permission.EXECUTE)),
):
    """Ouvre une session PTY réelle (permission EXECUTE)."""
    user = current_user_id(request) or "user"
    try:
        session = get_terminal_service().create(
            user=user, cwd=body.cwd, cols=body.cols, rows=body.rows
        )
    except TerminalError as exc:
        raise _http_error(exc) from exc
    return session.to_dict()


@router.get("/sessions")
async def list_sessions(_: bool = Depends(require_permission(Permission.READ))):
    """Sessions du service (les mortes sont purgées avant réponse)."""
    return {"sessions": [s.to_dict() for s in get_terminal_service().list_sessions()]}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, _: bool = Depends(require_permission(Permission.READ))):
    """Une session — l'état vient du Core, jamais recalculé ici."""
    try:
        return get_terminal_service().get(session_id).to_dict()
    except TerminalError as exc:
        raise _http_error(exc) from exc


@router.post("/sessions/{session_id}/input")
async def send_input(
    session_id: str,
    body: SendInput,
    _: bool = Depends(require_permission(Permission.EXECUTE)),
):
    """stdin : écrit dans le PTY (Ctrl+C = `\x03`)."""
    try:
        get_terminal_service().write(session_id, body.data)
    except TerminalError as exc:
        raise _http_error(exc) from exc
    return {"status": "sent"}


@router.post("/sessions/{session_id}/resize")
async def resize_session(
    session_id: str,
    body: ResizeSession,
    _: bool = Depends(require_permission(Permission.EXECUTE)),
):
    """Resize du PTY (ioctl TIOCSWINSZ)."""
    try:
        get_terminal_service().resize(session_id, cols=body.cols, rows=body.rows)
    except TerminalError as exc:
        raise _http_error(exc) from exc
    return {"status": "resized"}


@router.post("/sessions/{session_id}/interrupt")
async def interrupt_session(
    session_id: str, _: bool = Depends(require_permission(Permission.EXECUTE))
):
    """Ctrl+C explicite : SIGINT au groupe de processus."""
    try:
        get_terminal_service().interrupt(session_id)
    except TerminalError as exc:
        raise _http_error(exc) from exc
    return {"status": "interrupted"}


@router.delete("/sessions/{session_id}")
async def close_session(session_id: str, _: bool = Depends(require_permission(Permission.EXECUTE))):
    """Termine la session et nettoie le processus (aucune fuite)."""
    try:
        return get_terminal_service().terminate(session_id).to_dict()
    except TerminalError as exc:
        raise _http_error(exc) from exc


# ── WebSocket ────────────────────────────────────────────────────────────────


def _extract_ws_token(websocket: WebSocket) -> str | None:
    """Token JWT depuis la query string, le cookie `ethan_token` ou l'en-tête."""
    token = websocket.query_params.get("token")
    if token:
        return token
    cookie = websocket.cookies.get("ethan_token")
    if cookie:
        return cookie
    header = websocket.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header.split(" ", 1)[1]
    return None


async def _authorize_ws(websocket: WebSocket) -> str | None:
    """Authentifie + autorise un WebSocket. Retourne l'user ou None.

    `auth_middleware` est HTTP-only : sans cette vérification explicite, le
    terminal serait un shell accessible sans JWT.
    """
    token = _extract_ws_token(websocket)
    if not token:
        await websocket.close(code=4401, reason="authentication required")
        return None
    try:
        payload = await verify_token_string(token)
    except HTTPException:
        await websocket.close(code=4401, reason="invalid token")
        return None
    role = payload.get("role")
    if not role or not rbac.has_permission(role, Permission.EXECUTE):
        await websocket.close(code=4403, reason="permission execute required")
        return None
    return payload.get("sub", "user")


@router.websocket("/ws")
async def terminal_ws(websocket: WebSocket, session_id: str | None = None):
    """Terminal interactif : PTY réel ↔ WebSocket (stdin/stdout/stderr).

    Client → serveur (JSON) :
        {"type":"input","data":"..."}    — stdin (Ctrl+C = "\\x03")
        {"type":"resize","cols":N,"rows":N}
        {"type":"interrupt"}              — Ctrl+C explicite
        {"type":"ping"}                   — keepalive → {"type":"pong"}

    Serveur → client (JSON) :
        {"type":"session", ...}           — état initial (Core)
        {"type":"output","data":"..."}    — octets PTY décodés (ANSI conservés)
        {"type":"exit","exit_code":N}
        {"type":"error","code":...,"detail":"..."}
    """
    user = await _authorize_ws(websocket)
    if user is None:
        return

    service = get_terminal_service()

    # Session existante (reconnexion) ou nouvelle session.
    if session_id:
        try:
            session = service.get(session_id)
        except TerminalError:
            await websocket.close(code=4404, reason="unknown session")
            return
    else:
        try:
            session = service.create(user=user)
        except TerminalError:
            await websocket.close(code=4403, reason="session refused")
            return

    await websocket.accept()
    await websocket.send_json({"type": "session", **session.to_dict()})

    async def pump_output() -> None:
        """Relie le PTY → WebSocket en continu (streaming, ANSI brut)."""
        while True:
            chunk = await asyncio.to_thread(service.read, session.id, 65536, 0.1)
            if chunk:
                await websocket.send_json(
                    {"type": "output", "data": chunk.decode("utf-8", errors="replace")}
                )
                continue
            current = service._sessions.get(session.id)
            if current is None or current.state != TerminalState.RUNNING:
                break

        exit_code = None
        with contextlib.suppress(Exception):
            exit_code = service.reap(session.id, blocking=False)
        with contextlib.suppress(Exception):
            await websocket.send_json({"type": "exit", "exit_code": exit_code})
        with contextlib.suppress(Exception):
            await websocket.close(code=1000)

    async def read_client() -> None:
        """Lit les messages client et les applique au PTY."""
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            kind = msg.get("type")
            try:
                if kind == "input":
                    service.write(session.id, msg.get("data", ""))
                elif kind == "resize":
                    service.resize(
                        session.id,
                        cols=int(msg.get("cols", 80)),
                        rows=int(msg.get("rows", 24)),
                    )
                elif kind == "interrupt":
                    service.interrupt(session.id)
                elif kind == "ping":
                    await websocket.send_json({"type": "pong"})
            except TerminalError as exc:
                with contextlib.suppress(Exception):
                    await websocket.send_json(
                        {"type": "error", "code": exc.code, "detail": str(exc)}
                    )

    pump = asyncio.create_task(pump_output())
    reader = asyncio.create_task(read_client())

    try:
        done, pending = await asyncio.wait({pump, reader}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
    except WebSocketDisconnect:
        logger.info("terminal: WS déconnecté (session=%s)", session.id)
    except Exception as exc:  # noqa: BLE001 — une WS ne doit jamais tuer l'API
        logger.warning("terminal: erreur WS: %s", exc)
    finally:
        # Déconnexion ≠ mort du terminal : le processus reste vivant et suivi
        # par le service (reconnexion possible via `?session_id=`). On ne
        # termine donc PAS la session ici — sinon fermer l'onglet tuerait le
        # shell en cours d'installation.
        pump.cancel()
        reader.cancel()


__all__ = ["get_terminal_service", "router", "set_terminal_service"]
