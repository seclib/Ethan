"""
Tests du module OSINT Policy (Phase 2-6).

Vérifie :
- Refus d'accès OSINT sans autorisation (capability osint:collect),
- Blocage des opérations à risque disproportionné (géolocalisation précise),
- Traçabilité de la provenance sur chaque collecte,
- Détection des données personnelles et TTL réduit,
- Respect des limites de conservation (TTL),
- Domaines réservés bloqués (localhost, métadonnées cloud, etc.),
- Tentatives de contournement de la politique centrale (fail-closed).
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from core.security.data.sensitive import SensitiveDataClassifier, SensitiveKind
from core.security.osint_policy import (
    DEFAULT_OSINT_TTL_SECONDS,
    MAX_GEOLOCATION_RADIUS_KM,
    OSINTPolicyManager,
    OSINTProvenance,
)
from core.security.policy.capabilities import (
    CapabilityManager,
    RiskLevel,
    resolve_safe_path,
)


@pytest.fixture
def roots(tmp_path: Path) -> list[str]:
    return [str(tmp_path.resolve())]


@pytest.fixture
def cap_manager(roots: list[str]) -> CapabilityManager:
    m = CapabilityManager(allowed_roots=roots)
    m.grant(
        subject="agent:analyst",
        category="osint",
        operation="collect",
        resource=str(Path(roots[0]) / "osint-targets" / "**"),
        scope="self",
        ttl_seconds=3600,
        risk_level=RiskLevel.MEDIUM,
        origin="user:consent",
    )
    return m


@pytest.fixture
def osint_policy(cap_manager: CapabilityManager) -> OSINTPolicyManager:
    return OSINTPolicyManager(cap_manager)


class TestOSINTAuthorization:
    """Autorisation de collecte OSINT."""

    def test_collect_allowed_with_capability(
        self,
        osint_policy: OSINTPolicyManager,
        roots: list[str],
    ) -> None:
        target = str(Path(roots[0]) / "osint-targets" / "example.com")
        result, reason, auth_id = osint_policy.authorize_collect(
            "agent:analyst", target
        )
        assert auth_id is not None
        assert auth_id != ""
    def test_collect_denied_without_capability(
        self,
        osint_policy: OSINTPolicyManager,
        roots: list[str],
    ) -> None:
        target = str(Path(roots[0]) / "osint-targets" / "example.com")
        result, reason, auth_id = osint_policy.authorize_collect(
            "agent:unknown", target
        )
        assert auth_id is None
        assert "fail-closed" in reason or "No matching" in reason

    def test_collect_denied_reserved_domain(
        self,
        osint_policy: OSINTPolicyManager,
    ) -> None:
        result, reason, auth_id = osint_policy.authorize_collect(
            "agent:analyst", "http://localhost:8000"
        )
        assert auth_id is None
        assert "réservé" in reason or "reserved" in reason.lower()

        result, reason, auth_id = osint_policy.authorize_collect(
            "agent:analyst", "http://169.254.169.254/latest/meta-data/"
        )
        assert auth_id is None
        assert "réservé" in reason or "reserved" in reason.lower()

class TestOSINTProvenance:
    """Traçabilité de la provenance."""

    def test_provenance_attached_on_collect(
        self,
        osint_policy: OSINTPolicyManager,
        roots: list[str],
    ) -> None:
        target = str(Path(roots[0]) / "osint-targets" / "example.com")
        result, reason, auth_id = osint_policy.authorize_collect(
            "agent:analyst", target
        )
        assert auth_id is not None

        prov = osint_policy.build_provenance(
            source="duckduckgo",
            method="web_search",
            target=target,
            authorization_id=auth_id,
            content="résultat de recherche public",
            confidence=0.9,
        )
        assert prov.source == "duckduckgo"
        assert prov.method == "web_search"
        assert prov.authorization_id == auth_id
        assert prov.target == target
        assert prov.personal_data is False
        assert prov.confidence == 0.9
        assert prov.retention_ttl_seconds == DEFAULT_OSINT_TTL_SECONDS
        d = prov.to_dict()
        assert d["source"] == "duckduckgo"
        assert d["personal_data"] is False

    def test_provenance_detects_personal_data(
        self,
        osint_policy: OSINTPolicyManager,
        roots: list[str],
    ) -> None:
        target = str(Path(roots[0]) / "osint-targets" / "example.com")
        _, _, auth_id = osint_policy.authorize_collect("agent:analyst", target)

        prov = osint_policy.build_provenance(
            source="web_ingest",
            method="page_fetch",
            target=target,
            authorization_id=auth_id,
            content="Contactez Jean Dupont à jean.dupont@example.com",
        )
        assert prov.personal_data is True
        assert prov.retention_ttl_seconds == 24 * 60 * 60

    def test_provenance_ttl_override(
        self,
        osint_policy: OSINTPolicyManager,
        roots: list[str],
    ) -> None:
        target = str(Path(roots[0]) / "osint-targets" / "example.com")
        _, _, auth_id = osint_policy.authorize_collect("agent:analyst", target)

        prov = osint_policy.build_provenance(
            source="custom",
            method="api",
            target=target,
            authorization_id=auth_id,
            retention_ttl_seconds=3600,
        )
        assert prov.retention_ttl_seconds == 3600

class TestOSINTGeolocation:
    """Contrôle de géolocalisation."""

    def test_geolocation_large_radius_allowed(
        self,
        osint_policy: OSINTPolicyManager,
        roots: list[str],
    ) -> None:
        target = str(Path(roots[0]) / "osint-targets" / "**")
        osint_policy._caps.grant(
            subject="agent:analyst",
            category="osint",
            operation="collect",
            resource=target,
            scope="self",
            ttl_seconds=3600,
            risk_level=RiskLevel.MEDIUM,
            origin="user:consent",
        )
        result, reason = osint_policy.check_geolocation(
            "agent:analyst", 48.8566, 2.3522, radius_km=10.0
        )
        assert result is not None

    def test_geolocation_precise_requires_authorization(
        self,
        osint_policy: OSINTPolicyManager,
    ) -> None:
        result, reason = osint_policy.check_geolocation(
            "agent:analyst", 48.8566, 2.3522, radius_km=0.1
        )
        assert result is not None
        assert "refusée" in reason or "DENY" in str(result) or "refus" in reason.lower()

    def test_max_geolocation_radius_constant(self) -> None:
        assert MAX_GEOLOCATION_RADIUS_KM == 1.0

class TestOSINTRetention:
    """Limites de conservation (TTL)."""

    def test_retention_register_and_expiry(
        self,
        osint_policy: OSINTPolicyManager,
    ) -> None:
        osint_policy.register_retention("mission-1", ttl_seconds=1)
        remaining = osint_policy.get_retention_ttl("mission-1")
        assert remaining is not None
        assert remaining >= 0
        assert osint_policy.is_retention_expired("mission-1") is False

        time.sleep(1.1)
        assert osint_policy.is_retention_expired("mission-1") is True

    def test_unknown_mission_not_expired(
        self,
        osint_policy: OSINTPolicyManager,
    ) -> None:
        assert osint_policy.is_retention_expired("mission-inexistante") is False
        assert osint_policy.get_retention_ttl("mission-inexistante") is None

    def test_default_ttl_constant(self) -> None:
        assert DEFAULT_OSINT_TTL_SECONDS == 7 * 24 * 60 * 60


class TestOSINTPersonalData:
    """Détection des données personnelles dans les résultats OSINT."""

    def test_personal_data_detected(
        self,
        osint_policy: OSINTPolicyManager,
    ) -> None:
        assert osint_policy.has_personal_data(
            "Email: alice@example.com"
        ) is True
        assert osint_policy.has_personal_data(
            "Contenu public sans donnée personnelle"
        ) is False

    def test_scan_returns_kinds(
        self,
        osint_policy: OSINTPolicyManager,
    ) -> None:
        scan = osint_policy.scan_for_personal_data("Contact: bob@firma.fr")
        assert SensitiveKind.PERSONAL_DATA in scan.kinds


class TestOSINTNoCircumvention:
    """Tentatives de contournement de la politique centrale."""

    def test_fail_closed_no_capability(
        self,
        roots: list[str],
    ) -> None:
        m = CapabilityManager(allowed_roots=roots)
        policy = OSINTPolicyManager(m)
        result, reason, auth_id = policy.authorize_collect(
            "agent:attacker", "https://example.com"
        )
        assert auth_id is None
        assert result is not None

    def test_capability_cannot_exceed_scope(
        self,
        roots: list[str],
    ) -> None:
        m = CapabilityManager(allowed_roots=roots)
        m.grant(
            subject="agent:analyst",
            category="osint",
            operation="collect",
            resource=str(Path(roots[0]) / "osint-targets" / "**"),
            scope="self",
            ttl_seconds=3600,
            risk_level=RiskLevel.LOW,
            origin="user:consent",
        )
        policy = OSINTPolicyManager(m)
        result, _, auth_id = policy.authorize_collect(
            "agent:analyst", "/etc/passwd"
        )
        assert auth_id is None

    def test_no_implicit_privilege(
        self,
        roots: list[str],
    ) -> None:
        m = CapabilityManager(allowed_roots=roots)
        policy = OSINTPolicyManager(m)
        result, _, auth_id = policy.authorize_collect(
            "agent:anyone", "https://example.com"
        )
        assert auth_id is None

