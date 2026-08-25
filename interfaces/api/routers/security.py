"""Security router — 2FA (TOTP) enrollment and admin user management.

ETHAN Core owns the logic:
- TOTP secret lifecycle lives in core/auth/totp.py (RFC 6238, stdlib).
- User accounts live in the PostgreSQL ``users`` table (same source of
  truth as POST /auth/login).

The WebUI only renders the enrollment/management flows.
"""

from __future__ import annotations

import logging
from typing import Any

import bcrypt
from fastapi import APIRouter, HTTPException, Request

from core.auth.totp import generate_secret, provisioning_uri, verify_code

logger = logging.getLogger(__name__)

router = APIRouter(tags=["security"])

_pg_pool = None


def set_security_pool(pool: Any) -> None:
    """Inject the asyncpg pool (startup)."""
    global _pg_pool
    _pg_pool = pool


def _require_admin(request: Request) -> str:
    payload = getattr(request.state, "token_payload", {})
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé. Rôle admin requis.")
    return payload.get("sub", "")


async def _fetch_user(username: str) -> dict[str, Any] | None:
    if _pg_pool is None:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    async with _pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, roles, is_active, totp_secret, totp_enabled, created_at"
            " FROM users WHERE username = $1",
            username,
        )
    return dict(row) if row else None


# ══ 2FA — TOTP enrollment ═══════════════════════════════════════════════


@router.get("/auth/2fa/status")
async def twofa_status(request: Request):
    username = request.state.token_payload.get("sub", "")
    user = await _fetch_user(username)
    if user is None:
        raise HTTPException(404, "User not found")
    return {
        "enabled": bool(user["totp_enabled"]),
        "pending": bool(user["totp_secret"]) and not user["totp_enabled"],
    }


@router.post("/auth/2fa/setup")
async def twofa_setup(request: Request):
    """Generate a TOTP secret and return the otpauth:// provisioning URI.

    The secret is stored but NOT enabled until /auth/2fa/confirm validates
    a first code from the authenticator app.
    """
    username = request.state.token_payload.get("sub", "")
    secret = generate_secret()
    async with _pg_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET totp_secret = $1, totp_enabled = false,"
            " updated_at = now() WHERE username = $2",
            secret,
            username,
        )
    uri = provisioning_uri(secret, username)
    return {"enabled": False, "secret": secret, "provisioning_uri": uri}


@router.post("/auth/2fa/confirm")
async def twofa_confirm(request: Request, data: dict[str, Any]):
    """Verify a first TOTP code and activate 2FA."""
    username = request.state.token_payload.get("sub", "")
    code = str(data.get("code", ""))
    user = await _fetch_user(username)
    if user is None or not user["totp_secret"]:
        raise HTTPException(400, "Aucune inscription 2FA en cours. Appelez /auth/2fa/setup.")
    if not verify_code(user["totp_secret"], code):
        raise HTTPException(401, "Code 2FA invalide.")
    async with _pg_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET totp_enabled = true, updated_at = now()"
            " WHERE username = $1",
            username,
        )
    return {"enabled": True, "status": "2FA activée"}


@router.post("/auth/2fa/disable")
async def twofa_disable(request: Request):
    username = request.state.token_payload.get("sub", "")
    async with _pg_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET totp_secret = '', totp_enabled = false,"
            " updated_at = now() WHERE username = $1",
            username,
        )
    return {"enabled": False, "status": "2FA désactivée"}


# ══ Admin user management ═══════════════════════════════════════════════


@router.get("/users")
async def list_users(request: Request):
    _require_admin(request)
    async with _pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, username, roles, is_active, totp_enabled, created_at, updated_at"
            " FROM users ORDER BY created_at ASC"
        )
    return [dict(r) for r in rows]


@router.post("/users")
async def create_user(request: Request, data: dict[str, Any]):
    admin = _require_admin(request)
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    role = str(data.get("role", "user"))
    if not username or len(password) < 6:
        raise HTTPException(422, "username requis et mot de passe ≥ 6 caractères.")
    if role not in ("user", "admin"):
        raise HTTPException(422, "role doit être 'user' ou 'admin'.")
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()
    async with _pg_pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM users WHERE username = $1", username)
        if exists:
            raise HTTPException(409, f"L'utilisateur '{username}' existe déjà.")
        row = await conn.fetchrow(
            "INSERT INTO users (username, password_hash, roles)"
            " VALUES ($1, $2, $3::text[])"
            " RETURNING id, username, roles, is_active, totp_enabled, created_at",
            username,
            password_hash,
            [role],
        )
    logger.info("User '%s' created by admin '%s'", username, admin)
    return dict(row)


@router.put("/users/{username}/activate")
async def set_user_active(request: Request, username: str, data: dict[str, Any]):
    _require_admin(request)
    active = bool(data.get("is_active", True))
    async with _pg_pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE users SET is_active = $1, updated_at = now() WHERE username = $2",
            active,
            username,
        )
    if result.endswith("0"):
        raise HTTPException(404, f"Utilisateur '{username}' introuvable.")
    return {"username": username, "is_active": active}