"""ETHAN Data Protection & Anti-Exfiltration System.

Système de protection des données sensibles et de prévention d'exfiltration.

Ce module garantit que :
- Une lecture locale de données ne permet JAMAIS une transmission
  externe automatique (separation locale vs reseau).
- Le contenu outbound est scanne systematiquement a la sortie.
- Les secrets ne peuvent pas etre exfiltrés via network, MCP, shell ou
  configuration — le LLM ou un agent ne peut contourner ces protections
  par prompt injection ou abus d'outil.

Ce module est independant du LLM : aucune instruction de modele ne peut
le desactiver, le contourner ou modifier les patterns.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

from core.security.policy.types import ActionCategory


# ── Classification de sensibilité ─────────────────────────────────────────────

class Sensitivity(IntEnum):
    """Niveau de sensibilité d'une resource ou d'un contenu."""
    CLEAN = 0        # Pas de données sensibles
    LOW = 1          # Potentiellement identifiable (email, nom)
    MEDIUM = 2       # Informations personnelles / métier
    HIGH = 3         # Secrets techniques (clés API, mots de passe)
    CRITICAL = 4     # Secrets critiques (clés privées, root)


# ── Patterns de secrets ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class SecretPattern:
    """Un pattern de détection de secret."""
    name: str
    pattern: re.Pattern[str]
    sensitivity: Sensitivity
    description: str = ""


# Patterns couvrant : credentials, SSH keys, API keys, tokens, cookies,
# secrets, password stores, private config, personal data.
SECRET_PATTERNS: list[SecretPattern] = [
    SecretPattern(
        name="openai_key",
        pattern=re.compile(r"sk(?:-proj)?-[A-Za-z0-9]{20,}"),
        sensitivity=Sensitivity.HIGH,
        description="Clé API OpenAI",
    ),
    SecretPattern(
        name="anthropic_key",
        pattern=re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
        sensitivity=Sensitivity.HIGH,
        description="Clé API Anthropic",
    ),
    SecretPattern(
        name="aws_access_key",
        pattern=re.compile(r"AKIA[0-9A-Z]{16,20}"),
        sensitivity=Sensitivity.HIGH,
        description="Clé d'accès AWS",
    ),
    SecretPattern(
        name="aws_secret_key",
        pattern=re.compile(r"(?<![A-Za-z0-9])[0-9a-zA-Z/+=]{40}(?![A-Za-z0-9])"),
        sensitivity=Sensitivity.HIGH,
        description="Clé secrète AWS (40 chars)",
    ),
    SecretPattern(
        name="github_token",
        pattern=re.compile(r"ghp_[A-Za-z0-9]{36,64}"),
        sensitivity=Sensitivity.HIGH,
        description="Token GitHub personnel",
    ),
    SecretPattern(
        name="github_app_token",
        pattern=re.compile(r"ghu_[A-Za-z0-9]{36,64}"),
        sensitivity=Sensitivity.HIGH,
        description="Token GitHub App",
    ),
    SecretPattern(
        name="github_server_token",
        pattern=re.compile(r"ghs_[A-Za-z0-9]{36,64}"),
        sensitivity=Sensitivity.HIGH,
        description="Token GitHub Server-to-Server",
    ),
    SecretPattern(
        name="slack_token",
        pattern=re.compile(r"xox[baprs]-([0-9a-zA-Z]{10,})"),
        sensitivity=Sensitivity.HIGH,
        description="Token Slack",
    ),
    SecretPattern(
        name="slack_webhook",
        pattern=re.compile(
            r"https?://hooks\.slack\.com/services/T[0-9a-zA-Z_-]+/"
            r"B[0-9a-zA-Z_-]+/[0-9a-zA-Z_-]+"
        ),
        sensitivity=Sensitivity.HIGH,
        description="Webhook Slack",
    ),
    SecretPattern(
        name="jwt_token",
        pattern=re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        ),
        sensitivity=Sensitivity.HIGH,
        description="Jeton JWT",
    ),
    SecretPattern(
        name="google_oauth",
        pattern=re.compile(r"ya29\.[0-9A-Za-z_-]{20,}(?:[.-][0-9A-Za-z_-]+)*"),
        sensitivity=Sensitivity.HIGH,
        description="Token OAuth Google",
    ),
    SecretPattern(
        name="private_key_pem",
        pattern=re.compile(
            r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"
        ),
        sensitivity=Sensitivity.CRITICAL,
        description="Clé privée PEM",
    ),
    SecretPattern(
        name="ssh_private_key",
        pattern=re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----"),
        sensitivity=Sensitivity.CRITICAL,
        description="Clé privée SSH",
    ),
    SecretPattern(
        name="url_with_password",
        pattern=re.compile(r"[a-z]+://[^:/\s]+:[^@/\s]+@"),
        sensitivity=Sensitivity.HIGH,
        description="URL contenant un mot de passe",
    ),
    SecretPattern(
        name="generic_api_key",
        pattern=re.compile(
            r"(?i)(?:api[_-]?key|apikey|secret|token|password|passwd|pwd)"
            r"\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?"
        ),
        sensitivity=Sensitivity.MEDIUM,
        description="Clé API / secret générique",
    ),
    SecretPattern(
        name="email",
        pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        sensitivity=Sensitivity.LOW,
        description="Adresse email",
    ),
    SecretPattern(
        name="ssn",
        pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        sensitivity=Sensitivity.MEDIUM,
        description="Numéro de sécurité sociale (US)",
    ),
    SecretPattern(
        name="phone_number",
        pattern=re.compile(
            r"\b\+?1?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        sensitivity=Sensitivity.LOW,
        description="Numéro de téléphone",
    ),
]