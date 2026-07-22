"""ETHAN Boot Diagnostic — explains why ETHAN won't start.

Usage:
    from interfaces.cli.core.diagnostic import BootDiagnostic

    diag = BootDiagnostic()
    results = diag.check_all()
    print(diag.explain_failure())
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""
    name: str
    passed: bool
    detail: str = ""
    fix: str = ""


@dataclass
class DiagnosticReport:
    """Full diagnostic report."""
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failures(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total_count(self) -> int:
        return len(self.checks)


class BootDiagnostic:
    """Diagnostique pourquoi ETHAN ne démarre pas.

    Vérifie les prérequis système et les services avant un `ethan up`.
    """

    REQUIRED_PORTS = [8000, 8080, 3000, 4222, 6379, 5432]
    MIN_MEMORY_GB = 4
    MIN_DISK_GB = 10

    def __init__(self):
        self._docker_available: Optional[bool] = None

    def check_all(self) -> DiagnosticReport:
        """Run all diagnostic checks and return a report."""
        return DiagnosticReport(checks=[
            self._check_docker(),
            self._check_docker_compose(),
            self._check_memory(),
            self._check_disk(),
            self._check_ports(),
            self._check_compose_file(),
        ])

    def explain_failure(self) -> str:
        """Generate a human-readable explanation of why ETHAN won't start."""
        report = self.check_all()

        if report.all_passed:
            return (
                "✓ Tous les prérequis sont satisfaits.\n"
                "  ETHAN devrait démarrer. Essayez : ethan up"
            )

        lines = [
            f"✗ {len(report.failures)} problème(s) détecté(s) — ETHAN ne peut pas démarrer :",
            "",
        ]

        for i, failure in enumerate(report.failures, 1):
            lines.append(f"  {i}. {failure.name}")
            if failure.detail:
                lines.append(f"     → {failure.detail}")
            if failure.fix:
                lines.append(f"     ↳ {failure.fix}")
            lines.append("")

        lines.append(f"  ({report.passed_count}/{report.total_count} checks OK)")
        return "\n".join(lines)

    # ─── Individual checks ──────────────────────────────────────────

    def _check_docker(self) -> CheckResult:
        """Check if Docker daemon is running."""
        if shutil.which("docker") is None:
            return CheckResult(
                name="Docker installé",
                passed=False,
                detail="La commande 'docker' est introuvable dans le PATH",
                fix="Installez Docker : https://docs.docker.com/get-docker/",
            )

        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return CheckResult(
                    name="Docker daemon actif",
                    passed=False,
                    detail="Docker est installé mais le daemon ne répond pas",
                    fix="Démarrez le daemon : sudo systemctl start docker",
                )
            return CheckResult(
                name="Docker daemon actif",
                passed=True,
                detail="Docker répond correctement",
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name="Docker daemon actif",
                passed=False,
                detail="Docker ne répond pas (timeout 5s)",
                fix="Redémarrez Docker : sudo systemctl restart docker",
            )
        except Exception as e:
            return CheckResult(
                name="Docker daemon actif",
                passed=False,
                detail=f"Erreur : {e}",
                fix="Vérifiez l'installation de Docker",
            )

    def _check_docker_compose(self) -> CheckResult:
        """Check if docker compose plugin is available."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return CheckResult(
                    name="Docker Compose",
                    passed=False,
                    detail="Le plugin 'docker compose' n'est pas disponible",
                    fix="Installez le plugin compose : sudo apt install docker-compose-plugin",
                )
            version = result.stdout.strip().split("\n")[0]
            return CheckResult(
                name="Docker Compose",
                passed=True,
                detail=version,
            )
        except FileNotFoundError:
            return CheckResult(
                name="Docker Compose",
                passed=False,
                detail="'docker compose' n'est pas une commande valide",
                fix="Installez le plugin compose v2 : https://docs.docker.com/compose/install/",
            )
        except Exception as e:
            return CheckResult(
                name="Docker Compose",
                passed=False,
                detail=f"Erreur : {e}",
                fix="Vérifiez l'installation de Docker Compose",
            )

    def _check_memory(self) -> CheckResult:
        """Check available system memory."""
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        kb = int(line.split()[1])
                        gb = kb / (1024 * 1024)
                        if gb >= self.MIN_MEMORY_GB:
                            return CheckResult(
                                name="Mémoire RAM",
                                passed=True,
                                detail=f"{gb:.1f} Go disponible",
                            )
                        return CheckResult(
                            name="Mémoire RAM",
                            passed=False,
                            detail=f"Seulement {gb:.1f} Go disponible (minimum {self.MIN_MEMORY_GB} Go)",
                            fix="Libérez de la mémoire ou ajoutez de la RAM",
                        )
            return CheckResult(
                name="Mémoire RAM",
                passed=False,
                detail="Impossible de lire /proc/meminfo",
                fix="Vérifiez le système d'exploitation",
            )
        except Exception as e:
            return CheckResult(
                name="Mémoire RAM",
                passed=False,
                detail=f"Erreur : {e}",
                fix="Vérifiez /proc/meminfo",
            )

    def _check_disk(self) -> CheckResult:
        """Check available disk space."""
        try:
            stat = os.statvfs("/var/lib/docker" if os.path.exists("/var/lib/docker") else ".")
            free_bytes = stat.f_bavail * stat.f_frsize
            free_gb = free_bytes / (1024 ** 3)
            if free_gb >= self.MIN_DISK_GB:
                return CheckResult(
                    name="Espace disque",
                    passed=True,
                    detail=f"{free_gb:.1f} Go disponible",
                )
            return CheckResult(
                name="Espace disque",
                passed=False,
                detail=f"Seulement {free_gb:.1f} Go disponible (minimum {self.MIN_DISK_GB} Go)",
                fix="Libérez de l'espace disque : docker system prune -a",
            )
        except Exception as e:
            return CheckResult(
                name="Espace disque",
                passed=False,
                detail=f"Erreur : {e}",
                fix="Vérifiez l'espace disque",
            )

    def _check_ports(self) -> CheckResult:
        """Check if required ports are free."""
        occupied = []
        for port in self.REQUIRED_PORTS:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                occupied.append(port)

        if not occupied:
            return CheckResult(
                name="Ports requis",
                passed=True,
                detail=f"Tous les ports libres ({', '.join(map(str, self.REQUIRED_PORTS))})",
            )

        return CheckResult(
            name="Ports requis",
            passed=False,
            detail=f"Ports occupés : {', '.join(map(str, occupied))}",
            fix="Arrêtez les services utilisant ces ports ou changez-les dans .env",
        )

    def _check_compose_file(self) -> CheckResult:
        """Check if docker-compose.yml exists."""
        compose_path = os.path.join(os.getcwd(), "docker-compose.yml")
        if os.path.exists(compose_path):
            return CheckResult(
                name="docker-compose.yml",
                passed=True,
                detail="Présent",
            )
        return CheckResult(
            name="docker-compose.yml",
            passed=False,
            detail="Fichier introuvable dans le répertoire courant",
            fix="Exécutez depuis la racine du projet ETHAN",
        )
