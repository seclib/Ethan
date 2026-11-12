"""Tests for Docker and deployment files.

Vérifie l'intégrité des artefacts de déploiement actuels :
- Dockerfiles dans deploy/ (api, kernel, ui, pg_backup, python-base)
- docker-compose.yml à la racine (services nats, redis, postgres, api)
- unit systemd dans infrastructure/systemd/
"""

from __future__ import annotations

from pathlib import Path

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

    def test_api_knows_kernel_url(self):
        """L'API reçoit l'URL interne du kernel (nom de service Docker).

        Régression : sans ``ETHAN_KERNEL_URL``, ``SystemDiagnostics`` retombait
        sur ``http://localhost:8080`` — adresse invalide depuis le conteneur
        ``api`` — et le WebUI affichait « Kernel Runtime injoignable ».
        """
        import importlib

        yaml_mod = importlib.import_module("yaml")
        data = yaml_mod.safe_load(COMPOSE_PATH.read_text())
        api_env = data["services"]["api"].get("environment", {})
        kernel_url = api_env.get("ETHAN_KERNEL_URL")
        assert kernel_url == "http://kernel:8080", (
            f"api.ETHAN_KERNEL_URL must target the kernel service, got: {kernel_url!r}"
        )

    def test_kernel_port_published_on_host(self):
        """Le port 8080 reste publié sur le host (diagnostics/administration)."""
        import importlib

        yaml_mod = importlib.import_module("yaml")
        data = yaml_mod.safe_load(COMPOSE_PATH.read_text())
        ports = data["services"]["kernel"].get("ports", [])
        assert any("8080" in str(port) for port in ports), (
            f"kernel must publish 8080 for host access, got: {ports}"
        )


class TestPythonDependencies:
    """Cohérence entre les dépendances Python déclarées et le code."""

    def test_psutil_is_declared(self):
        """``psutil`` est requis par ``core/diagnostics/system.py``.

        Il doit rester déclaré dans l'extra ``server`` (installé dans l'image
        de base commune) : sans lui, les métriques CPU/mémoire du diagnostic
        tombent en ``unavailable``.
        """
        content = (ROOT / "pyproject.toml").read_text()
        assert "psutil" in content, "psutil missing from pyproject.toml"


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
