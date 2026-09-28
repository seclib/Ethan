"""Connecteur Email SMTP/IMAP — auth par identifiants (aucun OAuth).

SÉPARATION DES MODES (exigence d'architecture) : pour Gmail et tout
fournisseur supportant OAuth, utiliser le connecteur ``email`` (API Google).
Ce connecteur vise les boîtes GÉNÉRIQUES (FAI, serveurs auto-hébergés).

Audit des 8 points :
1. Auth : username + mot de passe (mot de passe d'application recommandé)
   — PAS d'OAuth : les serveurs IMAP/SMTP génériques ne le proposent pas.
2. Permissions déclaratives (pas de scopes OAuth) : ``mailbox.read``
   (IMAP) et ``mailbox.send`` (SMTP — sensible) ; le Core refuse une
   opération si la permission n'est pas accordée à la connexion.
3. Credentials : imap_host/imap_port, smtp_host/smtp_port, username,
   password. Le mot de passe n'est JAMAIS stocké en clair dans un record
   public, un event ou un log : il vit uniquement dans le domaine dédié
   ``connection-tokens`` (store secrets Core/Runtime).
4. Opérations : ``fetch_messages`` (IMAP, lecture des N derniers messages),
   ``send_message`` (SMTP). Pas de gestion des dossiers/filtres
   (non implémenté volontairement — moindre privilège).
5. Test : login IMAP RÉEL (IMAP4_SSL) — prouve que les identifiants
   fonctionnent avant tout stockage.
6. Révocation : aucune API — changer/révoquer le mot de passe côté serveur
   mail ; la déconnexion ETHAN purge les secrets locaux.
7. Erreurs : échec IMAP/SMTP → ``ConnectionError`` avec le motif
   (identifiants, hôte/port, TLS) — jamais de traceback brut exposé.
8. Expiration : sans objet (mot de passe long-lived) — le test de
   connexion détecte une révocation serveur à chaque utilisation.
"""

from __future__ import annotations

import asyncio
import email as email_lib
import imaplib
import smtplib
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from typing import Any

from core.integrations.connections.base import (
    ClientCredentials,
    ConnectionError,
    ConnectionProvider,
    CredentialRequirement,
    HttpLike,
    OperationSpec,
    ScopeSpec,
    TokenBundle,
)


class EmailSmtpImapProvider(ConnectionProvider):
    id = "email-smtp-imap"
    label = "Email (SMTP/IMAP)"
    description = (
        "Boîte générique via IMAP/SMTP (FAI, auto-hébergé) — identifiants "
        "stockés uniquement dans le magasin de secrets du Core."
    )
    authorize_url = ""  # pas d'OAuth — flux start/callback jamais utilisés
    token_url = ""
    auth_method = "password-smtp-imap"

    @property
    def scopes(self) -> list[ScopeSpec]:
        return [
            ScopeSpec("mailbox.read", "Lire les messages récents via IMAP.", False),
            ScopeSpec("mailbox.send", "Envoyer des emails via SMTP.", True),
        ]

    @property
    def credential_requirements(self) -> list[CredentialRequirement]:
        return [
            CredentialRequirement(
                "imap_host", "Hôte IMAP (ex. imap.fournisseur.tld).", secret=False
            ),
            CredentialRequirement(
                "imap_port",
                "Port IMAP (993 SSL par défaut).",
                secret=False,
                required=False,
            ),
            CredentialRequirement("smtp_host", "Hôte SMTP.", secret=False),
            CredentialRequirement(
                "smtp_port",
                "Port SMTP (587 STARTTLS ou 465 SSL).",
                secret=False,
                required=False,
            ),
            CredentialRequirement(
                "username", "Identifiant de la boîte (souvent l'adresse).", secret=False
            ),
            CredentialRequirement(
                "password",
                "Mot de passe (application recommandé) — stocké chiffré côté Core.",
            ),
        ]

    @property
    def operations(self) -> list[OperationSpec]:
        return [
            OperationSpec(
                "fetch_messages",
                "Récupérer les N derniers messages.",
                scope="mailbox.read",
            ),
            OperationSpec(
                "send_message",
                "Envoyer un email via SMTP.",
                scope="mailbox.send",
                write=True,
            ),
        ]

    # ── Flux OAuth : non applicables (erreur explicite, jamais silencieuse)

    async def exchange_code(
        self, http: HttpLike, creds: ClientCredentials, code: str, redirect_uri: str
    ) -> TokenBundle:
        raise ConnectionError("SMTP/IMAP connector does not use OAuth — use connect_credentials")

    async def test_connection(self, http: HttpLike, tokens: TokenBundle) -> dict[str, Any]:
        raise ConnectionError(
            "SMTP/IMAP connector: use test_credentials (IMAP login), not test_connection"
        )

    # ── Test réel des identifiants (IMAP login) ───────────────────────────

    async def test_credentials(self, credentials: dict[str, str]) -> dict[str, Any]:
        """Login IMAP RÉEL — identité publique (username, hôte, total)."""
        host = str(credentials.get("imap_host") or "").strip()
        user = str(credentials.get("username") or "").strip()
        password = str(credentials.get("password") or "")
        if not host or not user or not password:
            raise ConnectionError("SMTP/IMAP: imap_host, username and password are required")
        port = int(credentials.get("imap_port") or 993)

        def _login() -> int:
            client = imaplib.IMAP4_SSL(host, port)
            try:
                client.login(user, password)
                typ, data = client.select("INBOX", readonly=True)
                if typ != "OK":
                    raise ConnectionError("SMTP/IMAP: cannot open INBOX")
                return int(data[0] or 0)
            finally:
                try:
                    client.logout()
                except Exception:  # noqa: BLE001 — fermeture best effort
                    pass

        try:
            total = await asyncio.to_thread(_login)
        except ConnectionError:
            raise
        except Exception as exc:  # imaplib lève des exceptions variées
            raise ConnectionError(
                f"SMTP/IMAP login failed for {user!r} on {host}:{port} — "
                "check host, port and credentials"
            ) from exc
        return {"username": user, "imap_host": host, "mailbox_total": total}

    # ── Opérations IMAP/SMTP (stdlib, exécutées hors event loop) ─────────

    @staticmethod
    def _decode(raw: Any) -> str:
        try:
            return str(make_header(decode_header(raw or "")))
        except Exception:  # noqa: BLE001 — entête malformée
            return str(raw or "")

    async def op_fetch_messages(
        self, http: HttpLike | None, ctx: dict[str, Any], params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        cred = ctx["credentials"]
        host = str(cred.get("imap_host") or "")
        port = int(cred.get("imap_port") or 993)
        user, password = (
            str(cred.get("username") or ""),
            str(cred.get("password") or ""),
        )
        limit = max(1, min(int(params.get("limit", 10)), 50))

        def _fetch() -> list[dict[str, Any]]:
            client = imaplib.IMAP4_SSL(host, port)
            messages: list[dict[str, Any]] = []
            try:
                client.login(user, password)
                client.select("INBOX", readonly=True)
                typ, data = client.search(None, "ALL")
                if typ != "OK":
                    raise ConnectionError("SMTP/IMAP: search failed")
                uids = (data[0] or b"").split()[-limit:]
                for uid in reversed(uids):
                    typ, msg_data = client.fetch(uid, "(BODY.PEEK[HEADER])")
                    if typ != "OK" or not msg_data or not msg_data[0]:
                        continue
                    msg = email_lib.message_from_bytes(msg_data[0][1])
                    messages.append(
                        {
                            "uid": uid.decode("ascii", "replace"),
                            "from": self._decode(msg.get("From")),
                            "subject": self._decode(msg.get("Subject")),
                            "date": self._decode(msg.get("Date")),
                        }
                    )
                return messages
            finally:
                try:
                    client.logout()
                except Exception:  # noqa: BLE001
                    pass

        try:
            return await asyncio.to_thread(_fetch)
        except ConnectionError:
            raise
        except Exception as exc:
            raise ConnectionError(
                f"SMTP/IMAP fetch failed on {host}:{port} — check credentials/permissions"
            ) from exc

    async def op_send_message(
        self, http: HttpLike | None, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        cred = ctx["credentials"]
        host = str(cred.get("smtp_host") or "").strip()
        if not host:
            raise ConnectionError("SMTP/IMAP: smtp_host is required to send")
        port = int(cred.get("smtp_port") or 587)
        user, password = (
            str(cred.get("username") or ""),
            str(cred.get("password") or ""),
        )
        to = str(params.get("to") or "").strip()
        subject = str(params.get("subject") or "").strip()
        body = str(params.get("body") or "")
        if not to or not subject:
            raise ConnectionError("send_message requires 'to' and 'subject'")
        use_ssl = port == 465

        def _send() -> None:
            message = MIMEText(body, "plain", "utf-8")
            message["From"] = user
            message["To"] = to
            message["Subject"] = subject
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port)
            else:
                server = smtplib.SMTP(host, port)
            try:
                if not use_ssl:
                    server.starttls()
                server.login(user, password)
                server.sendmail(user, [to], message.as_string())
            finally:
                try:
                    server.quit()
                except Exception:  # noqa: BLE001
                    pass

        try:
            await asyncio.to_thread(_send)
        except Exception as exc:
            raise ConnectionError(
                f"SMTP send failed via {host}:{port} — check credentials and recipient"
            ) from exc
        return {"sent_to": to, "smtp_host": host, "smtp_port": port}
