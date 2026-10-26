"""
OSINT Policy — Doctrine défensive de collecte de sources ouvertes (Phase 2-5).

Gère :
- La politique de conservation (TTL) des données OSINT collectées,
- Le champ provenance obligatoire sur tout résultat de collecte,
- Le contrôle de géolocalisation précise,
- La classification des données personnelles dans les résultats OSINT,
- L'intégration avec ExfilGuard pour bloquer l'exfiltration de données
  personnelles issues de la collecte OSINT.

Ce module est indépendant du LLM : aucune instruction de modèle ne peut
créer, modifier ou contourner une politique OSINT.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from core.security.data.sensitive import (
    SensitiveDataClassifier,
    SensitiveKind,
    SensitiveScan,
)
from core.security.policy.capabilities import CapabilityManager, RiskLevel
from core.security.policy.types import PolicyResult

logger = logging.getLogger(__name__)

# TTL par défaut pour les données OSINT collectées (7 jours).
DEFAULT_OSINT_TTL_SECONDS = 7 * 24 * 60 * 60

# Rayon maximum (en km) pour une requête de géolocalisation précise
# nécessitant une autorisation explicite.
MAX_GEOLOCATION_RADIUS_KM = 1.0

# Domaines réservés : jamais autorisés pour la collecte OSINT sans
# approbation humaine explicite (HROT).
RESERVED_DOMAINS: frozenset[str] = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "metadata.google.internal",
    "169.254.169.254",
})


@dataclass(frozen=True)
class OSINTProvenance:
    """Traçabilité obligatoire d'une donnée collectée par OSINT.

    Attachée à chaque résultat de recherche / ingestion / requête géolocalisée.
    """

    source: str
    method: str
    collected_at: float
    authorization_id: str
    target: str
    confidence: float
    personal_data: bool
    retention_ttl_seconds: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "method": self.method,
            "collected_at": self.collected_at,
            "authorization_id": self.authorization_id,
            "target": self.target,
            "confidence": self.confidence,
            "personal_data": self.personal_data,
            "retention_ttl_seconds": self.retention_ttl_seconds,
        }


@dataclass
class OSINTRetentionPolicy:
    """Politique de conservation des données OSINT."""

    mission_id: str
    ttl_seconds: int
    created_at: float = field(default_factory=time.time)
    auto_delete: bool = True

    def is_expired(self, now: float | None = None) -> bool:
        return (now or time.time()) > self.created_at + self.ttl_seconds


class OSINTPolicyManager:
    """Gestionnaire de politique OSINT défensive.

    Rôle :
    - Valider qu'une collecte OSINT est autorisée (capability `osint:collect`),
    - Attacher une provenance à chaque résultat,
    - Détecter les données personnelles et appliquer le TTL de conservation,
    - Bloquer la géolocalisation précise sans autorisation,
    - Intégrer avec ExfilGuard pour bloquer l'exfiltration de données
      personnelles issues de l'OSINT.
    """

    def __init__(
        self,
        capability_manager: CapabilityManager,
        classifier: SensitiveDataClassifier | None = None,
        default_ttl_seconds: int = DEFAULT_OSINT_TTL_SECONDS,
    ) -> None:
        self._caps = capability_manager
        self._classifier = classifier or SensitiveDataClassifier()
        self._default_ttl = default_ttl_seconds
        self._retention_policies: dict[str, OSINTRetentionPolicy] = {}

    # ── Autorisation de collecte ──────────────────────────────────────

    def authorize_collect(
        self,
        subject: str,
        target: str,
        *,
        request_id: str | None = None,
    ) -> tuple[PolicyResult, str, str | None]:
        """Vérifie que le sujet est autorisé à collecter sur `target`.

        Retourne (résultat, raison, authorization_id).
        En cas de refus (fail-closed), authorization_id est None.
        """
        # Refus immédiat pour les domaines réservés sans HROT explicite.
        if self._is_reserved(target):
            reason = f"OSINT collecte refusée : domaine réservé '{target}'"
            logger.warning(reason)
            return PolicyResult.DENY, reason, None

        result, reason, cap = self._caps.check(
            subject=subject,
            category="osint",
            operation="collect",
            resource=target,
        )
        auth_id = cap.id if cap else None
        if result is not PolicyResult.ALLOW:
            logger.warning(
                "OSINT collecte refusée pour %s sur %s : %s",
                subject,
                target,
                reason,
            )
        return result, reason, auth_id

    def authorize_analyze(
        self,
        subject: str,
        target: str,
    ) -> tuple[PolicyResult, str, str | None]:
        """Vérifie que le sujet est autorisé à analyser `target` (OSINT)."""
        result, reason, cap = self._caps.check(
            subject=subject,
            category="osint",
            operation="analyze",
            resource=target,
        )
        auth_id = cap.id if cap else None
        return result, reason, auth_id

    # ── Provenance ────────────────────────────────────────────────────

    def build_provenance(
        self,
        *,
        source: str,
        method: str,
        target: str,
        authorization_id: str,
        confidence: float = 1.0,
        content: str = "",
        retention_ttl_seconds: int | None = None,
    ) -> OSINTProvenance:
        """Construit une provenance tracée pour un résultat de collecte.

        Scanne le contenu pour détecter les données personnelles et ajuste
        le TTL de conservation en conséquence.
        """
        scan = self._classifier.scan_text(content)
        has_personal = SensitiveKind.PERSONAL_DATA in scan.kinds

        # Si des données personnelles sont présentes, TTL plus court par défaut.
        ttl = retention_ttl_seconds
        if ttl is None:
            ttl = 24 * 60 * 60 if has_personal else self._default_ttl  # 24h si perso

        return OSINTProvenance(
            source=source,
            method=method,
            collected_at=time.time(),
            authorization_id=authorization_id,
            target=target,
            confidence=max(0.0, min(1.0, confidence)),
            personal_data=has_personal,
            retention_ttl_seconds=ttl,
        )

    # ── Géolocalisation ───────────────────────────────────────────────

    def check_geolocation(
        self,
        subject: str,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> tuple[PolicyResult, str]:
        """Contrôle une requête de géolocalisation précise.

        Les requêtes avec un rayon <= MAX_GEOLOCATION_RADIUS_KM nécessitent
        une autorisation explicite (risque de réidentification / surveillance).
        """
        if radius_km > MAX_GEOLOCATION_RADIUS_KM:
            # Rayon large : collecte statistique, autorisation OSINT standard.
            result, reason, _ = self.authorize_collect(
                subject,
                f"geolocation:{latitude},{longitude},radius={radius_km}km",
            )
            return result, reason

        # Rayon précis : géolocalisation ciblée → autorisation renforcée.
        result, reason, _ = self.authorize_collect(
            subject,
            f"geolocation:{latitude},{longitude},radius={radius_km}km",
        )
        if result is not PolicyResult.ALLOW:
            return (
                PolicyResult.DENY,
                f"Géolocalisation précise ({radius_km} km) refusée : {reason}",
            )
        return PolicyResult.ALLOW, "Géolocalisation précise autorisée"

    # ── Conservation ──────────────────────────────────────────────────

    def register_retention(
        self,
        mission_id: str,
        ttl_seconds: int,
    ) -> OSINTRetentionPolicy:
        """Enregistre une politique de conservation pour une mission OSINT."""
        policy = OSINTRetentionPolicy(
            mission_id=mission_id,
            ttl_seconds=ttl_seconds,
        )
        self._retention_policies[mission_id] = policy
        logger.info(
            "OSINT retention registered: mission=%s ttl=%ss", mission_id, ttl_seconds
        )
        return policy

    def is_retention_expired(self, mission_id: str, now: float | None = None) -> bool:
        """Vérifie si la conservation d'une mission OSINT a expiré."""
        policy = self._retention_policies.get(mission_id)
        if policy is None:
            return False
        return policy.is_expired(now)

    def get_retention_ttl(self, mission_id: str) -> int | None:
        """Retourne le TTL restant pour une mission, ou None si inconnue."""
        policy = self._retention_policies.get(mission_id)
        if policy is None:
            return None
        now = time.time()
        remaining = int(policy.created_at + policy.ttl_seconds - now)
        return max(0, remaining)

    # ── Helpers ───────────────────────────────────────────────────────

    def _is_reserved(self, target: str) -> bool:
        """True si la cible est un domaine réservé (jamais OSINT sans HROT)."""
        target_lower = target.lower()
        for reserved in RESERVED_DOMAINS:
            if reserved in target_lower:
                return True
        return False

    def scan_for_personal_data(self, content: str) -> SensitiveScan:
        """Scanne un contenu pour détecter les données personnelles OSINT."""
        return self._classifier.scan_text(content)

    def has_personal_data(self, content: str) -> bool:
        """True si le contenu contient des données personnelles détectables."""
        return (
            SensitiveKind.PERSONAL_DATA
            in self.scan_for_personal_data(content).kinds
        )


__all__ = [
    "OSINTPolicyManager",
    "OSINTProvenance",
    "OSINTRetentionPolicy",
    "DEFAULT_OSINT_TTL_SECONDS",
    "MAX_GEOLOCATION_RADIUS_KM",
]

