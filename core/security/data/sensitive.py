"""Classification des donnees sensibles (Phase 06).

Détecte les catégories de données à protéger : credentials, clés SSH,
API keys, tokens, cookies, secrets, password stores, configuration privée
et données personnelles — dans un texte ou un chemin de fichier.

Ce module est **indépendant du LLM** : la détection est purement structurelle
(regex + chemins) et ne dépend d'aucune instruction de modèle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


class SensitiveKind:
    """Catégories de données sensibles reconnues."""

    CREDENTIALS = "credentials"
    SSH_KEY = "ssh_private_key"
    API_KEY = "api_key"
    TOKEN = "token"
    COOKIE = "cookie"
    SECRET = "secret"
    PASSWORD_STORE = "password_store"
    PRIVATE_CONFIG = "private_config"
    PERSONAL_DATA = "personal_data"


SENSITIVE_KINDS: tuple[str, ...] = (
    SensitiveKind.CREDENTIALS,
    SensitiveKind.SSH_KEY,
    SensitiveKind.API_KEY,
    SensitiveKind.TOKEN,
    SensitiveKind.COOKIE,
    SensitiveKind.SECRET,
    SensitiveKind.PASSWORD_STORE,
    SensitiveKind.PRIVATE_CONFIG,
    SensitiveKind.PERSONAL_DATA,
)

# Patterns de secrets dans un texte (ordre : le plus spécifique d'abord).
_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Clés privées SSH (multi-formats)
    (
        SensitiveKind.SSH_KEY,
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?"
            r"-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
        ),
    ),
    # Tokens GitHub / Slack / JWT
    (
        SensitiveKind.TOKEN,
        re.compile(
            r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"
            r"|\bxox[baprs]-[A-Za-z0-9-]{10,}\b"
            r"|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
    ),
    # Clés API connues (OpenAI / AWS / Google / Stripe)
    (
        SensitiveKind.API_KEY,
        re.compile(
            r"\bsk-[A-Za-z0-9_-]{20,}\b"
            r"|\bAKIA[0-9A-Z]{16}\b"
            r"|\bAIza[0-9A-Za-z_-]{35}\b"
            r"|\bsk_live_[0-9A-Za-z]{24,}\b"
        ),
    ),
    # Cookies de session
    (
        SensitiveKind.COOKIE,
        re.compile(r"\b(?:sessionid|connect\.sid|PHPSESSID|JSESSIONID)=[A-Za-z0-9%._-]{8,}"),
    ),
    # Paires clé=valeur manifestement sensibles (secret=, password=, token=)
    (
        SensitiveKind.SECRET,
        re.compile(
            r"\b(?:secret|password|passwd|api[_-]?key|auth[_-]?token|private[_-]?key)"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9_@#!$%^&*()+=\-\./]{12,}['\"]?"
        ),
    ),
    # Données personnelles (email + carte bancaire)
    (
        SensitiveKind.PERSONAL_DATA,
        re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            r"|\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
        ),
    ),
)

# Chemins de fichiers sensibles (glob simple — marqueurs dans le chemin).
_SENSITIVE_PATH_MARKERS: tuple[str, ...] = (
    "/.ssh/",
    "/.aws/credentials",
    "/.aws/config",
    "/.gnupg/",
    "/.config/gcloud/",
    "/.config/gh/",
    "/.npmrc",
    "/.pypirc",
    "/.netrc",
    "/.git-credentials",
    "/.docker/config.json",
    "/.password-store/",
    "/password-store/",
    "/.local/share/keyrings/",
    "/.gnome2/keyrings/",
    "/.env",
    "/.env.",
    "/id_rsa",
    "/id_ed25519",
    "/id_dsa",
    "/.pgpass",
    "/.my.cnf",
    "/.kube/config",
    "/.kube/",
    "/credentials.json",
    "/client_secret.json",
    "/service-account",
    "/vault-token",
    "/secrets/",
    "/etc/shadow",
    "/etc/passwd",
    "/etc/ssh/",
)


@dataclass(frozen=True)
class SensitiveScan:
    """Résultat d'un scan : catégories détectées + occurrences masquées."""

    kinds: frozenset[str] = field(default_factory=frozenset)
    matches: tuple[tuple[str, str], ...] = ()  # (kind, extrait masqué)

    @property
    def sensitive(self) -> bool:
        """True si au moins une donnée sensible a été détectée."""
        return bool(self.kinds)

    @property
    def summary(self) -> str:
        """Résumé lisible (audit)."""
        if not self.kinds:
            return "clean"
        return "sensitive:" + ",".join(sorted(self.kinds))


class SensitiveDataClassifier:
    """Détecte et masque les données sensibles dans du texte ou un chemin.

    Utilisé par le ``ExfilGuard`` pour inspecter tout contenu sortant et tout
    chemin accédé. La détection est structurelle — jamais influencée par le
    contenu sémantique du prompt.
    """

    def __init__(self, text_patterns: Iterable[tuple[str, re.Pattern[str]]] | None = None) -> None:
        self._text_patterns = tuple(text_patterns or _TEXT_PATTERNS)

    # ── Scan de texte ────────────────────────────────────────────────────

    def scan_text(self, text: str) -> SensitiveScan:
        """Scanne un texte et retourne les catégories sensibles détectées."""
        if not text:
            return SensitiveScan()
        found: set[str] = set()
        matches: list[tuple[str, str]] = []
        for kind, pattern in self._text_patterns:
            for m in pattern.finditer(text):
                found.add(kind)
                matches.append((kind, self._mask(m.group(0))))
        return SensitiveScan(kinds=frozenset(found), matches=tuple(matches))

    def redact(self, text: str) -> str:
        """Remplace chaque occurrence de donnée sensible par un marqueur."""
        if not text:
            return text
        redacted = text
        for kind, pattern in self._text_patterns:
            redacted = pattern.sub(f"[REDACTED:{kind}]", redacted)
        return redacted

    # ── Scan de chemin ───────────────────────────────────────────────────

    def is_sensitive_path(self, path: str | Path) -> bool:
        """True si le chemin pointe vers une zone de données sensibles."""
        normalized = str(path).replace("\\", "/")
        return any(marker in normalized for marker in _SENSITIVE_PATH_MARKERS)

    def scan_path(self, path: str | Path) -> SensitiveScan:
        """Retourne les catégories sensibles d'un chemin de fichier."""
        normalized = str(path).replace("\\", "/")
        kinds: set[str] = set()
        if normalized.endswith(("/.env", ".env")):
            kinds.add(SensitiveKind.SECRET)
        if "/.ssh/" in normalized or normalized.endswith(("id_rsa", "id_ed25519")):
            kinds.add(SensitiveKind.SSH_KEY)
        if any(
            marker in normalized
            for marker in ("/credentials", "/client_secret", "/service-account")
        ):
            kinds.add(SensitiveKind.CREDENTIALS)
        if any(
            marker in normalized
            for marker in ("/.password-store/", "/password-store/", "keyrings/")
        ):
            kinds.add(SensitiveKind.PASSWORD_STORE)
        if normalized.endswith((".kube/config", "/etc/shadow")):
            kinds.add(SensitiveKind.PRIVATE_CONFIG)
        if kinds:
            return SensitiveScan(
                kinds=frozenset(kinds),
                matches=((next(iter(kinds)), self._mask(normalized)),),
            )
        return SensitiveScan()

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _mask(value: str) -> str:
        """Masque un extrait (garde début + fin)."""
        if len(value) <= 4:
            return "[…]"
        return value[:4] + "…" + value[-4:]
