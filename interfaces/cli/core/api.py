"""ETHAN CLI — shared helpers for commands backed by the Core API.

Every Core-backed command goes through the SAME single HTTP boundary
(`core.client.request_json`) and the SAME rendering rules (contract §4).
A command module therefore only declares its verbs and the Core route each one
calls — it never re-implements transport, auth, JSON decoding or exit codes.

This is what keeps the First Law of AGENTS.md true: the CLI reveals Core
capabilities, it never owns them.
"""

from __future__ import annotations

from interfaces.cli.core import colors as clr
from interfaces.cli.core.context import get_context
from interfaces.cli.core.errors import CLIError, usage_error
from interfaces.cli.core.exit_codes import ExitCode, normalize_exit


def api_get(path: str, **kwargs):
    """GET a Core route through the shared HTTP boundary."""
    from interfaces.cli.core.client import request_json

    return request_json("GET", path, **kwargs)


def api_post(path: str, payload: dict | None = None, **kwargs):
    """POST to a Core route through the shared HTTP boundary."""
    from interfaces.cli.core.client import request_json

    return request_json("POST", path, payload, **kwargs)


def api_put(path: str, payload: dict | None = None, **kwargs):
    """PUT to a Core route through the shared HTTP boundary."""
    from interfaces.cli.core.client import request_json

    return request_json("PUT", path, payload, **kwargs)


def api_delete(path: str, **kwargs):
    """DELETE a Core route through the shared HTTP boundary."""
    from interfaces.cli.core.client import request_json

    return request_json("DELETE", path, **kwargs)


def api_stream(path: str, payload: dict, **kwargs):
    """POST to a Core SSE route and yield parsed events (single boundary).

    Same HTTP boundary as `api_get`/`api_post` — commands stream without
    ever re-implementing transport, auth or error mapping (§5).
    """
    from interfaces.cli.core.client import stream_sse

    return stream_sse(path, payload, **kwargs)


def emit(payload, *, rows=None, columns=None) -> int:
    """Render a Core payload honouring the active output mode.

    In JSON mode the payload is passed through untouched (§4.2 — the CLI
    renames, masks and invents no business field). In human mode an aligned
    table is printed when both `rows` and `columns` are given, otherwise the
    payload is shown as JSON.

    `columns` is a list of ``(header, width)`` pairs, used only for widths.

    Returns:
        The contract exit code for a successful operation (0).
    """
    ctx = get_context()

    # `--quiet`: a success with data to show prints nothing on stdout (§4.4).
    # In JSON mode nothing changes: the document stays parseable.
    if ctx.quiet and not ctx.is_json:
        return int(ExitCode.SUCCESS)

    if ctx.is_json:
        ctx.emit_json(payload)
        return int(ExitCode.SUCCESS)

    if rows is not None and columns is not None:
        header = "  ".join(name.ljust(width) for name, width in columns)
        print(clr.C.BOLD + header + clr.C.RESET)
        print(clr.C.DIM + "  ".join("─" * width for _, width in columns) + clr.C.RESET)
        for row in rows:
            cells = [str(cell).ljust(width) for cell, (_, width) in zip(row, columns)]
            print("  ".join(cells))
        return int(ExitCode.SUCCESS)

    if isinstance(payload, (dict, list)):
        import json

        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        print(payload)
    return int(ExitCode.SUCCESS)


def items_of(payload, keys: tuple[str, ...] = ()) -> list:
    """Extract the list carried by a Core response.

    Core replies with either a bare list or an envelope
    (``{"providers": [...]}``). `keys` lists the envelope fields to try, in
    order; the payload itself is returned when it is already a list.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys or ("items",):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if value is not None and key in payload:
                return [value]
        if not keys:
            return []
    return []


def table(payload, *, columns, keys: tuple[str, ...] = (), default_label="(none)") -> int:
    """Render a Core list payload as an aligned table.

    Args:
        payload: what the Core returned (list or envelope).
        columns: ``[(header, width, field), ...]`` — the field is the key read
            from each item, so the CLI never has to rebuild the rows itself.
        keys: envelope fields to look for, in order.
        default_label: text shown when the list is empty.

    Returns:
        0 on success.
    """
    items = items_of(payload, keys)

    if not items:
        ctx = get_context()
        if ctx.is_json:
            # In JSON mode stdout carries exactly one document (§4.2), so the
            # "nothing here" notice must never reach it.
            ctx.emit_json(payload)
            return int(ExitCode.SUCCESS)
        if ctx.quiet:
            return int(ExitCode.SUCCESS)
        print(clr.C.DIM + f"  {default_label}" + clr.C.RESET)
        return int(ExitCode.SUCCESS)

    rows = []
    for item in items:
        if not isinstance(item, dict):
            rows.append([item] + [""] * (len(columns) - 1))
            continue
        rows.append([_cell(item.get(field)) for _, _, field in columns])

    return emit(payload, rows=rows, columns=[(header, width) for header, width, _ in columns])


def _cell(value) -> str:
    """One table cell: full identifiers are never truncated (§4.1)."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value) if value else "—"
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items()) if value else "—"
    return str(value)


def subcommand(
    args: list[str],
    verbs: dict[str, str],
    *,
    command: str,
    usage: str,
    default: str | None = None,
):
    """Resolve a verb from ``args`` with a usage error when invalid.

    An unknown verb in a valid family is a USAGE error → exit 2 (contract §5),
    never a silent no-op. When the verb is absent, `default` is used.

    Raises:
        CLIError: exit code 2 for an unknown verb.
    """
    if not args:
        if default is not None:
            return default, []
        raise usage_error(f"missing subcommand for '{command}'", hint=f"usage: {usage}")

    verb = args[0]
    if verb in ("-h", "--help"):
        raise usage_error(f"usage: {usage}", hint="run 'ethan help' for details")
    if verb not in verbs:
        from interfaces.cli.core.ux import UX

        suggestion = UX.suggest_command(verb, sorted(verbs))
        hint = (
            f"did you mean '{suggestion}'? usage: {command} <{'|'.join(sorted(verbs))}>"
            if suggestion
            else f"usage: {usage}"
        )
        raise usage_error(f"unknown {command} subcommand: '{verb}'", hint=hint)
    return verb, args[1:]


def require_id(value: str, *, name: str, command: str, usage: str) -> str:
    """Return `value` or raise a usage error when the identifier is missing."""
    if not value:
        raise usage_error(f"missing <{name}>", hint=f"usage: {usage}")
    return value


__all__ = [
    "CLIError",
    "ExitCode",
    "api_delete",
    "api_get",
    "api_post",
    "api_put",
    "api_stream",
    "emit",
    "normalize_exit",
    "require_id",
    "subcommand",
    "table",
]
