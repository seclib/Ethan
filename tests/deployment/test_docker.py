"""Tests for Docker and deployment files.

Vérifie l'intégrité des artefacts de déploiement actuels :
- Dockerfiles dans deploy/ (api, kernel, ui, pg_backup, python-base)
- docker-compose.yml à la racine (services nats, redis, postgres, api)
- unit systemd dans infrastructure/systemd/
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent.parent
DEPLOY_DIR = ROOT / "deploy"
COMPOSE_PATH = ROOT / "docker-compose.yml"
SYSTEMD_DIR = ROOT / "infrastructure" / "systemd"


class TestDockerFiles:
    """Vérifie la présence et la structure des Dockerfiles."""

    def test_dockerfiles_exist(self):
        """Les Dockerfiles de production existent dans deploy/."""
        expected = [
            "Dockerfile.api",
            "Dockerfile.kernel",
            "Dockerfile.ui",
            "Dockerfile.pg_backup",
            "Dockerfile.python-base",
        ]
        for name in expected:
            assert (DEPLOY_DIR / name).is_file(), f"{name} missing in deploy/"

    def test_dockerfile_has_cmd(self):
        """Les Dockerfiles utilisent CMD pour le démarrage."""
        content = (DEPLOY_DIR / "Dockerfile.api").read_text()
        assert "CMD" in content

    def test_dockerfile_copies_source_dirs(self):
        """Les Dockerfiles copient les répertoires source (core, sdk, interfaces)."""
        content = (DEPLOY_DIR / "Dockerfile.api").read_text()
        # La structure actuelle copie les packages individuels (pas src/ monolithique)
        assert "COPY core/ core/" in content
        assert "COPY sdk/ sdk/" in content


class TestDockerCompose:
    """Vérifie la structure du docker-compose.yml racine."""

    def test_docker_compose_exists(self):
        assert COMPOSE_PATH.is_file()

    def test_docker_compose_valid_yaml(self):
        import importlib

        yaml_mod = None
        try:
            yaml_mod = importlib.import_module("yaml")
        except ImportError:
            pass

        content = COMPOSE_PATH.read_text()
        assert "services:" in content

        if yaml_mod is not None:
            data = yaml_mod.safe_load(content)
            assert "services" in data

    def test_docker_compose_has_core_services(self):
        """Les services infrastructure minimaux sont présents."""
        content = COMPOSE_PATH.read_text()
        for service in ("nats:", "redis:", "postgres:"):
            assert service in content, f"service {service} missing from compose"


class TestSystemdUnit:
    """Vérifie la présence du unit systemd."""

    def test_systemd_unit_exists(self):
        """Le unit ethan-core existe dans infrastructure/systemd/."""
        assert (SYSTEMD_DIR / "ethan-core.service").is_file()

    def test_systemd_unit_content(self):
        """Le unit démarre la stack via ethan up."""
        content = (SYSTEMD_DIR / "ethan-core.service").read_text()
        assert "ethan" in content.lower()
        assert "ExecStart" in content
