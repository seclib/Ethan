"""ExtensionManager — couche de gestion commune à Capabilities, Plugins et Cookbook.

C'est l'UNIQUE gestionnaire du cycle de vie des extensions. Il ne possede
aucun runtime : il delegue aux handlers de type (`handlers.py`) et garantit
que les invariants suivants valent pour les trois types.

Invariants (le frontend ne peut pas les contourner) :

1. **Le Core est la source de verite.** L'interface n'affiche que l'etat reel
   renvoye ici ; elle ne simule jamais une installation reussie.
2. **Aucune operation ne reste bloquee.** Toute operation suit un chemin
   terminal (succes / erreur / timeout / annulation). Le delai est borne par
   `_OPERATION_TIMEOUT_S` et les operations sont reconciliees au demarrage.
3. **Persistance durable.** Etats et operations vivent dans `CoreRecordStore`
   (PostgreSQL) — jamais en memoire Python ni dans l'etat du frontend.
4. **Le type reste explicite.** Une recette n'est jamais presentee comme un
   plugin, et les actions proposees dependent du type reel.

Les trois systemes d'origine continuent de fonctionner : le gestionnaire unifie
est une COUCHE au-dessus d'eux, jamais un remplacement (compatibilite).
"""

from __future__ import annotations

import asyncio
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Any

from core.extensions.handlers import CapabilityHandler
from core.extensions.types import (
    ExtensionKind,
    ExtensionOperation,
    ExtensionRuntimeState,
    ExtensionSpec,
    ExtensionState,
    ExtensionStatus,
    OperationStatus,
    TransitionError,
)
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

# Un SEUL domaine pour les etats des trois types : c'est la materialisation de
# l'unification. Les domaines historiques (`capability_manager`,
# `webui_plugins`, `cookbook-installed`) restent la verite de leur systeme.
_STATE_DOMAIN = "extensions"
_OPERATION_DOMAIN = "extension_operations"

# Bornes d'operation : une installation ne reste jamais « en cours » indefiniment.
_OPERATION_TIMEOUT_S = 900.0
_OPERATION_RETENTION_S = 24.0 * 3600.0
_OPERATION_MAX_KEPT = 50

# Borne dure du suivi d'une operation native (10 min a 1 s).
_MIRROR_MAX_POLLS = 600
_MIRROR_POLL_INTERVAL_S = 1.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_epoch(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _new_op_id() -> str:
    return "opx_" + secrets.token_hex(6)


def _op_public(op: dict[str, Any]) -> dict[str, Any]:
    """Vue d'une operation pour l'API : jamais de task asyncio ni cle interne."""
    public = {k: v for k, v in op.items() if k not in ("task", "deadline")}
    public["done"] = op.get("status") in OperationStatus.TERMINAL
    return public


def _public_detail(kind: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Champs utiles a l'interface, filtres selon le type. Aucun secret expose."""
    if kind == ExtensionKind.CAPABILITY:
        return {
            "container_id": raw.get("container_id"),
            "capability_type": raw.get("type"),
            "health": raw.get("health"),
        }
    if kind == ExtensionKind.PLUGIN:
        return {
            "status": raw.get("status"),
            "tools": raw.get("tools", []),
            "skills": raw.get("skills", []),
            "mcp": raw.get("mcp", []),
            "permissions": raw.get("permissions", []),
        }
    if kind == ExtensionKind.COOKBOOK:
        return {"created": raw.get("created", []), "version": raw.get("version")}
    return {}


class ExtensionManager:
    """Gestionnaire commun — un seul cycle de vie pour trois types."""

    def __init__(
        self,
        *,
        handlers: dict[str, Any],
        store: CoreRecordStore | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._handlers = handlers
        self._store = store or CoreRecordStore()
        self._bus = event_bus
        self._operations: dict[str, dict[str, Any]] = {}

    # ── Resolution type ─────────────────────────────────────────────────

    async def _handler_for_id(self, ext_id: str) -> tuple[str, Any]:
        """Retrouve le type ET le handler d'une extension.

        Le type n'est jamais devine : il est lu dans l'etat persiste, sinon
        deduit du catalogue. Une extension est donc toujours traitee par le
        gestionnaire qui connait reellement sa semantique.
        """
        cached = await self._store.get(_STATE_DOMAIN, ext_id)
        if cached and cached.get("kind") in self._handlers:
            kind = str(cached["kind"])
            return kind, self._handlers[kind]
        for kind, handler in self._handlers.items():
            for spec in await handler.discover():
                if spec.id == ext_id:
                    return kind, handler
        return "", None

    async def _require(self, ext_id: str) -> tuple[str, Any]:
        kind, handler = await self._handler_for_id(ext_id)
        if handler is None:
            raise KeyError(ext_id)
        return kind, handler

    # ── Persistence ─────────────────────────────────────────────────────

    async def _save_state(self, state: ExtensionRuntimeState) -> None:
        state.updated_at = _now_iso()
        await self._store.save(_STATE_DOMAIN, state.id, state.to_dict())

    async def load_state(self, ext_id: str) -> ExtensionRuntimeState:
        """Etat persiste, ou un etat AVAILABLE par defaut.

        L'etat n'est jamais suppose : il est lu, ou initialise honnetement a
        AVAILABLE (une extension non installee n'est pas « installee »).
        """
        raw = await self._store.get(_STATE_DOMAIN, ext_id)
        if raw:
            return ExtensionRuntimeState.from_dict(raw)
        return ExtensionRuntimeState(id=ext_id, state=ExtensionState.AVAILABLE)

    # ── Catalogue / decouverte ──────────────────────────────────────────

    async def discover(self) -> list[ExtensionStatus]:
        """Catalogue unifie : les trois types, un seul format de sortie.

        Chaque handler reste maitre de son catalogue ; le gestionnaire ne fait
        que normaliser. Aucun type n'est transforme en un autre.
        """
        statuses: list[ExtensionStatus] = []
        for kind, handler in self._handlers.items():
            try:
                specs = await handler.discover()
            except Exception as exc:  # noqa: BLE001 — un handler casse n'entraine pas les autres
                logger.exception("Extensions: decouverte %s impossible", kind)
                marker = f"__error__{kind}"
                statuses.append(
                    ExtensionStatus(
                        spec=ExtensionSpec(
                            id=marker, kind=kind, name=kind, description=str(exc)[:200]
                        ),
                        state=ExtensionRuntimeState(
                            id=marker,
                            kind=kind,
                            state=ExtensionState.ERROR,
                            last_error=str(exc)[:300],
                        ),
                        actions=(),
                    )
                )
                continue
            for spec in specs:
                statuses.append(await self._status_for(spec))
        return statuses

    async def get(self, ext_id: str) -> ExtensionStatus | None:
        """Etat unifie d'une extension, source de verite du Core."""
        for _kind, handler in self._handlers.items():
            for spec in await handler.discover():
                if spec.id == ext_id:
                    return await self._status_for(spec)
        return None

    async def _status_for(self, spec: ExtensionSpec) -> ExtensionStatus:
        """Vue unifiee : etat reel + actions reellement possibles.

        L'etat affiche est celui du systeme d'origine (jamais simule) ; les
        actions sont filtrees selon l'etat ET le type (un Cookbook n'est jamais
        propose « enable » s'il ne sait pas le faire).
        """
        state = await self.load_state(spec.id)
        state.kind = spec.kind
        # Le handler est résolu par son `kind` DÉCLARÉ, pas par la clé d'enregistrement :
        # une spec peut déclarer un type différent (handler de test, alias).
        # Sans cela, la lecture de l'état lèverait un KeyError au lieu de
        # renvoyer l'état réel.
        handler = None
        for registered in self._handlers.values():
            if getattr(registered, "kind", None) == spec.kind:
                handler = registered
                break
        raw: dict[str, Any] = {}
        if handler is None:
            state.state = ExtensionState.ERROR
            state.last_error = f"aucun handler pour le type '{spec.kind}'"
        else:
            try:
                raw = await handler.status(spec.id)
            except Exception as exc:  # noqa: BLE001 — l'erreur est VISIBLE, jamais masquee
                logger.exception("Extensions: statut %s (%s) illisible", spec.id, spec.kind)
                state.state = ExtensionState.ERROR
                state.last_error = str(exc)[:300]
                raw = {}
            else:
                state.state = await self._derive_state(spec, raw, state)
        if state.state not in ExtensionState.ALL:
            state.state = ExtensionState.AVAILABLE
        await self._save_state(state)
        return ExtensionStatus(
            spec=spec,
            state=state,
            actions=self.available_actions(spec, state),
            detail=_public_detail(spec.kind, raw),
        )

    async def _derive_state(
        self, spec: ExtensionSpec, raw: dict[str, Any], state: ExtensionRuntimeState
    ) -> str:
        """Traduit l'etat brut du systeme d'origine vers l'etat unifie."""
        if spec.kind == ExtensionKind.CAPABILITY:
            state.enabled = bool(raw.get("enabled", state.enabled))
            state.installed_version = raw.get("installed_version", state.installed_version)
            if raw.get("last_error"):
                state.last_error = str(raw["last_error"])[:300]
            return CapabilityHandler.state_map().get(
                str(raw.get("state", "")), ExtensionState.AVAILABLE
            )
        if spec.kind == ExtensionKind.PLUGIN:
            status = str(raw.get("status", ""))
            state.enabled = status == "active"
            state.installed_version = raw.get("version", state.installed_version)
            if status == "active":
                return ExtensionState.ENABLED
            if status == "inactive":
                return ExtensionState.DISABLED
            return ExtensionState.AVAILABLE
        # Cookbook : la presence de la recette EST l'installation.
        installed = bool(raw) or bool((spec.payload or {}).get("installed"))
        if installed:
            state.installed_version = raw.get("version", spec.version)
            return ExtensionState.INSTALLED
        return ExtensionState.AVAILABLE

    def available_actions(
        self, spec: ExtensionSpec, state: ExtensionRuntimeState
    ) -> tuple[str, ...]:
        """Actions reellement possibles — decidees par le Core, pas l'UI.

        Une extension en cours ne propose aucune action (evite les courses) et
        une recette Cookbook ne se voit jamais proposer « enable » : elle ne
        sait pas le faire, et le Core refuse de mentir a l'interface.
        """
        if state.state in ExtensionState.BUSY:
            return ()
        if state.state == ExtensionState.AVAILABLE:
            return (ExtensionOperation.INSTALL,)
        if state.state == ExtensionState.ERROR:
            return (ExtensionOperation.INSTALL, ExtensionOperation.UNINSTALL)
        actions: list[str] = []
        if spec.kind == ExtensionKind.COOKBOOK:
            actions.append(ExtensionOperation.UNINSTALL)
            if spec.updatable:
                actions.append(ExtensionOperation.UPDATE)
            return tuple(actions)
        if state.state == ExtensionState.ENABLED:
            actions.append(ExtensionOperation.DISABLE)
        else:
            actions.append(ExtensionOperation.ENABLE)
        actions.append(ExtensionOperation.UNINSTALL)
        if spec.updatable:
            actions.append(ExtensionOperation.UPDATE)
        if spec.plannable:
            actions.append("configure")
        return tuple(actions)

# ── Operations : persistance et bornes ──────────────────────────────

    async def _start_operation(self, ext_id: str, kind: str, op: str, actor: str) -> str:
        op_id = _new_op_id()
        record = {
            "operation_id": op_id,
            "extension_id": ext_id,
            "kind": kind,
            "operation": op,
            "status": OperationStatus.RUNNING,
            "actor": actor,
            "progress": 0,
            "error": None,
            "started_at": _now_iso(),
            "updated_at": _now_iso(),
            "finished_at": None,
            "cancel_requested": False,
        }
        self._operations[op_id] = {**record, "deadline": time.time() + _OPERATION_TIMEOUT_S}
        # Persistee AVANT le lancement : une installation en cours est toujours
        # interrogeable, meme si l'API s'arrete dans la seconde suivante.
        await self._store.save(_OPERATION_DOMAIN, op_id, record)
        return op_id

    async def _finish_operation(
        self, op_id: str, status: str, error: str | None = None
    ) -> None:
        op = self._operations.get(op_id)
        if op is None or op.get("status") in OperationStatus.TERMINAL:
            return
        op["status"] = status
        op["error"] = (error or "")[:300] or None
        op["finished_at"] = _now_iso()
        op["updated_at"] = _now_iso()
        op["progress"] = 100
        record = {k: v for k, v in op.items() if k not in ("task", "deadline")}
        await self._store.save(_OPERATION_DOMAIN, op_id, record)

    async def _reload(self, ext_id: str) -> ExtensionRuntimeState | None:
        """Recharge l'etat reel depuis le systeme d'origine."""
        try:
            status = await self.get(ext_id)
        except Exception:  # noqa: BLE001
            return None
        return status.state if status else None

    async def _fail(
        self, ext_id: str, state: ExtensionRuntimeState, op_id: str, exc: Exception
    ) -> None:
        state.state = ExtensionState.ERROR
        state.last_error = str(exc)[:300]
        await self._save_state(state)
        await self._finish_operation(op_id, OperationStatus.ERROR, str(exc))

    async def _escape_busy(self, ext_id: str, reason: str) -> None:
        """Sort une extension d'un etat « en cours » vers ERROR."""
        state = await self.load_state(ext_id)
        if state.state in ExtensionState.BUSY:
            state.state = ExtensionState.ERROR
            state.last_error = reason
            await self._save_state(state)

    async def _timeout(self, ext_id: str, op_id: str) -> None:
        reason = f"delai depasse ({_OPERATION_TIMEOUT_S:.0f}s) - operation interrompue"
        await self._finish_operation(op_id, OperationStatus.TIMEOUT, reason)
        await self._escape_busy(ext_id, reason)

    async def _already_done(self, ext_id: str, kind: str, op: str) -> str:
        """Operation deja satisfaite : identifiant immediatement terminal."""
        op_id = await self._start_operation(ext_id, kind, op, "user")
        await self._finish_operation(op_id, OperationStatus.SUCCESS)
        return op_id

    async def _mirror_native_operation(self, ext_id: str, op_id: str, native_op: str) -> None:
        """Replique l'operation native dans le registre unifie.

        Le CapabilityManager reste maitre de son propre cycle de vie : on ne
        duplique aucune logique, on lit son etat et on le refleet. La boucle a
        une borne dure : une operation native disparue ne bloque jamais l'UI.
        """
        _kind, handler = await self._require(ext_id)

        async def watch() -> None:
            try:
                for _ in range(_MIRROR_MAX_POLLS):
                    await asyncio.sleep(_MIRROR_POLL_INTERVAL_S)
                    native = await handler.get_operation(native_op)
                    if native is None:
                        break  # trace purgee : on ne reste pas bloque
                    if native.get("status") in OperationStatus.TERMINAL:
                        status = str(native.get("status"))
                        await self._finish_operation(op_id, status, native.get("error"))
                        refreshed = await self._reload(ext_id)
                        if refreshed is not None:
                            await self._save_state(refreshed)
                        return
                await self._timeout(ext_id, op_id)
            except asyncio.CancelledError:  # pragma: no cover
                raise
            except Exception as exc:  # noqa: BLE001
                logger.exception("Extensions: suivi de l'operation %s", op_id)
                await self._finish_operation(op_id, OperationStatus.ERROR, str(exc))

        task = asyncio.create_task(watch())
        self._operations[op_id]["task"] = task
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

# ── Cycle de vie ────────────────────────────────────────────────────

    async def install(
        self, ext_id: str, config: dict[str, Any] | None = None, *, actor: str = "user"
    ) -> str:
        """Installe une extension. Retourne TOUJOURS un `operation_id`.

        L'operation est persistee avant execution et suit toujours un chemin
        terminal : une installation ne peut pas rester « en cours » pour
        toujours (delai borne + reconciliation au demarrage).
        """
        kind, handler = await self._require(ext_id)
        state = await self.load_state(ext_id)
        state.kind = kind
        if state.state in ExtensionState.BUSY:
            raise TransitionError(f"{ext_id} deja en cours (etat={state.state})")
        if state.state == ExtensionState.ENABLED:
            return await self._already_done(ext_id, kind, ExtensionOperation.INSTALL)
        op_id = await self._start_operation(ext_id, kind, ExtensionOperation.INSTALL, actor)
        state.state = ExtensionState.INSTALLING
        state.last_error = None
        await self._save_state(state)
        try:
            native_op = await handler.install(ext_id, config or {})
        except Exception as exc:  # noqa: BLE001 — l'erreur est remontee, jamais masquee
            await self._fail(ext_id, state, op_id, exc)
            raise
        if native_op:
            # Le systeme d'origine pilote sa propre operation : on suit son
            # etat au lieu de dupliquer la logique.
            await self._mirror_native_operation(ext_id, op_id, str(native_op))
            return op_id
        # Operation synchrone (plugin / cookbook) : terminee au retour.
        refreshed = await self._reload(ext_id)
        if refreshed is not None:
            await self._save_state(refreshed)
        else:
            state.state = ExtensionState.INSTALLED
            await self._save_state(state)
        await self._finish_operation(op_id, OperationStatus.SUCCESS)
        return op_id

    async def uninstall(
        self, ext_id: str, *, delete_data: bool = False, actor: str = "user"
    ) -> str:
        """Desinstalle — la suppression des donnees reste EXPLICITE."""
        kind, handler = await self._require(ext_id)
        state = await self.load_state(ext_id)
        state.kind = kind
        if state.state in ExtensionState.BUSY:
            raise TransitionError(f"{ext_id} deja en cours (etat={state.state})")
        op_id = await self._start_operation(ext_id, kind, ExtensionOperation.UNINSTALL, actor)
        state.state = ExtensionState.UNINSTALLING
        await self._save_state(state)
        try:
            native_op = await handler.uninstall(ext_id, delete_data)
        except Exception as exc:  # noqa: BLE001
            await self._fail(ext_id, state, op_id, exc)
            raise
        if native_op:
            await self._mirror_native_operation(ext_id, op_id, str(native_op))
            return op_id
        refreshed = await self._reload(ext_id)
        if refreshed is not None:
            await self._save_state(refreshed)
        else:
            state.state = ExtensionState.AVAILABLE
            state.config = {}
            state.installed_version = None
            state.runtime_meta = {}
            await self._save_state(state)
        await self._finish_operation(op_id, OperationStatus.SUCCESS)
        return op_id

    async def update(self, ext_id: str, *, actor: str = "user") -> str:
        """Mise a jour : re-applique l'installation (idempotent).

        Un type sans runtime n'a pas de version a migrer : la mise a jour
        consiste a re-appliquer, ce que le handler du type definit.
        """
        kind, handler = await self._require(ext_id)
        state = await self.load_state(ext_id)
        state.kind = kind
        if state.state in ExtensionState.BUSY:
            raise TransitionError(f"{ext_id} deja en cours (etat={state.state})")
        op_id = await self._start_operation(ext_id, kind, ExtensionOperation.UPDATE, actor)
        state.state = ExtensionState.UPDATING
        await self._save_state(state)
        try:
            native_op = await handler.install(ext_id, state.config)
        except Exception as exc:  # noqa: BLE001
            await self._fail(ext_id, state, op_id, exc)
            raise
        if native_op:
            await self._mirror_native_operation(ext_id, op_id, str(native_op))
            return op_id
        refreshed = await self._reload(ext_id)
        if refreshed is not None:
            await self._save_state(refreshed)
        await self._finish_operation(op_id, OperationStatus.SUCCESS)
        return op_id

    async def enable(self, ext_id: str, *, actor: str = "user") -> str:
        """Active l'extension — refuse un type qui ne sait pas le faire."""
        kind, handler = await self._require(ext_id)
        state = await self.load_state(ext_id)
        state.kind = kind
        if state.state == ExtensionState.ENABLED:
            return await self._already_done(ext_id, kind, ExtensionOperation.ENABLE)
        op_id = await self._start_operation(ext_id, kind, ExtensionOperation.ENABLE, actor)
        state.state = ExtensionState.ENABLING
        await self._save_state(state)
        try:
            await handler.enable(ext_id)
        except Exception as exc:  # noqa: BLE001
            await self._fail(ext_id, state, op_id, exc)
            raise
        refreshed = await self._reload(ext_id)
        if refreshed is not None:
            await self._save_state(refreshed)
        else:
            state.state = ExtensionState.ENABLED
            state.enabled = True
            await self._save_state(state)
        await self._finish_operation(op_id, OperationStatus.SUCCESS)
        return op_id

    async def disable(self, ext_id: str, *, actor: str = "user") -> str:
        """Desactive l'extension (sans rien supprimer)."""
        kind, handler = await self._require(ext_id)
        state = await self.load_state(ext_id)
        state.kind = kind
        if state.state == ExtensionState.DISABLED:
            return await self._already_done(ext_id, kind, ExtensionOperation.DISABLE)
        op_id = await self._start_operation(ext_id, kind, ExtensionOperation.DISABLE, actor)
        state.state = ExtensionState.DISABLING
        await self._save_state(state)
        try:
            await handler.disable(ext_id)
        except Exception as exc:  # noqa: BLE001
            await self._fail(ext_id, state, op_id, exc)
            raise
        refreshed = await self._reload(ext_id)
        if refreshed is not None:
            await self._save_state(refreshed)
        else:
            state.state = ExtensionState.DISABLED
            state.enabled = False
            await self._save_state(state)
        await self._finish_operation(op_id, OperationStatus.SUCCESS)
        return op_id

    async def configure(
        self, ext_id: str, config: dict[str, Any], *, actor: str = "user"
    ) -> ExtensionRuntimeState:
        """Applique une configuration validee par le systeme d'origine."""
        kind, handler = await self._require(ext_id)
        state = await self.load_state(ext_id)
        state.kind = kind
        await handler.configure(ext_id, config or {})
        refreshed = await self._reload(ext_id)
        if refreshed is not None:
            await self._save_state(refreshed)
        return refreshed or state

    async def logs(self, ext_id: str, tail: int = 200) -> dict[str, Any]:
        """Logs du runtime — explicitement absents pour les types sans runtime.

        Le handler declare l'absence de logs plutot que de renvoyer un vide
        trompeur qui laisserait croire a un runtime silencieux.
        """
        _kind, handler = await self._require(ext_id)
        return await handler.logs(ext_id, tail)

    async def plan(
        self, ext_id: str, *, uninstall: bool = False
    ) -> dict[str, Any] | None:
        """Plan de mutation, quand le type sait en produire un."""
        _kind, handler = await self._require(ext_id)
        return await handler.plan(ext_id, uninstall)

    # ── Observabilite des operations ─────────────────────────────────────

    async def get_operation(self, op_id: str) -> dict[str, Any] | None:
        """Une operation, lue en memoire puis en base (survit a un refresh)."""
        op = self._operations.get(op_id)
        if op is not None:
            return _op_public(op)
        record = await self._store.get(_OPERATION_DOMAIN, op_id)
        if not record:
            return None
        return _op_public(record)

    async def list_operations(self) -> list[dict[str, Any]]:
        """Toutes les operations connues (en cours ET terminees)."""
        records = await self._store.list(_OPERATION_DOMAIN)
        merged: dict[str, dict[str, Any]] = {
            r.get("operation_id"): r for r in records if r.get("operation_id")
        }
        for op_id, op in self._operations.items():
            merged[op_id] = {k: v for k, v in op.items() if k not in ("task", "deadline")}
        return sorted(
            merged.values(), key=lambda r: str(r.get("started_at") or ""), reverse=True
        )

    async def cancel_operation(self, op_id: str) -> bool:
        """Annule une operation : la sortie est TOUJOURS immediate."""
        op = self._operations.get(op_id)
        if op is not None:
            op["cancel_requested"] = True
            task = op.get("task")
            if isinstance(task, asyncio.Task) and not task.done():
                task.cancel()
            await self._finish_operation(op_id, OperationStatus.CANCELLED, "annulee")
            ext_id = str(op.get("extension_id") or "")
            if ext_id:
                await self._escape_busy(ext_id, "operation annulee")
            return True
        record = await self._store.get(_OPERATION_DOMAIN, op_id)
        if not record or record.get("status") in OperationStatus.TERMINAL:
            return False
        await self._store.save(
            _OPERATION_DOMAIN,
            op_id,
            {
                **record,
                "status": OperationStatus.CANCELLED,
                "error": "annulee",
                "finished_at": _now_iso(),
                "updated_at": _now_iso(),
            },
        )
        ext_id = str(record.get("extension_id") or "")
        if ext_id:
            await self._escape_busy(ext_id, "operation annulee")
        return True

    async def recover_operations(self) -> dict[str, int]:
        """Reconciliation au demarrage — aucune operation ne reste bloquee.

        Appelee au boot de l'API. Une operation `RUNNING` au moment de l'arret
        ne peut plus etre suivie (la tache asyncio est morte) : elle est donc
        terminee en `ERROR`, ou en `TIMEOUT` si le delai etait depasse.
        L'extension concernee sort d'un etat « en cours » fige.
        """
        records = await self._store.list(_OPERATION_DOMAIN)
        recovered = 0
        timed_out = 0
        now = time.time()
        for record in records:
            op_id = str(record.get("operation_id") or "")
            if not op_id or record.get("status") in OperationStatus.TERMINAL:
                continue
            started = _iso_epoch(record.get("started_at"))
            expired = started is not None and (now - started) > _OPERATION_TIMEOUT_S
            status = OperationStatus.TIMEOUT if expired else OperationStatus.ERROR
            reason = (
                f"delai depasse ({_OPERATION_TIMEOUT_S:.0f}s) - operation interrompue"
                if expired
                else "interrompue par un redemarrage de l'API"
            )
            await self._store.save(
                _OPERATION_DOMAIN,
                op_id,
                {
                    **record,
                    "status": status,
                    "error": reason,
                    "finished_at": _now_iso(),
                    "updated_at": _now_iso(),
                    "progress": 100,
                },
            )
            recovered += 1
            if expired:
                timed_out += 1
            ext_id = str(record.get("extension_id") or "")
            if ext_id:
                await self._escape_busy(ext_id, reason)
        await self._prune_operations()
        return {"recovered": recovered, "timed_out": timed_out}

    async def _prune_operations(self) -> None:
        """Purge les operations terminees au-dela de la retention / du plafond."""
        records = await self._store.list(_OPERATION_DOMAIN)
        now = time.time()
        for record in records:
            if record.get("status") not in OperationStatus.TERMINAL:
                continue
            stamp = _iso_epoch(record.get("finished_at") or record.get("started_at"))
            if stamp is not None and (now - stamp) > _OPERATION_RETENTION_S:
                await self._store.delete(_OPERATION_DOMAIN, str(record.get("operation_id")))
        survivors = [
            r
            for r in await self._store.list(_OPERATION_DOMAIN)
            if r.get("status") in OperationStatus.TERMINAL
        ]
        if len(survivors) > _OPERATION_MAX_KEPT:
            survivors.sort(key=lambda r: str(r.get("finished_at") or ""), reverse=True)
            for record in survivors[_OPERATION_MAX_KEPT:]:
                await self._store.delete(_OPERATION_DOMAIN, str(record.get("operation_id")))

