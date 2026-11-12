"""Tests sécurité — garde-fou SSRF du Core (core.knowledge.web_ingest).

Ce fichier remplace l'ancien test de l'ancien module « openjarvis.security.ssrf »
(retiré). La protection SSRF d'ETHAN vit désormais dans
``core.knowledge.web_ingest._validate_public_url`` : elle est appliquée à
chaque URL avant toute récupération (fail-closed).

Plage couverte :
- schémas non-web (file, gopher, ...) rejetés ;
- localhost et hostnames locaux (``.local``) rejetés ;
- littéraux IP privés (RFC1918, loopback, link-local, multicast, broadcast)
  rejetés, y compris formes IPv6 (``::ffff:``, ``::127.0.0.1``, ``::``) ;
- DNS résolu : toutes les adresses doivent être publiques ;
- résolution DNS en échec ⇒ refuse (fail-closed) ;
- URL publique avec DNS public ⇒ autorisée et normalisée.
"""

from __future__ import annotations

import pytest
from core.knowledge.web_ingest import _validate_public_url


def _resolver(*addresses: str):
    """Construit un résolveur DNS factice retournant les adresses données."""

    def _resolve(_hostname: str) -> list[str]:
        return list(addresses)

    return _resolve


PUBLIC_IPS = ("93.184.216.34", "1.1.1.1")


class TestIsPrivateLiteral:
    """Littéraux IP : jamais autorisés (quelle que soit la forme)."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/",
            "http://127.255.255.255/",
            "http://10.0.0.1/",
            "http://10.255.255.255/",
            "http://172.16.0.1/",
            "http://172.31.255.255/",
            "http://192.168.0.1/",
            "http://192.168.1.100/",
            "http://169.254.0.1/",  # link-local
            "http://0.0.0.0/",
            "http://0.1.2.3/",  # 0.0.0.0/8 route vers localhost
            "http://239.0.0.1/",  # multicast
            "http://255.255.255.255/",  # broadcast
            "http://[::1]/",
            "http://[::ffff:127.0.0.1]/",  # IPv4-mapped loopback
            "http://[::ffff:10.0.0.1]/",  # IPv4-mapped RFC1918
            "http://[::ffff:192.168.1.1]/",
            "http://[::ffff:169.254.169.254]/",  # IPv4-mapped link-local / AWS
            "http://[::127.0.0.1]/",  # IPv4-compatible loopback
        ],
    )
    def test_blocks_private_literal(self, url: str) -> None:
        with pytest.raises(ValueError):
            _validate_public_url(url, _resolver(*PUBLIC_IPS))


class TestSchemeAndHost:
    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "gopher://127.0.0.1:70/",
            "ftp://example.com/file",
            "ssh://example.com",
            "//example.com/path",  # pas de schéma
            "http:///",  # pas de hostname
        ],
    )
    def test_rejects_non_web_schemes(self, url: str) -> None:
        with pytest.raises(ValueError):
            _validate_public_url(url, _resolver(*PUBLIC_IPS))

    def test_rejects_localhost_hostnames(self) -> None:
        with pytest.raises(ValueError, match="localhost"):
            _validate_public_url("http://localhost:8000/", _resolver(*PUBLIC_IPS))
        with pytest.raises(ValueError, match=r"\.local"):
            _validate_public_url("http://internal.local/", _resolver(*PUBLIC_IPS))

    def test_rejects_aws_metadata(self) -> None:
        with pytest.raises(ValueError):
            _validate_public_url("http://169.254.169.254/latest/meta-data/", _resolver(*PUBLIC_IPS))
        with pytest.raises(ValueError):
            _validate_public_url("http://metadata.google.internal/", _resolver("169.254.169.254"))


class TestDnsResolution:
    """Logique de résolution DNS : fail-closed sur l'ensemble des adresses."""

    def test_rejects_dns_resolving_to_private(self) -> None:
        with pytest.raises(ValueError, match="non publique"):
            _validate_public_url("http://internal.example.com/api", _resolver("10.0.0.5"))

    def test_rejects_mixed_public_and_private(self) -> None:
        # Une seule adresse privée parmi plusieurs ⇒ refus (fail-closed).
        with pytest.raises(ValueError):
            _validate_public_url("http://dual.example.com/", _resolver("8.8.8.8", "192.168.1.1"))

    def test_rejects_dns_failure(self) -> None:
        def _broken(_hostname: str) -> list[str]:
            raise OSError("NXDOMAIN")

        with pytest.raises(ValueError, match="DNS"):
            _validate_public_url("http://does-not-exist.example.com/", _broken)

    def test_rejects_dns_no_addresses(self) -> None:
        with pytest.raises(ValueError, match="Aucune adresse"):
            _validate_public_url("http://no-address.example.com/", _resolver())

    def test_allows_public_url_with_public_dns(self) -> None:
        normalized = _validate_public_url(
            "https://Example.com/Path?q=1#frag", _resolver(*PUBLIC_IPS)
        )
        assert normalized == "https://example.com/Path?q=1"
        # host normalisé en minuscules, fragment retiré.


__all__ = [
    "TestDnsResolution",
    "TestIsPrivateLiteral",
    "TestSchemeAndHost",
]
