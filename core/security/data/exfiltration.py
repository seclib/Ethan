"""Garde anti-exfiltration (Phase 06).

Garantit qu'aucune donnée locale ne peut quitter ETHAN sans politique
explicite. Les quatre flux sont **indépendants** :

    LOCAL_READ          (filesystem read)
    LOCAL_WRITE         (filesystem write)
    NETWORK_ACCESS      (connexion réseau sortante)
    EXTERNAL_TRANSMISSION  (envoi de contenu vers une destination)

La capacité ``READ LOCAL DATA`` ne confère **jamais** ``SEND DATA EXTERNALLY`` :
chaque flux doit être autorisé séparément, et toute transmission externe passe
obligatoirement par ``ExfilGuard`` — jamais par un appel direct à un outil.

Invariant anti prompt-injection : le contenu récupéré (fichier, page Web,
sortie de tool, mémoire) est traité comme des **données non fiables**. Il ne
peut ni créer une autorisation, ni la modifier, ni la révoquer. Seule une
politique explicite (``authorize_transmission``) le peut.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable

from core.security.data.sensitive import (
    SensitiveDataClassifier,
    SensitiveScan,
)

logger = logging.getLogger(__name__)


class DataFlow(StrEnum):
    """Les quatre flux de données — indépendants."""

    LOCAL_READ = "local_read"
    LOCAL_WRITE = "local_write"
    NETWORK_ACCESS = "network_access"
    EXTERNAL_TRANSMISSION = "external_transmission"


class TransmitResult(StrEnum):
    """Résultat d'une évaluation de transmission externe."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"
    REDACTED = "redacted"


@dataclass(frozen=True)
class TransmissionDecision:
    """Décision du garde pour une transmission externe."""

    result: TransmitResult
    reason: str
    destination: str = ""
    sensitive_kinds: frozenset[str] = frozenset()
    policy_id: str | None = None
    timestamp: float = field(default_factory=time.time)

    @property
    def allowed(self) -> bool:
        """True si le contenu peut être envoyé (ALLOW ou REDACTED)."""
        return self.result in (TransmitResult.ALLOW, TransmitResult.REDACTED)

    def to_dict(self) -> dict[str, object]:
        """Sérialisation pour l'audit."""
        return {
            "result": self.result.value,
            "reason": self.reason,
            "destination": self.destination,
            "sensitive_kinds": sorted(self.sensitive_kinds),
            "policy_id": self.policy_id,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class TransmissionPolicy:
    """Politique explicite de transmission externe.

    Accordée par un administrateur (jamais par un LLM, agent ou contenu).
    ``allowed_kinds`` : ensembles de catégories sensibles autorisées à sortir
    (ex. ``{"personal_data"}``) ; une chaîne vide = aucun secret autorisé.
    """

    id: str
    destination: str  # glob, ex "https://api.example.com/**"
    allowed_kinds: frozenset[str] = frozenset()
    granted_by: str = "admin"
    granted_at: float = field(default_factory=time.time)
    ttl_seconds: int | None = None

    def is_expired(self, now: float | None = None) -> bool:
        """True si la politique a expiré (TTL écoulé)."""
        if self.ttl_seconds is None:
            return False
        return (now or time.time()) > self.granted_at + self.ttl_seconds

    def to_audit_dict(self) -> dict[str, object]:
        """Sérialisation pour l'audit (sans données sensibles)."""
        return {
            "id": self.id,
            "destination": self.destination,
            "allowed_kinds": sorted(self.allowed_kinds),
            "granted_by": self.granted_by,
            "granted_at": self.granted_at,
            "ttl_seconds": self.ttl_seconds,
        }

# ── Helpers ────────────────────────────────────────────────────────────────────


def policy_id(destination: str, allowed_kinds: frozenset[str]) -> str:
    """Génère un ID de politique déterministe SHA-256."""
    h = hashlib.sha256(
        f"{destination}:{','.join(sorted(allowed_kinds))}".encode()
    ).hexdigest()
    return f"tx_{h[:16]}"


def _glob_match(pattern: str, value: str) -> bool:
    """Glob simple : ``*`` matche n'importe quelle séquence."""
    if pattern == "*":
        return True
    if pattern == value:
        return True
    if pattern.endswith("**"):
        return value.startswith(pattern[:-2])
    if "*" in pattern:
        import fnmatch

        return fnmatch.fnmatchcase(value, pattern)
    return False


# ── Anti prompt-injection structurelle ───────────────────────────────────────

def strip_instruction_blocks(content: str) -> str:
    """Nettoie un contenu récupéré de toute tentative d'instruction.

    Le contenu externe est des **données**, jamais des instructions.
    Les blocs ``<system>`` / ``<instruction>`` / ``system:`` sont retirés
    pour empêcher un fichier/page/tool de tenter d'injecter une directive.

    Fonction module partagée : utilisée par ``ExfilGuard`` et par le
    ``PromptGuard`` (séparation données/instructions, Constitution CT-4).
    """
    import re

    cleaned = re.sub(
        r"(?is)<\s*system\s*>.*?<\s*/\s*system\s*>", "[blocked]", content
    )
    cleaned = re.sub(
        r"(?is)<\s*instruction\s*>.*?<\s*/\s*instruction\s*>",
        "[blocked]",
        cleaned,
    )
    cleaned = re.sub(
        r"(?im)^\s*(system|instruction|developer)\s*:\s*.*$",
        "[blocked]",
        cleaned,
    )
    return cleaned


class ExfilGuard:
    """Point d'entrée **obligatoire** pour toute transmission externe.

    Règles :
    - ``authorize_transmission`` crée une politique explicite (fail-closed :
      sans politique, toute transmission est refusée).
    - ``evaluate`` scanne le contenu sortant : un secret non couvert par la
      politique est refusé (ou masqué en mode ``redact``).
    - ``transmit`` n'appelle jamais le callback si la décision n'est pas
      autorisée.
    - Le contenu récupéré ne peut jamais créer/modifier une politique
      (anti prompt-injection structurelle).
    """

    def __init__(
        self,
        classifier: SensitiveDataClassifier | None = None,
        require_confirmation: bool = False,
        redact: bool = True,
    ) -> None:
        self._classifier = classifier or SensitiveDataClassifier()
        self._policies: dict[str, TransmissionPolicy] = {}
        self._audit: list[TransmissionDecision] = []
        self._require_confirmation = require_confirmation
        self._redact = redact

    # ── Administration des politiques (jamais par le LLM) ────────────────

    def authorize_transmission(
        self,
        destination: str,
        allowed_kinds: set[str] | None = None,
        granted_by: str = "admin",
        ttl_seconds: int | None = None,
    ) -> TransmissionPolicy:
        """Crée une politique explicite de transmission vers une destination.

        ``allowed_kinds=None`` ou vide = **aucun** secret autorisé à sortir
        (seul du contenu non sensible peut transiter).
        """
        kinds = frozenset(allowed_kinds or set())
        policy = TransmissionPolicy(
            id=policy_id(destination, kinds),
            destination=destination,
            allowed_kinds=kinds,
            granted_by=granted_by,
            ttl_seconds=ttl_seconds,
        )
        self._policies[policy.id] = policy
        logger.info(
            "Transmission policy granted: %s -> %s (kinds=%s, by=%s)",
            policy.id, destination, sorted(kinds), granted_by,
        )
        return policy

    def revoke_transmission(self, destination: str) -> bool:
        """Révoque toutes les politiques d'une destination."""
        removed = False
        for pid, policy in list(self._policies.items()):
            if _glob_match(policy.destination, destination) or (
                policy.destination == destination
            ):
                del self._policies[pid]
                removed = True
        if removed:
            logger.info("Transmission policies revoked for %s", destination)
        return removed

    def list_policies(self) -> list[TransmissionPolicy]:
        """Liste les politiques actives (non expirées)."""
        now = time.time()
        return [p for p in self._policies.values() if not p.is_expired(now)]


    # ── Évaluation d'une transmission externe ────────────────────────────

    def evaluate(
        self,
        destination: str,
        content: str,
        source: str = "unknown",
    ) -> TransmissionDecision:
        """Évalue si ``content`` peut être envoyé vers ``destination``.

        - Aucune politique explicite -> DENY (fail-closed, CR-4).
        - Contenu sensible non couvert par la politique -> DENY / REDACTED.
        - Contenu non sensible + politique -> ALLOW.
        """
        policy = self._find_policy(destination)
        if policy is None:
            decision = TransmissionDecision(
                result=TransmitResult.DENY,
                reason=(
                    "Aucune politique explicite de transmission vers cette "
                    "destination (fail-closed CR-4)."
                ),
                destination=destination,
            )
            self._audit.append(decision)
            return decision

        scan: SensitiveScan = self._classifier.scan_text(content)
        uncovered = scan.kinds - policy.allowed_kinds

        if uncovered:
            if self._redact:
                decision = TransmissionDecision(
                    result=TransmitResult.REDACTED,
                    reason=(
                        "Contenu sensible non autorisé -> masqué avant envoi "
                        f"({','.join(sorted(uncovered))})."
                    ),
                    destination=destination,
                    sensitive_kinds=frozenset(scan.kinds),
                    policy_id=policy.id,
                )
            else:
                decision = TransmissionDecision(
                    result=TransmitResult.DENY,
                    reason=(
                        "Contenu sensible non autorisé par la politique "
                        f"({','.join(sorted(uncovered))})."
                    ),
                    destination=destination,
                    sensitive_kinds=frozenset(scan.kinds),
                    policy_id=policy.id,
                )
            self._audit.append(decision)
            return decision

        if scan.sensitive and self._require_confirmation:
            decision = TransmissionDecision(
                result=TransmitResult.REQUIRE_CONFIRMATION,
                reason="Transmission de donnees sensibles : confirmation requise.",
                destination=destination,
                sensitive_kinds=frozenset(scan.kinds),
                policy_id=policy.id,
            )
            self._audit.append(decision)
            return decision

        decision = TransmissionDecision(
            result=TransmitResult.ALLOW,
            reason="Transmission autorisée par la politique explicite.",
            destination=destination,
            sensitive_kinds=frozenset(scan.kinds),
            policy_id=policy.id,
        )
        self._audit.append(decision)
        return decision


    # ── Exécution protégée (jamais de callback si non autorisé) ──────────

    async def transmit(
        self,
        destination: str,
        content: str,
        fn: Callable[[str], object],
        source: str = "unknown",
    ) -> object:
        """Évalue puis exécute ``fn(content)`` uniquement si autorisé.

        En mode ``redact``, le contenu masqué est envoyé (le callback reçoit
        le contenu nettoyé). En mode ``deny``, le callback n'est jamais appelé.
        """
        decision = self.evaluate(destination, content, source=source)

        if decision.result is TransmitResult.DENY:
            raise ExfilBlockedError(decision)
        if decision.result is TransmitResult.REQUIRE_CONFIRMATION:
            raise ExfilConfirmationRequiredError(decision)

        payload = content
        if decision.result is TransmitResult.REDACTED:
            payload = self._classifier.redact(content)
        return await _call(fn, payload)

    # ── Anti prompt-injection structurelle ───────────────────────────────

    def sanitize_external_content(self, content: str) -> str:
        """Nettoie un contenu récupéré de toute tentative d'instruction.

        Point d'entrée historique, délègue à ``strip_instruction_blocks`` :
        la logique de nettoyage est partagée entre le guard et le
        ``PromptGuard`` (Constitution CT-4) — une seule source de vérité.
        """
        return strip_instruction_blocks(content)

    # ── Audit ─────────────────────────────────────────────────────────────

    @property
    def audit_log(self) -> list[TransmissionDecision]:
        """Journal d'audit append-only (lecture seule)."""
        return list(self._audit)

    def audit_summary(self) -> dict[str, int]:
        """Résumé statistique de l'audit."""
        counts: dict[str, int] = {}
        for decision in self._audit:
            counts[decision.result.value] = counts.get(decision.result.value, 0) + 1
        return {
            "total": len(self._audit),
            **{k: v for k, v in sorted(counts.items())},
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _find_policy(self, destination: str) -> TransmissionPolicy | None:
        """Trouve la politique la plus spécifique pour une destination."""
        best: TransmissionPolicy | None = None
        best_specificity = -1
        now = time.time()
        for policy in self._policies.values():
            if policy.is_expired(now):
                continue
            if _glob_match(policy.destination, destination):
                specificity = len(policy.destination)
                if specificity > best_specificity:
                    best = policy
                    best_specificity = specificity
        return best


class ExfilError(Exception):
    """Erreur générique du garde anti-exfiltration."""


class ExfilBlockedError(ExfilError):
    """Transmission externe bloquée (aucune autorisation)."""

    def __init__(self, decision: TransmissionDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason)


class ExfilConfirmationRequiredError(ExfilError):
    """Transmission sensible en attente de confirmation humaine."""

    def __init__(self, decision: TransmissionDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason)


async def _call(fn: Callable[[str], object], payload: str) -> object:
    """Appelle la fonction, qu'elle soit sync ou async."""
    import inspect

    if inspect.iscoroutinefunction(fn):
        return await fn(payload)
    result = fn(payload)
    if inspect.isawaitable(result):
        return await result
    return result

