"""ETHAN extension — the unified extension system (Core state machine).

Contract : docs/specs/CLI_CONTRACT.md §8.11.

Routes verified in `interfaces/api/routers/extensions.py` :

    GET  /v1/extensions                     catalogue with current state
    GET  /v1/extensions/{id}
    GET  /v1/extensions/{id}/plan           what an operation would do
    GET  /v1/extensions/{id}/logs
    POST /v1/extensions/{id}/install        → operation (async)
    POST /v1/extensions/{id}/enable         → operation (async)
    POST /v1/extensions/{id}/disable        → operation (async)
    POST /v1/extensions/{id}/update         → operation (async)
    POST /v1/extensions/{id}/uninstall      → operation (async)
    GET  /v1/extensions/operations          every operation (in progress and settled)
    GET  /v1/extensions/operations/{id}     poll an operation
    POST /v1/extensions/operations/{id}/cancel

ONE family covers the three kinds (`capability`, `plugin`, `cookbook`) through
the ONE Core lifecycle — the CLI never grows a per-kind manager. The
vocabulary displayed here is the Core's own (`AVAILABLE`, `INSTALLING`,
`INSTALLED`, …) — the CLI never translates it into its own words (§4.1). An
illegal transition is rejected by the Core with HTTP 409 → exit 8 (§5), so
the state machine is never second-guessed here.

Asynchronous operations are NOT presented as finished:

- default: the CLI polls until the operation settles, showing the Core's own
  `progress` on **stderr** (stdout stays clean, §4.2) — exit 0 on SUCCESS,
  1 on ERROR/CANCELLED with the Core's `error` surfaced, 7 when
  `--wait-timeout` expires, 130 when the user interrupts (the operation
  keeps running on the Core: `ethan extension operation <id>` recovers it);
- `--no-wait`: returns the operation object immediately (exit 0 =
  accepted). Recommended in CI with `ethan extension operation <id>`.

Security: every call goes through the authenticated single HTTP boundary;
permissions (READ / SETTINGS), RBAC and validation are enforced by the Core
and the API middleware — this command never bypasses them.
"""

from __future__ import annotations

import sys
import time

from interfaces.cli.core import colors as clr
from interfaces.cli.core.api import (
    api_get,
    api_post,
    emit,
    require_id,
    subcommand,
    table,
)
from interfaces.cli.core.context import get_context
from interfaces.cli.core.errors import CLIError, usage_error
from interfaces.cli.core.exit_codes import ExitCode
from interfaces.cli.registry import register

VERBS = {
    "list": "GET /v1/extensions",
    "info": "GET /v1/extensions/{id}",
    "show": "GET /v1/extensions/{id}",  # synonyme explicite de info (§8.11)
    "plan": "GET /v1/extensions/{id}/plan",
    "logs": "GET /v1/extensions/{id}/logs",
    "install": "POST /v1/extensions/{id}/install",
    "enable": "POST /v1/extensions/{id}/enable",
    "disable": "POST /v1/extensions/{id}/disable",
    "update": "POST /v1/extensions/{id}/update",
    "uninstall": "POST /v1/extensions/{id}/uninstall",
    "operations": "GET /v1/extensions/operations",
    "operation": "GET /v1/extensions/operations/{id}",
    "cancel": "POST /v1/extensions/operations/{id}/cancel",
}

USAGE = (
    "ethan extension <list|info|show|plan|logs|install|uninstall|enable|disable|"
    "update|operations|operation|cancel> [id] [--kind k] [--state s] [--query q] "
    "[--no-wait] [--wait-timeout SEC] [--yes]"
)

COLUMNS = [
    ("ID", 32, "id"),
    ("TYPE", 12, "kind"),
    ("STATE", 14, "state"),
    ("VERSION", 12, "version"),
]

#: Human field view of a single extension (`info`).
INFO_FIELDS = (
    "id",
    "kind",
    "state",
    "enabled",
    "installed_version",
    "last_error",
    "updated_at",
    "actions",
)

#: Operation columns for the recovery listing (`operations`).
OPERATION_COLUMNS = [
    ("OPERATION", 18, "operation_id"),
    ("EXTENSION", 28, "extension_id"),
    ("OP", 12, "operation"),
    ("STATUS", 10, "status"),
    ("PROGRESS", 8, "progress"),
]

#: Envelope keys the Core may use for these listings.
KEYS = ("extensions",)
OPERATION_KEYS = ("operations",)

#: Terminal statuses of a Core operation (`core.extensions.types.OperationStatus`).
OP_TERMINAL = frozenset({"SUCCESS", "ERROR", "TIMEOUT", "CANCELLED"})

#: Contract exit code per terminal operation status (§5).
OP_EXIT = {
    "SUCCESS": ExitCode.SUCCESS,
    "ERROR": ExitCode.OPERATION_FAILED,
    "TIMEOUT": ExitCode.TIMEOUT,
    "CANCELLED": ExitCode.OPERATION_FAILED,
}

#: Default number of seconds spent waiting for an async operation.
DEFAULT_WAIT_TIMEOUT = 120.0
POLL_INTERVAL = 2.0

#: Verbs that mutate the installed payload — destructive without `--yes` (T8).
DESTRUCTIVE_VERBS = frozenset({"uninstall"})


def _has(args: list[str], flag: str) -> bool:
    return flag in args


def _option(args: list[str], flag: str) -> str | None:
    """Value of ``--flag value`` when present, None otherwise."""
    if flag not in args:
        return None
    index = args.index(flag)
    if index + 1 >= len(args):
        raise usage_error(f"option {flag} requires a value", hint=f"usage: {flag} <value>")
    return args[index + 1]


def _flag_value(args: list[str], flag: str, default: float) -> float:
    if flag not in args:
        return default
    index = args.index(flag)
    if index + 1 >= len(args):
        raise usage_error(f"option {flag} requires a value", hint=f"usage: {flag} <sec>")
    try:
        return float(args[index + 1])
    except ValueError:
        raise usage_error(
            f"invalid {flag} value: {args[index + 1]!r}", hint=f"{flag} expects seconds"
        ) from None


def _operation_id(payload) -> str | None:
    """Extract the operation identifier from a Core operation envelope."""
    if not isinstance(payload, dict):
        return None
    for field in ("operation_id", "id"):
        if payload.get(field):
            return str(payload[field])
    return None


def _op_status(operation: dict) -> str:
    """Status vocabulary of a Core operation (uppercase).

    The operation record uses `OperationStatus` (`RUNNING`, `SUCCESS`, …);
    `done` is the router's boolean short-hand. An ExtensionState found in a
    legacy payload is returned as-is so the terminal check never guesses.
    """
    value = operation.get("status")
    if isinstance(value, str) and value:
        return value.upper()
    if operation.get("done"):
        return "SUCCESS"
    for field in ("state", "result"):
        value = operation.get(field)
        if isinstance(value, dict):
            value = value.get("state") or value.get("status")
        if isinstance(value, str) and value:
            return value.upper()
    return "RUNNING"


def _stderr(message: str) -> None:
    """Diagnostics go to stderr — stdout stays reserved for output (§4.2)."""
    print(message, file=sys.stderr)


def _announce(identifier: str, verb: str, operation_id: str) -> None:
    """Human mode: say the operation was accepted and where to follow it."""
    if get_context().quiet:
        return
    _stderr(
        f"{clr.C.CYAN}◇ {verb} {identifier}: operation {operation_id} accepted "
        f"— waiting…{clr.C.RESET}"
    )
    _stderr(f"  {clr.C.DIM}recover anytime: ethan extension operation {operation_id}{clr.C.RESET}")


def _progress(operation: dict, signature: list) -> None:
    """Stream the Core's own progress on stderr (never stdout, §4.2)."""
    if get_context().quiet:
        return
    current = (_op_status(operation), operation.get("progress"))
    if current == signature[0]:
        return
    signature[0] = current
    status, progress = current
    shown = f"{progress}%" if isinstance(progress, (int, float)) else "—"
    _stderr(
        f"  {clr.C.DIM}… {operation.get('extension_id', '?')} "
        f"{operation.get('operation', '')} {shown} ({status}){clr.C.RESET}"
    )


def _wait_for(operation_id: str, timeout: float, *, announce: tuple | None = None) -> dict:
    """Poll an async operation until it settles or the deadline passes.

    The terminal vocabulary is the Core's `OperationStatus` — `SUCCESS` ends
    the wait (an operation that never settles would otherwise spin until the
    client deadline). Progress is streamed on stderr only.

    Returns:
        The final Core operation object.

    Raises:
        CLIError: exit 7 when the deadline expires (contract §5).
    """
    if announce is not None:
        _announce(announce[0], announce[1], operation_id)
    deadline = time.monotonic() + timeout
    signature: list = [None]
    while True:
        operation = api_get(f"/v1/extensions/operations/{operation_id}")
        if not isinstance(operation, dict):
            raise CLIError(
                f"operation {operation_id} returned no state",
                code="CLI-WAIT",
                context="the Core answered without an operation record",
                hint=f"poll it again: ethan extension operation {operation_id}",
                exit_code=ExitCode.OPERATION_FAILED,
            )
        if _op_status(operation) in OP_TERMINAL:
            return operation
        _progress(operation, signature)
        if time.monotonic() >= deadline:
            raise CLIError(
                f"operation {operation_id} still running after {timeout:g}s",
                code="CLI-WAIT",
                context="the Core operation did not settle in time",
                hint=f"poll it later: ethan extension operation {operation_id}",
                exit_code=ExitCode.TIMEOUT,
            )
        time.sleep(POLL_INTERVAL)


def _confirm_destructive(identifier: str, verb: str, args: list[str]) -> None:
    """Destructive verb guard (contract T8).

    Without an explicit confirmation and without an interactive terminal the
    command is a usage error (exit 2) and NOTHING is sent to the Core.
    """
    ctx = get_context()
    if ctx.assume_yes or _has(args, "--yes"):
        return
    try:
        interactive = bool(sys.stdin.isatty())
    except Exception:  # noqa: BLE001 — a detached stream counts as non-interactive
        interactive = False
    if not interactive:
        raise usage_error(
            f"'{verb} {identifier}' is destructive and requires confirmation",
            hint="re-run with --yes when there is no terminal",
        )
    try:
        answer = input(f"{verb} {identifier}? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = ""
    if answer not in ("y", "yes"):
        raise usage_error(f"{verb} {identifier} declined — nothing was executed")


def _finalise(operation: dict, verb: str, identifier: str) -> int:
    """Surface the settled operation and return its contract exit code."""
    status = _op_status(operation)
    emit(operation)
    if status != "SUCCESS" and not get_context().quiet:
        error = operation.get("error") or status.lower()
        _stderr(f"{clr.C.RED}✗ {verb} {identifier} failed: {error}{clr.C.RESET}")
    return int(OP_EXIT.get(status, ExitCode.OPERATION_FAILED))


@register(
    "extension",
    group="core",
    description="Manage the unified extension system",
    usage=USAGE,
)
def cmd_extension(args: list[str]) -> int:
    """Manage extensions through the Core API."""
    verb, rest = subcommand(args, VERBS, command="extension", usage=USAGE, default="list")

    if verb == "list":
        kind = _option(rest, "--kind")
        # Validate every option BEFORE any network call (contract T5).
        state = _option(rest, "--state")
        query = _option(rest, "--query")
        path = f"/v1/extensions?kind={kind}" if kind else "/v1/extensions"
        payload = _filter_list(api_get(path), state, query)
        return table(payload, columns=COLUMNS, keys=KEYS, default_label="no extension")

    if verb == "operations":
        payload = api_get("/v1/extensions/operations")
        return table(
            payload,
            columns=OPERATION_COLUMNS,
            keys=OPERATION_KEYS,
            default_label="no operation",
        )

    identifier = require_id(rest[0] if rest else "", name="id", command="extension", usage=USAGE)

    if verb in ("info", "show"):
        return _emit_info(api_get(f"/v1/extensions/{identifier}"))
    if verb in ("plan", "logs"):
        return emit(api_get(f"/v1/extensions/{identifier}/{verb}"))
    if verb == "operation":
        return emit(api_get(f"/v1/extensions/operations/{identifier}"))
    if verb == "cancel":
        return emit(api_post(f"/v1/extensions/operations/{identifier}/cancel", {}))

    if verb in DESTRUCTIVE_VERBS:
        _confirm_destructive(identifier, verb, rest)

    # Validate options BEFORE any network call (contract T5).
    wait_timeout = _flag_value(rest, "--wait-timeout", DEFAULT_WAIT_TIMEOUT)

    # Lifecycle verbs return 202 + an operation object.
    payload = api_post(f"/v1/extensions/{identifier}/{verb}", {})
    operation_id = _operation_id(payload)

    if _has(rest, "--no-wait") or not operation_id:
        if operation_id and not get_context().quiet:
            _stderr(
                f"◇ operation {operation_id} accepted — follow it with: "
                f"ethan extension operation {operation_id}"
            )
        return emit(payload)

    try:
        settled = _wait_for(operation_id, wait_timeout, announce=(identifier, verb))
    except KeyboardInterrupt:
        # The terminal may close here: the Core operation keeps running and a
        # new session recovers it (persistence, contract §8.11).
        _stderr(
            f"\n◇ interrupted — {operation_id} keeps running on the Core; "
            f"recover with: ethan extension operation {operation_id}"
        )
        return int(ExitCode.INTERRUPTED)
    return _finalise(settled, verb, identifier)


def _filter_list(payload, state: str | None, query: str | None):
    """Selection on Core fields (`--state`, `--query`) — no state invented."""
    if (not state and not query) or not isinstance(payload, dict):
        return payload
    items = payload.get("extensions")
    if not isinstance(items, list):
        return payload
    wanted = state.upper() if state else None
    needle = query.lower() if query else None
    filtered = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if wanted and str(item.get("state", "")).upper() != wanted:
            continue
        if needle:
            haystack = " ".join(
                str(item.get(field, "")) for field in ("id", "kind", "state")
            ).lower()
            if needle not in haystack:
                continue
        filtered.append(item)
    return {**payload, "extensions": filtered}


def _emit_info(payload) -> int:
    """One extension: field view in human mode, untouched payload in JSON."""
    if not isinstance(payload, dict):
        return emit(payload)
    from interfaces.cli.core.api import _cell

    rows = [[field, _cell(payload.get(field))] for field in INFO_FIELDS]
    return emit(payload, rows=rows, columns=[("FIELD", 20), ("VALUE", 56)])
