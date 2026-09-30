"""Core-owned password reset — forgot-password tokens and single-use reset.

ETHAN Core owns the reset-token lifecycle.  The API layer is a thin gateway:
it maps HTTP verbs onto this manager and must never embed the token or
account logic itself (Première Loi d'ETHAN).

Security invariants (section « secret » des règles ETHAN) :
- le token brut n'est JAMAIS stocké : seul son SHA-256 est persisté ;
- le token brut n'est JAMAIS journalisé ni embarqué dans un événement ;
- les tokens sont à usage unique et expirent (défaut : 15 minutes) ;
- une nouvelle demande révoque les tokens précédents du même compte ;
- la couche API ne doit pas révéler si un compte existe (anti-énumération).
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from typing import Any

from core.ethan_types.event import Event, EventType

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 15 * 60
MIN_PASSWORD_LENGTH = 6


def _hash_token(raw_token: str) -> str:
    """Empreinte du token : seul le hash vit en base."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class PasswordResetError(Exception):
    """Erreur métier de réinitialisation (token invalide, expiré, etc.)."""


class PasswordResetManager:
    """Cycle de vie des tokens « mot de passe oublié ».

    Args:
        pg_pool: pool asyncpg injecté au démarrage (optionnel — un stockage
            en mémoire est utilisé en fallback pour le développement
            autonome et les tests, selon le même pattern que CoreRecordStore).
        event_bus: bus d'événements optionnel (in-memory ou NATS).
        ttl_seconds: durée de vie des tokens.
    """

    def __init__(
        self,
        pg_pool: Any | None = None,
        event_bus: Any | None = None,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        self._pg = pg_pool
        self._bus = event_bus
        env_ttl = os.getenv("ETHAN_PASSWORD_RESET_TTL")
        try:
            self._ttl = int(
                ttl_seconds if ttl_seconds is not None else (env_ttl or DEFAULT_TTL_SECONDS)
            )
        except ValueError:
            self._ttl = DEFAULT_TTL_SECONDS
        # Fallback mémoire : {token_hash: {"username", "expires_at", "used"}}
        self._memory: dict[str, dict[str, Any]] = {}

    # ── demande de réinitialisation ──────────────────────────────────────

    async def request_reset(self, username: str) -> str | None:
        """Crée un token de réinitialisation pour ``username``.

        Retourne le token **brut** (à transmettre au canal de notification),
        ou ``None`` si l'utilisateur n'existe pas / est inactif.  La couche
        appelante ne doit PAS différencier les deux cas dans sa réponse
        HTTP (anti-énumération).
        """
        username = str(username or "").strip()
        if not username:
            return None
        if self._pg is not None:
            async with self._pg.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT username FROM users WHERE username = $1 AND is_active",
                    username,
                )
                if user is None:
                    return None
                # Une nouvelle demande révoque les tokens précédents.
                await conn.execute(
                    "DELETE FROM password_reset_tokens WHERE username = $1",
                    username,
                )

        raw_token = secrets.token_urlsafe(32)
        token_hash = _hash_token(raw_token)
        if self._pg is not None:
            async with self._pg.acquire() as conn:
                await conn.execute(
                    "INSERT INTO password_reset_tokens (token_hash, username, expires_at)"
                    " VALUES ($1, $2, now() + make_interval(secs => $3))",
                    token_hash,
                    username,
                    self._ttl,
                )
        else:
            import time

            # Une nouvelle demande révoque les tokens précédents du compte
            # (cohérence avec la branche PostgreSQL).
            self._memory = {h: e for h, e in self._memory.items() if e["username"] != username}
            self._memory[token_hash] = {
                "username": username,
                "expires_at": time.monotonic() + self._ttl,
                "used": False,
            }

        # Événement SANS le token (aucun secret dans les événements).
        await self._publish(
            EventType.USER_PASSWORD_RESET_REQUESTED,
            {"username": username, "ttl_seconds": self._ttl},
        )
        return raw_token

    # ── validation du token ──────────────────────────────────────────────

    async def peek_username(self, raw_token: str) -> str | None:
        """Retourne le username associé au token si valide (sans le consommer)."""
        username, expires_at, used = await self._fetch(raw_token)
        if username is None or used:
            return None
        if expires_at is not None:
            import time

            if time.monotonic() >= expires_at:
                return None
        return username

    async def reset_password(self, raw_token: str, new_password: str) -> dict[str, Any]:
        """Réinitialise le mot de passe avec le token fourni (usage unique)."""
        if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
            raise PasswordResetError(
                f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
            )
        import bcrypt

        token_hash = _hash_token(str(raw_token or ""))
        username: str | None = None

        if self._pg is not None:
            async with self._pg.acquire() as conn:
                async with conn.transaction():
                    # Consommation atomique : UPDATE … RETURNING garantit
                    # l'usage unique même en cas de requêtes concurrentes.
                    row = await conn.fetchrow(
                        "UPDATE password_reset_tokens"
                        " SET used = true, consumed_at = now()"
                        " WHERE token_hash = $1 AND used = false AND expires_at > now()"
                        " RETURNING username",
                        token_hash,
                    )
                    if row is None:
                        raise PasswordResetError("Token invalide ou expiré.")
                    username = row["username"]
                    await conn.execute(
                        "UPDATE users SET password_hash = $1, updated_at = now()"
                        " WHERE username = $2",
                        bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode(),
                        username,
                    )
        else:
            entry = self._memory.get(token_hash)
            if entry is None or entry["used"]:
                raise PasswordResetError("Token invalide ou expiré.")
            import time

            if time.monotonic() >= entry["expires_at"]:
                raise PasswordResetError("Token invalide ou expiré.")
            entry["used"] = True
            username = entry["username"]

        await self._publish(
            EventType.USER_PASSWORD_RESET_COMPLETED,
            {"username": username},
        )
        logger.info("Password reset completed for user '%s'", username)
        return {"status": "ok", "username": username}

    async def purge_expired(self) -> int:
        """Purge les tokens expirés (maintenance / cron)."""
        if self._pg is None:
            import time

            before = len(self._memory)
            self._memory = {
                h: e for h, e in self._memory.items() if time.monotonic() < e["expires_at"]
            }
            return before - len(self._memory)
        async with self._pg.acquire() as conn:
            n = await conn.fetchval(
                "WITH d AS (DELETE FROM password_reset_tokens WHERE expires_at <= now()"
                " RETURNING 1) SELECT count(*) FROM d"
            )
        return int(n or 0)

    # ── internes ─────────────────────────────────────────────────────────

    async def _fetch(self, raw_token: str) -> tuple[str | None, float | None, bool]:
        """Lit le record token : (username, expires_at monotonic|None, used)."""
        token_hash = _hash_token(str(raw_token or ""))
        if self._pg is not None:
            async with self._pg.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT username, expires_at, used FROM password_reset_tokens"
                    " WHERE token_hash = $1",
                    token_hash,
                )
            if row is None:
                return None, None, True
            import time

            remaining = max(
                0.0, (row["expires_at"].timestamp() - time.time()) if row["expires_at"] else 0
            )
            return row["username"], time.monotonic() + remaining, bool(row["used"])
        entry = self._memory.get(token_hash)
        if entry is None:
            return None, None, True
        return entry["username"], entry["expires_at"], entry["used"]

    async def _publish(self, event_type: EventType, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        try:
            await self._bus.publish(
                event_type.value,
                Event(type=event_type, source="core.auth.password_reset", payload=payload),
            )
        except Exception:  # noqa: BLE001 — l'event ne doit jamais casser le flux
            logger.exception("password reset: publication d'événement échouée")


# ── injection du pool (même pattern que security.py) ──────────────────────

_manager: PasswordResetManager | None = None


def set_password_reset_pool(pg_pool: Any) -> None:
    """Injecte le pool asyncpg (appelé au démarrage de l'API)."""
    global _manager
    _manager = PasswordResetManager(pg_pool=pg_pool)


def get_password_reset_manager() -> PasswordResetManager:
    """Retourne le manager injecté, ou une instance mémoire de secours."""
    global _manager
    if _manager is None:
        _manager = PasswordResetManager()
    return _manager
