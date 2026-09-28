"""Tests du Capability Manager (core/capability_manager) — spec section 11.

Couverture : detection, installation, idempotence, echec + rollback,
demarrage/arret, health check, desinstallation (conservation vs suppression
des donnees), dependances, etats intermediaires, annulation.

Le backend reel (Docker/pip) est remplace par un FakeBackend controle :
les tests valident la logique du Core, pas Docker.
"""

from __future__ import annotations

import asyncio
import platform
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from core.capability_manager import backends as backends_mod
from core.capability_manager import manager as mgr_mod
from core.capability_manager.manager import CapabilityManager, _validate_config
from core.capability_manager.types import (
    CapabilityRuntimeState,
    CapabilitySpec,
    CapabilityState,
    CapabilityType,
    ConfigField,
    Dependency,
    HealthCheck,
    Provenance,
    Requirements,
    TransitionError,
)


# ── backend factice ─────────────────────────────────────────────────────────
class FakeBackend:
    """Backend controllable : enregistre les appels, echoue a la demande."""

    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.fail_on: set[str] = set()
        self.block: asyncio.Event | None = None

    async def check_prerequisites(self, spec: CapabilitySpec) -> tuple[bool, str]:
        return True, "ok"

    async def execute(
        self, spec: CapabilitySpec, phase: str, config: dict[str, Any]
    ) -> tuple[bool, str]:
        if self.block is not None and phase == "install":
            await self.block.wait()
        self.calls.append((phase, spec.id, dict(config)))
        if phase in self.fail_on:
            return False, "echec simule: " + phase
        return True, "ok"

    async def plan(self, spec: CapabilitySpec, phase: str) -> list[tuple[str, str]]:
        return [("action simulee " + phase, phase)]

    async def rollback(self, spec: CapabilitySpec, phase: str) -> tuple[bool, str]:
        self.calls.append(("rollback:" + phase, spec.id, {}))
        return True, "rollback effectue"


# ── helpers ─────────────────────────────────────────────────────────────────
def make_spec(cap_id: str = "cap-a", **over: Any) -> CapabilitySpec:
    """Spec minimale valide pour le backend docker (actions dans l'allowlist).
    Le backend reel est remplace par le FakeBackend via monkeypatch."""
    fields: dict[str, Any] = dict(
        id=cap_id,
        name="Cap " + cap_id,
        description="capability de test",
        type=CapabilityType.SERVICE,
        version="1.0.0",
        backend="docker",
        requires_confirmation=True,
        install_actions=({"action": "check_docker"},),
        start_actions=({"action": "start", "name": "ethan-" + cap_id},),
        stop_actions=({"action": "stop", "name": "ethan-" + cap_id},),
        uninstall_actions=(
            {
                "action": "remove",
                "name": "ethan-" + cap_id,
                "keep_data": True,
                "data_to_delete": [{"kind": "volume", "name": "vol-" + cap_id}],
            },
        ),
    )
    fields.update(over)
    return CapabilitySpec(**fields)


async def wait_done(mgr: CapabilityManager, op_id: str, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        op = mgr.get_operation(op_id)
        assert op is not None, "operation inconnue: " + op_id
        if op["done"]:
            return op
        await asyncio.sleep(0.02)
    pytest.fail("operation non terminee dans le delai: " + op_id)


@pytest.fixture()
def fake_backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture()
def mgr(fake_backend: FakeBackend, monkeypatch: pytest.MonkeyPatch) -> CapabilityManager:
    real_get_backend = mgr_mod.get_backend

    def _get(name: str):
        if name == "docker":
            return fake_backend
        return real_get_backend(name)

    monkeypatch.setattr(mgr_mod, "get_backend", _get)
    m = CapabilityManager()
    m.register(make_spec("cap-a"))
    return m


# ── enregistrement + validation (section 10) ───────────────────────────────
class TestRegistration:
    def test_register_and_list(self, mgr: CapabilityManager) -> None:
        assert [s.id for s in mgr.list_specs()] == ["cap-a"]
        assert mgr.get_spec("cap-a") is not None
        assert mgr.get_spec("inconnu") is None

    def test_action_hors_allowlist_rejetee(self) -> None:
        m = CapabilityManager()
        bad = make_spec("bad", install_actions=({"action": "shell", "cmd": "rm -rf /"},))
        with pytest.raises(ValueError, match="interdite"):
            m.register(bad)
        # la spec rejettee n'est pas enregistree
        assert m.get_spec("bad") is None

    def test_etat_initial_supported_pas_installed(self, mgr: CapabilityManager) -> None:
        st = mgr._states.get("cap-a")
        if st is None:
            pytest.skip("etat charge paresseusement")
        assert st.state == CapabilityState.SUPPORTED


# ── detection (section 3) ──────────────────────────────────────────────────
class TestDetection:
    pytestmark = pytest.mark.asyncio

    async def test_detect_non_installe(self, mgr: CapabilityManager) -> None:
        results = await mgr.detect()
        assert results["cap-a"].state == CapabilityState.NOT_INSTALLED

    async def test_status_reflete_etat(self, mgr: CapabilityManager) -> None:
        await mgr.detect()
        status = await mgr.status("cap-a")
        assert status["state"] == CapabilityState.NOT_INSTALLED
        assert status["enabled"] is False
        # jamais un booleen : l'etat est une valeur de la machine a etats
        assert status["state"] in CapabilityState.ALL

    async def test_status_all(self, mgr: CapabilityManager) -> None:
        all_status = await mgr.status_all()
        assert {s["id"] for s in all_status} == {"cap-a"}


# ── installation (sections 4 + 8) ──────────────────────────────────────────
class TestInstall:
    pytestmark = pytest.mark.asyncio

    async def test_install_success_reaches_ready(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        op_id = await mgr.install("cap-a", actor="tester")
        op = await wait_done(mgr, op_id)
        assert op["error"] is None
        status = await mgr.status("cap-a")
        assert status["state"] == CapabilityState.READY
        assert status["installed_version"] == "1.0.0"
        phases = [c[0] for c in fake_backend.calls if c[1] == "cap-a"]
        assert "install" in phases and "start" in phases
        assert op["done"] is True

    async def test_install_avec_config_valide(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        m2 = CapabilityManager()
        m2.register(
            make_spec(
                "cfg",
                config_schema=(ConfigField(name="tag", type="string", choices=("a", "b")),),
            )
        )
        op_id = await m2.install("cfg", config={"tag": "b"})
        await wait_done(m2, op_id)
        install_calls = [c for c in fake_backend.calls if c[0] == "install"]
        assert install_calls and install_calls[-1][2] == {"tag": "b"}

    async def test_install_idempotente_si_ready(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        op1 = await mgr.install("cap-a")
        await wait_done(mgr, op1)
        nb_before = len([c for c in fake_backend.calls if c[0] == "install"])
        op2 = await mgr.install("cap-a")
        op = await wait_done(mgr, op2)
        # deja realise : aucune nouvelle execution backend, etat intact
        nb_after = len([c for c in fake_backend.calls if c[0] == "install"])
        assert nb_after == nb_before
        assert any("déjà" in s[0] or "deja" in s[0] for s in op["steps_done"])
        assert (await mgr.status("cap-a"))["state"] == CapabilityState.READY

    async def test_install_echec_backend_rollback_et_erreur(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        fake_backend.fail_on = {"install"}
        op_id = await mgr.install("cap-a")
        op = await wait_done(mgr, op_id)
        assert op["error"] is not None
        status = await mgr.status("cap-a")
        assert status["state"] == CapabilityState.ERROR
        assert status["last_error"] is not None
        phases = [c[0] for c in fake_backend.calls]
        assert "rollback:install" in phases  # rollback appele
        assert "start" not in phases  # jamais demarre

    async def test_install_dependance_manquante_bloque(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        m2 = CapabilityManager()
        m2.register(
            make_spec(
                "dep",
                dependencies=(
                    Dependency(
                        id="outil",
                        kind="system",
                        command=("binaire-ethan-absent-xyz",),
                    ),
                ),
            )
        )
        op_id = await m2.install("dep")
        op = await wait_done(m2, op_id)
        assert op["error"] is not None
        assert not [c for c in fake_backend.calls if c[0] == "install"]
        assert (await m2.status("dep"))["state"] == CapabilityState.ERROR

    async def test_install_capability_inconnue(self, mgr: CapabilityManager) -> None:
        with pytest.raises((KeyError, ValueError, LookupError)):
            await mgr.install("n-importe-quoi")

    async def test_health_gate_pas_ready_sans_endpoint(self, mgr: CapabilityManager) -> None:
        """Section 8 : installe + demarre != READY si le check functional echoue."""
        m2 = CapabilityManager()
        m2.register(
            make_spec(
                "sick",
                health_checks=(
                    HealthCheck(
                        kind="endpoint",
                        level="functional",
                        url="http://127.0.0.1:9/readyz",
                    ),
                ),
            )
        )
        op_id = await m2.install("sick")
        await wait_done(m2, op_id)
        status = await m2.status("sick")
        assert status["state"] != CapabilityState.READY
        # un test explicite le confirme UNHEALTHY
        result = await m2.test("sick")
        assert result["ok"] is False
        assert result["level"] == "failing"

    async def test_test_method_ok_apres_install(self, mgr: CapabilityManager) -> None:
        op_id = await mgr.install("cap-a")
        await wait_done(mgr, op_id)
        result = await mgr.test("cap-a")
        assert result["ok"] is True
        assert result["level"] == "ready"


# ── enable / disable / configure ───────────────────────────────────────────
class TestEnableConfigure:
    pytestmark = pytest.mark.asyncio

    async def test_enable_exige_ready(self, mgr: CapabilityManager) -> None:
        with pytest.raises(TransitionError):
            await mgr.enable("cap-a")

    async def test_enable_disable_cycle(self, mgr: CapabilityManager) -> None:
        op_id = await mgr.install("cap-a")
        await wait_done(mgr, op_id)
        await mgr.enable("cap-a")
        assert (await mgr.status("cap-a"))["enabled"] is True
        await mgr.disable("cap-a")
        assert (await mgr.status("cap-a"))["enabled"] is False

    async def test_configure_valide_et_persiste(self, mgr: CapabilityManager) -> None:
        m2 = CapabilityManager()
        m2.register(
            make_spec(
                "cfg",
                config_schema=(ConfigField(name="port", type="port", default=1000),),
            )
        )
        op_id = await m2.install("cfg")
        await wait_done(m2, op_id)
        await m2.configure("cfg", {"port": 4321})
        assert (await m2.status("cfg"))["config_keys"] == ["port"]

    async def test_configure_rejette_champ_inconnu(self, mgr: CapabilityManager) -> None:
        m2 = CapabilityManager()
        m2.register(make_spec("cfg", config_schema=(ConfigField(name="port", type="port"),)))
        with pytest.raises(ValueError, match="inconnu"):
            await m2.configure("cfg", {"inject": "; rm -rf /"})


def test_validate_config_injection_rejetee() -> None:
    spec = make_spec(
        "v",
        config_schema=(
            ConfigField(name="tag", type="string", choices=("a", "b")),
            ConfigField(name="port", type="port", min_value=1, max_value=10),
        ),
    )
    with pytest.raises(ValueError):
        _validate_config(spec, {"tag": "a; rm -rf /"})
    with pytest.raises(ValueError):
        _validate_config(spec, {"port": 99999})
    with pytest.raises(ValueError):
        _validate_config(spec, {"champ_inconnu": 1})
    cleaned = _validate_config(spec, {"tag": "a", "port": "7"})
    assert cleaned == {"tag": "a", "port": 7}


# ── plans (section 4 : previsible avant execution) ─────────────────────────
class TestPlans:
    pytestmark = pytest.mark.asyncio

    async def test_plan_install(self, mgr: CapabilityManager) -> None:
        plan = await mgr.plan_install("cap-a")
        assert plan.capability_id == "cap-a"
        assert plan.operation == "install"
        assert len(plan.steps) >= 2
        assert plan.requires_confirmation is True

    async def test_plan_uninstall_destructif_explicite(self, mgr: CapabilityManager) -> None:
        keep = await mgr.plan_uninstall("cap-a", delete_data=False)
        wipe = await mgr.plan_uninstall("cap-a", delete_data=True)
        assert not any(s.destructive for s in keep.steps)
        assert any(s.destructive for s in wipe.steps)
        assert wipe.requires_confirmation is True


# ── désinstallation (section 5) ────────────────────────────────────────────
class TestUninstall:
    pytestmark = pytest.mark.asyncio

    async def _install(self, mgr: CapabilityManager) -> None:
        op_id = await mgr.install("cap-a")
        await wait_done(mgr, op_id)

    async def test_uninstall_conserve_donnees(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        await self._install(mgr)
        op_id = await mgr.uninstall("cap-a", delete_data=False)
        op = await wait_done(mgr, op_id)
        assert op["error"] is None
        status = await mgr.status("cap-a")
        assert status["state"] == CapabilityState.SUPPORTED
        assert status["enabled"] is False
        remove_calls = [c for c in fake_backend.calls if c[0] == "uninstall"]
        assert remove_calls
        # les donnees ne doivent PAS figurer dans l'action passee au backend
        assert (
            "keep_data" not in remove_calls[-1][2]
            or remove_calls[-1][2].get("keep_data") is not False
        )

    async def test_uninstall_supprime_donnees_explicite(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        await self._install(mgr)
        op_id = await mgr.uninstall("cap-a", delete_data=True)
        op = await wait_done(mgr, op_id)
        assert op["error"] is None
        assert (await mgr.status("cap-a"))["state"] == CapabilityState.SUPPORTED

    async def test_uninstall_arrete_avant_retrait(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        await self._install(mgr)
        fake_backend.calls.clear()
        op_id = await mgr.uninstall("cap-a")
        await wait_done(mgr, op_id)
        phases = [c[0] for c in fake_backend.calls]
        assert phases.index("stop") < phases.index("uninstall")

    async def test_uninstall_bloque_si_dependant_actif(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        """Section 10 : pas de retrait d'une dependance d'une capability active."""
        await self._install(mgr)
        mgr.register(
            make_spec(
                "cap-b",
                dependencies=(Dependency(id="cap-a", kind="capability"),),
            )
        )
        op_b = await mgr.install("cap-b")
        await wait_done(mgr, op_b)
        await mgr.enable("cap-b")
        op_id = await mgr.uninstall("cap-a")
        op = await wait_done(mgr, op_id)
        assert op["error"] is not None
        assert "cap-b" in op["error"]
        # cap-a n'a pas ete materiallement retiree
        assert not [c for c in fake_backend.calls if c[1] == "cap-a" and c[0] == "uninstall"]

    async def test_uninstall_capability_inconnue(self, mgr: CapabilityManager) -> None:
        with pytest.raises((KeyError, ValueError, LookupError)):
            await mgr.uninstall("fantome")


# ── parcours complet (cycle de vie de bout en bout) ────────────────────────
class TestLifecycleBoutEnBout:
    """Parcours nominal complet sur un seul composant (ADR-4001).

    detect → plan → install → test → enable → disable → uninstall.
    Les classes ci-dessus vérifient chaque transition isolément ; celle-ci
    verrouille leur continuité : chaque étape doit être atteignable depuis
    l'état produit par la précédente, sans « trou » dans la machine à états.
    """

    pytestmark = pytest.mark.asyncio

    async def test_parcours_complet(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        mgr.register(
            make_spec(
                "e2e",
                config_schema=(ConfigField(name="port", type="port", default=11434),),
            )
        )

        # 1. Détection : supporté, pas encore installé (jamais inventé).
        await mgr.detect()
        assert (await mgr.status("e2e"))["state"] == CapabilityState.NOT_INSTALLED

        # 2. Plan : l'utilisateur voit les opérations AVANT toute mutation.
        plan = await mgr.plan_install("e2e")
        assert plan.requires_confirmation is True
        assert len(plan.steps) >= 2

        # 3. Installation avec configuration : → READY, version enregistrée.
        op = await wait_done(mgr, await mgr.install("e2e", config={"port": 11435}, actor="e2e"))
        assert op["error"] is None
        status = await mgr.status("e2e")
        assert status["state"] == CapabilityState.READY
        assert status["installed_version"] == "1.0.0"
        assert status["config_keys"] == ["port"]

        # 4. Test fonctionnel réel : la santé confirme READY.
        result = await mgr.test("e2e")
        assert result["ok"] is True
        assert (await mgr.status("e2e"))["state"] == CapabilityState.READY

        # 5. Activation (exige READY), puis désactivation (flag seul).
        await mgr.enable("e2e")
        assert (await mgr.status("e2e"))["enabled"] is True
        await mgr.disable("e2e")
        assert (await mgr.status("e2e"))["enabled"] is False

        # 6. Désinstallation en conservant les données : arrêt avant retrait,
        #    retour à SUPPORTED, configuration purgée, plus d'erreur.
        op_id = await mgr.uninstall("e2e", delete_data=False)
        await wait_done(mgr, op_id)
        phases = [c[0] for c in fake_backend.calls if c[1] == "e2e"]
        assert phases.index("stop") < phases.index("uninstall")
        final = await mgr.status("e2e")
        assert final["state"] == CapabilityState.SUPPORTED
        assert final["enabled"] is False
        assert final["config_keys"] == []
        assert final["last_error"] is None

        # 7. Traçabilité : les opérations du parcours restent listables.
        assert op_id in {o["operation_id"] for o in mgr.list_operations()}


# ── etats intermediaires + annulation (section 4) ─────────────────────────
class TestIntermediates:
    pytestmark = pytest.mark.asyncio

    async def test_etat_intermediaire_installation_visible(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        fake_backend.block = asyncio.Event()
        op_id = await mgr.install("cap-a")
        seen: list[str] = []
        for _ in range(100):
            st = (await mgr.status("cap-a"))["state"]
            seen.append(st)
            if st == CapabilityState.INSTALLING:
                break
            await asyncio.sleep(0.01)
        assert CapabilityState.INSTALLING in seen
        fake_backend.block.set()
        await wait_done(mgr, op_id)

    async def test_install_refusee_si_deja_en_cours(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        fake_backend.block = asyncio.Event()
        op1 = await mgr.install("cap-a")
        await asyncio.sleep(0.05)
        with pytest.raises(TransitionError):
            await mgr.install("cap-a")
        fake_backend.block.set()
        await wait_done(mgr, op1)

    async def test_cancel_operation(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        fake_backend.block = asyncio.Event()
        op_id = await mgr.install("cap-a")
        ok = await mgr.cancel_operation(op_id)
        assert ok is True
        op = await wait_done(mgr, op_id)
        assert op["cancel_requested"] is True or op["error"] is not None
        assert (await mgr.status("cap-a"))["state"] in (
            CapabilityState.ERROR,
            CapabilityState.NOT_INSTALLED,
        )
        fake_backend.block.set()

    async def test_cancel_operation_inconnue(self, mgr: CapabilityManager) -> None:
        assert await mgr.cancel_operation("op_introuvable") is False

    async def test_list_operations(self, mgr: CapabilityManager) -> None:
        op_id = await mgr.install("cap-a")
        await wait_done(mgr, op_id)
        ops = mgr.list_operations()
        assert op_id in {o["operation_id"] for o in ops}


# ── dependances entre capabilities (section 4) ────────────────────────────
class TestCapabilityDependencies:
    pytestmark = pytest.mark.asyncio

    async def test_dependance_capability_manquante_bloque_install(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        mgr.register(
            make_spec(
                "cap-c",
                dependencies=(Dependency(id="cap-absente", kind="capability"),),
            )
        )
        op_id = await mgr.install("cap-c")
        op = await wait_done(mgr, op_id)
        assert op["error"] is not None
        assert not [c for c in fake_backend.calls if c[1] == "cap-c" and c[0] == "install"]

    async def test_dependance_capability_satisfaite_ok(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        op_a = await mgr.install("cap-a")
        await wait_done(mgr, op_a)
        mgr.register(make_spec("cap-d", dependencies=(Dependency(id="cap-a", kind="capability"),)))
        op_d = await mgr.install("cap-d")
        op = await wait_done(mgr, op_d)
        assert op["error"] is None
        assert (await mgr.status("cap-d"))["state"] == CapabilityState.READY


# ── catalogue builtin (sections 1 + 6 + 7) ─────────────────────────────────
class TestBuiltin:
    def test_catalogue_enregistre_et_valide(self) -> None:
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        ids = {s.id for s in m.list_specs()}
        assert {"qdrant", "chromadb"} <= ids

    def test_qdrant_supported_pas_installe_par_defaut(self) -> None:
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        st = m._states["qdrant"]
        assert st.state == CapabilityState.SUPPORTED
        assert st.enabled is False

    def test_qdrant_spec_declaration(self) -> None:
        from core.capability_manager.builtin import build_manager, qdrant

        build_manager()  # le catalogue passe la validation d'enregistrement
        q = qdrant()
        assert q.requires_confirmation is True  # jamais automatique
        assert q.backend == "docker"
        assert any(d.id == "docker" for d in q.dependencies)
        # desinstallation : conservation des donnees par defaut
        removes = [a for a in q.uninstall_actions if a["action"] == "remove"]
        assert removes and all(a.get("keep_data") is True for a in removes)
        # checks de sante declaratifs (tcp + endpoint)
        kinds = {hc.kind for hc in q.health_checks}
        assert "tcp" in kinds and "endpoint" in kinds


# ── capacité builtin "memory" (spec §8 : Ready + Configure, jamais install) ─
class TestBuiltinMemory:
    pytestmark = pytest.mark.asyncio

    async def test_memory_in_catalogue(self) -> None:
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        ids = {s.id for s in m.list_specs()}
        assert "memory" in ids

    async def test_memory_detected_ready(self) -> None:
        """Le builtin est détecté présent et sa santé réelle validée → READY."""
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        await m.detect()
        st = m._states["memory"]
        assert st.state == CapabilityState.READY
        assert st.enabled is False  # disponible mais pas activé par défaut

    async def test_memory_health_check_real(self) -> None:
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        st = m._states["memory"]
        result = await m._health.evaluate(m._registry["memory"], st)
        assert result["ok"] is True
        assert result["level"] == "ready"
        kinds = {c["kind"] for c in result["checks"]}
        assert "builtin" in kinds

    async def test_memory_no_install_path(self) -> None:
        """Un builtin ne propose jamais d'installation : uninstall → SUPPORTED."""
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        await m.detect()  # → READY
        op_id = await m.uninstall("memory", delete_data=False)
        op = await wait_done(m, op_id)
        assert op["error"] is None
        st = m._states["memory"]
        assert st.state == CapabilityState.SUPPORTED

    async def test_memory_configure(self) -> None:
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        await m.detect()
        state = await m.configure("memory", {"collection": "ethan-dev"})
        assert state.config.get("collection") == "ethan-dev"


# ── start / stop (section 3 de la spec UI) ─────────────────────────────────
class TestStartStop:
    pytestmark = pytest.mark.asyncio

    async def test_stop_then_start_cycle(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        op_id = await mgr.install("cap-a")
        await wait_done(mgr, op_id)
        await mgr.stop("cap-a")
        assert (await mgr.status("cap-a"))["state"] == CapabilityState.STOPPED
        phases = [c[0] for c in fake_backend.calls]
        assert "stop" in phases
        health = await mgr.start("cap-a")
        assert health["ok"] is True
        assert (await mgr.status("cap-a"))["state"] == CapabilityState.READY

    async def test_stop_refuse_si_pas_actif(self, mgr: CapabilityManager) -> None:
        with pytest.raises(TransitionError):
            await mgr.stop("cap-a")

    async def test_start_refuse_si_pas_installe(self, mgr: CapabilityManager) -> None:
        with pytest.raises(TransitionError):
            await mgr.start("cap-a")


class TestExtendedTypes:
    """Tests des types de composants étendus et de la provenance."""

    def test_all_types_in_frozenset(self) -> None:
        """Tous les types déclarés sont dans CapabilityType.ALL."""
        for attr in (
            "PROVIDER",
            "MODEL",
            "VECTOR_DATABASE",
            "RUNTIME",
            "SERVICE",
            "INTEGRATION",
            "TOOL",
            "EMBEDDING",
            "RERANKER",
            "STT_TTS",
            "MCP_SERVER",
            "PLUGIN",
            "SKILL",
        ):
            value = getattr(CapabilityType, attr)
            assert value in CapabilityType.ALL, f"{attr} absent de ALL"

    def test_provenance_default(self) -> None:
        from core.capability_manager.types import Provenance

        p = Provenance()
        assert p.source == "builtin"
        assert p.author == "ETHAN"
        assert p.checksum == ""

    def test_provenance_custom(self) -> None:
        from core.capability_manager.types import Provenance

        p = Provenance(
            source="official",
            author="Redis Ltd.",
            url="https://redis.io",
            license="RSALv2",
            checksum="abc123",
        )
        assert p.source == "official"
        assert p.checksum == "abc123"

    def test_spec_with_provenance_validates(self) -> None:
        from core.capability_manager.types import Provenance

        spec = make_spec(
            "prov",
            type=CapabilityType.SERVICE,
            provenance=Provenance(
                source="community",
                author="Test",
                url="https://example.com",
            ),
        )
        # Should not raise
        spec.validate()

    def test_spec_with_invalid_provenance_rejected(self) -> None:
        from core.capability_manager.types import Provenance

        spec = make_spec(
            "bad-prov",
            provenance=Provenance(source="malicious"),
        )
        with pytest.raises(ValueError, match="provenance"):
            spec.validate()

    def test_new_type_spec_registers(self) -> None:
        """Un composant de type EMBEDDING s'enregistre correctement."""
        m = CapabilityManager()
        spec = make_spec("emb-a", type=CapabilityType.EMBEDDING)
        m.register(spec)
        assert m.get_spec("emb-a") is not None
        assert m.get_spec("emb-a").type == CapabilityType.EMBEDDING

    def test_stt_tts_type(self) -> None:
        m = CapabilityManager()
        spec = make_spec("tts-a", type=CapabilityType.STT_TTS)
        m.register(spec)
        assert m.get_spec("tts-a").type == "stt_tts"


class TestStatusProvenance:
    """status() expose la provenance du spec — source unique pour les interfaces."""

    pytestmark = pytest.mark.asyncio

    async def test_status_exposes_provenance(self) -> None:
        """status() expose la provenance du spec (d'où vient le composant)."""
        from core.capability_manager.types import Provenance

        m = CapabilityManager()
        m.register(
            make_spec(
                "prov-api",
                provenance=Provenance(
                    source="community",
                    author="Seclib",
                    url="https://example.com/prov",
                    license="MIT",
                    checksum="sha256:deadbeef",
                ),
            )
        )
        prov = (await m.status("prov-api"))["provenance"]
        assert prov["source"] == "community"
        assert prov["author"] == "Seclib"
        assert prov["url"] == "https://example.com/prov"
        assert prov["license"] == "MIT"
        assert prov["checksum"] == "sha256:deadbeef"

    async def test_status_provenance_defaults_never_invented(self) -> None:
        """Sans provenance explicite : builtin/ETHAN, checksum vide (jamais inventé)."""
        m = CapabilityManager()
        m.register(make_spec("plain"))
        prov = (await m.status("plain"))["provenance"]
        assert prov["source"] == "builtin"
        assert prov["author"] == "ETHAN"
        assert prov["checksum"] == ""
        assert prov["signature"] == ""


class TestExpandedCatalog:
    """Tests du catalogue étendu."""

    def test_catalogue_includes_all_builtin(self) -> None:
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        ids = {s.id for s in m.list_specs()}
        expected = {
            "memory",
            "qdrant",
            "chromadb",
            "ollama",
            "redis",
            "searxng",
            "whisper",
            "mcp-filesystem",
        }
        assert expected <= ids

    def test_ollama_spec_executable_backend(self) -> None:
        from core.capability_manager.builtin import ollama

        spec = ollama()
        assert spec.backend == "executable"
        assert spec.type == CapabilityType.PROVIDER
        assert spec.provenance.source == "official"

    def test_redis_spec_docker_backend(self) -> None:
        from core.capability_manager.builtin import redis

        spec = redis()
        assert spec.backend == "docker"
        assert spec.type == CapabilityType.SERVICE
        assert any(d.id == "docker" for d in spec.dependencies)

    def test_whisper_spec_python_backend(self) -> None:
        from core.capability_manager.builtin import whisper

        spec = whisper()
        assert spec.backend == "python_package"
        assert spec.type == CapabilityType.STT_TTS

    def test_all_builtin_specs_validate(self) -> None:
        """Toutes les specs du catalogue passent la validation."""
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        for spec in m.list_specs():
            spec.validate()  # must not raise

    def test_all_builtin_have_provenance(self) -> None:
        """Chaque spec a une provenance non vide."""
        from core.capability_manager.builtin import build_manager

        m = build_manager()
        for spec in m.list_specs():
            assert spec.provenance.source in {"builtin", "official", "community", "custom"}
            assert spec.provenance.author


# ── detection reelle par backend (ESR-002 §5) ──────────────────────────────
class TestDetectInstalledByBackend:
    """Chaque backend declare une verification : la detection doit la lire.

    Regression : les backends `executable` et `python_package` etaient mal
    detectes — un composant pourtant present etait rendu « not installed ».
    """

    pytestmark = pytest.mark.asyncio

    @staticmethod
    def _spec(cap_id: str, backend: str, install_actions: tuple) -> CapabilitySpec:
        return make_spec(
            cap_id,
            backend=backend,
            install_actions=install_actions,
            start_actions=(),
            stop_actions=(),
            uninstall_actions=(),
        )

    async def test_executable_present_detecte_installe(self) -> None:
        spec = self._spec(
            "exe-present",
            "executable",
            ({"action": "verify_path", "executable": "python3"},),
        )
        assert await CapabilityManager()._detect_installed(spec) is True

    async def test_executable_absent_detecte_non_installe(self) -> None:
        spec = self._spec(
            "exe-absent",
            "executable",
            ({"action": "verify_path", "executable": "ethan-binaire-absent-xyz"},),
        )
        assert await CapabilityManager()._detect_installed(spec) is False

    async def test_python_verification_apres_pip_install(self) -> None:
        # `pip_install` precede `verify_import` dans le catalogue : la boucle
        # ne doit pas s'arreter a la premiere action.
        spec = self._spec(
            "py-present",
            "python_package",
            (
                {"action": "pip_install", "packages": ["json"]},
                {"action": "verify_import", "module": "json"},
            ),
        )
        assert await CapabilityManager()._detect_installed(spec) is True

    async def test_python_module_absent_non_installe(self) -> None:
        spec = self._spec(
            "py-absent",
            "python_package",
            (
                {"action": "pip_install", "packages": ["ethan-absent-xyz"]},
                {"action": "verify_import", "module": "ethan_absent_xyz"},
            ),
        )
        assert await CapabilityManager()._detect_installed(spec) is False

    async def test_sans_verification_declaree_non_installe(self) -> None:
        spec = self._spec(
            "sans-verif",
            "python_package",
            ({"action": "pip_install", "packages": ["json"]},),
        )
        assert await CapabilityManager()._detect_installed(spec) is False

    async def test_node_binaire_present_detecte(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(backends_mod, "node_prefix", lambda: tmp_path)
        binary = tmp_path / "bin" / "mcp-server-filesystem"
        binary.parent.mkdir(parents=True)
        binary.write_text("#!/bin/sh\nexit 0\n")
        binary.chmod(0o755)
        spec = self._spec(
            "node-present",
            "node_package",
            ({"action": "verify_binary", "binary": "mcp-server-filesystem"},),
        )
        assert await CapabilityManager()._detect_installed(spec) is True

    async def test_node_binaire_absent_non_installe(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(backends_mod, "node_prefix", lambda: tmp_path)
        spec = self._spec(
            "node-absent",
            "node_package",
            ({"action": "verify_binary", "binary": "mcp-server-filesystem"},),
        )
        assert await CapabilityManager()._detect_installed(spec) is False


# ── reconciliation detection → etat (ESR-002 §5) ───────────────────────────
class TestDetectReconciliation:
    """Un composant present mais jamais installe via ETHAN doit sortir de
    l'etat indetermine : detection → INSTALLED, puis sante → READY."""

    pytestmark = pytest.mark.asyncio

    @staticmethod
    def _register(m: CapabilityManager, cap_id: str, checks: tuple) -> None:
        m.register(
            make_spec(
                cap_id,
                backend="executable",
                install_actions=({"action": "verify_path", "executable": "python3"},),
                start_actions=(),
                stop_actions=(),
                uninstall_actions=(),
                health_checks=checks,
            )
        )

    async def test_present_et_sain_devient_ready(self) -> None:
        m = CapabilityManager()
        self._register(m, "exe-sain", (HealthCheck(kind="builtin"),))
        await m.detect()
        st = m._states["exe-sain"]
        assert st.state == CapabilityState.READY
        assert st.last_error is None

    async def test_present_mais_sante_refusee_reste_installe(self) -> None:
        m = CapabilityManager()
        self._register(m, "exe-malade", (HealthCheck(kind="tcp", port="port"),))
        await m.detect()
        st = m._states["exe-malade"]
        assert st.state == CapabilityState.INSTALLED
        assert st.last_error == "santé refusée"


# ── sante : resolution des defauts du schema (spec §7) ─────────────────────
class TestHealthConfigDefaults:
    """Un champ jamais saisi vaut son défaut déclaré : un composant qui
    tourne sur les défauts n'est pas jugé « santé refusée » (cas ollama :
    démon joignable mais `{config.base_url}` résolu en vide)."""

    @staticmethod
    def _spec() -> CapabilitySpec:
        return make_spec(
            "health-defaults",
            backend="builtin",
            install_actions=(),
            start_actions=(),
            stop_actions=(),
            uninstall_actions=(),
            config_schema=(
                ConfigField(name="port", type="port", required=False, default=59999),
                ConfigField(
                    name="base_url",
                    type="string",
                    required=False,
                    default="http://localhost:11434",
                ),
            ),
            health_checks=(HealthCheck(kind="tcp", level="functional", port="port"),),
        )

    def test_resolve_utilise_le_defaut_si_config_absent(self) -> None:
        from core.capability_manager.health import _resolve

        spec = self._spec()
        state = CapabilityRuntimeState(id=spec.id)
        defaults = {f.name: f.default for f in spec.config_schema}
        assert (
            _resolve("{config.base_url}/api/tags", state, defaults)
            == "http://localhost:11434/api/tags"
        )

    def test_resolve_config_saisie_l_emporte_sur_le_defaut(self) -> None:
        from core.capability_manager.health import _resolve

        spec = self._spec()
        state = CapabilityRuntimeState(id=spec.id, config={"base_url": "http://h:1"})
        defaults = {f.name: f.default for f in spec.config_schema}
        assert _resolve("{config.base_url}/api/tags", state, defaults) == "http://h:1/api/tags"


class TestHealthConfigDefaultsCheck:
    """Les checks `tcp` partent avec le port effectif : défaut déclaré ou
    valeur saisie par l'utilisateur."""

    pytestmark = pytest.mark.asyncio

    async def test_tcp_utilise_le_port_par_defaut(self) -> None:
        from core.capability_manager.health import HealthChecker

        spec = TestHealthConfigDefaults._spec()
        state = CapabilityRuntimeState(id=spec.id)
        result = await HealthChecker().evaluate(spec, state)
        detail = result["checks"][0]["detail"]
        # le port par défaut est réellement utilisé (jamais « non configure »)
        assert "59999" in detail
        assert "non configure" not in detail

    async def test_tcp_config_saisie_l_emporte(self) -> None:
        from core.capability_manager.health import HealthChecker

        spec = TestHealthConfigDefaults._spec()
        state = CapabilityRuntimeState(id=spec.id, config={"port": 59998})
        result = await HealthChecker().evaluate(spec, state)
        assert "59998" in result["checks"][0]["detail"]


# ── backend node_package (ESR-004 §4) ──────────────────────────────────────
class TestNodePackageBackend:
    """Backend npm : allowlist, prerequis, argv confine, rollback, plan."""

    pytestmark = pytest.mark.asyncio

    @staticmethod
    def _spec(**over: Any) -> CapabilitySpec:
        fields: dict[str, Any] = dict(
            backend="node_package",
            install_actions=(
                {"action": "npm_install", "packages": ["@scope/pkg@1.2.3"]},
                {"action": "verify_binary", "binary": "pkg-cli"},
            ),
            start_actions=(),
            stop_actions=(),
            uninstall_actions=({"action": "npm_uninstall", "packages": ["@scope/pkg"]},),
        )
        fields.update(over)
        return make_spec("node-cap", **fields)

    @staticmethod
    def _fake_run(calls: list[list[str]]):
        async def fake_run(argv: list[str], timeout: float = 300.0) -> tuple[bool, str]:
            calls.append(list(argv))
            return True, "ok"

        return fake_run

    @staticmethod
    def _fake_binary(tmp_path: Path, name: str = "pkg-cli") -> Path:
        binary = tmp_path / "bin" / name
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text("#!/bin/sh\nexit 0\n")
        binary.chmod(0o755)
        return binary

    async def test_prerequis_npm_absent_message_explicite(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(backends_mod.NodePackageBackend, "_npm", lambda self: None)
        backend = backends_mod.get_backend("node_package")
        ok, msg = await backend.check_prerequisites(self._spec())
        assert ok is False
        assert "npm" in msg and "Node.js" in msg

    async def test_install_argv_confinee_au_prefixe_ethan(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[list[str]] = []
        monkeypatch.setattr(backends_mod, "_run", self._fake_run(calls))
        monkeypatch.setattr(backends_mod, "node_prefix", lambda: tmp_path)
        monkeypatch.setattr(backends_mod.NodePackageBackend, "_npm", lambda self: "/usr/bin/npm")
        self._fake_binary(tmp_path)

        backend = backends_mod.get_backend("node_package")
        ok, msg = await backend.execute(self._spec(), "install", {})
        assert ok is True
        assert msg == "ok"
        assert calls == [
            [
                "/usr/bin/npm",
                "install",
                "--global",
                "--prefix",
                str(tmp_path),
                "--no-audit",
                "--no-fund",
                "@scope/pkg@1.2.3",
            ]
        ]

    async def test_verify_binaire_absent_echoue(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(backends_mod, "node_prefix", lambda: tmp_path)
        monkeypatch.setattr(backends_mod.NodePackageBackend, "_npm", lambda self: "/usr/bin/npm")
        backend = backends_mod.get_backend("node_package")
        ok, msg = await backend.execute(
            self._spec(install_actions=({"action": "verify_binary", "binary": "absent-cli"},)),
            "install",
            {},
        )
        assert ok is False
        assert "absent-cli" in msg

    async def test_rollback_desinstalle_le_paquet(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[list[str]] = []
        monkeypatch.setattr(backends_mod, "_run", self._fake_run(calls))
        monkeypatch.setattr(backends_mod, "node_prefix", lambda: tmp_path)
        monkeypatch.setattr(backends_mod.NodePackageBackend, "_npm", lambda self: "/usr/bin/npm")
        backend = backends_mod.get_backend("node_package")
        ok, _ = await backend.rollback(self._spec(), "install")
        assert ok is True
        # la version epinglee est retiree : npm uninstall attend le nom
        assert calls[0][:4] == ["/usr/bin/npm", "uninstall", "--global", "--prefix"]
        assert calls[0][-1] == "@scope/pkg"

    async def test_plan_install_et_uninstall(self) -> None:
        backend = backends_mod.get_backend("node_package")
        spec = self._spec()
        install_steps = await backend.plan(spec, "install")
        uninstall_steps = await backend.plan(spec, "uninstall")
        assert "@scope/pkg@1.2.3" in install_steps[0][0]
        assert "@scope/pkg" in uninstall_steps[0][0]
        assert await backend.plan(spec, "start") == []


# ── node_package : registre & helpers (tests synchrones) ───────────────────
class TestNodePackageBackendRegistre:
    """Registre et helpers npm — aucun I/O asynchrone ici."""

    def test_action_hors_allowlist_rejetee(self) -> None:
        m = CapabilityManager()
        bad = make_spec(
            "node-bad",
            backend="node_package",
            install_actions=({"action": "npm_exec", "argv": ["sh", "-c", "true"]},),
            start_actions=(),
            stop_actions=(),
            uninstall_actions=(),
        )
        with pytest.raises(ValueError, match="interdite"):
            m.register(bad)
        assert m.get_spec("node-bad") is None

    def test_verify_binaire_non_executable_refuse(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(backends_mod, "node_prefix", lambda: tmp_path)
        binary = tmp_path / "bin" / "pkg-cli"
        binary.parent.mkdir(parents=True)
        binary.write_text("donnees")  # present mais sans bit executable
        binary.chmod(0o644)
        assert backends_mod.node_binary_ok("pkg-cli") is False

    def test_unpinned_retire_la_version(self) -> None:
        assert backends_mod._unpinned("@scope/pkg@1.2.3") == "@scope/pkg"
        assert backends_mod._unpinned("pkg@1.2.3") == "pkg"
        assert backends_mod._unpinned("pkg") == "pkg"


# ── catalogue : serveur MCP Node (premier composant mcp_server) ────────────
class TestMcpFilesystemCatalog:
    """L'entree de catalogue honore la discipline (versions figees, rien
    d'invente) et le type `mcp_server` a enfin un representant."""

    def test_spec_mcp_filesystem(self) -> None:
        from core.capability_manager.builtin import mcp_filesystem

        spec = mcp_filesystem()
        assert spec.type == CapabilityType.MCP_SERVER
        assert spec.backend == "node_package"
        assert spec.install_actions[0]["packages"] == [
            "@modelcontextprotocol/server-filesystem@2026.8.31"
        ]
        assert spec.provenance.source == "official"
        assert spec.provenance.url
        # aucune metadonnee inventee : la licence upstream n'est pas declaree
        assert spec.provenance.license == ""
        # transport stdio : pas de processus permanent a demarrer
        assert spec.start_actions == ()
        assert spec.stop_actions == ()

    def test_enregistre_dans_le_catalogue(self) -> None:
        from core.capability_manager.builtin import build_manager

        spec = build_manager().get_spec("mcp-filesystem")
        assert spec is not None
        assert spec.type == CapabilityType.MCP_SERVER


# ── vocabulaire public (alias « component ») ───────────────────────────────
class TestAliasComponentManager:
    def test_alias_est_une_identite_stricte(self) -> None:
        """`ComponentManager` (vocabulaire API /v1/components) est le manager
        canonique du Core — jamais une seconde implementation ni un wrapper."""


# ── prérequis déclarés : compatibilité + ressources (PRÉREQUIS) ────────────
class TestRequirementsSpec:
    """`requirements` : déclaration typée, rien d'inventé, validation stricte."""

    def test_defaut_aucune_exigence(self) -> None:
        spec = make_spec("req-def")
        assert spec.requirements.is_empty() is True
        assert spec.requirements.to_dict() == {
            "os": [],
            "arch": [],
            "min_ram_mb": None,
            "min_disk_mb": None,
        }
        spec.validate()

    def test_exigences_invalides_rejetees(self) -> None:
        with pytest.raises(ValueError, match=r"requirements\.min_ram_mb"):
            make_spec("req-bad-ram", requirements=Requirements(min_ram_mb=0)).validate()
        with pytest.raises(ValueError, match=r"requirements\.min_disk_mb"):
            make_spec("req-bad-disk", requirements=Requirements(min_disk_mb=-5)).validate()
        with pytest.raises(ValueError, match=r"requirements\.os"):
            make_spec("req-bad-os", requirements=Requirements(os=("",))).validate()
        with pytest.raises(ValueError, match=r"requirements\.arch"):
            CapabilityManager().register(
                make_spec("req-bad-arch", requirements=Requirements(arch=(" ",)))
            )


class TestRequirementsGates:
    """Vérifiés AVANT toute mutation ; une mesure impossible n'est jamais
    transformée en échec (un verdict non fondé est refusé)."""

    pytestmark = pytest.mark.asyncio

    async def test_os_incompatible_detecte_supported(self, mgr: CapabilityManager) -> None:
        mgr.register(make_spec("req-os", requirements=Requirements(os=("plan9",))))
        states = await mgr.detect()
        assert states["req-os"].state == CapabilityState.SUPPORTED
        assert "prerequis" in (states["req-os"].last_error or "")
        # un composant sans exigence déclarée n'est pas affecté
        assert states["cap-a"].state == CapabilityState.NOT_INSTALLED

    async def test_os_incompatible_bloque_install_sans_mutation(
        self, mgr: CapabilityManager, fake_backend: FakeBackend
    ) -> None:
        mgr.register(make_spec("req-os2", requirements=Requirements(os=("plan9",))))
        op = await wait_done(mgr, await mgr.install("req-os2"))
        assert op["error"]
        assert [c for c in fake_backend.calls if c[1] == "req-os2"] == []
        state = await mgr._load_state("req-os2")
        assert state.state == CapabilityState.ERROR
        assert "prerequis" in (state.last_error or "")

    async def test_arch_incompatible_bloque(self, mgr: CapabilityManager) -> None:
        mgr.register(make_spec("req-arch", requirements=Requirements(arch=("sparc64",))))
        op = await wait_done(mgr, await mgr.install("req-arch"))
        assert op["error"]
        state = await mgr._load_state("req-arch")
        assert "architecture" in (state.last_error or "")

    async def test_ram_non_verifiable_non_bloquant(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(mgr_mod, "psutil", None)
        m = CapabilityManager()
        spec = make_spec("req-ram", requirements=Requirements(min_ram_mb=1))
        m.register(spec)
        ok, msg = await m._check_requirements(spec)
        assert ok is True
        assert "non verifiable" in msg

    async def test_disque_insuffisant_bloque(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            mgr_mod.shutil,
            "disk_usage",
            lambda path: SimpleNamespace(free=10 * 1024 * 1024, total=1, used=0),
        )
        m = CapabilityManager()
        spec = make_spec("req-disk", requirements=Requirements(min_disk_mb=100_000))
        m.register(spec)
        ok, msg = await m._check_requirements(spec)
        assert ok is False
        assert "disque" in msg

    async def test_exigences_satisfaites(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            mgr_mod.shutil,
            "disk_usage",
            lambda path: SimpleNamespace(free=10**12, total=1, used=0),
        )
        monkeypatch.setattr(
            mgr_mod,
            "psutil",
            SimpleNamespace(virtual_memory=lambda: SimpleNamespace(available=8 * 1024**3)),
        )
        m = CapabilityManager()
        spec = make_spec(
            "req-ok",
            requirements=Requirements(
                os=(platform.system().lower(),),
                arch=(platform.machine().lower(),),
                min_ram_mb=512,
                min_disk_mb=1024,
            ),
        )
        m.register(spec)
        ok, msg = await m._check_requirements(spec)
        assert ok is True
        assert msg == "prerequis satisfaits"

    async def test_status_expose_requirements(self, mgr: CapabilityManager) -> None:
        mgr.register(
            make_spec("req-status", requirements=Requirements(os=("linux",), min_ram_mb=512))
        )
        status = await mgr.status("req-status")
        assert status["requirements"] == {
            "os": ["linux"],
            "arch": [],
            "min_ram_mb": 512,
            "min_disk_mb": None,
        }

        from core.capability_manager import ComponentManager

        assert ComponentManager is CapabilityManager
        assert ComponentManager.__name__ == "CapabilityManager"


# ── intégrité : digest déclaré = réellement vérifié (SÉCURITÉ) ─────────────
class TestIntegrityHelpers:
    def test_normalisation_digest(self) -> None:
        assert backends_mod._sha256_hex("sha256:" + "A" * 64) == "a" * 64
        assert backends_mod._sha256_hex("repo/img@sha256:" + "b" * 64) == "b" * 64
        assert backends_mod._sha256_hex("integrite-base64-xyz") is None
        assert backends_mod._sha256_hex("") is None


class TestDockerIntegrity:
    """Un `provenance.checksum` déclaré est vérifié après le `pull` ; un champ
    vide signifie « non déclaré », jamais « conforme »."""

    pytestmark = pytest.mark.asyncio

    def _docker_spec(self, checksum: str) -> CapabilitySpec:
        return make_spec(
            "hash-a",
            install_actions=(
                {"action": "pull", "image": "ghcr.io/ethan/svc:1.0"},
                {
                    "action": "run",
                    "name": "ethan-hash",
                    "image": "ghcr.io/ethan/svc:1.0",
                },
            ),
            provenance=Provenance(source="official", author="ETHAN", checksum=checksum),
        )

    async def test_digest_conforme_installe(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[list[str]] = []

        async def fake_run(argv, timeout=300.0):
            calls.append(list(argv))
            if argv[1] == "image":
                return True, "ghcr.io/ethan/svc@sha256:" + "a" * 64
            if argv[1] == "container":
                return False, "No such container"
            return True, "ok"

        monkeypatch.setattr(backends_mod, "_run", fake_run)
        backend = backends_mod.DockerBackend()
        ok, _ = await backend.execute(self._docker_spec("sha256:" + "a" * 64), "install", {})
        assert ok is True
        assert any(c[1] == "image" and "inspect" in c for c in calls)

    async def test_digest_non_conforme_refuse(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_run(argv, timeout=300.0):
            if argv[1] == "image":
                return True, "ghcr.io/ethan/svc@sha256:" + "b" * 64
            if argv[1] == "container":
                return False, "No such container"
            return True, "ok"

        monkeypatch.setattr(backends_mod, "_run", fake_run)
        backend = backends_mod.DockerBackend()
        ok, msg = await backend.execute(self._docker_spec("sha256:" + "a" * 64), "install", {})
        assert ok is False
        assert "digest non conforme" in msg

    async def test_checksum_non_comparable_refuse(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_run(argv, timeout=300.0):
            if argv[1] == "container":
                return False, "No such container"
            return True, "ok"

        monkeypatch.setattr(backends_mod, "_run", fake_run)
        backend = backends_mod.DockerBackend()
        ok, msg = await backend.execute(self._docker_spec("base64:abcd"), "install", {})
        assert ok is False
        assert "non verifiable" in msg

    async def test_sans_checksum_aucune_inspection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[list[str]] = []

        async def fake_run(argv, timeout=300.0):
            calls.append(list(argv))
            if argv[1] == "container":
                return False, "No such container"
            return True, "ok"

        monkeypatch.setattr(backends_mod, "_run", fake_run)
        backend = backends_mod.DockerBackend()
        ok, _ = await backend.execute(self._docker_spec(""), "install", {})
        assert ok is True
        assert [c for c in calls if c[1] == "image"] == []


# ── logs composant : réels (Docker) ou indisponibilité annoncée ────────────
class TestComponentLogs:
    pytestmark = pytest.mark.asyncio

    async def test_docker_logs_reels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[list[str]] = []

        async def fake_run(argv, timeout=300.0):
            calls.append(list(argv))
            return True, "ligne 1\nligne 2"

        monkeypatch.setattr(backends_mod, "_run", fake_run)
        m = CapabilityManager()
        m.register(make_spec("logs-a"))
        out = await m.logs("logs-a", tail=50)
        assert out == {
            "capability_id": "logs-a",
            "source": "docker",
            "available": True,
            "tail": 50,
            "lines": ["ligne 1", "ligne 2"],
            "detail": "",
        }
        assert calls[0][:4] == ["docker", "logs", "--tail", "50"]

    async def test_logs_builtin_indisponible_honnete(self) -> None:
        from core.capability_manager.builtin import build_manager

        out = await build_manager().logs("memory")
        assert out["available"] is False
        assert out["lines"] == []
        assert out["detail"]

    async def test_tail_invalide_rejete(self) -> None:
        m = CapabilityManager()
        m.register(make_spec("logs-b"))
        with pytest.raises(ValueError, match="tail"):
            await m.logs("logs-b", tail=0)
        with pytest.raises(ValueError, match="tail"):
            await m.logs("logs-b", tail=5000)
