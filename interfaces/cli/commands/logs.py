"""ETHAN logs — local CLI journal and Core component logs.

Contract : docs/specs/CLI_CONTRACT.md §8.16.

Two sources, both read-only:

- the **local CLI journal** (`~/.ethan/logs.json`, written by the CLI itself);
- the **Core component logs** (`GET /v1/components/{capability_id}/logs`),
  which is where an operator looks when a service misbehaves.

The raw Docker stream (`docker compose logs`) stays reachable with `--raw`,
because it is the only way to see a container that cannot start. No pager is
ever used: `--tail`/`--limit` are the scriptable path (§3.2).

SECRETS: every line is scrubbed before it is printed. A token, a password or
an API key must never reach a terminal, a log file or a CI transcript
(rule AGENTS « secret », contract §6.4).
"""

from __future__ import annotations

import re

from interfaces.cli.core import logging as logs
from interfaces.cli.core.api import ExitCode, api_get, emit, subcommand
from interfaces.cli.core.errors import usage_error
from interfaces.cli.registry import register

VERBS = {
    "list": "show the recent local CLI journal",
    "errors": "show only the failed local entries",
    "search": "filter the local journal by text",
    "component": "GET /v1/components/{capability_id}/logs — Core service logs",
}

USAGE = "ethan logs <list|errors|search|component> [args] [--tail N] [--level LEVEL] [--no-color]"

#: Values that look like a credential and must never be printed.
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]+"),
    re.compile(r"(?i)\b(authorization)\s*[:=]\s*\S+"),
    re.compile(r"\b(sk|pk|ghp|xox[baprs])[-_][A-Za-z0-9\-_]{8,}"),
    re.compile(r"(?i)\b(token|password|passwd|secret|api[_-]?key)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\b(jwt|eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)"),
)

REDACTED = "«redacted»"


def scrub(text: str) -> str:
    """Remove anything that looks like a credential from a log line."""
    if not isinstance(text, str):
        return text
    cleaned = text
    for pattern in _SECRET_PATTERNS:
        cleaned = pattern.sub(REDACTED, cleaned)
    return cleaned


def scrub_entry(entry: dict) -> dict:
    """Scrub every string field of a journal entry."""
    return {key: scrub(value) if isinstance(value, str) else value for key, value in entry.items()}


def _tail_option(args: list[str], default: int) -> int:
    if "--tail" not in args and "--last" not in args:
        return default
    flag = "--tail" if "--tail" in args else "--last"
    index = args.index(flag)
    # `--last` alone keeps its historical meaning of "the default tail".
    if index + 1 >= len(args):
        if flag == "--last":
            return default
        raise usage_error(f"option {flag} requires a value", hint=f"usage: {flag} <N>")
    try:
        value = int(args[index + 1])
    except ValueError:
        raise usage_error(
            f"invalid {flag} value: {args[index + 1]!r}", hint=f"{flag} expects an integer"
        ) from None
    if value <= 0:
        raise usage_error(f"invalid {flag} value: {value!r}", hint=f"{flag} must be > 0")
    return value


def _level_filter(args: list[str], entries: list[dict]) -> list[dict]:
    """Filter entries by the severity stored in the `status` field."""
    if "--level" not in args:
        return entries
    index = args.index("--level")
    if index + 1 >= len(args):
        raise usage_error("option --level requires a value", hint="usage: --level <LEVEL>")
    wanted = args[index + 1].lower()
    known = {"ok", "error"}
    if wanted not in known:
        raise usage_error(
            f"unknown level: {wanted!r}", hint=f"expected one of: {', '.join(sorted(known))}"
        )
    return [entry for entry in entries if str(entry.get("status", "")).lower() == wanted]


def _render(entries: list[dict]) -> int:
    """Print the local journal, scrubbed and without colour."""
    for raw in entries:
        entry = scrub_entry(raw)
        parts = [
            f"  {entry.get('ts', '?')}",
            f"{entry.get('command', '?')}",
            f"-> {entry.get('status', '?')}",
        ]
        if entry.get("latency_ms") is not None:
            parts.append(f"({entry['latency_ms']}ms)")
        if entry.get("error"):
            parts.append(scrub(str(entry["error"])))
        print(" ".join(str(part) for part in parts))
    if not entries:
        print("  (no entry)")
    return int(ExitCode.SUCCESS)


@register(
    "logs",
    group="infra",
    description="Read the CLI journal and Core component logs",
    usage=USAGE,
)
def cmd_logs(args: list[str]) -> int:
    """Read logs, filtering by text, level and service.

    Backward compatible: `ethan logs --last N`, `--errors` and a bare text
    query keep working exactly as before, alongside the explicit verbs.
    """
    # Legacy call forms are resolved before the verb parser so existing
    # scripts and habits do not break (contract §2.2).
    if not args:
        verb, rest = "list", []
    elif args[0] in VERBS:
        verb, rest = subcommand(args, VERBS, command="logs", usage=USAGE, default="list")
    elif args[0] in ("--errors", "errors"):
        verb, rest = "errors", args[1:]
    elif args[0] in ("--last", "--tail"):
        verb, rest = "list", args
    else:
        # Bare text: `ethan logs chat` filters the journal.
        verb, rest = "search", args

    if verb == "list":
        entries = logs.query_last(_tail_option(args, 20))
        return _render(_level_filter(args, entries))

    if verb == "errors":
        entries = logs.query_errors(_tail_option(args, 50))
        return _render(_level_filter(args, entries))

    if verb == "search":
        query = " ".join(part for part in rest if not part.startswith("--")).strip()
        # A bare `--last N` must not be mistaken for a search term.
        query = " ".join(part for part in query.split() if not part.isdigit()).strip()
        if not query:
            return _render(_level_filter(args, logs.query_last(_tail_option(args, 20))))
        entries = logs.query_text(query, _tail_option(args, 20))
        return _render(_level_filter(args, entries))

    if verb == "component":
        if not rest:
            raise usage_error(
                "missing <capability-id>",
                hint="usage: ethan logs component <capability-id> [--tail N]",
            )
        capability = rest[0]
        payload = api_get(f"/v1/components/{capability}/logs")
        if isinstance(payload, dict):
            lines = payload.get("logs") or payload.get("lines") or []
            if isinstance(lines, list):
                for line in lines[-_tail_option(args, 50) :]:
                    print(scrub(str(line)))
                return int(ExitCode.SUCCESS)
        return emit(payload)

    raise usage_error(f"unsupported verb: {verb}", hint=f"usage: {USAGE}")
