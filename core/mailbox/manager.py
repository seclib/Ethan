"""Core-owned Email inbox — IMAP via stdlib only. RFC-0001.

Credentials come exclusively from the environment (never committed,
never stored in records/logs/events):
    ETHAN_EMAIL_IMAP_HOST, ETHAN_EMAIL_IMAP_PORT (def 993),
    ETHAN_EMAIL_USER, ETHAN_EMAIL_PASSWORD, ETHAN_EMAIL_FOLDER (def INBOX)
"""

from __future__ import annotations

import asyncio
import email
import imaplib
import logging
import os
import re
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import Any

logger = logging.getLogger(__name__)


class EmailNotConfigured(RuntimeError):
    """No IMAP account configured in the environment."""


class EmailManager:
    """Minimal read-only inbox (list + read)."""

    def _settings(self) -> dict[str, str] | None:
        host = os.environ.get("ETHAN_EMAIL_IMAP_HOST")
        user = os.environ.get("ETHAN_EMAIL_USER")
        password = os.environ.get("ETHAN_EMAIL_PASSWORD")
        if not (host and user and password):
            return None
        return {
            "imap_host": host,
            "imap_port": int(os.environ.get("ETHAN_EMAIL_IMAP_PORT", "993")),
            "user": user,
            "password": password,
            "folder": os.environ.get("ETHAN_EMAIL_FOLDER", "INBOX"),
        }

    async def list_messages(self, limit: int = 20) -> list[dict[str, Any]]:
        settings = self._settings()
        if not settings:
            raise EmailNotConfigured(
                "Email non configuré : définir ETHAN_EMAIL_IMAP_HOST / "
                "ETHAN_EMAIL_USER / ETHAN_EMAIL_PASSWORD dans l'environnement"
            )
        return await asyncio.to_thread(self._fetch_list, settings, min(max(limit, 1), 50))

    async def get_message(self, uid: str) -> dict[str, Any]:
        settings = self._settings()
        if not settings:
            raise EmailNotConfigured("Email non configuré")
        return await asyncio.to_thread(self._fetch_message, settings, uid)

    @staticmethod
    def _decode(value: Any) -> str:
        if value is None:
            return ""
        try:
            return str(make_header(decode_header(value)))
        except Exception:  # noqa: BLE001
            return str(value)

    def _connect(self, s: dict[str, str]) -> imaplib.IMAP4_SSL:
        client = imaplib.IMAP4_SSL(s["imap_host"], s["imap_port"])
        client.login(s["user"], s["password"])
        client.select(s["folder"], readonly=True)
        return client

    @staticmethod
    def _iso_date(msg: email.message.Message) -> str:
        raw = msg.get("Date", "")
        try:
            return parsedate_to_datetime(raw).isoformat() if raw else ""
        except Exception:  # noqa: BLE001
            return raw

    def _fetch_list(self, s: dict[str, str], limit: int) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        client = self._connect(s)
        try:
            status, data = client.search(None, "ALL")
            if status != "OK":
                return messages
            ids = data[0].split()
            for num in reversed(ids[-limit:]):
                status, msg_data = client.fetch(
                    num, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)] UID)"
                )
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue
                header_bytes = b""
                uid = num.decode()
                for part in msg_data:
                    if isinstance(part, tuple):
                        header_bytes = part[1]
                        m = re.search(rb"UID (\d+)", part[0] or b"")
                        if m:
                            uid = m.group(1).decode()
                msg = email.message_from_bytes(header_bytes)
                from_addr = parseaddr(self._decode(msg.get("From", "")))
                messages.append({
                    "uid": uid,
                    "from": from_addr[1],
                    "from_name": from_addr[0],
                    "subject": self._decode(msg.get("Subject", "")),
                    "date": self._iso_date(msg),
                })
        finally:
            try:
                client.logout()
            except Exception:  # noqa: BLE001
                pass
        return messages

    def _fetch_message(self, s: dict[str, str], uid: str) -> dict[str, Any]:
        client = self._connect(s)
        try:
            status, data = client.uid("FETCH", uid.encode(), "(BODY.PEEK[])")
            if status != "OK" or not data or not data[0]:
                raise LookupError(f"Message UID {uid} introuvable")
            msg = email.message_from_bytes(data[0][1])
            body = self._extract_body(msg)
            return {
                "uid": uid,
                "from": parseaddr(self._decode(msg.get("From", "")))[1],
                "to": parseaddr(self._decode(msg.get("To", "")))[1],
                "subject": self._decode(msg.get("Subject", "")),
                "date": self._iso_date(msg),
                "body": body,
            }
        finally:
            try:
                client.logout()
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _extract_body(msg: email.message.Message) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and part.get_payload(decode=True):
                    charset = part.get_content_charset() or "utf-8"
                    return part.get_payload(decode=True).decode(charset, errors="replace")
            return ""
        payload = msg.get_payload(decode=True)
        if not payload:
            return ""
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")