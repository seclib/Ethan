"""Politique d'egress du Core — une seule politique pour toute sortie réseau.

Surface auditée : ``core/security/egress.py``, partagé par les serveurs MCP
(``core/tools/server_policy``) et les providers LLM
(``core/llm/provider_factory``).  Un provider LLM est un point de sortie : son
``base_url`` choisit **où partent les conversations**.  Sans garde, enregistrer
un provider suffisait à exporter tout le contexte hors du système, ou à faire
toucher au Core un endpoint de métadonnées cloud (vol de credentials d'instance).

Garantis ici :
- la classe « toujours interdite » (métadonnées, link-local) est refusée, y
  compris quand le mode privé est autorisé et y compris **via le DNS** ;
- les endpoints légitimes d'ETHAN restent acceptés sans dépendre du DNS
  (``ollama``, ``vllm``, ``host.docker.internal``, loopback) — un garde qui
  ferait échouer le boot n'est pas un garde, c'est une régression ;
- les deux surfaces (MCP et LLM) refusent **la même** destination.
"""

from __future__ import annotations

import pytest
from core.llm.provider_factory import create_provider_from_config
from core.security.egress import (
    assert_literal_destination,
    is_forbidden_address,
    validate_egress_url,
)
from core.tools.server_policy import ServerPolicyError, validate_server_config

# ── Classe « toujours interdite » ───────────────────────────────────────────

FORBIDDEN_LITERALS = [
    "http://169.254.169.254/latest/meta-data/",  # AWS/GCP/OpenStack
    "http://100.100.100.200/latest/meta-data/",  # Alibaba Cloud
    "http://[fd00:ec2::254]/",  # IPv6 IMDS
    "http://169.254.169.253/",  # link-local (Azure WireServer)
]


@pytest.mark.parametrize("url", FORBIDDEN_LITERALS)
def test_literal_guard_blocks_metadata_and_link_local(url: str):
    with pytest.raises(ValueError, match="forbidden"):
        assert_literal_destination(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://metadata.goog/",
    ],
)
def test_literal_guard_blocks_metadata_hostnames(url: str):
    with pytest.raises(ValueError, match="metadata endpoint"):
        assert_literal_destination(url)


@pytest.mark.parametrize(
    "address,expected",
    [
        ("169.254.169.254", True),
        ("169.254.1.1", True),  # link-local tout court
        ("fd00:ec2::254", True),
        ("::ffff:169.254.169.254", True),  # IPv4 mappé en IPv6 : même piège
        ("not-an-ip", True),  # non résoluble → refusé (fail-closed)
        ("127.0.0.1", False),
        ("10.0.0.5", False),
        ("8.8.8.8", False),
    ],
)
def test_is_forbidden_address(address: str, expected: bool):
    assert is_forbidden_address(address) is expected


# ── Schémas et credentials inline ───────────────────────────────────────────


@pytest.mark.parametrize(
    "url,reason",
    [
        ("file:///etc/passwd", "scheme"),
        ("gopher://127.0.0.1:11211/", "scheme"),
        ("http:///v1/models", "hostname"),
        ("https://user:pass@api.openai.com/v1", "credentials"),
    ],
)
def test_literal_guard_rejects_bad_structure(url: str, reason: str):
    with pytest.raises(ValueError, match=reason):
        assert_literal_destination(url)


# ── Les destinations légitimes d'ETHAN doivent rester acceptées ─────────────


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://host.docker.internal:11434",  # défault embarqué d'ETHAN
        "http://vllm:8000/v1",  # nom docker-compose
        "http://192.168.1.20:1234/v1",  # LM Studio en LAN
        "https://api.openai.com/v1",
        "https://openrouter.ai/api/v1",
    ],
)
def test_literal_guard_allows_legit_endpoints_without_dns(url: str):
    """Aucune résolution DNS : le boot ne dépend jamais du DNS.

    Ces URL sont exactement les valeurs par défaut de
    ``ProviderManager._default_provider_configs`` ; si ce test échoue,
    ``ethan up`` est cassé.
    """
    assert_literal_destination(url)


def test_literal_guard_preserves_url_verbatim():
    """Le garde normalise son **retour**, mais ETHAN conserve l'URL d'origine.

    Piège évité : ``assert_literal_destination`` renvoie une URL normalisée
    (hostname en minuscules, ``/`` ajouté quand le chemin est vide).  Stocker
    cette valeur à la place de l'URL saisie casserait la jointure des chemins
    côté provider (``.../v1`` + ``/chat/completions``).  Le garde sert donc à
    **valider**, et la factory conserve la chaîne d'origine telle quelle.
    """
    # Retour normalisé (documenté).
    assert assert_literal_destination("http://OLLAMA:11434/v1") == "http://ollama:11434/v1"
    assert assert_literal_destination("http://localhost:11434") == "http://localhost:11434/"

    # Ce qui est réellement persisté par ETHAN : la valeur d'origine.
    provider = create_provider_from_config(
        {"type": "ollama", "name": "local", "base_url": "http://Ollama:11434/v1"}
    )
    assert provider._base_url == "http://Ollama:11434/v1"


# ── Mode complet (avec DNS) : un hostname peut mentir ───────────────────────


def test_dns_pointing_at_metadata_is_refused_even_in_private_mode():
    """``evil.test`` résout vers IMDS → refusé même avec le mode privé actif."""
    with pytest.raises(ValueError, match="forbidden"):
        validate_egress_url(
            "http://evil.test/",
            allow_private=True,
            resolver=lambda _host: ["169.254.169.254"],
        )


def test_private_destination_requires_private_mode():
    with pytest.raises(ValueError):
        validate_egress_url(
            "http://internal.corp/",
            allow_private=False,
            resolver=lambda _host: ["10.10.0.7"],
        )


def test_private_destination_accepted_in_private_mode():
    out = validate_egress_url(
        "http://internal.corp/v1",
        allow_private=True,
        resolver=lambda _host: ["10.10.0.7"],
    )
    assert out == "http://internal.corp/v1"


def test_dns_failure_fails_closed():
    import socket

    def _boom(_host: str) -> list[str]:
        raise socket.gaierror("no dns")

    with pytest.raises(ValueError, match="DNS resolution failed"):
        validate_egress_url("http://nowhere.test/", allow_private=True, resolver=_boom)


# ── Intégration : la factory LLM applique la politique ──────────────────────


@pytest.mark.parametrize("base_url", FORBIDDEN_LITERALS)
def test_provider_factory_refuses_metadata_endpoint(base_url: str):
    with pytest.raises(ValueError, match="invalid provider base_url"):
        create_provider_from_config(
            {"type": "openai", "name": "evil", "base_url": base_url, "api_key": "x"}
        )


@pytest.mark.parametrize("base_url", ["http://ollama:11434", "http://127.0.0.1:8000/v1"])
def test_provider_factory_accepts_local_endpoints(base_url: str):
    config = {"type": "ollama", "name": "local", "base_url": base_url}
    assert create_provider_from_config(config) is not None


def test_provider_factory_rejects_non_http_scheme():
    config = {"type": "ollama", "name": "evil", "base_url": "file:///tmp"}
    with pytest.raises(ValueError, match="invalid provider base_url"):
        create_provider_from_config(config)


# ── Coherence inter-surfaces : une seule politique ──────────────────────────


@pytest.mark.parametrize("base_url", FORBIDDEN_LITERALS)
def test_mcp_and_llm_refuse_the_same_destination(base_url: str):
    """MCP et providers LLM partagent LA même politique (pas deux)."""
    with pytest.raises(ValueError):
        assert_literal_destination(base_url)
    with pytest.raises(ServerPolicyError):
        validate_server_config(name="x", url=base_url, metadata={"transport": "http"})
