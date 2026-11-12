"""Tests du système d'extensions unifié (Core).

Couvre les trois types — Capability, Plugin, Cookbook — et le gestionnaire
commun : découverte, install, enable, disable, uninstall, update, erreur,
timeout, persistence et reprise après redémarrage.

Le Core est la source de vérité : aucun test ne doit pouvoir passer si une
installation est « réussie » alors que le handler a échoué.
"""

from __future__ import annotations

from typing import Any

import pytest
from core.extensions import (
    CapabilityHandler,
    CookbookHandler,
    ExtensionKind,
    ExtensionManager,
    ExtensionOperation,
    ExtensionRuntimeState,
    ExtensionSpec,
    ExtensionState,
    OperationStatus,
    PluginHandler,
    TransitionError,
)
from core.extensions.handlers import ExtensionHandler
from core.extensions.manager import _OPERATION_DOMAIN
from core.state.record_store import CoreRecordStore


class FakeStore(CoreRecordStore):
    """Store en mémoire : simule la persistance sans base de données."""

    def __init__(self) -> None:
        self.data: dict[tuple[str, str], dict[str, Any]] = {}

    async def save(self, domain: str, record_id: str, record: dict[str, Any]) -> None:
        self.data[(domain, record_id)] = dict(record)

    async def get(self, domain: str, record_id: str) -> dict[str, Any] | None:
        found = self.data.get((domain, record_id))
        return dict(found) if found else None

    async def list(self, domain: str) -> list[dict[str, Any]]:
        return [dict(v) for (d, _), v in self.data.items() if d == domain]

    async def delete(self, domain: str, record_id: str) -> bool:
        return self.data.pop((domain, record_id), None) is not None


class StubHandler(ExtensionHandler):
    """Handler générique pilotant un type simulé."""

    kind = "stub"

    def __init__(self, *, fail: bool = False, names: list[str] | None = None) -> None:
        self.fail = fail
        self.names = names or ["alpha", "beta"]
        self.installed: set[str] = set()
        self.enabled: set[str] = set()
        self.calls: list[str] = []

    async def discover(self) -> list[ExtensionSpec]:
        return [
            ExtensionSpec(id=n, kind=self.kind, name=n.upper(), version="1.0.0")
            for n in self.names
        ]

    async def install(self, ext_id: str, config: dict[str, Any]) -> str:
        self.calls.append(f"install:{ext_id}")
        if self.fail:
            raise RuntimeError("boom install")
        self.installed.add(ext_id)
        return ""

    async def uninstall(self, ext_id: str, delete_data: bool) -> str:
        self.calls.append(f"uninstall:{ext_id}:{delete_data}")
        if self.fail:
            raise RuntimeError("boom uninstall")
        self.installed.discard(ext_id)
        self.enabled.discard(ext_id)
        return ""

    async def enable(self, ext_id: str) -> None:
        self.calls.append(f"enable:{ext_id}")
        if self.fail:
            raise RuntimeError("boom enable")
        self.enabled.add(ext_id)

    async def disable(self, ext_id: str) -> None:
        self.calls.append(f"disable:{ext_id}")
        self.enabled.discard(ext_id)

    async def configure(self, ext_id: str, config: dict[str, Any]) -> None:
        self.calls.append(f"configure:{ext_id}")

    async def status(self, ext_id: str) -> dict[str, Any]:
        if ext_id not in self.installed:
            return {}
        return {"status": "active" if ext_id in self.enabled else "inactive"}

    async def logs(self, ext_id: str, tail: int = 200) -> dict[str, Any]:
        return {"logs": "", "lines": []}

    async def get_operation(self, op_id: str) -> dict[str, Any] | None:
        return None

    async def cancel_operation(self, op_id: str) -> bool:
        return False


@pytest.fixture
def store() -> FakeStore:
    return FakeStore()


@pytest.fixture
def handler() -> StubHandler:
    return StubHandler()

# ── Découverte ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestDiscovery:
    async def test_discover_returns_all_types(self, store: FakeStore):
        handlers = {}
        for kind in ExtensionKind.ALL:
            h = StubHandler()
            h.kind = kind
            handlers[kind] = h
        mgr = ExtensionManager(handlers=handlers, store=store)
        statuses = await mgr.discover()
        assert len(statuses) == 6
        assert {s.spec.kind for s in statuses} == set(ExtensionKind.ALL)

    async def test_kind_is_explicit(self, manager: ExtensionManager, handler: StubHandler):
        statuses = await manager.discover()
        assert all(s.spec.kind == handler.kind for s in statuses)

    async def test_broken_handler_does_not_break_others(self, store: FakeStore):
        class Broken(StubHandler):
            async def discover(self):
                raise RuntimeError("catalogue casse")

        ok_handler = StubHandler()
        ok_handler.kind = "ok"
        mgr = ExtensionManager(handlers={"broken": Broken(), "ok": ok_handler}, store=store)
        statuses = await mgr.discover()
        assert any(s.state.state == ExtensionState.ERROR for s in statuses)
        assert any(s.spec.kind == "ok" for s in statuses)

    async def test_actions_reflect_real_state(self, manager: ExtensionManager):
        statuses = {s.spec.id: s for s in await manager.discover()}
        assert statuses["alpha"].actions == (ExtensionOperation.INSTALL,)


# ── Installation ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestInstall:
    async def test_install_persists_state(self, manager: ExtensionManager):
        op_id = await manager.install("alpha")
        assert op_id
        op = await manager.get_operation(op_id)
        assert op["status"] == OperationStatus.SUCCESS
        assert op["done"] is True

    async def test_install_error_is_visible(self, store: FakeStore):
        mgr = ExtensionManager(handlers={"stub": StubHandler(fail=True)}, store=store)
        with pytest.raises(RuntimeError):
            await mgr.install("alpha")
        state = await mgr.load_state("alpha")
        assert state.state == ExtensionState.ERROR
        assert "boom install" in (state.last_error or "")

    async def test_error_operation_recorded(self, store: FakeStore):
        mgr = ExtensionManager(handlers={"stub": StubHandler(fail=True)}, store=store)
        with pytest.raises(RuntimeError):
            await mgr.install("alpha")
        ops = await mgr.list_operations()
        assert ops and ops[0]["status"] == OperationStatus.ERROR
        assert ops[0]["error"]
# ── Enable / Disable / Uninstall / Update ───────────────────────────────────


@pytest.mark.asyncio
class TestLifecycle:
    async def test_enable_then_disable(self, manager: ExtensionManager, handler: StubHandler):
        await manager.install("alpha")
        await manager.enable("alpha")
        await manager.disable("alpha")
        assert "enable:alpha" in handler.calls
        assert "disable:alpha" in handler.calls

    async def test_enable_already_enabled_returns_terminal_op(
        self, manager: ExtensionManager
    ):
        await manager.install("alpha")
        await manager.enable("alpha")
        op_id = await manager.enable("alpha")
        assert (await manager.get_operation(op_id))["done"] is True

    async def test_enable_error_is_visible(self, store: FakeStore):
        handler = StubHandler()
        mgr = ExtensionManager(handlers={"stub": handler}, store=store)
        await mgr.install("alpha")
        handler.fail = True
        with pytest.raises(RuntimeError):
            await mgr.enable("alpha")
        assert (await mgr.load_state("alpha")).state == ExtensionState.ERROR

    async def test_uninstall_clears_install(self, manager: ExtensionManager, handler: StubHandler):
        await manager.install("alpha")
        await manager.uninstall("alpha")
        assert "alpha" not in handler.installed

    async def test_uninstall_passes_delete_data(
        self, manager: ExtensionManager, handler: StubHandler
    ):
        await manager.install("alpha")
        await manager.uninstall("alpha", delete_data=True)
        assert "uninstall:alpha:True" in handler.calls

    async def test_update_reapplies(self, manager: ExtensionManager, handler: StubHandler):
        await manager.install("alpha")
        await manager.update("alpha")
        assert handler.calls.count("install:alpha") == 2

    async def test_configure_delegates(self, manager: ExtensionManager, handler: StubHandler):
        await manager.install("alpha")
        await manager.configure("alpha", {"k": "v"})
        assert "configure:alpha" in handler.calls


# ── Persistence / restart / timeout ─────────────────────────────────────────


@pytest.mark.asyncio
class TestPersistence:
    async def test_state_survives_new_manager(self, store: FakeStore, handler: StubHandler):
        mgr = ExtensionManager(handlers={"stub": handler}, store=store)
        await mgr.install("alpha")
        await mgr.enable("alpha")
        restarted = ExtensionManager(handlers={"stub": handler}, store=store)
        state = await restarted.load_state("alpha")
        # L'etat persiste par le manager AVANT redemarrage doit etre retrouve.
        assert state.state == ExtensionState.INSTALLED
        assert state.installed_version == "1.0.0"

    async def test_operation_readable_after_restart(self, store: FakeStore, handler: StubHandler):
        mgr = ExtensionManager(handlers={"stub": handler}, store=store)
        op_id = await mgr.install("alpha")
        restarted = ExtensionManager(handlers={"stub": handler}, store=store)
        op = await restarted.get_operation(op_id)
        assert op is not None and op["done"] is True

    async def test_unknown_operation_returns_none(self, manager: ExtensionManager):
        assert await manager.get_operation("opx_inexistant") is None


@pytest.mark.asyncio
class TestRecovery:
    async def test_recover_terminates_dangling_operation(
        self, store: FakeStore, handler: StubHandler
    ):
        mgr = ExtensionManager(handlers={"stub": handler}, store=store)
        _dangling_operation(store)
        await store.save(
            "extensions",
            "alpha",
            ExtensionRuntimeState(
                id="alpha", kind="stub", state=ExtensionState.INSTALLING
            ).to_dict(),
        )
        summary = await mgr.recover_operations()
        assert summary["recovered"] == 1
        op = await mgr.get_operation("opx_pend")
        assert op["status"] in {OperationStatus.ERROR, OperationStatus.TIMEOUT}
        assert op["done"] is True
        # L'extension ne doit plus être figée « en cours ».
        assert (await mgr.load_state("alpha")).state == ExtensionState.ERROR

    async def test_recover_is_idempotent(self, store: FakeStore, handler: StubHandler):
        mgr = ExtensionManager(handlers={"stub": handler}, store=store)  # noqa: F841
# ── Spécificités par type ───────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTypeSpecifics:
    """Le type reste explicite : aucun handler ne déguise un autre type."""

    async def test_three_handlers_declare_their_kind(self):
        assert CapabilityHandler.kind == ExtensionKind.CAPABILITY
        assert PluginHandler.kind == ExtensionKind.PLUGIN
        assert CookbookHandler.kind == ExtensionKind.COOKBOOK

    async def test_capability_state_mapping(self):
        mapping = CapabilityHandler.state_map()
        assert mapping["READY"] == ExtensionState.ENABLED
        assert mapping["RUNNING"] == ExtensionState.ENABLED
        assert mapping["NOT_INSTALLED"] == ExtensionState.AVAILABLE
        assert mapping["UNHEALTHY"] == ExtensionState.ERROR
        assert mapping["UNINSTALLING"] == ExtensionState.UNINSTALLING

    async def test_cookbook_offers_no_enable_action(self, store: FakeStore):
        cook = StubHandler()
        cook.kind = ExtensionKind.COOKBOOK
        mgr = ExtensionManager(handlers={ExtensionKind.COOKBOOK: cook}, store=store)
        await mgr.install("alpha")
        status = await mgr.get("alpha")
        assert ExtensionOperation.ENABLE not in status.actions
        assert ExtensionOperation.UNINSTALL in status.actions

    async def test_cookbook_enable_refused_by_core(self, store: FakeStore):
        class Cookbookish(StubHandler):
            kind = ExtensionKind.COOKBOOK

            async def enable(self, ext_id: str) -> None:
                raise NotImplementedError("Les recettes n'ont pas d'activation")

        mgr = ExtensionManager(handlers={ExtensionKind.COOKBOOK: Cookbookish()}, store=store)
        await mgr.install("alpha")
        with pytest.raises(NotImplementedError):
            await mgr.enable("alpha")

    async def test_plugin_installed_is_disabled_not_enabled(self, store: FakeStore):
        class Pluginish(StubHandler):
            kind = ExtensionKind.PLUGIN

            async def status(self, ext_id: str) -> dict[str, Any]:
                return {"status": "inactive"} if ext_id in self.installed else {}

        mgr = ExtensionManager(handlers={ExtensionKind.PLUGIN: Pluginish()}, store=store)
        await mgr.install("alpha")
        status = await mgr.get("alpha")
        assert status.state.state == ExtensionState.DISABLED
        assert ExtensionOperation.ENABLE in status.actions

    async def test_plugin_active_becomes_enabled(self, store: FakeStore):
        class Pluginish(StubHandler):
            kind = ExtensionKind.PLUGIN

            async def status(self, ext_id: str) -> dict[str, Any]:
                if ext_id not in self.installed:
                    return {}
                return {"status": "active" if ext_id in self.enabled else "inactive"}

        mgr = ExtensionManager(handlers={ExtensionKind.PLUGIN: Pluginish()}, store=store)
        await mgr.install("alpha")
        await mgr.enable("alpha")
        status = await mgr.get("alpha")
        assert status.state.state == ExtensionState.ENABLED
        assert ExtensionOperation.DISABLE in status.actions

    async def test_mixed_catalogue_keeps_types_separated(self, store: FakeStore):
        handlers = {}
        for kind in ExtensionKind.ALL:
            h = StubHandler(names=["shared"])
            h.kind = kind
            handlers[kind] = h
        mgr = ExtensionManager(handlers=handlers, store=store)
        statuses = await mgr.discover()
        assert len(statuses) == 3
        assert {s.spec.kind for s in statuses} == set(ExtensionKind.ALL)
        _dangling_operation(store)
        await mgr.recover_operations()
        assert (await mgr.recover_operations())["recovered"] == 0

    async def test_cancel_immediate_exit(self, store: FakeStore, handler: StubHandler):
        mgr = ExtensionManager(handlers={"stub": handler}, store=store)
        _dangling_operation(store, op_id="opx_x")
        assert await mgr.cancel_operation("opx_x") is True
        assert (await mgr.get_operation("opx_x"))["status"] == OperationStatus.CANCELLED

    async def test_cancel_unknown_returns_false(self, manager: ExtensionManager):
        assert await manager.cancel_operation("opx_nope") is False

    async def test_timeout_path_sets_terminal(self, store: FakeStore, handler: StubHandler):
        mgr = ExtensionManager(handlers={"stub": handler}, store=store)
        op_id = await mgr._start_operation("alpha", "stub", "install", "user")
        await mgr._timeout("alpha", op_id)
        op = await mgr.get_operation(op_id)
        assert op["status"] == OperationStatus.TIMEOUT
        assert op["done"] is True

    async def test_concurrent_install_rejected(self, manager: ExtensionManager):
        await manager._save_state(
            ExtensionRuntimeState(id="alpha", kind="stub", state=ExtensionState.INSTALLING)
        )
        with pytest.raises(TransitionError):
            await manager.install("alpha")

    async def test_unknown_extension_raises_keyerror(self, manager: ExtensionManager):
        with pytest.raises(KeyError):
            await manager.install("inexistant")

@pytest.fixture
def manager(store: FakeStore, handler: StubHandler) -> ExtensionManager:
    return ExtensionManager(handlers={handler.kind: handler}, store=store)


def _dangling_operation(store: FakeStore, op_id: str = "opx_pend", ext_id: str = "alpha") -> None:
    """Simule une opération laissée RUNNING par un arrêt brutal."""
    import asyncio

    asyncio.get_event_loop_policy()  # no-op :garde l'import explicite
    store.data[(_OPERATION_DOMAIN, op_id)] = {
        "operation_id": op_id,
        "extension_id": ext_id,
        "kind": "stub",
        "operation": "install",
        "status": OperationStatus.RUNNING,
        "started_at": "2999-01-01T00:00:00+00:00",
        "updated_at": "2999-01-01T00:00:00+00:00",
        "error": None,
        "progress": 10,
    }
