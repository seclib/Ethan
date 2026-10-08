"""Tests unitaires et d'intégration pour les points d'entrée du Model Hub.

Ces tests couvrent les axes prioritaires du Model Hub sans dépendre
d'accès réseau, de conteneurs ou de services hétéroclites :

1. Registre de modèles (ModelRegistry / ModelHub.list_catalog)
2. Découverte et recherche (ModelHub.discover)
3. Détection physique (HardwareDetector / get_system_hardware)
4. Compatibilité (CompatibilityResult / status et status_label)
5. Détection d'artefacts et formats (inspect_hf_model, formats)
6. Intégration Hugging Face (search_hf_models, inspect_hf_model)
7. Intégration Ollama (install_or_use_model, provider_hint)
8. Détection de runtime (choose_execution_strategy)
9. Téléchargement / installation (ModelDownloader, install_or_use_model)
10. Santé des endpoints (check_runtime_health)
11. Contrats API (ModelHub répond aux questions "peut-il fonctionner ?")
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from core.hardware.fit import check_model_compatibility
from core.models.downloader import get_model_downloader
from core.models.hub import ModelHub, get_model_hub
from core.models.registry import ModelEntry


def _hardware(
    total_ram: float = 32.0,
    available_ram: float = 24.0,
    cpu_cores: int = 16,
    gpu_count: int = 1,
    gpu_name: str = "RTX 4090",
    gpu_vram: float = 24.0,
    gpu_vram_free: float = 22.0,
    backend: str = "cuda",
) -> dict[str, float | int | str | None]:
    """Construction d'un dictionnaire de matériel de test."""
    return {
        "total_ram_gb": total_ram,
        "available_ram_gb": available_ram,
        "cpu_cores": cpu_cores,
        "gpu_count": gpu_count,
        "gpu_name": gpu_name,
        "gpu_vram_gb": gpu_vram,
        "gpu_vram_free_gb": gpu_vram_free,
        "backend": backend,
    }


def _cpu_hardware(
    total_ram: float = 16.0,
    available_ram: float = 10.0,
    cpu_cores: int = 8,
    gpu_count: int = 0,
    gpu_vram: float = 0.0,
    backend: str = "cpu",
) -> dict[str, float | int | str]:
    return {
        "total_ram_gb": total_ram,
        "available_ram_gb": available_ram,
        "cpu_cores": cpu_cores,
        "gpu_count": gpu_count,
        "gpu_vram_gb": gpu_vram,
        "gpu_vram_free_gb": 0.0,
        "backend": backend,
    }


# ── 1 & 2. Registre et découverte ────────────────────────────────────────────


def test_singleton_get_model_hub() -> None:
    """get_model_hub retourne une instance unique et initialisée."""
    assert get_model_hub() is get_model_hub()


def test_list_catalog_returns_registry_entries_with_compatibility() -> None:
    """list_catalog expose le catalogue enrichi de compatibilité sans créer de doublon."""
    hub = ModelHub()
    results = hub.list_catalog(query="llama", hardware=_hardware())

    assert isinstance(results, list)
    assert len(results) >= 1

    for entry in results:
        assert "compatibility" in entry
        assert entry["compatibility"]["status"] in (
            "compatible",
            "compatible_with_constraints",
            "incompatible",
            "insufficient_info",
        )
        assert "execution_method" in entry["compatibility"]


@pytest.mark.asyncio
async def test_detect_artifact_formats_hf_builds_artifact_view() -> None:
    """inspect_hf_model et fit sont bien consolidés dans detect_artifact_formats."""
    hub = ModelHub()
    fake_hf = {
        "repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
        "params_b": 7.0,
        "formats_available": ["gguf", "safetensors"],
        "is_gated": False,
        "description": "Modèle inspecté en direct.",
        "pipeline_tag": "text-generation",
    }

    with patch(
        "core.models.hub.inspect_hf_model",
        return_value=fake_hf,
    ):
        result = await hub.detect_artifact_formats(
            "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
            hardware=_hardware(),
        )

    assert result["model_id"] == "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    assert result["formats_available"] == ["gguf", "safetensors"]
    assert result["is_gated"] is False
    assert result["params_b"] == 7.0
    assert result["compatible"] is True
    assert result["status"] == "compatible"
    assert result["status_label"] == "Compatible"
    assert result["details"]["model_id"] == "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"


@pytest.mark.asyncio
async def test_detect_artifact_formats_local_registry_entry_use_known_formats() -> None:
    """Un modèle déjà référencé dans le registre expose ses formats présumés."""
    hub = ModelHub()
    entry = ModelEntry(
        id="llama3.2:3b",
        name="Llama 3.2 3B",
        provider="ollama",
        repo_id="llama3.2:3b",
        params_b=3.2,
        formats_available=["gguf"],
        quantization="Q4_K_M",
        source="curated",
    )

    with patch.object(hub._registry, "get", return_value=entry):
        result = await hub.detect_artifact_formats("llama3.2:3b", hardware=_cpu_hardware())

    assert result["formats_available"] == ["gguf"]
    assert result["params_b"] == 3.2
    assert result["compatible"] is True
    assert result["status"] == "compatible_with_constraints"
    assert result["recommended_runtime"] == "ollama"
    assert result["recommended_format"] == "gguf"


def test_compatibility_enumerates_all_four_states() -> None:
    """Le moteur de compatibilité expose les quatre réponses autorisées."""
    hardware = _cpu_hardware(total_ram=16.0, available_ram=10.0, cpu_cores=8)

    small = check_model_compatibility("llama3.2:3b", params_b=3.2, hardware=hardware)
    assert small.status == "compatible_with_constraints"
    assert small.status_label == "Compatible avec contraintes"
    assert small.compatible is True

    big = check_model_compatibility("llama3.1:70b", params_b=70.0, hardware=hardware)
    assert big.status == "incompatible"
    assert big.status_label == "Incompatible"
    assert big.compatible is False

    unknown = check_model_compatibility("sans-info", params_b=0.0)
    assert unknown.status == "insufficient_info"
    assert unknown.status_label == "Information insuffisante"
    assert unknown.compatible is False


@pytest.mark.asyncio
async def test_inspect_returns_controlled_statuses_for_known_models() -> None:
    """inspect répond toujours d'une des quatre façons contrôlées et jamais de fausse conversion."""
    hub = ModelHub()

    with patch(
        "core.models.hub.check_model_compatibility",
        return_value=check_model_compatibility(
            "llama3.2:3b", params_b=3.2, quantization="Q4_K_M", hardware=_cpu_hardware()
        ),
    ):
        cpu = await hub.inspect("llama3.2:3b", hardware=_cpu_hardware())
    assert cpu["status"] == "compatible_with_constraints"
    assert cpu["status_label"] == "Compatible avec contraintes"

    with patch(
        "core.models.hub.check_model_compatibility",
        return_value=check_model_compatibility(
            "llama3.1:70b", params_b=70.0, quantization="Q4_K_M", hardware=_cpu_hardware()
        ),
    ):
        tiny = await hub.inspect("llama-3.1-70b", hardware=_cpu_hardware())
    assert tiny["status"] == "incompatible"
    assert tiny["status_label"] == "Incompatible"
    assert tiny["conversion_supported"] is False


@pytest.mark.asyncio
async def test_discover_supports_hf_artifact_formats_without_network() -> None:
    """La découverte enrichit Hugging Face sans appeler le réseau en production."""
    hub = ModelHub()
    fake_hf = [
        {
            "id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
            "name": "Qwen2.5-Coder-7B-Instruct-GGUF",
            "repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
            "provider": "huggingface",
            "formats_available": ["gguf", "safetensors"],
        }
    ]

    with patch(
        "core.models.hub.search_hf_models",
        new=AsyncMock(return_value=fake_hf),
    ):
        results = await hub.discover(
            query="qwen",
            source="all",
            hardware=_hardware(),
        )

    hf_entries = [r for r in results if r.get("provider") == "huggingface"]
    assert hf_entries, "Aucun modèle Hugging Face n'a été enrichi par la découverte"
    assert hf_entries[0]["formats_available"] == ["gguf", "safetensors"]


@pytest.mark.asyncio
async def test_install_flow_records_download_and_calls_installer() -> None:
    """L'installation centrale utilise le téléchargeur existant et enregistre l'état."""
    hub = ModelHub()
    mock_installer = AsyncMock(
        return_value={
            "success": True,
            "model_id": "llama3.2:3b",
            "runtime": "ollama",
            "provider": "ollama",
            "message": "Modèle llama3.2:3b installé et prêt à l'emploi dans ETHAN.",
            "strategy": {"recommended_runtime": "ollama", "compatible": True},
        }
    )

    with patch(
        "core.llm.model_installer.install_or_use_model",
        new=mock_installer,
    ):
        result = await hub.install(
            model_id="llama3.2:3b",
            provider_hint="ollama",
            store=None,
            hardware=_hardware(),
        )

    assert result["success"] is True
    assert result["runtime"] == "ollama"
    mock_installer.assert_awaited_once()
    assert hub.list_downloads()[0]["status"] == "completed"


def test_downloader_records_and_lists_tasks() -> None:
    """Le téléchargeur expose un état par tâche et un listing par récence."""
    downloader = get_model_downloader()

    task = downloader.record_task(
        task_id="dl-qwen_7b",
        repo_id="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
        runtime="ollama",
        status="downloading",
        percent=25.0,
        error=None,
    )

    assert task["status"] == "downloading"
    assert task["repo_id"] == "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    assert task["percent"] == 25.0

    listing = downloader.list_downloads()
    assert listing[0]["id"] == "dl-qwen_7b"
    assert isinstance(listing, list)


# ── Compléments : variantes Ollama, runtimes supportés, santé directe ────────


@pytest.mark.asyncio
async def test_detect_artifact_formats_resolves_ollama_latest_variant() -> None:
    """Une variante Ollama « :latest » résout l'entrée registre au lieu de « insufficient_info »."""
    hub = ModelHub()
    res = await hub.detect_artifact_formats("llama3.2:latest", hardware=_hardware())

    assert res["formats_origin"] == "registry"
    assert res["params_b"] == 3.2
    assert res["status"] in (
        "compatible",
        "compatible_with_constraints",
        "incompatible",
        "insufficient_info",
    )
    assert res["status"] != "insufficient_info"


@pytest.mark.asyncio
async def test_detect_artifact_formats_exposes_supported_runtimes_and_no_forced_conversion() -> (
    None
):
    """detect_artifact_formats expose les runtimes supportés et ne force aucune conversion."""
    hub = ModelHub()
    res = await hub.detect_artifact_formats("llama3.2:3b", hardware=_hardware())

    assert isinstance(res["supported_runtimes"], list)
    assert "ollama" in res["supported_runtimes"]
    assert res["conversion_supported"] is False
    assert res["conversion_operations"] == []


@pytest.mark.asyncio
async def test_check_runtime_health_probes_local_runtimes_without_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sans manager, le health-check sonde les endpoints locaux (pas « uninitialized »)."""

    async def _fake_probe(self, base_url: str, health_path: str) -> dict[str, object]:
        if base_url == "http://localhost:11434":
            return {"reachable": True, "latency_ms": 4.2}
        return {"reachable": False, "latency_ms": None}

    monkeypatch.setattr(ModelHub, "_probe_runtime_endpoint", _fake_probe)

    hub = ModelHub()
    health = await hub.check_runtime_health(manager=None)

    assert health["status"] == "healthy"
    assert health["runtimes"]["ollama"]["reachable"] is True
    assert health["runtimes"]["ollama"]["enabled"] is False
    assert "llamacpp" not in health["runtimes"]


@pytest.mark.asyncio
async def test_list_installed_unions_store_and_live_ollama_models() -> None:
    """list_installed unit fiches ModelStore et modèles Ollama servis en direct, sans doublon."""

    class _FakeModel:
        def __init__(self, mid: str) -> None:
            self.id = mid
            self.name = mid
            self.model = mid
            self.provider = "ollama"
            self.capabilities = ["chat"]

    class _FakeStore:
        async def list_models(self):
            return [{"id": "qwen2.5:7b", "name": "qwen2.5:7b", "provider": "ollama"}]

    class _FakeManager:
        async def list_models(self):
            return [_FakeModel("qwen2.5:7b"), _FakeModel("llama3.2:latest")]

    hub = ModelHub()
    installed = await hub.list_installed(store=_FakeStore(), manager=_FakeManager())

    by_id = {m["id"]: m for m in installed}
    assert set(by_id) == {"qwen2.5:7b", "llama3.2:latest"}
    assert by_id["llama3.2:latest"]["source"] == "live"
    assert by_id["llama3.2:latest"]["is_installed"] is True
    assert "compatibility" in by_id["llama3.2:latest"]


@pytest.mark.asyncio
async def test_check_runtime_health_reports_reachable_status() -> None:
    """check_runtime_health ne lance aucun jeton si la connextion échoue."""
    hub = ModelHub()

    class _FakeManager:
        async def list_providers(self):
            return [
                {
                    "id": "ollama",
                    "name": "ollama",
                    "enabled": True,
                    "base_url": "http://localhost:11434",
                    "capabilities": ["llm"],
                }
            ]

        async def test_connection(self, provider_id: str):
            return {"connected": True, "status": "connected", "latency_ms": 12.5}

    manager = _FakeManager()
    health = await hub.check_runtime_health(manager=manager)

    assert health["status"] == "healthy"
    assert health["runtimes"]["ollama"]["reachable"] is True
    assert health["runtimes"]["ollama"]["latency_ms"] == 12.5

    with patch(
        "core.models.hub.check_model_compatibility",
        return_value=check_model_compatibility("gpt-4o-mini", hardware=_cpu_hardware()),
    ):
        cloud = await hub.inspect("gpt-4o-mini", hardware=_cpu_hardware())
    assert cloud["status"] == "compatible"
    assert "Cloud" in cloud["method"]


# ── Self-probes ETHAN : localhost:8000 n'est pas un runtime externe ──────────


@pytest.mark.asyncio
async def test_probe_runtime_endpoint_rejects_ethan_self_identity() -> None:
    """Un endpoint renvoyant ``service: api|kernel`` est un self-probe ETHAN.

    Régression D1 : la sonde vLLM frappait ``localhost:8000/health``, qui est
    l'API ETHAN elle-même — le faux « reachable » déclarait un vLLM fantôme.
    """
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - API stdlib
            if self.path == "/health":
                body = json.dumps(
                    {"status": "ok", "service": "api", "nats_connected": True}
                ).encode()
            else:
                body = json.dumps({"models": []}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: object) -> None:
            """Silence le logging stdlib du serveur de test."""

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{port}"

        self_probe = await ModelHub._probe_runtime_endpoint(base, "/health")
        assert self_probe["ethan_self"] is True
        assert self_probe["reachable"] is False

        runtime_probe = await ModelHub._probe_runtime_endpoint(base, "/models")
        assert runtime_probe["ethan_self"] is False
        assert runtime_probe["reachable"] is True
        assert isinstance(runtime_probe["latency_ms"], float)
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.asyncio
async def test_check_runtime_health_ignores_ethan_self_endpoints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le health-check exclut un runtime dont la sonde est un self-probe ETHAN."""

    async def _fake_probe(self, base_url: str, health_path: str) -> dict[str, object]:
        if base_url == "http://localhost:8000":
            return {"reachable": False, "latency_ms": 1.0, "ethan_self": True}
        if base_url == "http://localhost:11434":
            return {"reachable": True, "latency_ms": 4.2, "ethan_self": False}
        return {"reachable": False, "latency_ms": None, "ethan_self": False}

    monkeypatch.setattr(ModelHub, "_probe_runtime_endpoint", _fake_probe)

    hub = ModelHub()
    health = await hub.check_runtime_health(manager=None)

    assert "vllm" not in health["runtimes"]
    assert health["runtimes"]["ollama"]["reachable"] is True
    assert health["status"] == "healthy"
