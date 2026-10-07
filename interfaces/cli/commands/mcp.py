"""ETHAN mcp — MCP tool servers registered in the Core.

Contract : docs/specs/CLI_CONTRACT.md (MCP servers are Core capabilities
exposed under `/v1/tools/servers`; the CLI adds no server of its own).

Routes verified in `interfaces/api/routers/capabilities.py` :

    GET    /v1/tools/servers
    GET    /v1/tools/servers/{id}
    POST   /v1/tools/servers
    PUT    /v1/tools/servers/{id}
    PUT    /v1/tools/servers/{id}/status
    POST   /v1/tools/servers/{id}/sync
    DELETE /v1/tools/servers/{id}
    GET    /v1/tools/servers/... via ?enabled=

The connection itself, the handshake and the tool inventory belong to the
Core. This command registers, inspects and syncs servers; credentials are
never displayed (rule AGENTS « secret »).
"""

from __future__ import annotations

from interfaces.cli.core.api import (
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
    "list": "GET /v1/tools/servers",
    "show": "GET /v1/tools/servers/{id}",
    "add": "POST /v1/tools/servers",
    "update": "PUT /v1/tools/servers/{id}",
    "enable": "PUT /v1/tools/servers/{id}/status",
    "disable": "PUT /v1/tools/servers/{id}/status",
    "sync": "POST /v1/tools/servers/{id}/sync",
    "remove": "DELETE /v1/tools/servers/{id}",
}

USAGE = "ethan mcp <list|show|add|update|enable|disable|sync|remove> [args]"

COLUMNS = [
    ("ID", 28, "id"),
    ("NAME", 22, "name"),
    ("TRANSPORT", 12, "transport"),
    ("ENABLED", 8, "enabled"),
    ("STATUS", 14, "status"),
]

#: Envelope keys the Core may use for this listing.
KEYS = ("servers",)


def _flag(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "—"


def _body(pairs: list[str]) -> dict:
    """Parse ``key=value`` pairs into a Core payload."""
    body: dict = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            raise usage_error(f"invalid field assignment: {pair!r}", hint="expected <field=value>")
        body[key] = value
    return body


@register(
    "mcp",
    group="core",
    description="Manage Core MCP tool servers",
    usage=USAGE,
)
def cmd_mcp(args: list[str]) -> int:
    """Manage MCP tool servers through the Core API."""
    verb, rest = subcommand(args, VERBS, command="mcp", usage=USAGE, default="list")

    if verb == "list":
        payload = api_get("/v1/tools/servers")
        return table(payload, columns=COLUMNS, keys=KEYS, default_label="no MCP server")

    if verb == "add":
        if len(rest) < 2:
            raise usage_error(
                "missing server definition",
                hint="usage: ethan mcp add <name> <url> [transport=stdio|sse|http]",
            )
        body = {"name": rest[0], "url": rest[1]}
        body.update(_body(rest[2:]))
        return emit(api_post("/v1/tools/servers", body))

    server_id = require_id(rest[0] if rest else "", name="id", command="mcp", usage=USAGE)

    if verb == "show":
        return emit(api_get(f"/v1/tools/servers/{server_id}"))

    if verb == "update":
        if len(rest) < 2:
            raise usage_error(
                "missing <field=value>", hint="usage: ethan mcp update <id> <field=value>"
            )
        return emit(api_put(f"/v1/tools/servers/{server_id}", _body(rest[1:])))

    if verb in ("enable", "disable"):
        return emit(api_put(f"/v1/tools/servers/{server_id}/status", {"enabled": verb == "enable"}))

    if verb == "sync":
        return emit(api_post(f"/v1/tools/servers/{server_id}/sync", {}))

    if verb == "remove":
        return emit(api_delete(f"/v1/tools/servers/{server_id}"))

    raise usage_error(f"unsupported verb: {verb}", hint=f"usage: {USAGE}")
