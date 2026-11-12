"""Tests HTTP du routeur `mcp_installer` — gateway REST du Core.

Couvre :
- le contrat historique `/v1/mcp/installer/*` (analyse persistée + installation HROT) ;
- le contrat Phase 2 `/v1/mcp/analyze` (analyse partagée API/CLI, sans exécution).

Les acquisitions réseau réelles (npm/GitHub) sont remplacées par des plans/analyseurs
simulés quand on teste le contrat HTTP ; les contrôles de sûreté (SSRF, validation,
absence d'exécution de code tiers) sont exercés sur les chemins réels.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from core.approval import ApprovalAuthority, ApprovalEngine
from core.mcp_installer import (
    CommandResult,
    InstallationPlan,
    McpInstaller,
    ProjectAnalysis,
    RuntimeType,
    SourceType,
    TransportType,
)
from core.mcp_installer.isolation import DefaultInstallIsolationProvider
from core.state.record_store import CoreRecordStore
from core.tools.servers import ToolServerManager
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from interfaces.api.routers import mcp_installer as installer_routes


def _authority() -> ApprovalAuthority:
    return ApprovalAuthority(
        principal_id="operator",
        principal_type="HUMAN",
        authenticated=True,
        permissions=("ADMIN",),
        human=True,
        trusted=True,
    )


def _custom_plan(source: str = "/bin/echo hello") -> InstallationPlan:
    """Plan stdio minimal, identique dans sa forme à une analyse réelle."""
    analysis = ProjectAnalysis(
        name="/bin/echo",
        source_type=SourceType.CUSTOM_COMMAND,
        source_url=source,
        runtime=RuntimeType.UNKNOWN,
        transport=TransportType.STDIO,
        is_mcp_server=False,
        entry_point="/bin/echo",
    )
    plan = InstallationPlan(
        source=source,
        name="/bin/echo",
        source_type=SourceType.CUSTOM_COMMAND,
        runtime=RuntimeType.UNKNOWN,
        transport=TransportType.STDIO,
        execution_command="/bin/echo",
        execution_args=["hello"],
        install_actions=["vérifier la commande"],
        required_permissions=["approbation HROT"],
        analysis=analysis,
    )
    plan.expected_mcp_config = {
        "name": "bin-echo",
        "url": "stdio://bin-echo",
        "transport": "stdio",
        "metadata": {"transport": "stdio", "command": "/bin/echo", "args": ["hello"]},
    }
    return plan


def _mcp_npm_plan(
    source: str = "npx -y @example/mcp-server", confirmed: bool = True
) -> InstallationPlan:
    analysis = ProjectAnalysis(
        name="@example/mcp-server",
        version="1.2.3",
        publisher="example",
        description="Model Context Protocol server for tests",
        license="MIT",
        source_type=SourceType.NPM_COMMAND,
        source_url=source,
        runtime=RuntimeType.NODE,
        runtime_version=">=18",
        package_manager="npm",
        entry_point="dist/index.js",
        transport=TransportType.STDIO,
        dependencies=["@modelcontextprotocol/sdk"],
        env_vars=["MCP_TOKEN_NAME"],
        is_mcp_server=confirmed,
        tool_type="mcp_server" if confirmed else "unknown",
        prerequisites=[],
        errors=[],
        metadata_available=True,
    )
    plan = InstallationPlan(
        source=source,
        name="@example/mcp-server",
        source_type=SourceType.NPM_COMMAND,
        resolved_version="1.2.3",
        runtime=RuntimeType.NODE,
        package_manager="npm",
        dependencies=["@modelcontextprotocol/sdk"],
        install_actions=[
            "Installer le package épinglé dans l'isolation : "
            "npm install @example/mcp-server@1.2.3"
        ],
        execution_command="/usr/bin/node",
        execution_args=["/tmp/isolation/node_modules/@example/mcp-server/dist/index.js"],
        execution_env={},
        transport=TransportType.STDIO,
        isolation="dedicated_directory",
        required_permissions=[
            "Permission.ADMIN (enregistrement du serveur)",
            "Approbation humaine HROT",
        ],
        expected_mcp_config={
            "name": "example-mcp-server",
            "url": "stdio://example-mcp-server",
            "transport": "stdio",
            "metadata": {
                "transport": "stdio",
                "command": "/usr/bin/node",
                "args": ["/tmp/isolation/node_modules/@example/mcp-server/dist/index.js"],
            },
        },
        analysis=analysis,
    )
    return plan


def _build_app(role: str, installer: McpInstaller) -> FastAPI:
    """Application minimale : routeurs installer + analyse partagée, identité simulée."""
    installer_routes.set_mcp_installer(installer)
    app = FastAPI()

    @app.middleware("http")
    async def _identity(request: Request, call_next):
        request.state.token_payload = {"sub": "operator", "role": role}
        request.state.user = "operator"
        return await call_next(request)

    app.include_router(installer_routes.router)
    app.include_router(installer_routes.shared_router)
    return app


@pytest.fixture()
def installer(monkeypatch, tmp_path) -> Iterator[McpInstaller]:
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", "/bin/echo")
    approval = ApprovalEngine()

    async def fake_sync(_self, _server_id):
        return []

    monkeypatch.setattr(ToolServerManager, "sync_tools", fake_sync)

    instance = McpInstaller(
        tool_servers=ToolServerManager(store=CoreRecordStore()),
        approval_engine=approval,
        store=CoreRecordStore(),
        install_root=tmp_path / "servers",
        isolation_provider=DefaultInstallIsolationProvider(allow_simulated=True, simulated_effective=True),
    )
    instance.approval = approval  # type: ignore[attr-defined]
    try:
        yield instance
    finally:
        asyncio.run(instance.shutdown())
        installer_routes.set_mcp_installer(None)


async def _wait_for(condition, timeout: float = 5.0) -> Any:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = await condition()
        if value:
            return value
        await asyncio.sleep(0.01)
    raise AssertionError("condition never satisfied")


def _assert_shared_contract(body: dict[str, Any]) -> None:
    """Contrat Phase 2 minimal attendu par WebUI et CLI."""
    assert "analysis_id" in body and body["analysis_id"]
    assert body["analysis_status"] in {
        "confirmed_mcp_server",
        "probable_mcp_server",
        "undetermined_package_type",
        "non_mcp_package",
        "invalid_or_unsupported_source",
    }
    for section in ("source", "project_analysis", "installation_plan", "identification", "plan"):
        assert section in body, f"missing section: {section}"
    assert body["source"]["type"]
    assert body["source"]["original"]
    pa = body["project_analysis"]
    for key in (
        "detected_project_type",
        "runtime",
        "runtime_version_requirements",
        "package_manager",
        "dependencies",
        "potential_mcp_identification",
        "confidence",
        "evidence",
        "detected_entry_point",
        "detected_transport",
    ):
        assert key in pa, key
    ip = body["installation_plan"]
    for key in (
        "required_actions",
        "installation_command",
        "launch_command",
        "environment_variable_names",
        "mcp_configuration",
        "required_permissions",
        "isolation_requirements",
        "warnings",
        "unresolved_prerequisites",
    ):
        assert key in ip, key
    assert "command" in ip["launch_command"]
    assert "args" in ip["launch_command"]
    assert "transport" in ip["launch_command"]
    # Jamais de valeur d'environnement exposée.
    assert isinstance(ip["environment_variable_names"], list)
    assert body["identification"]["status"] == body["analysis_status"]


# ── Phase 2 : /v1/mcp/analyze (contrat partagé) ─────────────────────


def test_shared_analyze_endpoint_returns_structured_contract(installer, monkeypatch):
    plan = _custom_plan()
    monkeypatch.setattr(
        "core.mcp_installer.service.generate_installation_plan", lambda _source: plan
    )

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/analyze", json={"source": "/bin/echo hello"})
            assert response.status_code == 200, response.text
            body = response.json()
            _assert_shared_contract(body)
            assert body["analysis_status"] == "undetermined_package_type"
            assert body["source"]["type"] == "custom_command"
            assert body["installation_plan"]["launch_command"]["command"] == "/bin/echo"
            assert body["installation_plan"]["environment_variable_names"] == []

    asyncio.run(scenario())


def test_installer_analyze_endpoint_remains_compatible(installer, monkeypatch):
    plan = _custom_plan()
    monkeypatch.setattr(
        "core.mcp_installer.service.generate_installation_plan", lambda _source: plan
    )

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post(
                "/v1/mcp/installer/analyze", json={"source": "/bin/echo hello"}
            )
            assert response.status_code == 200, response.text
            body = response.json()
            # Compatibilité Phase 1
            assert body["analysis_id"]
            assert body["is_mcp_server"] is False
            assert body["requires_confirmation"] is True
            assert body["plan"]["execution_command"] == "/bin/echo"
            # Enrichissement Phase 2
            _assert_shared_contract(body)

    asyncio.run(scenario())


def test_analyze_npm_package_confirmed_mcp(installer, monkeypatch):
    plan = _mcp_npm_plan("npx -y @example/mcp-server", confirmed=True)
    monkeypatch.setattr(
        "core.mcp_installer.service.generate_installation_plan", lambda _source: plan
    )

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post(
                "/v1/mcp/analyze", json={"source": "npx -y @example/mcp-server"}
            )
            assert response.status_code == 200, response.text
            body = response.json()
            _assert_shared_contract(body)
            assert body["analysis_status"] == "confirmed_mcp_server"
            assert body["source"]["package_name"] == "@example/mcp-server"
            assert body["source"]["package_version"] == "1.2.3"
            assert body["project_analysis"]["runtime"] == "node"
            assert body["project_analysis"]["detected_entry_point"] == "dist/index.js"
            assert body["project_analysis"]["evidence"]
            assert body["installation_plan"]["mcp_configuration"]["transport"] == "stdio"
            assert (
                body["installation_plan"]["mcp_configuration"]["metadata"]["command"]
                == "/usr/bin/node"
            )
            assert "MCP_TOKEN_NAME" in body["installation_plan"]["environment_variable_names"]

    asyncio.run(scenario())


def test_analyze_npx_command_and_package_source_types(installer, monkeypatch):
    calls: list[str] = []

    def fake_plan(source: str) -> InstallationPlan:
        calls.append(source)
        st = SourceType.NPM_COMMAND if source.startswith("npx ") else SourceType.NPM_PACKAGE
        p = _mcp_npm_plan(source, confirmed=True)
        p.source = source
        p.source_type = st
        if p.analysis:
            p.analysis.source_type = st
            p.analysis.source_url = source
        return p

    monkeypatch.setattr("core.mcp_installer.service.generate_installation_plan", fake_plan)

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            r1 = await client.post("/v1/mcp/analyze", json={"source": "npx -y @example/mcp-server"})
            r2 = await client.post("/v1/mcp/analyze", json={"source": "@example/mcp-server"})
            assert r1.status_code == 200 and r2.status_code == 200
            assert r1.json()["source"]["type"] == "npm_command"
            assert r2.json()["source"]["type"] == "npm_package"
            assert calls == ["npx -y @example/mcp-server", "@example/mcp-server"]

    asyncio.run(scenario())


def test_analyze_github_repository(installer, monkeypatch):
    analysis = ProjectAnalysis(
        name="rea-agents",
        version="0.1.0",
        description="MCP server for reverse engineering",
        source_type=SourceType.GITHUB,
        source_url="https://github.com/example/repo",
        runtime=RuntimeType.NODE,
        package_manager="npm",
        transport=TransportType.STDIO,
        is_mcp_server=True,
        tool_type="mcp_server",
        metadata_available=True,
    )
    plan = InstallationPlan(
        source="https://github.com/example/repo",
        name="rea-agents",
        source_type=SourceType.GITHUB,
        runtime=RuntimeType.NODE,
        package_manager="npm",
        transport=TransportType.STDIO,
        install_actions=["Cloner le dépôt", "Installer les dépendances npm avec --ignore-scripts"],
        required_permissions=["Accès réseau GitHub (clone)"],
        isolation="dedicated_directory",
        expected_mcp_config={},
        analysis=analysis,
    )
    monkeypatch.setattr("core.mcp_installer.service.generate_installation_plan", lambda _s: plan)

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/analyze", json={"source": "https://github.com/example/repo"})
            assert response.status_code == 200, response.text
            body = response.json()
            _assert_shared_contract(body)
            assert body["source"]["type"] == "github"
            assert body["project_analysis"]["detected_project_type"] == "git_repository"
            assert body["analysis_status"] in {"confirmed_mcp_server", "probable_mcp_server"}

    asyncio.run(scenario())


def test_analyze_remote_http_endpoint(monkeypatch, tmp_path):
    # Chemin réel de validation URL/egress (sans connexion ni handshake MCP).
    # La résolution DNS est simulée pour rester déterministe ; la politique
    # d'egress réelle (schéma, creds, adresses interdites) est exercée.
    monkeypatch.setattr(
        "core.knowledge.web_ingest._default_resolver", lambda _host: ["93.184.216.34"]
    )
    monkeypatch.setattr(
        "core.security.egress.resolve_hostname", lambda _host: ["93.184.216.34"]
    )
    monkeypatch.delenv("ETHAN_MCP_ALLOW_PRIVATE_HOSTS", raising=False)
    installer = McpInstaller(
        tool_servers=ToolServerManager(store=CoreRecordStore()),
        approval_engine=ApprovalEngine(),
        store=CoreRecordStore(),
        install_root=tmp_path / "servers",
    )
    installer_routes.set_mcp_installer(installer)

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/analyze", json={"source": "https://mcp.example.com/sse"})
            assert response.status_code == 200, response.text
            body = response.json()
            _assert_shared_contract(body)
            assert body["source"]["type"] == "remote_http"
            assert body["analysis_status"] == "probable_mcp_server"
            assert body["project_analysis"]["detected_transport"] == "http"
            assert any(
                "handshake" in e.lower() or "non exécuté" in e.lower()
                for e in body["identification"]["evidence"]
            )
        await installer.shutdown()
        installer_routes.set_mcp_installer(None)

    asyncio.run(scenario())


def test_analyze_non_mcp_and_uncertain(installer, monkeypatch):
    non_mcp = ProjectAnalysis(
        name="left-pad",
        version="1.3.0",
        description="String padding utility",
        source_type=SourceType.NPM_PACKAGE,
        runtime=RuntimeType.NODE,
        package_manager="npm",
        transport=TransportType.UNKNOWN,
        is_mcp_server=False,
        tool_type="unknown",
        metadata_available=True,
    )
    uncertain = ProjectAnalysis(
        name="mystery-tool",
        source_type=SourceType.NPM_PACKAGE,
        runtime=RuntimeType.NODE,
        package_manager="npm",
        is_mcp_server=False,
        tool_type="unknown",
        metadata_available=False,
        errors=["npm not found on PATH"],
    )

    def mk(analysis: ProjectAnalysis, source: str) -> InstallationPlan:
        return InstallationPlan(
            source=source,
            name=analysis.name,
            source_type=analysis.source_type,
            runtime=analysis.runtime,
            package_manager=analysis.package_manager,
            transport=analysis.transport,
            analysis=analysis,
        )

    plans = {
        "left-pad": mk(non_mcp, "left-pad"),
        "mystery-tool": mk(uncertain, "mystery-tool"),
    }
    monkeypatch.setattr("core.mcp_installer.service.generate_installation_plan", lambda s: plans[s])

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            r1 = await client.post("/v1/mcp/analyze", json={"source": "left-pad"})
            r2 = await client.post("/v1/mcp/analyze", json={"source": "mystery-tool"})
            assert r1.status_code == 200 and r2.status_code == 200
            b1, b2 = r1.json(), r2.json()
            assert b1["analysis_status"] == "non_mcp_package"
            assert b1["project_analysis"]["potential_mcp_identification"] == "non_mcp"
            assert b2["analysis_status"] == "undetermined_package_type"
            assert b2["requires_confirmation"] is True

    asyncio.run(scenario())


def test_analyze_missing_runtime_and_dependencies(installer, monkeypatch):
    analysis = ProjectAnalysis(
        name="node-mcp",
        source_type=SourceType.NPM_PACKAGE,
        runtime=RuntimeType.NODE,
        package_manager="npm",
        is_mcp_server=True,
        metadata_available=True,
        prerequisites=["Node.js not found on PATH", "npm not found on PATH"],
        errors=["Node.js is required but not installed"],
        dependencies=["@modelcontextprotocol/sdk"],
    )
    plan = InstallationPlan(
        source="node-mcp",
        name="node-mcp",
        source_type=SourceType.NPM_PACKAGE,
        runtime=RuntimeType.NODE,
        package_manager="npm",
        dependencies=["@modelcontextprotocol/sdk"],
        analysis=analysis,
    )
    monkeypatch.setattr("core.mcp_installer.service.generate_installation_plan", lambda _s: plan)

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/analyze", json={"source": "node-mcp"})
            assert response.status_code == 200
            body = response.json()
            _assert_shared_contract(body)
            assert body["installation_plan"]["unresolved_prerequisites"]
            joined = " ".join(
                body["installation_plan"]["unresolved_prerequisites"]
                + body["installation_plan"]["warnings"]
            )
            assert "Node.js" in joined

    asyncio.run(scenario())


# ── Sécurité : SSRF, validation, absence d'exécution ────────────────


@pytest.mark.parametrize(
    "source",
    [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8080/mcp",
        "http://localhost/mcp",
        "http://10.0.0.5/mcp",
        "http://[::1]/mcp",
        "https://user:pass@example.com/mcp",
    ],
)
def test_analyze_rejects_ssrf_and_unsafe_remote_urls(monkeypatch, tmp_path, source):
    monkeypatch.delenv("ETHAN_MCP_ALLOW_PRIVATE_HOSTS", raising=False)

    async def scenario() -> None:
        inst = McpInstaller(
            tool_servers=ToolServerManager(store=CoreRecordStore()),
            approval_engine=ApprovalEngine(),
            store=CoreRecordStore(),
            install_root=tmp_path / "servers",
        )
        installer_routes.set_mcp_installer(inst)
        app = _build_app("admin", inst)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/analyze", json={"source": source})
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["analysis_status"] == "invalid_or_unsupported_source"
            assert body["source"]["type"] == "remote_http"
        await inst.shutdown()
        installer_routes.set_mcp_installer(None)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "source,expected_type",
    [
        ("http://github.com/owner/repo", "github"),
        ("https://github.com/owner", "github"),
        ("https://user:token@github.com/owner/repo", "github"),
        ("https://github.com", "github"),
    ],
)
def test_analyze_rejects_invalid_github_sources(monkeypatch, tmp_path, source, expected_type):
    # Validation avant tout clone (chemin réel source_acquirer/project_analyzer).
    monkeypatch.setattr(
        "core.mcp_installer.source_acquirer.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("git clone/npm must not run")),
    )

    async def scenario() -> None:
        inst = McpInstaller(
            tool_servers=ToolServerManager(store=CoreRecordStore()),
            approval_engine=ApprovalEngine(),
            store=CoreRecordStore(),
            install_root=tmp_path / "servers",
        )
        installer_routes.set_mcp_installer(inst)
        app = _build_app("admin", inst)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/analyze", json={"source": source})
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["source"]["type"] == expected_type
            assert body["analysis_status"] == "invalid_or_unsupported_source"
        await inst.shutdown()
        installer_routes.set_mcp_installer(None)

    asyncio.run(scenario())


def test_analyze_never_executes_third_party_code(installer, monkeypatch):
    """Aucune commande d'installation/exécution ne doit être lancée pendant l'analyse."""
    runner_calls: list[Any] = []

    async def fail_runner(argv, cwd, timeout):
        runner_calls.append((argv, cwd, timeout))
        raise AssertionError(f"runner must not be called during analyze: {argv}")

    installer._runner = fail_runner  # type: ignore[attr-defined]

    # Analyse = aucune exécution tiers : le runner Core ne doit pas être appelé
    # et aucun chemin d'installation (npm/pip/npx/setup.py) ne doit être déclenché.

    # On ne touche pas subprocess globalement de façon cassante pour tout (asyncio),
    # mais on vérifie le contrat principal : runner Core non appelé et analyse d'une
    # commande custom ne déclenche rien.
    plan = _custom_plan()
    monkeypatch.setattr(
        "core.mcp_installer.service.generate_installation_plan", lambda _s: plan
    )

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/analyze", json={"source": "/bin/echo hello"})
            assert response.status_code == 200
            _assert_shared_contract(response.json())
        assert runner_calls == []

    asyncio.run(scenario())


def test_analyze_oversized_npm_metadata_is_rejected(monkeypatch):
    from core.mcp_installer.source_validation import McpSourceValidationError, bounded_stdout

    with pytest.raises(McpSourceValidationError) as exc:
        bounded_stdout("x" * 1_000_001)
    assert exc.value.code == "MCP-SOURCE-TOO-LARGE"


def test_analyze_npm_view_timeout_maps_to_undetermined(monkeypatch, tmp_path):
    import subprocess

    def timeout_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0] if args else "npm", timeout=30)

    monkeypatch.setattr("core.mcp_installer.source_acquirer.subprocess.run", timeout_run)

    async def scenario() -> None:
        inst = McpInstaller(
            tool_servers=ToolServerManager(store=CoreRecordStore()),
            approval_engine=ApprovalEngine(),
            store=CoreRecordStore(),
            install_root=tmp_path / "servers",
        )
        installer_routes.set_mcp_installer(inst)
        app = _build_app("admin", inst)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/analyze", json={"source": "@scope/unknown-pkg"})
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["analysis_status"] == "undetermined_package_type"
            evidence = body["identification"]["evidence"] + body["installation_plan"]["warnings"]
            assert any("timed out" in e or "timeout" in e.lower() for e in evidence)
        await inst.shutdown()
        installer_routes.set_mcp_installer(None)

    asyncio.run(scenario())


def test_analyze_rbac_admin_required(installer):
    async def scenario() -> None:
        app = _build_app("viewer", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            denied = await client.post("/v1/mcp/analyze", json={"source": "/bin/echo hello"})
            assert denied.status_code == 403
            denied_legacy = await client.post(
                "/v1/mcp/installer/analyze", json={"source": "/bin/echo hello"}
            )
            assert denied_legacy.status_code == 403

    asyncio.run(scenario())


def test_mcp_configuration_compatible_with_tool_server_manager(installer, monkeypatch):
    plan = _mcp_npm_plan()
    monkeypatch.setattr("core.mcp_installer.service.generate_installation_plan", lambda _s: plan)

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post(
                "/v1/mcp/analyze", json={"source": "npx -y @example/mcp-server"}
            )
            assert response.status_code == 200
            body = response.json()
            cfg = body["installation_plan"]["mcp_configuration"]
            # Contrat ToolServerManager.register / validate_server_config
            assert cfg["transport"] == "stdio"
            assert "metadata" in cfg and cfg["metadata"]["transport"] == "stdio"
            assert cfg["metadata"]["command"].startswith("/")
            assert isinstance(cfg["metadata"].get("args", []), list)

    asyncio.run(scenario())


# ── Contrat historique / installation (régression) ──────────────────


def test_install_requires_source_or_analysis_id(installer):
    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post("/v1/mcp/installer/install", json={})
            assert response.status_code == 422, response.text

    asyncio.run(scenario())


def test_unknown_analysis_id_maps_to_400(installer):
    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.post(
                "/v1/mcp/installer/install", json={"analysis_id": "deadbeef"}
            )
            assert response.status_code == 400, response.text
            assert response.json()["detail"]["code"] == "MCP-ANALYSIS-NOT-FOUND"

    asyncio.run(scenario())


def test_unconfirmed_identity_is_refused(installer, monkeypatch):
    plan = _custom_plan()
    monkeypatch.setattr(
        "core.mcp_installer.service.generate_installation_plan", lambda _source: plan
    )

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            analyzed = await client.post(
                "/v1/mcp/installer/analyze", json={"source": "/bin/echo hello"}
            )
            analysis_id = analyzed.json()["analysis_id"]
            response = await client.post(
                "/v1/mcp/installer/install", json={"analysis_id": analysis_id}
            )
            assert response.status_code == 400, response.text
            assert response.json()["detail"]["code"] == "MCP-CONFIRMATION-REQUIRED"

    asyncio.run(scenario())


def test_install_is_accepted_only_after_human_approval(installer, monkeypatch):
    plan = _custom_plan()
    monkeypatch.setattr(
        "core.mcp_installer.service.generate_installation_plan", lambda _source: plan
    )

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            analyzed = await client.post(
                "/v1/mcp/installer/analyze", json={"source": "/bin/echo hello"}
            )
            analysis_id = analyzed.json()["analysis_id"]

            requested = await client.post(
                "/v1/mcp/installer/install",
                json={"analysis_id": analysis_id, "confirmed_mcp": True},
            )
            assert requested.status_code == 202, requested.text
            installation = requested.json()
            assert installation["status"] == "pending_approval"
            installation_id = installation["id"]

            async def _request_id() -> str:
                record = await installer.get(installation_id)
                return str(record.get("approval_request_id") or "") if record else ""

            request_id = await _wait_for(_request_id)
            assert installer.approval.resolve(  # type: ignore[attr-defined]
                request_id, True, "approuvé", authority=_authority()
            )

            async def _installed() -> dict | None:
                record = await installer.get(installation_id)
                if record and record["status"] in {"installed", "failed"}:
                    return record
                return None

            async def _ready() -> dict | None:
                record = await installer.get(installation_id)
                if record and record["status"] in {"ready", "failed"}:
                    return record
                return None

            finished = await _wait_for(_ready)
            assert finished["status"] == "ready", finished
            assert finished["server_id"]
            assert Path(finished["installation_dir"]).is_dir()

            removed = await client.delete(f"/v1/mcp/installer/installations/{installation_id}")
            assert removed.status_code == 200, removed.text
            assert removed.json()["status"] in {"removed", "uninstalled"}

    asyncio.run(scenario())


def test_read_only_role_cannot_mutate(installer):
    async def scenario() -> None:
        app = _build_app("viewer", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/mcp/installer/analyze", json={"source": "/bin/echo hello"}
            )
            assert resp.status_code == 403
            resp = await client.post(
                "/v1/mcp/installer/install", json={"analysis_id": "deadbeef"}
            )
            assert resp.status_code == 403
            allowed = await client.get("/v1/mcp/installer/installations")
            assert allowed.status_code == 200 and allowed.json() == []

    asyncio.run(scenario())


def test_installer_unavailable_returns_503():
    installer_routes.set_mcp_installer(None)

    async def scenario() -> None:
        app = FastAPI()

        @app.middleware("http")
        async def _identity(request: Request, call_next):
            request.state.token_payload = {"sub": "operator", "role": "admin"}
            request.state.user = "operator"
            return await call_next(request)

        app.include_router(installer_routes.router)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            response = await client.get("/v1/mcp/installer/installations")
            assert response.status_code == 503

    asyncio.run(scenario())


def test_npm_install_uses_isolated_runner(installer, monkeypatch):
    calls: list[list[str]] = []

    async def fake_runner(argv: list[str], cwd: Path, _timeout: int) -> CommandResult:
        calls.append(argv)
        assert Path(argv[argv.index("--prefix") + 1]) == cwd
        return CommandResult(1, "", "réseau indisponible")

    installer._runner = fake_runner  # type: ignore[attr-defined]

    analysis = ProjectAnalysis(
        name="fake-mcp",
        source_type=SourceType.NPM_PACKAGE,
        runtime=RuntimeType.NODE,
        package_manager="npm",
        transport=TransportType.STDIO,
        is_mcp_server=True,
        metadata_available=True,
    )
    plan = InstallationPlan(
        source="fake-mcp",
        name="fake-mcp",
        source_type=SourceType.NPM_PACKAGE,
        runtime=RuntimeType.NODE,
        package_manager="npm",
        transport=TransportType.STDIO,
        analysis=analysis,
    )
    monkeypatch.setattr("core.mcp_installer.service.generate_installation_plan", lambda _s: plan)
    import shutil

    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required for the npm isolation path")
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", node)

    async def scenario() -> None:
        app = _build_app("admin", installer)
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            requested = await client.post(
                "/v1/mcp/installer/install",
                json={"source": "fake-mcp", "confirmed_mcp": True},
            )
            assert requested.status_code == 202, requested.text
            installation_id = requested.json()["id"]

            async def _request_id() -> str:
                record = await installer.get(installation_id)
                return str(record.get("approval_request_id") or "") if record else ""

            request_id = await _wait_for(_request_id)
            assert installer.approval.resolve(request_id, True, "ok", authority=_authority())

            async def _failed() -> dict | None:
                record = await installer.get(installation_id)
                if record and record["status"] == "failed":
                    return record
                return None

            finished = await _wait_for(_failed)
            assert "npm install a échoué" in finished["error"]
            assert calls and calls[0][1] == "install"
            assert "--ignore-scripts" in calls[0]

    asyncio.run(scenario())
