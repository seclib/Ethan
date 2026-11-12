"""Tests du service Core `McpInstaller` — installation MCP contrôlée.

Aucun réseau : l'analyse est remplacée par un plan explicite et le runner de
commandes est simulé. Ce qui est réellement testé reste le chemin Core :
approbation HROT, politique stdio fail-closed, isolation disque, manifeste,
enregistrement via `ToolServerManager`, désinstallation.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import time
from pathlib import Path

import pytest
from core.approval import ApprovalAuthority, ApprovalEngine
from core.mcp_installer import (
    CommandResult,
    InstallationPlan,
    InstallationState,
    McpInstaller,
    McpInstallError,
    ProjectAnalysis,
    RuntimeType,
    SourceType,
    TransportType,
    generate_installation_plan,
)
from core.mcp_installer.installer import build_mcp_config
from core.mcp_installer.isolation import DefaultInstallIsolationProvider
from core.state.record_store import CoreRecordStore
from core.tools.servers import ToolServerManager

NODE = shutil.which("node")


def _authority() -> ApprovalAuthority:
    return ApprovalAuthority(
        principal_id="operator",
        principal_type="HUMAN",
        authenticated=True,
        permissions=("ADMIN",),
        human=True,
        trusted=True,
    )


def _fake_npm_plan(version: str = "1.2.3") -> InstallationPlan:
    analysis = ProjectAnalysis(
        name="fake-mcp",
        version=version,
        description="A fake MCP server for tests",
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
        resolved_version=version,
        runtime=RuntimeType.NODE,
        package_manager="npm",
        transport=TransportType.STDIO,
        analysis=analysis,
    )
    plan.execution_command = shutil.which("npx") or "npx"
    plan.execution_args = ["-y", f"fake-mcp@{version}"]
    plan.install_actions = ["install fake-mcp"]
    plan.expected_mcp_config = build_mcp_config(plan)
    return plan


async def _wait_request_id(installer: McpInstaller, installation_id: str) -> str:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        record = await installer.get(installation_id)
        if record and record.get("approval_request_id"):
            return str(record["approval_request_id"])
        await asyncio.sleep(0.01)
    raise AssertionError("approval request was never published")



def _simulated_provider():
    # Phase 3 : double de test explicitement simulé (pas d'isolation réelle validée).
    return DefaultInstallIsolationProvider(allow_simulated=True, simulated_effective=True)


def _manager() -> ToolServerManager:
    return ToolServerManager(store=CoreRecordStore())


def test_plan_roundtrip_is_lossless():
    plan = _fake_npm_plan()
    restored = InstallationPlan.from_dict(plan.to_dict())
    assert restored.to_dict() == plan.to_dict()


def test_custom_command_plan_requires_confirmation():
    plan = generate_installation_plan("/bin/echo hello")
    assert plan.source_type is SourceType.CUSTOM_COMMAND
    assert plan.execution_command == "/bin/echo"
    assert plan.execution_args == ["hello"]
    assert plan.analysis is not None
    assert plan.analysis.is_mcp_server is False


def test_custom_command_refused_without_confirmation(monkeypatch):
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.delenv("ETHAN_MCP_STDIO_ALLOWLIST", raising=False)
    installer = McpInstaller(
        tool_servers=_manager(),
        approval_engine=ApprovalEngine(),
        store=CoreRecordStore(),
        isolation_provider=_simulated_provider(),
    )
    with pytest.raises(McpInstallError) as excinfo:
        asyncio.run(installer.request_install(actor="operator", source="/bin/echo hello"))
    assert excinfo.value.code == "MCP-CONFIRMATION-REQUIRED"


def test_custom_command_refused_by_stdio_policy(monkeypatch):
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.delenv("ETHAN_MCP_STDIO_ALLOWLIST", raising=False)
    installer = McpInstaller(
        tool_servers=_manager(),
        approval_engine=ApprovalEngine(),
        store=CoreRecordStore(),
        isolation_provider=_simulated_provider(),
    )
    with pytest.raises(McpInstallError) as excinfo:
        asyncio.run(
            installer.request_install(
                actor="operator", source="/bin/echo hello", confirmed_mcp=True
            )
        )
    assert excinfo.value.code == "MCP-POLICY"


def test_unknown_analysis_id_is_refused():
    installer = McpInstaller(
        tool_servers=_manager(),
        approval_engine=ApprovalEngine(),
        store=CoreRecordStore(),
    )
    with pytest.raises(McpInstallError) as excinfo:
        asyncio.run(
            installer.request_install(actor="operator", analysis_id="deadbeef")
        )
    assert excinfo.value.code == "MCP-ANALYSIS-NOT-FOUND"


def test_approved_custom_command_is_registered(monkeypatch, tmp_path):
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", "/bin/echo")
    store = CoreRecordStore()
    tool_servers = ToolServerManager(store=store)
    approval = ApprovalEngine()

    async def fake_sync(_self, _server_id):
        return []

    monkeypatch.setattr(ToolServerManager, "sync_tools", fake_sync)

    async def scenario(tmp_path: Path):
        installer = McpInstaller(
            tool_servers=tool_servers,
            approval_engine=approval,
            store=store,
            install_root=tmp_path / "servers",
            isolation_provider=_simulated_provider(),
        )
        with pytest.raises(McpInstallError) as excinfo:
            await installer.request_install(
                actor="operator", source="/bin/echo", confirmed_mcp=False
            )
        # `/bin/echo` sans argument reste une identité non confirmée : le
        # service ne doit jamais enregistrer un CLI classique comme MCP.
        assert excinfo.value.code == "MCP-CONFIRMATION-REQUIRED"

        record = await installer.request_install(
            actor="operator", source="/bin/echo hello", confirmed_mcp=True
        )
        request_id = await _wait_request_id(installer, record["id"])
        assert approval.resolve(request_id, True, "ok", authority=_authority())
        finished = await installer.wait(record["id"], timeout=5)
        assert finished is not None
        assert finished["status"] == InstallationState.READY.value
        assert finished["server_id"]
        server = await tool_servers.get(finished["server_id"])
        assert server is not None
        assert server["metadata"]["command"] == "/bin/echo"
        assert server["metadata"]["args"] == ["hello"]
        assert Path(finished["installation_dir"]).is_dir()
        manifest = json.loads(
            (Path(finished["installation_dir"]) / ".ethan-mcp-install.json").read_text(
                encoding="utf-8"
            )
        )
        assert manifest["source"] == "/bin/echo hello"
        assert manifest["server_id"] == finished["server_id"]

        removed = await installer.uninstall(record["id"], actor="operator")
        assert removed["status"] == InstallationState.UNINSTALLED.value
        assert await tool_servers.get(finished["server_id"]) is None
        assert not Path(finished["installation_dir"]).exists()

    asyncio.run(scenario(tmp_path=tmp_path))


def test_rejected_approval_never_installs(monkeypatch, tmp_path):
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", "/bin/echo")
    store = CoreRecordStore()
    tool_servers = ToolServerManager(store=store)
    approval = ApprovalEngine()

    async def scenario(tmp_path: Path):
        installer = McpInstaller(
            tool_servers=tool_servers,
            approval_engine=approval,
            store=store,
            install_root=tmp_path,
            isolation_provider=_simulated_provider(),
        )
        record = await installer.request_install(
            actor="operator", source="/bin/echo hi", confirmed_mcp=True
        )
        request_id = await _wait_request_id(installer, record["id"])
        assert approval.resolve(request_id, False, "refusé", authority=_authority())
        finished = await installer.wait(record["id"], timeout=5)
        assert finished is not None
        assert finished["status"] == InstallationState.REJECTED.value
        assert finished["server_id"] is None
        assert list(tmp_path.iterdir()) == []

    asyncio.run(scenario(tmp_path=tmp_path))


@pytest.mark.skipif(NODE is None, reason="node is required for the npm isolation path")
def test_npm_install_isolated_and_tracked(monkeypatch, tmp_path):
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", NODE)
    plan = _fake_npm_plan()
    store = CoreRecordStore()
    tool_servers = ToolServerManager(store=store)
    approval = ApprovalEngine()
    calls: list[list[str]] = []

    async def fake_runner(argv: list[str], cwd: Path, timeout: int) -> CommandResult:
        calls.append(argv)
        prefix = Path(argv[argv.index("--prefix") + 1])
        package = prefix / "node_modules" / "fake-mcp"
        (package / "bin").mkdir(parents=True, exist_ok=True)
        (package / "package.json").write_text(
            json.dumps(
                {
                    "name": "fake-mcp",
                    "version": "1.2.3",
                    "bin": {"fake-mcp": "bin/server.js"},
                }
            ),
            encoding="utf-8",
        )
        (package / "bin" / "server.js").write_text(
            "#!/usr/bin/env node\nconsole.log('mcp');\n", encoding="utf-8"
        )
        return CommandResult(0, "added 1 package", "")

    async def fake_sync(_self, _server_id):
        return []

    monkeypatch.setattr(ToolServerManager, "sync_tools", fake_sync)
    monkeypatch.setattr(
        "core.mcp_installer.service.generate_installation_plan", lambda _source: plan
    )

    async def scenario() -> None:
        installer = McpInstaller(
            tool_servers=tool_servers,
            approval_engine=approval,
            store=store,
            install_root=tmp_path / "servers",
            runner=fake_runner,
            isolation_provider=_simulated_provider(),
        )
        analyzed = await installer.analyze("fake-mcp")
        assert analyzed["is_mcp_server"] is True
        assert analyzed["requires_confirmation"] is False

        record = await installer.request_install(
            actor="operator", analysis_id=analyzed["analysis_id"]
        )
        request_id = await _wait_request_id(installer, record["id"])
        assert approval.resolve(request_id, True, "ok", authority=_authority())
        finished = await installer.wait(record["id"], timeout=10)
        assert finished is not None
        assert finished["status"] == InstallationState.READY.value
        assert finished["installed_version"] == "1.2.3"
        assert finished["sync"] == {"status": "ok", "tools": 0, "error": ""}

        install_dir = Path(finished["installation_dir"])
        assert install_dir.is_relative_to((tmp_path / "servers").resolve())
        assert (install_dir / ".ethan-mcp-install.json").is_file()
        config = finished["mcp_config"]
        assert config["metadata"]["command"] == NODE
        assert config["metadata"]["args"][0].endswith("bin/server.js")
        assert calls and calls[0][1] == "install"
        assert "--ignore-scripts" in calls[0]

        update = await installer.check_update(record["id"])
        assert update["current"] == "1.2.3"
        assert update["latest"] is None
        assert update["available"] is None

        removed = await installer.uninstall(record["id"], actor="operator")
        assert removed["status"] == InstallationState.UNINSTALLED.value
        assert not install_dir.exists()
        listed = await installer.list()
        assert listed == []
        history = await installer.list(include_removed=True)
        assert [item["id"] for item in history] == [record["id"]]

    asyncio.run(scenario())


@pytest.mark.skipif(NODE is None, reason="node is required for the npm isolation path")
def test_failed_npm_install_cleans_isolation(monkeypatch, tmp_path):
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", NODE)
    plan = _fake_npm_plan()
    store = CoreRecordStore()
    approval = ApprovalEngine()

    async def failing_runner(_argv: list[str], _cwd: Path, _timeout: int) -> CommandResult:
        return CommandResult(1, "", "network unavailable")

    monkeypatch.setattr(
        "core.mcp_installer.service.generate_installation_plan", lambda _source: plan
    )

    async def scenario() -> None:
        installer = McpInstaller(
            tool_servers=ToolServerManager(store=store),
            approval_engine=approval,
            store=store,
            install_root=tmp_path / "servers",
            runner=failing_runner,
            isolation_provider=_simulated_provider(),
        )
        record = await installer.request_install(actor="operator", source="fake-mcp")
        request_id = await _wait_request_id(installer, record["id"])
        assert approval.resolve(request_id, True, "ok", authority=_authority())
        finished = await installer.wait(record["id"], timeout=10)
        assert finished is not None
        assert finished["status"] == InstallationState.FAILED.value
        assert "npm install a échoué" in finished["error"]
        root = tmp_path / "servers"
        assert root.exists()
        assert list(root.iterdir()) == []

    asyncio.run(scenario())


def test_install_refused_when_isolation_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", "/bin/echo")
    monkeypatch.delenv("ETHAN_MCP_INSTALL_ISOLATION", raising=False)
    installer = McpInstaller(
        tool_servers=_manager(),
        approval_engine=ApprovalEngine(),
        store=CoreRecordStore(),
        install_root=tmp_path / "servers",
        # provider par défaut : fail closed
    )
    with pytest.raises(McpInstallError) as excinfo:
        asyncio.run(
            installer.request_install(
                actor="operator", source="/bin/echo hello", confirmed_mcp=True
            )
        )
    assert excinfo.value.code == "MCP-ISOLATION-UNAVAILABLE"


def test_modified_plan_invalidates_approval(monkeypatch, tmp_path):
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", "/bin/echo")
    store = CoreRecordStore()
    tool_servers = ToolServerManager(store=store)
    approval = ApprovalEngine()

    async def fake_sync(_self, _server_id):
        return []

    monkeypatch.setattr(ToolServerManager, "sync_tools", fake_sync)

    async def scenario() -> None:
        installer = McpInstaller(
            tool_servers=tool_servers,
            approval_engine=approval,
            store=store,
            install_root=tmp_path / "servers",
            isolation_provider=_simulated_provider(),
        )
        record = await installer.request_install(
            actor="operator", source="/bin/echo hello", confirmed_mcp=True
        )
        request_id = await _wait_request_id(installer, record["id"])
        # Altération du plan stocké après demande (avant exécution approuvée)
        stored = await store.get(installer._INSTALLATIONS, record["id"])  # type: ignore[attr-defined]
        assert stored is not None
        stored["plan"]["execution_args"] = ["tampered"]
        await store.save(installer._INSTALLATIONS, record["id"], stored)
        assert approval.resolve(request_id, True, "ok", authority=_authority())
        finished = await installer.wait(record["id"], timeout=5)
        assert finished is not None
        assert finished["status"] == InstallationState.FAILED.value
        assert finished.get("error")
        assert "plan modifié" in finished["error"] or "inval" in finished["error"].lower()

    asyncio.run(scenario())


def test_sync_verification_failure_does_not_mark_ready(monkeypatch, tmp_path):
    monkeypatch.setenv("ETHAN_MCP_INSTALL_ISOLATION", "simulated")
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", "/bin/echo")
    store = CoreRecordStore()
    tool_servers = ToolServerManager(store=store)
    approval = ApprovalEngine()

    async def failing_sync(_self, _server_id):
        raise RuntimeError("handshake failed")

    monkeypatch.setattr(ToolServerManager, "sync_tools", failing_sync)

    async def scenario() -> None:
        installer = McpInstaller(
            tool_servers=tool_servers,
            approval_engine=approval,
            store=store,
            install_root=tmp_path / "servers",
            isolation_provider=_simulated_provider(),
        )
        record = await installer.request_install(
            actor="operator", source="/bin/echo hello", confirmed_mcp=True
        )
        request_id = await _wait_request_id(installer, record["id"])
        assert approval.resolve(request_id, True, "ok", authority=_authority())
        finished = await installer.wait(record["id"], timeout=5)
        assert finished is not None
        assert finished["status"] == InstallationState.FAILED.value
        error = finished["error"].lower()
        assert "vérification" in error or "handshake" in error
        # Aucun serveur ne doit rester enregistré après échec de vérification.
        assert not (await tool_servers.list())
        # Répertoire d'isolation nettoyé.
        root = tmp_path / "servers"
        assert not root.exists() or list(root.iterdir()) == []

    asyncio.run(scenario())
