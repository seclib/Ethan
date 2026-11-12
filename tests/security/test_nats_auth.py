"""Tests d'authentification NATS — CTO P0-3 / Red Team « NATS sans auth ».

Le serveur ETHAN exige ``authorization { token: $NATS_TOKEN }``
(``infrastructure/nats/nats-server.conf``) : sans token, le démarrage échoue
(fail-closed, vérifié empiriquement contre ``nats:2.10-alpine``). Ces tests
verifient que :

- la configuration serveur (single + cluster) exige bien le token ;
- chaque service client reçoit ``NATS_TOKEN`` via docker-compose ;
- chaque point de connexion du code transmet ``nats_connect_options()``
  (garde-fou statique anti-régression : un site oublié = connexion refusée).

Ces tests ne touchent ni Docker ni le réseau.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from core.bus.nats_auth import nats_connect_options, nats_token

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Services qui se connectent au bus (clients obligatoires du token).
COMPOSE_CLIENT_SERVICES = ("api", "kernel", "modules")
# Confs des nœuds du cluster (patch docker-compose.cluster.yml).
CLUSTER_CONFS = (
    PROJECT_ROOT / "deploy" / "nats" / "nats-1.conf",
    PROJECT_ROOT / "deploy" / "nats" / "nats-2.conf",
    PROJECT_ROOT / "deploy" / "nats" / "nats-3.conf",
)
SINGLE_CONF = PROJECT_ROOT / "infrastructure" / "nats" / "nats-server.conf"


# ── Options de connexion (client) ────────────────────────────────────────────


class TestNatsConnectOptions:
    def test_token_present_when_env_defined(self, monkeypatch) -> None:
        monkeypatch.setenv("NATS_TOKEN", "ethan-unit-token")
        assert nats_token() == "ethan-unit-token"
        assert nats_connect_options() == {"token": "ethan-unit-token"}

    def test_no_options_when_env_absent(self, monkeypatch) -> None:
        monkeypatch.delenv("NATS_TOKEN", raising=False)
        assert nats_token() is None
        assert nats_connect_options() == {}

    def test_blank_token_treated_as_absent(self, monkeypatch) -> None:
        monkeypatch.setenv("NATS_TOKEN", "   ")
        assert nats_token() is None
        assert nats_connect_options() == {}


# ── Configuration serveur ────────────────────────────────────────────────────


class TestServerConfigRequiresToken:
    def test_single_node_conf_requires_env_token(self) -> None:
        conf = SINGLE_CONF.read_text(encoding="utf-8")
        assert "authorization" in conf
        # Résolution d'environnement (non quotée) : le serveur refuse de
        # démarrer si la variable est absente.
        assert re.search(r"token:\s*\$NATS_TOKEN\b", conf), conf

    def test_cluster_confs_require_env_token(self) -> None:
        for conf_path in CLUSTER_CONFS:
            conf = conf_path.read_text(encoding="utf-8")
            assert "authorization" in conf, conf_path
            assert re.search(r"token:\s*\$NATS_TOKEN\b", conf), conf_path


# ── docker-compose : le token est distribué à tous les clients ──────────────


class TestComposeDistributesToken:
    def _load(self, name: str) -> dict:
        return yaml.safe_load((PROJECT_ROOT / name).read_text(encoding="utf-8"))

    def test_single_node_server_gets_token_and_conf(self) -> None:
        services = self._load("docker-compose.yml")["services"]
        nats = services["nats"]
        assert "NATS_TOKEN" in (nats.get("environment") or {})
        # Conf montée + activée via -c (authorization réellement chargé).
        assert any("nats-server.conf" in str(v) for v in nats.get("volumes", []))
        assert "-c" in nats["command"]
        assert any("nats-server.conf" in str(part) for part in nats["command"])

    def test_every_client_service_receives_token(self) -> None:
        services = self._load("docker-compose.yml")["services"]
        for name in COMPOSE_CLIENT_SERVICES:
            env = services[name].get("environment") or {}
            assert "NATS_TOKEN" in env, f"service {name} sans NATS_TOKEN"

    def test_cluster_nodes_receive_token(self) -> None:
        services = self._load("docker-compose.cluster.yml")["services"]
        for name in ("nats", "nats-2", "nats-3"):
            env = services[name].get("environment") or {}
            assert "NATS_TOKEN" in env, f"nœud cluster {name} sans NATS_TOKEN"


# ── Régression statique : aucun point de connexion sans le token ────────────


class TestNoUnauthenticatedConnectSite:
    """Tout ``nats.connect`` du code actif doit passer par le helper.

    Les fichiers sous ``archive/`` (legacy hors périmètre) sont exclus.
    """

    def test_all_connect_calls_include_auth_options(self) -> None:
        offenders: list[str] = []
        for root in ("core", "interfaces", "plugins", "runtime", "kernel"):
            base = PROJECT_ROOT / root
            if not base.exists():
                continue
            for path in base.rglob("*.py"):
                text = path.read_text(encoding="utf-8", errors="replace")
                lines = text.splitlines()
                for lineno, line in enumerate(lines, 1):
                    if "nats.connect(" in line:
                        # L'appel peut être multi-lignes : on inspecte la
                        # fenêtre de 6 lignes à partir de la détection.
                        window = "\n".join(lines[lineno - 1 : lineno + 5])
                        if "nats_connect_options" not in window:
                            offenders.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno}")
        assert not offenders, (
            "Points de connexion NATS sans nats_connect_options() (CTO P0-3) : "
            + ", ".join(offenders)
        )


# ── Transmission effective du token par l'EventBus ──────────────────────────


class TestEventBusTransmitsToken:
    def test_bus_connect_passes_token_to_nats(self, monkeypatch) -> None:
        import asyncio

        import core.bus.nats_bus as nats_bus

        if not nats_bus.NATS_AVAILABLE:
            import pytest

            pytest.skip("nats-py non installé")

        captured: dict = {}

        async def _fake_connect(url, **kwargs):
            captured.update({"url": url, **kwargs})
            raise RuntimeError("stop after capture")

        monkeypatch.setattr(nats_bus.nats, "connect", _fake_connect)
        monkeypatch.setenv("NATS_TOKEN", "ethan-bus-token")

        bus = nats_bus.EventBus(servers="nats://localhost:4222")
        try:
            asyncio.run(bus.connect())
        except RuntimeError as exc:
            assert "stop after capture" in str(exc)

        assert captured.get("token") == "ethan-bus-token"
