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


# ── Protections cycle de vie ─────────────────────────────────────────────
#
# Un compte administrateur ne doit jamais pouvoir se verrouiller lui-même
# ni verrouiller le système :
#   - pas d'auto-démotion, d'auto-désactivation ni d'auto-suppression ;
#   - le dernier compte admin ne peut être ni démota, désactivé ni supprimé.
# Ces règles vivent ICI (couche API) car elles protègent la table users,
# source de vérité de l'authentification — aucun doublon ailleurs.


async def _count_active_admins(conn: Any) -> int:
    """Nombre de comptes admin actifs (protection « dernier admin »)."""
    return int(
        await conn.fetchval(
            "SELECT count(*) FROM users WHERE 'admin' = ANY(roles) AND is_active"
        )
    )


def _ensure_not_self(request: Request, username: str) -> str:
    """Interdit à un admin d'agir sur son propre compte (destructif)."""
    admin = _require_admin(request)
    if admin == username:
        raise HTTPException(
            403, "Action interdite sur votre propre compte (utilisez un autre admin)."
        )
    return admin


@router.put("/users/{username}")
async def update_user(request: Request, username: str, data: dict[str, Any]):
    """Mise à jour admin d'un utilisateur : rôle, statut et/ou mot de passe.

    Toutes les clés sont optionnelles (PATCH sémantique via PUT). Mot de passe
    haché bcrypt (même logique que POST /users). Protections : auto-modification
    de rôle interdite, dernier admin intouchable.
    """
    admin = _require_admin(request)
    role = data.get("role")
    is_active = data.get("is_active")
    password = data.get("password")

    if role is not None and role not in ("user", "admin"):
        raise HTTPException(422, "role doit être 'user' ou 'admin'.")
    if password is not None and (not isinstance(password, str) or len(password) < 6):
        raise HTTPException(422, "Le mot de passe doit contenir au moins 6 caractères.")
    if is_active is not None and not isinstance(is_active, bool):
        raise HTTPException(422, "is_active doit être un booléen.")
    if role is None and is_active is None and password is None:
        raise HTTPException(422, "Aucune modification fournie (role, is_active, password).")

    # Auto-protection : un admin ne change pas son propre rôle ni ne se
    # désactive (le changement de mot de passe personnel passe par le flux
    # utilisateur authentifié, pas par l'administration).
    if admin == username and (role is not None or is_active is False):
        raise HTTPException(
            403, "Un administrateur ne peut pas modifier son propre rôle ou se désactiver."
        )

    sets: list[str] = []
    args: list[Any] = []
    if role is not None:
        sets.append(f"roles = ${len(args) + 1}::text[]")
        args.append([role])
    if is_active is not None:
        sets.append(f"is_active = ${len(args) + 1}")
        args.append(is_active)
    if password is not None:
        sets.append(f"password_hash = ${len(args) + 1}")
        args.append(bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode())

    async with _pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            f"SELECT id, username, roles, is_active FROM users WHERE username = $1",
            username,
        )
        if row is None:
            raise HTTPException(404, f"Utilisateur '{username}' introuvable.")

        # Protection « dernier admin » : démotion ou désactivation d'un
        # compte admin alors qu'il est le seul garant du système.
        demotes = role == "user" and "admin" in row["roles"]
        deactivates = is_active is False and row["is_active"]
        if (demotes or deactivates) and "admin" in row["roles"]:
            if await _count_active_admins(conn) <= 1:
                raise HTTPException(
                    409, "Impossible : ce compte est le dernier administrateur actif."
                )

        updated = await conn.fetchrow(
            f"UPDATE users SET {', '.join(sets)}, updated_at = now()"
            f" WHERE username = ${len(args) + 1}"
            " RETURNING id, username, roles, is_active, totp_enabled, updated_at",
            *args,
            username,
        )
    logger.info("User '%s' updated by admin '%s' (keys=%s)", username, admin, sorted(data.keys()))
    return dict(updated)


@router.delete("/users/{username}")
async def delete_user(request: Request, username: str):
    """Suppression définitive d'un compte utilisateur.

    Protections : auto-suppression interdite ; le dernier admin actif ne
    peut être supprimé.
    """
    admin = _ensure_not_self(request, username)
    async with _pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, roles, is_active FROM users WHERE username = $1", username
        )
        if row is None:
            raise HTTPException(404, f"Utilisateur '{username}' introuvable.")
        if "admin" in row["roles"] and row["is_active"]:
            if await _count_active_admins(conn) <= 1:
                raise HTTPException(
                    409, "Impossible : ce compte est le dernier administrateur actif."
                )
        await conn.execute("DELETE FROM users WHERE username = $1", username)
    logger.info("User '%s' deleted by admin '%s'", username, admin)
    return {"status": "deleted", "username": username}


# ══ ETHAN Security — policies / capabilities / audit (lecture seule) ════


@router.get("/security/status")
async def security_status_endpoint(request: Request):
    """Résumé lecture seule du système de sécurité ETHAN.

    Représentation pour la WebUI (pas un panneau d'administration) :
    - politiques chargées (par niveau et effet)
    - capabilities actives (par sujet)
    - statistiques d'audit

    Logique dans ``core/security/status.py`` ; aucune donnée sensible ni
    secret n'est exposée ; aucun accès en mutation.
    """
    _require_admin(request)
    from core.security.status import security_status

    return security_status()