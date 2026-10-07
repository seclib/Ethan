"""ETHAN provider — LLM provider registry (Core-owned).

Contract : docs/specs/CLI_CONTRACT.md §8.10.

Routes verified in `interfaces/api/routers/providers.py` :

    GET    /providers               registered providers with their state
    GET    /providers/catalog       types supported by the Core factory
    GET    /providers/{id}
    POST   /providers
    PUT    /providers/{id}
    DELETE /providers/{id}
    GET    /providers/{id}/models
    GET    /providers/{id}/capabilities
    POST   /providers/{id}/test     → exit 1 when the connection fails (§8.10)
    PUT    /providers/{id}/default  (`default`, synonym `use`)

SECRETS (contract §6.4 / §8.10): the Core never returns an API key (only
`has_api_key`). The CLI therefore (1) masks every secret-shaped value in
its rendering — human AND json — and (2) refuses to accept a secret in a
command-line argument: the key enters only through `--api-key-stdin`
(stdin, never argv) and is transmitted once to Core, which owns it.
"""

from __future__ import annotations

import re
import sys

from interfaces.cli.core.api import (
    ExitCode,
    api_delete,
    api_get,
    api_post,
    api_put,
    emit,
    require_id,
    subcommand,
    table,
)
from interfaces.cli.core.errors import usage_error
from interfaces.cli.registry import register

VERBS = {
    "list": "GET /providers",
    "catalog": "GET /providers/catalog",
    "show": "GET /providers/{id}",
    "create": "POST /providers",
    "update": "PUT /providers/{id}",
    "delete": "DELETE /providers/{id}",
    "models": "GET /providers/{id}/models",
    "capabilities": "GET /providers/{id}/capabilities",
    "test": "POST /providers/{id}/test",
    "default": "PUT /providers/{id}/default",
    "use": "PUT /providers/{id}/default",
}

USAGE = (
    "ethan provider <list|catalog|show|create|update|delete|models|"
    "capabilities|test|default> [args]"
)

COLUMNS = [
    ("ID", 20, "id"),
    ("NAME", 18, "name"),
    ("TYPE", 14, "type"),
    ("ENABLED", 8, "enabled"),
    ("STATUS", 14, "status"),
    ("DEFAULT", 8, "is_default"),
    ("DEFAULT MODEL", 24, "default_model"),
]

#: Envelope keys the Core may use for this listing.
KEYS = ("providers",)

MODEL_KEYS = ("models", "items")

MODEL_COLUMNS = [
    ("ID", 40, "id"),
    ("CONTEXT", 10, "context_length"),
    ("LOCAL", 8, "is_local"),
]


def _flag(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "—"


#: Field names that must never carry a secret to stdout (§6.4 / §8.10).
_SECRET_FIELD_RE = re.compile(r"api_?key|secret|password|token", re.IGNORECASE)


def _scrub(obj):
    """Mask every secret-shaped STRING in a Core response.

    Defence in depth: the Core is contractually unable to return an API
    key, but even a leaking payload must not reach stdout — human or
    json mode (§8.10: json only carries key references, never values).
    Booleans like `has_api_key` are business fields and pass through.
    """
    if isinstance(obj, dict):
        return {
            key: (
                "***"
                if isinstance(value, str) and value and _SECRET_FIELD_RE.search(str(key))
                else _scrub(value)
            )
            for key, value in obj.items()
        }
    if isinstance(obj, list):
        return [_scrub(item) for item in obj]
    return obj


def _reject_secret_field(field: str) -> None:
    """A secret on the command line is a USAGE error, never a silent accept."""
    if _SECRET_FIELD_RE.search(field.replace("-", "_")):
        raise usage_error(
            f"refusing to read secret {field!r} from the command line",
            hint="use --api-key-stdin (value read from stdin, never argv)",
        )


def _read_secret_from_stdin() -> str:
    line = sys.stdin.readline().strip()
    if not line:
        raise usage_error(
            "empty secret on stdin",
            hint='pipe it: printf %s "$ETHAN_KEY" | ethan provider … --api-key-stdin',
        )
    return line


@register(
    "provider",
    group="core",
    description="Manage Core LLM providers",
    usage=USAGE,
)
def cmd_provider(args: list[str]) -> int:
    """Manage providers through the Core API."""
    verb, rest = subcommand(args, VERBS, command="provider", usage=USAGE, default="list")

    if verb == "list":
        payload = _scrub(api_get("/providers"))
        return table(payload, columns=COLUMNS, keys=KEYS, default_label="no provider registered")

    if verb == "catalog":
        return emit(_scrub(api_get("/providers/catalog")))

    if verb == "create":
        if len(rest) < 2:
            raise usage_error(
                "missing provider type",
                hint="usage: ethan provider create <type> <name> [--base-url URL] "
                "[--api-key-stdin]",
            )
        body = {"type": rest[0], "name": rest[1]}
        for option in rest[2:]:
            if option == "--api-key-stdin":
                body["api_key"] = _read_secret_from_stdin()
                continue
            key, sep, value = option.partition("=")
            if not sep:
                raise usage_error(
                    f"invalid option: {option!r}",
                    hint="expected --base-url=URL, --default-model=ID or --api-key-stdin",
                )
            field = key.lstrip("-").replace("-", "_")
            _reject_secret_field(field)
            body[field] = value
        return emit(_scrub(api_post("/providers", body)))

    provider_id = require_id(rest[0] if rest else "", name="id", command="provider", usage=USAGE)

    if verb == "show":
        return emit(_scrub(api_get(f"/providers/{provider_id}")))

    if verb == "update":
        if len(rest) < 2:
            raise usage_error(
                "missing <field=value>",
                hint="usage: ethan provider update <id> <field=value> [--api-key-stdin]",
            )
        body: dict = {}
        for pair in rest[1:]:
            if pair == "--api-key-stdin":
                body["api_key"] = _read_secret_from_stdin()
                continue
            key, sep, value = pair.partition("=")
            if not sep:
                raise usage_error(
                    f"invalid field assignment: {pair!r}",
                    hint="expected <field=value> or --api-key-stdin",
                )
            _reject_secret_field(key)
            body[key] = value
        return emit(_scrub(api_put(f"/providers/{provider_id}", body)))

    if verb == "delete":
        return emit(_scrub(api_delete(f"/providers/{provider_id}")))

    if verb == "models":
        payload = _scrub(api_get(f"/providers/{provider_id}/models"))
        return table(
            payload, columns=MODEL_COLUMNS, keys=MODEL_KEYS, default_label="no model available"
        )

    if verb == "capabilities":
        return emit(_scrub(api_get(f"/providers/{provider_id}/capabilities")))

    if verb == "test":
        payload = _scrub(api_post(f"/providers/{provider_id}/test"))
        code = emit(payload)
        # §8.10: the Core verdict is reported, not re-laballed — a failed
        # connection test exits 1 so scripts can branch on it.
        if isinstance(payload, dict) and payload.get("connected") is False:
            return int(ExitCode.OPERATION_FAILED)
        return code

    if verb in ("default", "use"):
        return emit(_scrub(api_put(f"/providers/{provider_id}/default", {})))

    raise usage_error(f"unsupported verb: {verb}", hint=f"usage: {USAGE}")
