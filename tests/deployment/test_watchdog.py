"""Tests du circuit breaker de ``scripts/cmd-watchdog.sh`` (Phase 3.3 du plan Boot).

Régression couverte : l'ancien watchdog ne filtrait que ``status=exited``.
Sous ``restart: unless-stopped`` (tous les services ETHAN), un crash-loop
apparaît en état ``restarting`` — jamais ``exited`` — donc le watchdog était
aveugle au seul cas qui compte. Il resetait aussi son compteur global après
chaque alerte, ce qui relançait les redémarrages en boucle indéfiniment.

Le script est exercé face à un stub ``docker`` injecté dans ``PATH`` :
aucune stack réelle n'est requise. Le test d'intégration final est ignoré
si la stack ETHAN n'est pas démarrée.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "cmd-watchdog.sh"

# Stub `docker` : piloté par les fichiers de DOCKER_STUB_DIR.
#   ps-output.json : lignes JSON renvoyées par `compose ps --format json`
#   ps-fail        : si présent, `compose ps` échoue (exit 1)
#   up-calls.log   : journal des `compose up -d <service>`
_STUB = """#!/usr/bin/env bash
set -u
STUB_DIR="${DOCKER_STUB_DIR:?DOCKER_STUB_DIR requis}"
if [[ "${1:-}" == "compose" ]]; then
    shift
    while [[ "${1:-}" == "-f" ]]; do shift 2; done
    case "${1:-}" in
        ps)
            if [[ -f "${STUB_DIR}/ps-fail" ]]; then exit 1; fi
            cat "${STUB_DIR}/ps-output.json" 2>/dev/null || true
            ;;
        up)
            echo "$*" >> "${STUB_DIR}/up-calls.log"
            ;;
    esac
fi
exit 0
"""


class WatchdogHarness:
    """Environnement isolé : stub docker + fichier d'état + runner."""

    def __init__(self, tmp_path: Path, max_restarts: int = 5) -> None:
        self.tmp_path = tmp_path
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        stub = bin_dir / "docker"
        stub.write_text(_STUB)
        stub.chmod(0o755)

        self.ps_output = tmp_path / "ps-output.json"
        self.ps_output.write_text("")
        self.state_file = tmp_path / "watchdog-state"

        self.env = os.environ.copy()
        self.env["PATH"] = f"{bin_dir}:{self.env['PATH']}"
        self.env["DOCKER_STUB_DIR"] = str(tmp_path)
        self.env["ETHAN_WATCHDOG_STATE"] = str(self.state_file)
        self.env["ETHAN_WATCHDOG_MAX_RESTARTS"] = str(max_restarts)

    def set_services(self, *services: tuple[str, str]) -> None:
        """Définit l'état Docker simulé : tuples ``(Service, State)``."""
        lines = [json.dumps({"Service": s, "State": st}) for s, st in services]
        self.ps_output.write_text("\n".join(lines) + ("\n" if lines else ""))

    def fail_ps(self) -> None:
        """Force l'échec de ``docker compose ps`` (daemon/compose KO)."""
        (self.tmp_path / "ps-fail").touch()

    def run(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=str(ROOT),
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def up_calls(self) -> list[str]:
        """Les ``up -d <service>`` réellement exécutés par le watchdog."""
        log = self.tmp_path / "up-calls.log"
        if not log.exists():
            return []
        return [line for line in log.read_text().splitlines() if line.strip()]

    def write_state(self, counts: dict[str, int]) -> None:
        self.state_file.write_text("".join(f"{svc} {cnt}\n" for svc, cnt in counts.items()))

    def read_state(self) -> dict[str, int]:
        if not self.state_file.exists():
            return {}
        result: dict[str, int] = {}
        for line in self.state_file.read_text().splitlines():
            parts = line.split()
            if len(parts) == 2:
                result[parts[0]] = int(parts[1])
        return result


@pytest.fixture()
def wd(tmp_path: Path) -> WatchdogHarness:
    return WatchdogHarness(tmp_path)


@pytest.fixture()
def wd_max3(tmp_path: Path) -> WatchdogHarness:
    """Watchdog avec MAX_RESTARTS=3 pour accélérer le test du circuit."""
    return WatchdogHarness(tmp_path, max_restarts=3)


class TestCircuitBreaker:
    """Le cœur de la Phase 3.3 : détection, redémarrage borné, réarmement."""

    def test_silencieux_quand_tout_va_bien(self, wd: WatchdogHarness):
        wd.set_services(("api", "running"), ("kernel", "running"))
        result = wd.run()
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert wd.up_calls() == []
        assert not wd.state_file.exists()

    def test_service_exited_est_redemarre(self, wd: WatchdogHarness):
        wd.set_services(("api", "exited"), ("kernel", "running"))
        result = wd.run()
        assert result.returncode == 0
        assert wd.up_calls() == ["up -d api"]
        assert wd.read_state() == {"api": 1}

    def test_crash_loop_restarting_est_detecte(self, wd: WatchdogHarness):
        """Régression : un crash-loop (``restart: unless-stopped``) est ``restarting``."""
        wd.set_services(("api", "restarting"))
        result = wd.run()
        assert result.returncode == 0
        assert wd.up_calls() == ["up -d api"]
        assert wd.read_state() == {"api": 1}

    def test_etat_dead_est_detecte(self, wd: WatchdogHarness):
        wd.set_services(("api", "dead"))
        wd.run()
        assert wd.up_calls() == ["up -d api"]

    def test_circuit_ouvert_stoppe_les_redemarrages(self, wd_max3: WatchdogHarness):
        """Après MAX échecs consécutifs : plus aucun redémarrage (fin des boucles)."""
        wd = wd_max3
        wd.set_services(("api", "restarting"))

        for _ in range(3):
            result = wd.run()
            assert result.returncode == 0  # sous le seuil : encore des restarts

        assert wd.up_calls() == ["up -d api"] * 3
        assert wd.read_state() == {"api": 3}

        # 4e échec consécutif → circuit ouvert
        result = wd.run()
        assert result.returncode == 1
        assert "Circuit ouvert" in result.stdout
        assert wd.up_calls() == ["up -d api"] * 3  # AUCUN nouveau restart
        assert wd.read_state() == {"api": 4}

    def test_alerte_unique_a_l_ouverture(self, wd_max3: WatchdogHarness):
        wd = wd_max3
        wd.set_services(("api", "exited"))
        for _ in range(4):
            wd.run()

        # 5e cycle : circuit déjà ouvert → message de continuation uniquement
        result = wd.run()
        assert result.returncode == 1
        assert "toujours ouvert" in result.stdout
        assert "Circuit ouvert" not in result.stdout

    def test_rearmement_progressif_apres_stabilite(self, wd: WatchdogHarness):
        """Un service stable décrémente le compteur d'un cran par cycle."""
        wd.write_state({"api": 2})
        wd.set_services(("api", "running"))

        wd.run()
        assert wd.read_state() == {"api": 1}

        wd.run()
        assert wd.read_state() == {}
        assert not wd.state_file.exists()

    def test_ps_en_echec_remonte_une_erreur(self, wd: WatchdogHarness):
        wd.fail_ps()
        result = wd.run()
        assert result.returncode == 1
        assert "Impossible d'interroger" in result.stdout

    def test_services_multiples_compteurs_independants(self, wd: WatchdogHarness):
        """Deux services en échec ont des compteurs séparés."""
        wd.set_services(("api", "restarting"), ("ui", "exited"))
        wd.run()
        assert wd.read_state() == {"api": 1, "ui": 1}
        assert sorted(wd.up_calls()) == ["up -d api", "up -d ui"]


class TestScriptContract:
    """Contrat statique du script."""

    def test_script_existe(self):
        assert SCRIPT.is_file()

    def test_syntaxe_bash_valide(self):
        result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


# ── Intégration : vraie stack (ignoré si non démarrée) ────────────────────


def _docker_stack_ready() -> bool:
    """True si le conteneur Compose ``nats`` tourne (stack ETHAN démarrée)."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "nats", "--format", "json"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return '"State":"running"' in result.stdout


requires_docker_stack = pytest.mark.skipif(
    not _docker_stack_ready(),
    reason="Stack Docker ETHAN non démarrée (docker compose ps nats vide)",
)


class TestLiveStack:
    """Le vrai script face à la vraie stack : silencieux quand tout est sain."""

    @requires_docker_stack
    def test_silencieux_sur_stack_saine(self, tmp_path: Path):
        env = os.environ.copy()
        env["ETHAN_WATCHDOG_STATE"] = str(tmp_path / "state")
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.strip() == ""


# ── Intégration : projet Compose jetable (bout en bout) ───────────────────


def _docker_available() -> bool:
    """True si le daemon Docker répond."""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


requires_docker = pytest.mark.skipif(not _docker_available(), reason="Docker daemon indisponible")


# Image locale (aucun pull réseau) + entrypoint neutralisé : le service
# « sleeper » reste simplement en vie jusqu'au stop du test.
_TEMP_COMPOSE = """\
services:
  sleeper:
    image: nginx:alpine
    entrypoint: ["sleep"]
    command: ["300"]
"""


@requires_docker
class TestLiveTempStack:
    """Bout en bout : un vrai conteneur stoppé est détecté et redémarré.

    Le projet Compose jetable est isolé de la stack ETHAN (nom de projet
    dérivé du dossier temporaire) ; ``COMPOSE_FILE`` est surchargé via
    l'environnement. Régression : sans ``ps --all``, un conteneur stoppé
    est invisible, donc jamais redémarré.
    """

    @pytest.fixture()
    def temp_stack(self, tmp_path: Path):
        compose = tmp_path / "compose.yml"
        compose.write_text(_TEMP_COMPOSE)

        def _compose(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                ["docker", "compose", "-f", str(compose), *args],
                capture_output=True,
                text=True,
                timeout=60,
            )

        up = _compose("up", "-d")
        if up.returncode != 0:
            pytest.skip(f"stack jetable non démarrée : {up.stderr.strip()}")
        try:
            yield compose, _compose
        finally:
            _compose("down", "-v", "--remove-orphans")

    def test_conteneur_stoppe_est_redemarre(self, tmp_path: Path, temp_stack):
        compose, _compose = temp_stack

        # Stop volontaire → état `exited` (invisible sans `ps --all`).
        stopped = _compose("stop", "sleeper")
        assert stopped.returncode == 0, stopped.stderr

        state_file = tmp_path / "watchdog-state"
        env = os.environ.copy()
        env["COMPOSE_FILE"] = str(compose)
        env["ETHAN_WATCHDOG_STATE"] = str(state_file)

        result = subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Détection + redémarrage effectifs
        assert "sleeper" in result.stdout, result.stdout + result.stderr
        assert state_file.read_text().strip() == "sleeper 1"

        ps = _compose("ps", "sleeper", "--format", "json")
        assert '"State":"running"' in ps.stdout, ps.stdout + ps.stderr
