"""CapabilityManager — cycle de vie des composants optionnels (Core-owned).

Source de verite : CoreRecordStore. Les mutations sont auditees et publiees
en evenements (Event Bus) quand un bus est fourni. `config` est write-only.
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import re
import secrets
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from core.audit.store import AuditStore
from core.audit.types import AuditCategory, AuditDecision
from core.bus.interface import EventBus
from core.capability_manager.backends import (
    get_backend,
    node_binary_ok,
    validate_install_actions,
)
from core.capability_manager.health import HealthChecker
from core.capability_manager.types import (
    CapabilityRuntimeState,
    CapabilitySpec,
    CapabilityState,
    MutationPlan,
    PlanStep,
    TransitionError,
)
from core.ethan_types.event import Event
from core.state.record_store import CoreRecordStore

try:  # psutil est une dependance runtime declaree (extra server).
    import psutil
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)
_DOMAIN = "capability_manager"


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _new_op_id() -> str:
    return "op_" + secrets.token_hex(6)


def _validate_config(spec: CapabilitySpec, config: dict[str, Any]) -> dict[str, Any]:
    """Valide l'input utilisateur contre la config_schema.
    Refuse champs inconnus / types invalides → rempart injection : seules des
    valeurs scalaires typées sont retournées ; aucune chaine ne peut devenir
    une argv (les backends n'interprettent jamais une valeur utilisateur comme
    commande)."""
    errors: list[str] = []
    allowed = {f.name: f for f in spec.config_schema}
    cleaned: dict[str, Any] = {}
    for key, value in config.items():
        if key not in allowed:
            errors.append("champ inconnu: " + repr(key))
            continue
        fdef = allowed[key]
        if fdef.choices and value not in fdef.choices:
            errors.append(repr(key) + " doit etre dans " + repr(tuple(fdef.choices)))
            continue
        if fdef.type in ("int", "port"):
            try:
                intval = int(value)
            except (TypeError, ValueError):
                errors.append(repr(key) + " doit etre un entier")
                continue
            if fdef.min_value is not None and intval < fdef.min_value:
                errors.append(repr(key) + " < min " + repr(fdef.min_value))
                continue
            if fdef.max_value is not None and intval > fdef.max_value:
                errors.append(repr(key) + " > max " + repr(fdef.max_value))
                continue
            cleaned[key] = intval
            continue
        if fdef.type == "bool":
            if not isinstance(value, bool):
                errors.append(repr(key) + " doit etre un boolen")
                continue
            cleaned[key] = value
            continue
        if not isinstance(value, str):
            errors.append(repr(key) + " doit etre une chaine")
            continue
        cleaned[key] = value
    for fname, fdef in allowed.items():
        if fdef.required and fname not in cleaned:
            errors.append("champ obligatoire manquant: " + repr(fname))
    if errors:
        raise ValueError("config invalide: " + "; ".join(errors))
    return cleaned


def _default_config(spec: CapabilitySpec) -> dict[str, Any]:
    return {f.name: f.default for f in spec.config_schema if f.default is not None}


async def _run_quiet(argv: list[str]) -> tuple[bool, str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError:
        return False, argv[0] + " introuvable"
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=20.0)
    except asyncio.TimeoutError:
        proc.kill()
        return False, "timeout"
    return proc.returncode == 0, (out or b"").decode(errors="replace")[:200]


def _python() -> str:
    import sys

    return sys.executable


def _available_ram_mb() -> int | None:
    """RAM disponible en Mio, ou ``None`` si non mesurable (jamais bloquant)."""
    if psutil is None:
        return None
    try:
        return int(psutil.virtual_memory().available / (1024 * 1024))
    except Exception:  # noqa: BLE001 — mesure best-effort, jamais bloquante
        return None


def _free_disk_mb(backend: str) -> int | None:
    """Espace libre minimal des cibles pertinentes, en Mio (``None`` sinon).

    Cible principale : le workspace ETHAN. Pour un composant Docker, l'espace
    de ``/var/lib/docker`` compte aussi (les images y sont stockées).
    """
    targets = [Path(os.environ.get("ETHAN_WORKSPACE_DIR", os.getcwd()))]
    if backend == "docker" and os.path.isdir("/var/lib/docker"):
        targets.append(Path("/var/lib/docker"))
    try:
        return int(min(shutil.disk_usage(str(path)).free for path in targets) / (1024 * 1024))
    except Exception:  # noqa: BLE001 — mesure best-effort, jamais bloquante
        return None


class CapabilityManager:
    """Gestionnaire central du cycle de vie des composants optionnels."""

    def __init__(
        self,
        *,
        store: CoreRecordStore | None = None,
        audit: AuditStore | None = None,
        bus: EventBus | None = None,
        registry: dict[str, CapabilitySpec] | None = None,
        check_external: bool = False,
    ) -> None:
        self.store = store or CoreRecordStore()
        self.audit = audit or AuditStore()
        self.bus = bus
        self.check_external = check_external
        self._registry: dict[str, CapabilitySpec] = dict(registry or {})
        self._health = HealthChecker()
        self._operations: dict[str, dict[str, Any]] = {}
        self._states: dict[str, CapabilityRuntimeState] = {}

    # ── registre des specs ──
    def register(self, spec: CapabilitySpec) -> None:
        """Enregistre une spec developpeur-définie (builtin/plugin signé)."""
        spec.validate()
        validate_install_actions(spec)
        self._registry[spec.id] = spec
        if spec.id not in self._states:
            self._states[spec.id] = CapabilityRuntimeState(id=spec.id)
        logger.info("capability enregistrée: %s", spec.id)

    def list_specs(self) -> list[CapabilitySpec]:
        return list(self._registry.values())

    def get_spec(self, capability_id: str) -> CapabilitySpec | None:
        return self._registry.get(capability_id)

    # ── état runtime ──
    async def _load_state(self, capability_id: str) -> CapabilityRuntimeState:
        if capability_id not in self._states:
            record = await self.store.get(_DOMAIN, capability_id)
            self._states[capability_id] = (
                CapabilityRuntimeState.from_dict(record)
                if record
                else CapabilityRuntimeState(id=capability_id)
            )
        return self._states[capability_id]

    async def _save_state(self, state: CapabilityRuntimeState) -> None:
        self._states[state.id] = state
        state.updated_at = _now()
        await self.store.save(_DOMAIN, state.id, state.to_dict())

    def _transition(self, state: CapabilityRuntimeState, target: str) -> None:
        current = state.state
        if not CapabilityState.can_transition(current, target):
            raise TransitionError(
                "transition impossible " + current + " -> " + target + " pour " + state.id
            )
        state.state = target

    def _require_spec(self, capability_id: str) -> CapabilitySpec:
        spec = self._registry.get(capability_id)
        if spec is None:
            raise KeyError("capability inconnue: " + capability_id)
        return spec

    # ── détection ──
    async def detect(self) -> dict[str, CapabilityRuntimeState]:
        """Détecte l'état réel de chaque capability enregistrée et le réconcile."""
        results: dict[str, CapabilityRuntimeState] = {}
        for cid, spec in self._registry.items():
            state = await self._load_state(cid)
            try:
                support_ok, support_msg = await self._check_support(spec)
                req_ok, req_msg = await self._check_requirements(spec)
                deps_ok, deps_msg = await self._check_dependencies(spec)
                installed = await self._detect_installed(spec)
                if not support_ok:
                    self._transition(state, CapabilityState.SUPPORTED)
                    # Retour à un état propre : l'erreur précédente n'est plus
                    # d'actualité (section 2 de la spec UI — état réel).
                    state.last_error = None
                elif not installed and not req_ok:
                    # Prérequis déclarés non satisfaits (compatibilité,
                    # ressources) : supporté mais non installable ici.
                    self._safe_set(state, CapabilityState.SUPPORTED)
                    state.last_error = req_msg
                elif not deps_ok:
                    self._transition(state, CapabilityState.SUPPORTED)
                    state.last_error = deps_msg
                elif not installed:
                    self._transition(state, CapabilityState.NOT_INSTALLED)
                    state.last_error = None
                else:
                    # Présence réelle vérifiée (ESR-002 §5) : la question
                    # « installé ? » est tranchée — y compris pour les
                    # `builtin`, présents par construction (Memory s'affiche
                    # Ready, jamais « not installed »). Les états déjà
                    # déterminés (RUNNING/READY/UNHEALTHY/STOPPED/
                    # CONFIGURATION_REQUIRED/ERROR) ne sont pas écrasés : la
                    # santé ci-dessous les réconcilie.
                    if state.state in (
                        CapabilityState.SUPPORTED,
                        CapabilityState.NOT_INSTALLED,
                    ):
                        self._safe_set(state, CapabilityState.INSTALLED)
                    health = await self._health.evaluate(spec, state)
                    self._reconcile_health(state, health)
                    if not health["ok"] and not state.last_error:
                        state.last_error = "santé refusée"
            except TransitionError:
                pass
            except Exception as exc:  # noqa: BLE001
                state.state = CapabilityState.ERROR
                state.last_error = str(exc)[:200]
            await self._save_state(state)
            results[cid] = state
        return results

    def _reconcile_health(self, state: CapabilityRuntimeState, health: dict[str, Any]) -> None:
        """Réconcilie l'état live avec le résultat de santé (transitions légales)."""
        if health["ok"]:
            if state.state in (
                CapabilityState.INSTALLED,
                CapabilityState.CONFIGURATION_REQUIRED,
                CapabilityState.UNHEALTHY,
                CapabilityState.RUNNING,
            ):
                self._safe_set(state, CapabilityState.READY)
        else:
            if state.state in (CapabilityState.RUNNING, CapabilityState.READY):
                self._safe_set(state, CapabilityState.UNHEALTHY)

    def _safe_set(self, state: CapabilityRuntimeState, target: str) -> None:
        try:
            self._transition(state, target)
        except TransitionError:
            state.state = target

    async def _check_support(self, spec: CapabilitySpec) -> tuple[bool, str]:
        try:
            backend = get_backend(spec.backend)
        except ValueError as exc:
            return False, str(exc)
        ok, msg = await backend.check_prerequisites(spec)
        if not ok:
            return False, msg
        return True, msg

    async def _check_requirements(self, spec: CapabilitySpec) -> tuple[bool, str]:
        """Prérequis déclarés : compatibilité (os/arch) et ressources.

        Vérifiés AVANT toute mutation, comme les dépendances. Rien n'est
        inventé : une exigence non déclarée n'est pas contrôlée, et une
        mesure indisponible (psutil absent) est rapportée « non
        vérifiable » sans bloquer — un verdict non fondé est refusé.
        """
        req = spec.requirements
        if req.is_empty():
            return True, "aucun prerequis declare"
        problems: list[str] = []
        notes: list[str] = []
        system = platform.system().lower()
        if req.os and system not in req.os:
            problems.append(f"os {system!r} non supporte (requis: {', '.join(req.os)})")
        machine = platform.machine().lower()
        if req.arch and machine not in req.arch:
            problems.append(
                f"architecture {machine!r} non supportee (requis: {', '.join(req.arch)})"
            )
        if req.min_ram_mb is not None:
            available_mb = _available_ram_mb()
            if available_mb is None:
                notes.append("RAM non verifiable (psutil indisponible)")
            elif available_mb < req.min_ram_mb:
                problems.append(f"RAM disponible {available_mb} Mo < requis {req.min_ram_mb} Mo")
        if req.min_disk_mb is not None:
            free_mb = _free_disk_mb(spec.backend)
            if free_mb is None:
                notes.append("disque non verifiable")
            elif free_mb < req.min_disk_mb:
                problems.append(f"disque libre {free_mb} Mo < requis {req.min_disk_mb} Mo")
        if problems:
            return False, "prerequis non satisfaits: " + "; ".join(problems)
        if notes:
            return True, "prerequis ok (" + "; ".join(notes) + ")"
        return True, "prerequis satisfaits"

    async def _check_dependencies(self, spec: CapabilitySpec) -> tuple[bool, str]:
        missing: list[str] = []
        for dep in spec.dependencies:
            if dep.kind == "system":
                cmd = dep.command or (dep.id,)
                if shutil.which(str(cmd[0])) is None and not dep.optional:
                    missing.append(dep.id)
            elif dep.kind == "capability":
                ds = self._states.get(dep.id)
                if ds is None or ds.state not in (
                    CapabilityState.RUNNING,
                    CapabilityState.READY,
                    CapabilityState.STOPPED,
                    CapabilityState.INSTALLED,
                ):
                    if not dep.optional:
                        missing.append(dep.id)
        if missing:
            return False, "dependances manquantes: " + repr(missing)
        return True, "ok"

    async def _detect_installed(self, spec: CapabilitySpec) -> bool:
        """Présence RÉELLE du composant, par backend (ESR-002 §5).

        On ne se fie qu'aux vérifications DÉCLARÉES par la spec
        (`verify_import`, `verify_path`, `verify_binary`) : jamais un fichier
        d'état, jamais une présence supposée. Sans vérification déclarée, le
        composant n'est jamais « installé » (état honnête).
        """
        if spec.backend == "builtin":
            # Toujours présent : le composant fait partie du process Core.
            return True
        if spec.backend == "docker":
            if shutil.which("docker") is None:
                return False
            name = None
            for a in spec.install_actions:
                if a.get("action") == "run":
                    name = str(a.get("name"))
                    break
            if not name:
                return False
            ok, _ = await _run_quiet(["docker", "container", "inspect", name])
            return ok
        if spec.backend == "python_package":
            # Toutes les actions sont parcourues : `pip_install` précède
            # `verify_import` dans le catalogue, seule la vérification compte.
            for a in spec.install_actions:
                if a.get("action") == "verify_import":
                    mod = a["module"]
                    code = (
                        "import importlib.util, sys; "
                        "cp=importlib.util.find_spec(" + repr(mod) + "); "
                        "sys.exit(0 if cp is not None else 1)"
                    )
                    ok, _ = await _run_quiet([_python(), "-c", code])
                    return ok
            return False
        if spec.backend == "executable":
            for a in spec.install_actions:
                if a.get("action") == "verify_path":
                    return shutil.which(str(a["executable"])) is not None
            return False
        if spec.backend == "node_package":
            for a in spec.install_actions:
                if a.get("action") == "verify_binary":
                    return node_binary_ok(str(a["binary"]))
            return False
        return False

    # ── plans ──
    def _resolve_plan(self, plan: MutationPlan) -> MutationPlan:
        """Resout les placeholders {config.field} dans les descriptions des etapes
        en utilisant les valeurs par defaut du schema de configuration."""
        spec = self._require_spec(plan.capability_id)
        defaults = {f.name: f.default for f in spec.config_schema if f.default is not None}

        def _repl(m: re.Match) -> str:
            return str(defaults.get(m.group(1), m.group(0)))

        new_steps = []
        for s in plan.steps:
            desc = re.sub(r"\{config\.(\w+)\}", _repl, s.description)
            new_steps.append(PlanStep(desc, s.kind, destructive=s.destructive))
        return MutationPlan(
            capability_id=plan.capability_id,
            operation=plan.operation,
            steps=tuple(new_steps),
            requires_confirmation=plan.requires_confirmation,
        )

    async def plan_install(self, capability_id: str) -> MutationPlan:
        spec = self._require_spec(capability_id)
        backend = get_backend(spec.backend)
        steps = [
            PlanStep(
                "Vérifier le support, les dependances, la compatibilité et les ressources",
                "verify",
            )
        ]
        for desc, kind in await backend.plan(spec, "install"):
            steps.append(PlanStep(desc, kind))
        steps.append(PlanStep("Demarrer et verifier la sante", "start"))
        return self._resolve_plan(
            MutationPlan(
                capability_id=capability_id,
                operation="install",
                steps=tuple(steps),
                requires_confirmation=spec.requires_confirmation,
            )
        )

    async def plan_uninstall(self, capability_id: str, delete_data: bool = False) -> MutationPlan:
        spec = self._require_spec(capability_id)
        backend = get_backend(spec.backend)
        steps = [PlanStep("Arret du composant " + capability_id, "stop")]
        steps += [PlanStep(d, k) for d, k in await backend.plan(spec, "uninstall")]
        steps.append(
            PlanStep("SUPPRESSION DES DONNEES PERSISTENTES", "data", destructive=True)
            if delete_data
            else PlanStep("Conserver les donnees persistantes", "data")
        )
        return self._resolve_plan(
            MutationPlan(
                capability_id=capability_id,
                operation="uninstall",
                steps=tuple(steps),
                requires_confirmation=spec.requires_confirmation or delete_data,
            )
        )

    # ── installation ──
    async def install(
        self,
        capability_id: str,
        config: dict[str, Any] | None = None,
        *,
        actor: str = "user",
    ) -> str:
        """Installe + demarre + teste. Idempotente si dejà READY. Retourne un operation_id."""
        spec = self._require_spec(capability_id)
        state = await self._load_state(capability_id)
        if state.state == CapabilityState.READY:
            return self._already_done(spec, state, "install", actor)
        if CapabilityState.BUSY & {state.state}:
            raise TransitionError(capability_id + " deja en cours (etat=" + state.state + ")")
        if state.state == CapabilityState.SUPPORTED:
            # Normalisation : SUPPORTED n'est pas installable directement,
            # il passe par NOT_INSTALLED (machine a etats section 3).
            self._transition(state, CapabilityState.NOT_INSTALLED)
            await self._save_state(state)
        validated = _validate_config(spec, config) if config else None
        op_id = _new_op_id()
        plan = await self.plan_install(capability_id)
        task = asyncio.create_task(self._do_install(op_id, plan, spec, state, validated, actor))
        self._operations[op_id] = {
            "capability_id": capability_id,
            "operation": "install",
            "task": task,
            "started_at": time.monotonic(),
            "steps_done": [],
            "progress": 0,
            "cancel_requested": False,
        }
        self._log_event("install", capability_id, actor, validated is not None)
        self._audit("install", "allowed", capability_id, actor, plan.to_dict())
        return op_id

    async def _do_install(
        self,
        op_id: str,
        plan: MutationPlan,
        spec: CapabilitySpec,
        state: CapabilityRuntimeState,
        config: dict[str, Any] | None,
        actor: str,
    ) -> None:
        op = self._operations[op_id]
        total = len(plan.steps)
        try:
            self._transition(state, CapabilityState.INSTALLING)
            await self._save_state(state)
            backend = get_backend(spec.backend)
            ok, msg = await self._check_support(spec)
            self._record_step(op, "support", 0, total, ok, msg)
            if not ok:
                raise RuntimeError(msg)
            ok, msg = await self._check_requirements(spec)
            self._record_step(op, "requirements", 0, total, ok, msg)
            if not ok:
                raise RuntimeError(msg)
            ok, msg = await self._check_dependencies(spec)
            self._record_step(op, "dependencies", 1, total, ok, msg)
            if not ok:
                raise RuntimeError(msg)
            if config:
                state.config = config
            ok, msg = await backend.execute(spec, "install", state.config or {})
            self._record_step(op, "install", 2, total, ok, msg)
            if not ok:
                await backend.rollback(spec, "install")
                self._transition(state, CapabilityState.NOT_INSTALLED)
                raise RuntimeError(msg)
            self._transition(state, CapabilityState.INSTALLED)
            await self._save_state(state)
            if spec.start_actions:
                self._transition(state, CapabilityState.STARTING)
                await self._save_state(state)
                ok, msg = await backend.execute(spec, "start", state.config)
                self._record_step(op, "start", 4, total, ok, msg)
                if not ok:
                    raise RuntimeError(msg)
            health = await self._health.evaluate(spec, state)
            self._record_step(op, "health", 5, total, health["ok"], health["level"])
            if health["ok"]:
                # Paliers section 8 : STARTING -> RUNNING -> READY
                self._transition(state, CapabilityState.RUNNING)
                self._transition(state, CapabilityState.READY)
            else:
                self._transition(state, CapabilityState.RUNNING)
            state.installed_version = spec.version
            await self._save_state(state)
            self._log_event("installed", spec.id, actor)
        except asyncio.CancelledError:
            op["cancel_requested"] = True
            state.state = CapabilityState.ERROR
            state.last_error = "installation annulee"
            await self._save_state(state)
            self._log_event("install_cancelled", spec.id, actor)
        except Exception as exc:
            op["error"] = str(exc)[:300]
            state.state = CapabilityState.ERROR
            state.last_error = str(exc)[:300]
            await self._save_state(state)
            self._log_event("install_failed", spec.id, actor)
            self._audit("install", "error", spec.id, actor, {"error": str(exc)[:200]})
        finally:
            op["progress"] = 100
            op["finished_at"] = time.monotonic()

    # ── configure / test ──
    async def configure(
        self, capability_id: str, config: dict[str, Any], *, actor: str = "user"
    ) -> CapabilityRuntimeState:
        spec = self._require_spec(capability_id)
        state = await self._load_state(capability_id)
        validated = _validate_config(spec, config)
        state.config = {**state.config, **validated}
        if state.state in (CapabilityState.READY, CapabilityState.RUNNING):
            backend = get_backend(spec.backend)
            if spec.stop_actions and spec.start_actions:
                await backend.execute(spec, "stop", state.config)
                await backend.execute(spec, "start", state.config)
        await self._save_state(state)
        self._log_event("configured", capability_id, actor)
        self._audit("configure", "allowed", capability_id, actor, {"keys": sorted(validated)})
        return state

    # ── start / stop (composant installé, sans réinstaller) ──
    async def start(self, capability_id: str, *, actor: str = "user") -> dict[str, Any]:
        """Démarre un composant installé et arrêté ; vérifie la santé."""
        spec = self._require_spec(capability_id)
        state = await self._load_state(capability_id)
        if state.state not in (CapabilityState.STOPPED, CapabilityState.INSTALLED):
            raise TransitionError(
                "impossible de démarrer " + capability_id + ": état=" + state.state
            )
        if not spec.start_actions:
            raise ValueError(capability_id + " ne déclare pas de démarrage")
        backend = get_backend(spec.backend)
        self._transition(state, CapabilityState.STARTING)
        await self._save_state(state)
        ok, msg = await backend.execute(spec, "start", state.config)
        if not ok:
            state.state = CapabilityState.ERROR
            state.last_error = msg[:300]
            await self._save_state(state)
            self._audit("start", "error", capability_id, actor, {"error": msg[:200]})
            raise RuntimeError(msg)
        health = await self._health.evaluate(spec, state)
        if health["ok"]:
            self._transition(state, CapabilityState.RUNNING)
            self._transition(state, CapabilityState.READY)
        else:
            self._transition(state, CapabilityState.RUNNING)
        await self._save_state(state)
        self._log_event("started", capability_id, actor, health["ok"])
        self._audit("start", "allowed", capability_id, actor)
        return health

    async def stop(self, capability_id: str, *, actor: str = "user") -> None:
        """Arrête un composant actif sans désinstaller (données conservées)."""
        spec = self._require_spec(capability_id)
        state = await self._load_state(capability_id)
        if state.state not in (
            CapabilityState.RUNNING,
            CapabilityState.READY,
            CapabilityState.UNHEALTHY,
        ):
            raise TransitionError("impossible d'arrêter " + capability_id + ": état=" + state.state)
        if not spec.stop_actions:
            raise ValueError(capability_id + " ne déclare pas d'arrêt")
        backend = get_backend(spec.backend)
        ok, msg = await backend.execute(spec, "stop", state.config)
        if not ok:
            self._audit("stop", "error", capability_id, actor, {"error": msg[:200]})
            raise RuntimeError(msg)
        self._safe_set(state, CapabilityState.STOPPED)
        await self._save_state(state)
        self._log_event("stopped", capability_id, actor)
        self._audit("stop", "allowed", capability_id, actor)

    async def test(self, capability_id: str, *, actor: str = "user") -> dict[str, Any]:
        spec = self._require_spec(capability_id)
        state = await self._load_state(capability_id)
        result = await self._health.evaluate(spec, state)
        if result["ok"]:
            self._safe_set(state, CapabilityState.READY)
        else:
            if state.state != CapabilityState.ERROR:
                state.state = CapabilityState.UNHEALTHY
            state.last_error = "échec du test de santé"
        await self._save_state(state)
        self._log_event("tested", capability_id, actor, result["ok"])
        return result

    # ── enable / disable ──
    async def enable(self, capability_id: str, *, actor: str = "user") -> None:
        state = await self._load_state(self._require_spec(capability_id).id)
        if state.state != CapabilityState.READY:
            raise TransitionError(
                "impossible d'activer "
                + capability_id
                + ": etat="
                + state.state
                + " (READY requis)"
            )
        state.enabled = True
        await self._save_state(state)
        self._log_event("enabled", capability_id, actor)
        self._audit("enable", "allowed", capability_id, actor)

    async def disable(self, capability_id: str, *, actor: str = "user") -> None:
        self._require_spec(capability_id)
        state = await self._load_state(capability_id)
        state.enabled = False
        await self._save_state(state)
        self._log_event("disabled", capability_id, actor)
        self._audit("disable", "allowed", capability_id, actor)

    # ── uninstall ──
    async def uninstall(
        self, capability_id: str, delete_data: bool = False, *, actor: str = "user"
    ) -> str:
        spec = self._require_spec(capability_id)
        state = await self._load_state(capability_id)
        if CapabilityState.BUSY & {state.state}:
            raise TransitionError(capability_id + " deja en cours (etat=" + state.state + ")")
        plan = await self.plan_uninstall(capability_id, delete_data)
        op_id = _new_op_id()
        task = asyncio.create_task(self._do_uninstall(op_id, plan, spec, state, delete_data, actor))
        self._operations[op_id] = {
            "capability_id": capability_id,
            "operation": "uninstall",
            "task": task,
            "started_at": time.monotonic(),
            "steps_done": [],
            "progress": 0,
            "cancel_requested": False,
        }
        self._log_event("uninstall", capability_id, actor, delete_data)
        self._audit("uninstall", "allowed", capability_id, actor, {"delete_data": delete_data})
        return op_id

    async def _do_uninstall(
        self,
        op_id: str,
        plan: MutationPlan,
        spec: CapabilitySpec,
        state: CapabilityRuntimeState,
        delete_data: bool,
        actor: str,
    ) -> None:
        op = self._operations[op_id]
        total = len(plan.steps)
        try:
            self._transition(state, CapabilityState.UNINSTALLING)
            await self._save_state(state)
            backend = get_backend(spec.backend)
            ok, msg = await self._check_dependent_enabled(spec)
            self._record_step(op, "dependents", 0, total, ok, msg)
            if not ok:
                raise RuntimeError(msg)
            if spec.stop_actions:
                ok, msg = await backend.execute(spec, "stop", state.config)
                self._record_step(op, "stop", 1, total, ok, msg)
                if not ok:
                    raise RuntimeError(msg)
            if spec.uninstall_actions:
                modified = []
                for a in spec.uninstall_actions:
                    a = dict(a)
                    if a.get("action") == "remove":
                        a["keep_data"] = not delete_data
                        a["data_to_delete"] = a.get("data_to_delete", []) if delete_data else []
                    modified.append(a)
                original = spec.uninstall_actions
                object.__setattr__(spec, "uninstall_actions", tuple(modified))
                try:
                    ok, msg = await backend.execute(spec, "uninstall", state.config)
                finally:
                    object.__setattr__(spec, "uninstall_actions", original)
                self._record_step(op, "uninstall", 2, total, ok, msg)
                if not ok:
                    raise RuntimeError(msg)
            state.state = CapabilityState.SUPPORTED
            state.enabled = False
            state.config = {}
            state.last_error = None
            state.runtime_meta = {}
            await self._save_state(state)
            self._log_event("uninstalled", spec.id, actor)
        except asyncio.CancelledError:
            op["cancel_requested"] = True
            state.state = CapabilityState.ERROR
            state.last_error = "désinstallation annulée"
            await self._save_state(state)
        except Exception as exc:
            op["error"] = str(exc)[:300]
            state.state = CapabilityState.ERROR
            state.last_error = str(exc)[:300]
            await self._save_state(state)
            self._log_event("uninstall_failed", spec.id, actor)
            self._audit("uninstall", "error", spec.id, actor, {"error": str(exc)[:200]})
        finally:
            op["progress"] = 100
            op["finished_at"] = time.monotonic()

    async def _check_dependent_enabled(self, spec: CapabilitySpec) -> tuple[bool, str]:
        for other_id, other in self._registry.items():
            if other_id == spec.id:
                continue
            for dep in other.dependencies:
                if dep.kind == "capability" and dep.id == spec.id:
                    ds = self._states.get(other_id)
                    if ds and ds.enabled:
                        return False, (
                            "impossible de désinstaller "
                            + spec.id
                            + ": "
                            + other_id
                            + " est active et en dépend"
                        )
        return True, "ok"

    # ── suivi d'opérations ──
    def get_operation(self, operation_id: str) -> dict[str, Any] | None:
        op = self._operations.get(operation_id)
        if op is None:
            return None
        task = op.get("task")
        done = True
        if task is not None:
            done = task.done()
        return {
            "operation_id": operation_id,
            "capability_id": op["capability_id"],
            "operation": op["operation"],
            "progress": op["progress"],
            "cancel_requested": op["cancel_requested"],
            "started_at": op.get("started_at"),
            "finished_at": op.get("finished_at"),
            "steps_done": list(op["steps_done"]),
            "done": done,
            "error": op.get("error"),
        }

    def list_operations(self) -> list[dict[str, Any]]:
        return [self.get_operation(op_id) for op_id in self._operations]

    async def cancel_operation(self, operation_id: str) -> bool:
        op = self._operations.get(operation_id)
        if op is None:
            return False
        task = op.get("task")
        if task is not None and task.done() and not task.cancelled():
            return False
        op["cancel_requested"] = True
        if task is not None and not task.done():
            task.cancel()
        return True

    # ── status public (pour l'API) ──
    async def status(self, capability_id: str) -> dict[str, Any]:
        spec = self._require_spec(capability_id)
        state = await self._load_state(capability_id)
        return {
            "id": spec.id,
            "name": spec.name,
            "description": spec.description,
            "type": spec.type,
            "version": spec.version,
            "backend": spec.backend,
            "state": state.state,
            "enabled": state.enabled,
            "installed_version": state.installed_version,
            "last_error": state.last_error,
            "config_keys": list(state.config.keys()),
            "updated_at": state.updated_at,
            # Prérequis déclarés (compatibilité/ressources) — statique, dérivé
            # du spec enregistré comme `provenance` et `config_schema`.
            "requirements": spec.requirements.to_dict(),
            # Déclaration (affichage WebUI) : dépendances, schéma de config,
            # données persistantes. Statique, dérivé du spec enregistré.
            "requires_confirmation": spec.requires_confirmation,
            "dependencies": [
                {
                    "id": d.id,
                    "kind": d.kind,
                    "description": d.description,
                    "optional": d.optional,
                }
                for d in spec.dependencies
            ],
            "config_schema": [
                {
                    "name": f.name,
                    "type": f.type,
                    "required": f.required,
                    "default": f.default,
                    "description": f.description,
                    "min_value": f.min_value,
                    "max_value": f.max_value,
                    "choices": list(f.choices) if f.choices else None,
                }
                for f in spec.config_schema
            ],
            "data_resources": [
                {
                    "kind": r.get("kind", ""),
                    "name": r.get("name") or r.get("path", ""),
                    "description": r.get("description", ""),
                }
                for r in spec.data_resources
            ],
            # Provenance (affichage WebUI/CLI) : d'où vient le composant, qui
            # l'a produit, et de quoi vérifier son intégrité. Statique — dérivé
            # du spec enregistré, jamais un champ modifiable par l'utilisateur.
            "provenance": {
                "source": spec.provenance.source,
                "author": spec.provenance.author,
                "url": spec.provenance.url,
                "license": spec.provenance.license,
                "checksum": spec.provenance.checksum,
                "signature": spec.provenance.signature,
            },
        }

    async def status_all(self) -> list[dict[str, Any]]:
        return [await self.status(s.id) for s in self._registry.values()]

    async def logs(self, capability_id: str, *, tail: int = 200) -> dict[str, Any]:
        """Logs d'exécution du composant (lecture seule, bornée).

        Le backend répond avec des logs RÉELS quand il en produit (Docker :
        `docker logs --tail N` du container déclaré par la spec) ; sinon il
        l'annonce honnêtement (`available=False` + raison) — jamais de faux
        contenu, jamais de lecture arbitraire dans le système.
        """
        spec = self._require_spec(capability_id)
        if isinstance(tail, bool) or not isinstance(tail, int) or not 1 <= tail <= 2000:
            raise ValueError("tail doit etre un entier entre 1 et 2000")
        state = await self._load_state(capability_id)
        backend = get_backend(spec.backend)
        logs_fn = getattr(backend, "logs", None)
        if logs_fn is None:
            ok, text = False, (f"le backend {spec.backend!r} ne fournit pas de logs a ETHAN")
        else:
            ok, text = await logs_fn(spec, state.config, tail)
        return {
            "capability_id": capability_id,
            "source": spec.backend,
            "available": ok,
            "tail": tail,
            "lines": text.splitlines() if ok and text else [],
            "detail": "" if ok else text,
        }

    # ── helpers internes ──
    def _already_done(
        self,
        spec: CapabilitySpec,
        state: CapabilityRuntimeState,
        operation: str,
        actor: str,
    ) -> str:
        op_id = _new_op_id()
        self._operations[op_id] = {
            "capability_id": spec.id,
            "operation": operation,
            "task": None,
            "started_at": time.monotonic(),
            "steps_done": [("déjà réalisé", True, "ok")],
            "progress": 100,
            "cancel_requested": False,
            "finished_at": time.monotonic(),
        }
        self._log_event(operation + "_skipped", spec.id, actor)
        return op_id

    def _record_step(
        self,
        op: dict,
        step: str,
        index: int,
        total: int,
        ok: bool,
        message: str,
    ) -> None:
        op["steps_done"].append((step, ok, message))
        op["progress"] = int(((index + 1) / max(total, 1)) * 100)

    def _log_event(
        self,
        event: str,
        capability_id: str,
        actor: str,
        extra: Any = None,
    ) -> None:
        if self.bus is None:
            return
        try:
            asyncio.create_task(
                self.bus.publish(
                    "ethan.capabilities." + event,
                    Event(
                        type="ethan.capability." + event,
                        source="core.capability_manager:" + actor,
                        payload={
                            "capability_id": capability_id,
                            "actor": actor,
                            "extra": extra,
                        },
                    ),
                )
            )
        except Exception:  # noqa: BLE001 — le bus ne doit pas casser le Core
            logger.debug("échec publication événement capability", exc_info=True)

    def _audit(
        self,
        action: str,
        decision: str,
        capability_id: str,
        actor: str,
        details: Any = None,
    ) -> None:
        try:
            self.audit.log(
                category=AuditCategory.SYSTEM,
                decision=getattr(AuditDecision, decision.upper(), AuditDecision.AUTO),
                action="capability:" + action + ":" + capability_id,
                actor=actor,
                source="core.capability_manager",
                details={"capability_id": capability_id, **(details or {})},
            )
        except Exception:  # noqa: BLE001
            logger.debug("échec audit capability", exc_info=True)
