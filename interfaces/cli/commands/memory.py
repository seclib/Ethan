"""ETHAN memory — Core engineering memory + local command history.

Subcommands:
  Core memory (engineering memory service) :
    health, events, event, component-history, records, vault-tree, vault-file,
    vault-search, vault-backlinks, vault-graph, vault-resolve, record
  Local CLI history (unchanged, CLI-only) :
    recent, frequent
"""

from __future__ import annotations

from interfaces.cli.core.api import (
    api_get,
    api_post,
    emit,
    require_id,
    subcommand,
    table,
)
from interfaces.cli.core import memory as mem_local
from interfaces.cli.core.errors import usage_error
from interfaces.cli.registry import register

mem = mem_local  # alias conservé pour les tests (cli.commands.memory.mem)

VERBS = {
    "health": "GET /v1/memory/health",
    "record": "POST /v1/memory/events",
    "vault-write": "POST /v1/memory/vault/file",
    "records": "GET /v1/memory/records",
    "events": "GET /v1/memory/events",
    "event": "GET /v1/memory/events/{record_id}",
    "component-history": "GET /v1/memory/components/{component}/history",
    "vault-tree": "GET /v1/memory/vault/tree",
    "vault-file": "GET /v1/memory/vault/file",
    "vault-backlinks": "GET /v1/memory/vault/backlinks",
    "vault-resolve": "GET /v1/memory/vault/resolve",
    "vault-search": "GET /v1/memory/vault/search",
    "vault-graph": "GET /v1/memory/vault/graph",
    "validate": "POST /v1/memory/events/validate",
    "recent": "local CLI history",
    "frequent": "local CLI history",
}

USAGE = "ethan memory <health|events|event|component-history|records|vault-*|recent|frequent> [args]"

COLUMNS_EVENTS = [("ID", 24, "id"), ("TYPE", 16, "record_type"), ("COMPONENT", 16, "component"), ("STATUS", 12, "status")]
COLUMNS_RECORDS = [("ID", 24, "id"), ("TYPE", 16, "record_type"), ("COMPONENT", 16, "component")]


def _events(rest):
    params = {}
    # support --component/--type/--status
    i = 0
    while i < len(rest):
        if rest[i] == "--component" and i + 1 < len(rest):
            params["component"] = rest[i + 1]
            i += 2
            continue
        if rest[i] == "--type" and i + 1 < len(rest):
            params["record_type"] = rest[i + 1]
            i += 2
            continue
        if rest[i] == "--status" and i + 1 < len(rest):
            params["status"] = rest[i + 1]
            i += 2
            continue
        i += 1
    from urllib.parse import urlencode
    qs = ("?" + urlencode(params)) if params else ""
    payload = api_get(f"/v1/memory/events{qs}")
    items = payload.get("results", payload) if isinstance(payload, dict) else payload
    items = items if isinstance(items, list) else []
    return table(items, columns=COLUMNS_EVENTS, keys=("results",), default_label="no memory event")


def _event(rest):
    rid = require_id(rest[0] if rest else "", name="record_id", command="memory", usage=USAGE)
    return emit(api_get(f"/v1/memory/events/{rid}"))


def _component_history(rest):
    comp = require_id(rest[0] if rest else "", name="component", command="memory", usage=USAGE)
    return emit(api_get(f"/v1/memory/components/{comp}/history"))


def _records(rest):
    params = {}
    i = 0
    while i < len(rest):
        if rest[i] == "--type" and i + 1 < len(rest):
            params["record_type"] = rest[i + 1]
            i += 2
            continue
        if rest[i] == "--component" and i + 1 < len(rest):
            params["component"] = rest[i + 1]
            i += 2
            continue
        if rest[i] == "--status" and i + 1 < len(rest):
            params["status"] = rest[i + 1]
            i += 2
            continue
        i += 1
    from urllib.parse import urlencode
    qs = ("?" + urlencode(params)) if params else ""
    payload = api_get(f"/v1/memory/records{qs}")
    items = payload if isinstance(payload, list) else payload.get("records", payload.get("results", []))
    items = items if isinstance(items, list) else []
    return table(items, columns=COLUMNS_RECORDS, keys=("records", "results"), default_label="no record")


def _vault_tree(rest):
    path = rest[0] if rest else ""
    qs = f"?path={path}" if path else ""
    return emit(api_get(f"/v1/memory/vault/tree{qs}"))


def _vault_file(rest):
    path = require_id(rest[0] if rest else "", name="path", command="memory", usage=USAGE)
    return emit(api_get(f"/v1/memory/vault/file?path={path}"))


def _vault_search(rest):
    q = " ".join(rest) if rest else ""
    from urllib.parse import quote
    return emit(api_get(f"/v1/memory/vault/search?q={quote(q)}"))


def _vault_backlinks(rest):
    path = require_id(rest[0] if rest else "", name="path", command="memory", usage=USAGE)
    return emit(api_get(f"/v1/memory/vault/backlinks?path={path}"))


def _vault_graph(rest):
    return emit(api_get("/v1/memory/vault/graph"))


def _vault_resolve(rest):
    path = require_id(rest[0] if rest else "", name="path", command="memory", usage=USAGE)
    return emit(api_get(f"/v1/memory/vault/resolve?path={path}"))


@register(
    "memory",
    group="core",
    description="Memoire Core (engineering memory) et historique CLI local",
    usage=USAGE,
)
def cmd_memory(args):
    # Local CLI history shortcuts (backward compat)
    if not args or args[0] == "recent":
        n = int(args[1]) if (len(args) > 1 and args[0] == "recent") else 8
        for e in mem_local.recent(n):
            print("  " + e["text"])
        return 0
    if args[0] == "frequent":
        n = int(args[1]) if len(args) > 1 else 5
        for e in mem_local.frequent(n):
            print("  " + e["text"] + "  x" + str(e["count"]))
        return 0

    verb, rest = subcommand(args, VERBS, command="memory", usage=USAGE)

    if verb == "health":
        return emit(api_get("/v1/memory/health"))
    if verb == "records":
        return _records(rest)
    if verb == "events":
        return _events(rest)
    if verb == "event":
        return _event(rest)
    if verb == "component-history":
        return _component_history(rest)
    if verb == "vault-tree":
        return _vault_tree(rest)
    if verb == "vault-file":
        return _vault_file(rest)
    if verb == "vault-backlinks":
        return _vault_backlinks(rest)
    if verb == "vault-resolve":
        return _vault_resolve(rest)
    if verb == "vault-search":
        return _vault_search(rest)
    if verb == "vault-graph":
        return _vault_graph(rest)
    if verb == "validate":
        # read JSON from stdin or args
        import json as _json
        import sys as _sys
        raw = _sys.stdin.read() if not rest else " ".join(rest)
        try:
            payload = _json.loads(raw)
        except Exception:
            raise usage_error("invalid JSON payload", hint=USAGE)
        return emit(api_post("/v1/memory/events/validate", payload))

    if verb == "record":
        import json as _json
        import sys as _sys
        raw = _sys.stdin.read() if not rest else " ".join(rest)
        try:
            payload = _json.loads(raw)
        except Exception:
            raise usage_error("invalid JSON payload", hint=USAGE)
        return emit(api_post("/v1/memory/events", payload))

    if verb == "vault-write":
        path = require_id(rest[0] if rest else "", name="path", command="memory", usage=USAGE)
        content = " ".join(rest[1:]) if len(rest) > 1 else ""
        return emit(api_post("/v1/memory/vault/file", {"path": path, "content": content}))

    raise usage_error(f"unknown memory subcommand: {verb}", hint=USAGE)
