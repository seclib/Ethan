"""Tests du connecteur SMTP/IMAP — identifiants FICTIFS, IMAP/SMTP mockés.

Vérifient : déclaration explicite (auth, permissions, credentials), test
réel simulé (login IMAP), isolation des secrets (jamais dans le record
public), opérations fetch/send via le ConnectionManager (permissions
enforced), et refus des flux OAuth.
"""

from __future__ import annotations

import base64
import imaplib

import pytest
from core.integrations.connections import ConnectionError, get_provider

from .conftest import FakeSecrets, make_manager

CREDENTIALS = {
    "imap_host": "imap.fake.tld",
    "imap_port": "993",
    "smtp_host": "smtp.fake.tld",
    "smtp_port": "587",
    "username": "user@fake.tld",
    "password": "app-password-fake",  # valeur de test — jamais réelle
}


class FakeIMAP:
    """IMAP4_SSL de test — ``bad`` comme mot de passe = échec de login."""

    instances: list["FakeIMAP"] = []

    def __init__(self, host: str, port: int) -> None:
        self.host, self.port = host, port
        self.selected: str | None = None
        FakeIMAP.instances.append(self)

    def login(self, user: str, password: str) -> tuple[str, list]:
        if password == "bad":
            raise RuntimeError("LOGIN failed")
        self.user = user
        return "OK", [b"Logged in"]

    def select(self, mailbox: str, readonly: bool = False) -> tuple[str, list]:
        self.selected = mailbox
        return "OK", [b"42"]

    def search(self, charset: str, *criteria: str) -> tuple[str, list]:
        return "OK", [b"1 2 3"]

    def fetch(self, uid: bytes, spec: str) -> tuple[str, list]:
        header = (
            b"From: Alice <alice@fake.tld>\r\n"
            b"Subject: =?utf-8?q?Bonjour?="
            b"\r\nDate: Mon, 01 Jan 2026 00:00:00 +0000\r\n"
        )
        return "OK", [(b"1 (BODY[HEADER] {80})", header)]

    def logout(self) -> tuple[str, list]:
        return "BYE", []


class FakeSMTP:
    sent: tuple[str, list, str] | None = None

    def __init__(self, host: str, port: int) -> None:
        self.host, self.port = host, port

    def starttls(self) -> tuple[str, str]:
        return (220, b"ready")

    def login(self, user: str, password: str) -> tuple[str, list]:
        return (235, [b"ok"])

    def sendmail(self, frm: str, to: list, msg: str) -> dict:
        FakeSMTP.sent = (frm, to, msg)
        return {}

    def quit(self) -> tuple[str, list]:
        return (221, [])


@pytest.fixture
def imap_mock(monkeypatch: pytest.MonkeyPatch) -> type[FakeIMAP]:
    FakeIMAP.instances = []
    monkeypatch.setattr(imaplib, "IMAP4_SSL", FakeIMAP)
    return FakeIMAP


@pytest.fixture(autouse=True)
def smtp_mock(monkeypatch: pytest.MonkeyPatch):
    import smtplib

    FakeSMTP.sent = None
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)


# ── Déclaration explicite ────────────────────────────────────────────────


def test_declares_password_auth_and_secret_credentials():
    provider = get_provider("email-smtp-imap")
    assert provider.auth_method == "password-smtp-imap"
    creds = {c.key: c for c in provider.credential_requirements}
    assert creds["password"].secret is True
    assert creds["username"].secret is False
    assert creds["imap_host"].required is True
    assert creds["imap_port"].required is False
    scopes = {s.scope: s for s in provider.scopes}
    assert scopes["mailbox.send"].sensitive is True
    ops = {op.name: op for op in provider.operations}
    assert ops["fetch_messages"].scope == "mailbox.read"
    assert ops["send_message"].scope == "mailbox.send" and ops["send_message"].write


@pytest.mark.asyncio
async def test_oauth_methods_are_explicitly_rejected():
    provider = get_provider("email-smtp-imap")
    with pytest.raises(ConnectionError, match="does not use OAuth"):
        await provider.exchange_code(None, None, "code", "uri")
    with pytest.raises(ConnectionError, match="test_credentials"):
        await provider.test_connection(None, None)


# ── Test réel simulé (login IMAP) ────────────────────────────────────────


@pytest.mark.asyncio
async def test_credentials_test_performs_real_imap_login(imap_mock):
    provider = get_provider("email-smtp-imap")
    account = await provider.test_credentials(CREDENTIALS)
    assert account == {
        "username": "user@fake.tld",
        "imap_host": "imap.fake.tld",
        "mailbox_total": 42,
    }
    assert imap_mock.instances[0].user == "user@fake.tld"


@pytest.mark.asyncio
async def test_credentials_test_fails_on_bad_password(imap_mock):
    provider = get_provider("email-smtp-imap")
    bad = {**CREDENTIALS, "password": "bad"}
    with pytest.raises(ConnectionError, match="login failed"):
        await provider.test_credentials(bad)


# ── Cycle de vie via ConnectionManager (intégration) ─────────────────────


@pytest.mark.asyncio
async def test_connect_password_stores_secret_outside_public_record(imap_mock):
    mgr = make_manager(secrets=FakeSecrets({}))
    record = await mgr.connect_password("u1", "email-smtp-imap", CREDENTIALS)
    assert record["status"] == "connected"
    assert record["account"]["username"] == "user@fake.tld"
    # ANTI-FUITE : le record public ne contient JAMAIS le mot de passe.
    assert "app-password-fake" not in str(record)
    assert "password" not in str(record)
    # Les secrets vivent UNIQUEMENT dans le domaine dédié.
    stored = await mgr._store.get("connection-tokens", "u1:email-smtp-imap")
    assert stored["kind"] == "password"
    assert stored["password"] == "app-password-fake"
    # Permissions accordées = permissions déclaratives du connecteur.
    assert set(record["scopes_granted"]) == {"mailbox.read", "mailbox.send"}


@pytest.mark.asyncio
async def test_connect_password_rejects_missing_required_credentials(imap_mock):
    mgr = make_manager(secrets=FakeSecrets({}))
    incomplete = {k: v for k, v in CREDENTIALS.items() if k != "password"}
    with pytest.raises(ConnectionError, match="Missing required credentials.*password"):
        await mgr.connect_password("u1", "email-smtp-imap", incomplete)


@pytest.mark.asyncio
async def test_connect_password_rejects_oauth_providers():
    mgr = make_manager(secrets=FakeSecrets({}))
    with pytest.raises(ConnectionError, match="use the OAuth flow"):
        await mgr.connect_password("u1", "github", {"username": "x", "password": "y"})


# ── Opérations via le manager (permissions enforced) ─────────────────────


@pytest.mark.asyncio
async def test_fetch_messages_operation(imap_mock):
    mgr = make_manager(secrets=FakeSecrets({}))
    await mgr.connect_password("u1", "email-smtp-imap", CREDENTIALS)
    result = await mgr.run_operation("u1", "email-smtp-imap", "fetch_messages", {"limit": 3})
    messages = result["result"]
    assert messages[0]["from"] == "Alice <alice@fake.tld>"
    assert messages[0]["subject"] == "Bonjour"
    assert imap_mock.instances[-1].selected == "INBOX"
    # ANTI-FUITE : le résultat ne contient ni mot de passe ni credential.
    assert "app-password-fake" not in str(result)


@pytest.mark.asyncio
async def test_send_message_operation_uses_smtp(imap_mock):
    mgr = make_manager(secrets=FakeSecrets({}))
    await mgr.connect_password("u1", "email-smtp-imap", CREDENTIALS)
    result = await mgr.run_operation(
        "u1",
        "email-smtp-imap",
        "send_message",
        {"to": "bob@fake.tld", "subject": "S", "body": "Corps du message"},
    )
    assert result["result"]["sent_to"] == "bob@fake.tld"
    assert FakeSMTP.sent is not None
    frm, to, msg = FakeSMTP.sent
    assert frm == "user@fake.tld" and to == ["bob@fake.tld"]
    assert "Subject: S" in msg
    # Corps MIME encodé base64 — vérifié en décodant la dernière partie.
    body_part = msg.rsplit("\n\n", 1)[-1].strip()
    assert base64.b64decode(body_part).decode() == "Corps du message"


@pytest.mark.asyncio
async def test_operation_requires_connected_connection(imap_mock):
    mgr = make_manager(secrets=FakeSecrets({}))
    # Connexion en erreur (mauvais mot de passe) : record persisté avec
    # statut ``error`` → toute opération est refusée.
    with pytest.raises(ConnectionError, match="login failed"):
        await mgr.connect_password("u1", "email-smtp-imap", {**CREDENTIALS, "password": "bad"})
    with pytest.raises(ConnectionError, match="is not connected"):
        await mgr.run_operation("u1", "email-smtp-imap", "fetch_messages", {})
