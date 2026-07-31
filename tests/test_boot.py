"""Boot Integration Test — Vérifie que ./ethan up fonctionne sans erreur."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

# ── Constants ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
API_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{API_URL}/health"
HEALTH_DETAILED = f"{API_URL}/health/detailed"
TIMEOUT_SECONDS = 120  # 2 minutes max for boot
POLL_INTERVAL = 5


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Helpers ────────────────────────────────────────────────────────────────

def run_cmd(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run a CLI command and return result."""
    return subprocess.run(
        cmd,
        cwd=cwd or str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )


async def wait_for_service(
    url: str,
    expected_status: int = 200,
    timeout: int = TIMEOUT_SECONDS,
) -> dict | None:
    """Poll an endpoint until it returns expected status or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == expected_status:
                return resp.json()
        except (requests.ConnectionError, requests.Timeout):
            pass
        await asyncio.sleep(POLL_INTERVAL)
    return None


# ── Tests ──────────────────────────────────────────────────────────────────

class TestBoot:
    """Test suite for ETHAN boot sequence."""

    def test_docker_compose_file_exists(self):
        """Vérifie que docker-compose.yml existe."""
        assert DOCKER_COMPOSE_FILE.exists(), (
            f"docker-compose.yml not found at {DOCKER_COMPOSE_FILE}"
        )

    def test_docker_compose_config_valid(self):
        """Vérifie que la configuration docker-compose est valide."""
        result = run_cmd(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "config"]
        )
        assert result.returncode == 0, (
            f"Invalid docker-compose config:\n{result.stderr}"
        )

    def test_docker_is_running(self):
        """Vérifie que Docker est disponible."""
        result = run_cmd(["docker", "info", "--format", "{{.ServerVersion}}"])
        assert result.returncode == 0, (
            f"Docker not available:\n{result.stderr}"
        )
        assert result.stdout.strip(), "Docker version not detected"

    def test_docker_compose_ls(self):
        """Vérifie que le projet ethan est listé par docker compose."""
        result = run_cmd(["docker", "compose", "ls", "--filter", "name=ethan"])
        assert result.returncode == 0
        assert "ethan" in result.stdout, "ETHAN project not found in docker compose ls"

    def test_all_services_healthy(self):
        """Vérifie que tous les services sont healthy."""
        result = run_cmd(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "ps", "--format", "json"]
        )
        assert result.returncode == 0

        # Parse JSON lines
        services = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    services.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        assert len(services) >= 6, (
            f"Expected at least 6 services, got {len(services)}"
        )

        # Check each service status
        for svc in services:
            name = svc.get("Name", "unknown")
            status = svc.get("Status", "")
            assert "healthy" in status.lower() or "running" in status.lower(), (
                f"Service {name} is not healthy: {status}"
            )

    @pytest.mark.asyncio
    async def test_api_health_endpoint(self):
        """Vérifie que l'API répond sur /health."""
        result = await wait_for_service(HEALTH_ENDPOINT)
        assert result is not None, (
            f"API health endpoint not responding after {TIMEOUT_SECONDS}s"
        )
        assert result.get("status") == "ok", (
            f"API health check failed: {result}"
        )
        assert result.get("service") == "api", (
            f"Expected service='api', got: {result}"
        )

    @pytest.mark.asyncio
    async def test_api_detailed_health(self):
        """Vérifie que tous les services de l'API sont connectés."""
        result = await wait_for_service(HEALTH_DETAILED)
        assert result is not None, (
            f"API detailed health not responding after {TIMEOUT_SECONDS}s"
        )
        assert result.get("status") == "ok", (
            f"API detailed health degraded: {json.dumps(result, indent=2)}"
        )
        checks = result.get("checks", {})
        for dep in ("nats", "redis", "postgresql"):
            assert checks.get(dep) == "connected", (
                f"Dependency '{dep}' not connected: {checks.get(dep)}"
            )

    def test_kernel_logs_no_crash(self):
        """Vérifie que les logs du kernel ne contiennent pas d'erreur fatale."""
        result = run_cmd(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "logs", "--tail=50", "kernel"]
        )
        # Check for crash indicators
        crash_patterns = [
            "Traceback (most recent call last)",
            "Error response from daemon",
            "AttributeError",
            "ModuleNotFoundError",
        ]
        for pattern in crash_patterns:
            assert pattern not in result.stdout, (
                f"Kernel logs contain crash pattern '{pattern}'"
            )

    def test_modules_logs_no_crash(self):
        """Vérifie que les logs des modules ne contiennent pas d'erreur fatale."""
        result = run_cmd(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "logs", "--tail=50", "modules"]
        )
        crash_patterns = [
            "No module named",
            "Traceback",
            "Error response from daemon",
        ]
        for pattern in crash_patterns:
            assert pattern not in result.stdout, (
                f"Modules logs contain crash pattern '{pattern}'"
            )

    def test_api_logs_no_crash(self):
        """Vérifie que les logs de l'API ne contiennent pas d'erreur fatale."""
        result = run_cmd(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "logs", "--tail=50", "api"]
        )
        crash_patterns = [
            "Traceback",
            "Error response from daemon",
            "Application startup failed",
        ]
        for pattern in crash_patterns:
            assert pattern not in result.stdout, (
                f"API logs contain crash pattern '{pattern}'"
            )

    def test_preflight_script(self):
        """Vérifie que le script de préflight s'exécute."""
        preflight = PROJECT_ROOT / "scripts" / "cmd-preflight.sh"
        if not preflight.exists():
            pytest.skip("preflight script not found")
        result = run_cmd(["bash", str(preflight)])
        # Non-zero exit is acceptable if checks fail, but script must not crash
        assert "Traceback" not in result.stderr, (
            f"Preflight script crashed:\n{result.stderr}"
        )


# ── Main Entry Point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])