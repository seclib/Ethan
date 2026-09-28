"""Tests du gestionnaire de réinitialisation de mot de passe (Core).

Le cycle de vie des tokens vit dans ``core/auth/password_reset.py``.
Ces tests valident les invariants de sécurité en mode fallback mémoire
(sans PostgreSQL) : hashage, TTL, usage unique et événements sans secret.
"""

from __future__ import annotations

import asyncio
import hashlib

import pytest
from core.auth.password_reset import (
    MIN_PASSWORD_LENGTH,
    PasswordResetError,
    PasswordResetManager,
)
from core.ethan_types.event import EventType


class RecordingBus:
    """Bus minimal qui enregistre les événements publiés."""

    def __init__(self) -> None:
        self.published: list[tuple[str, object]] = []

    async def publish(self, subject: str, event) -> None:
        self.published.append((subject, event))


def _run(coro):
    return asyncio.run(coro)


def test_reset_flow_happy_path():
    bus = RecordingBus()
    m = PasswordResetManager(event_bus=bus, ttl_seconds=60)

    async def flow():
        token = await m.request_reset("alice")
        assert token and len(token) >= 32
        assert await m.peek_username(token) == "alice"
        result = await m.reset_password(token, "NouveauMotDePasse1")
        assert result == {"status": "ok", "username": "alice"}
        return token

    token = _run(flow())

    # Le token n'est plus valide après consommation.
    assert _run(m.peek_username(token)) is None
    with pytest.raises(PasswordResetError):
        _run(m.reset_password(token, "AutreMotDePasse2"))

    # Les événements ne contiennent JAMAIS le token brut.
    subjects = [s for s, _ in bus.published]
    assert EventType.USER_PASSWORD_RESET_REQUESTED.value in subjects
    assert EventType.USER_PASSWORD_RESET_COMPLETED.value in subjects
    for _, event in bus.published:
        assert token not in str(event.payload)


def test_invalid_and_weak_passwords():
    m = PasswordResetManager(ttl_seconds=60)

    async def flow():
        token = await m.request_reset("bob")
        with pytest.raises(PasswordResetError):
            await m.reset_password("garbage-token", "Xxxxxxxxx1")
        with pytest.raises(PasswordResetError):
            await m.reset_password(token, "court")  # < MIN_PASSWORD_LENGTH
        return token

    _run(flow())
    assert MIN_PASSWORD_LENGTH >= 6


def test_new_request_revokes_previous_token():
    m = PasswordResetManager(ttl_seconds=60)

    async def flow():
        t1 = await m.request_reset("carol")
        t2 = await m.request_reset("carol")
        assert t1 != t2
        # t1 a été révoqué par la seconde demande.
        assert await m.peek_username(t1) is None
        assert await m.peek_username(t2) == "carol"
        return t2

    _run(flow())


def test_expired_token_rejected():
    m = PasswordResetManager(ttl_seconds=0)

    async def flow():
        token = await m.request_reset("dave")
        # TTL 0 → déjà expiré au moment de la consommation.
        with pytest.raises(PasswordResetError):
            await m.reset_password(token, "NouveauMotDePasse9")
        return token

    _run(flow())


def test_token_hash_only_stored_in_memory():
    m = PasswordResetManager(ttl_seconds=60)

    async def flow():
        token = await m.request_reset("erin")
        expected = hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert expected in m._memory  # seul le hash est persisté
        assert token not in m._memory
        return token

    _run(flow())
