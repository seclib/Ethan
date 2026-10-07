"""ETHAN model — LLM model catalogue and local installs.

Contract : docs/specs/CLI_CONTRACT.md §8.9.

Routes verified in `interfaces/api/routers/models.py` :

    GET  /models               registered models
    GET  /models/search        catalogue search (`info`/`show` below)
    GET  /models/installed     models present locally
    GET  /models/discover      discovery on the running runtime
    GET  /models/{id}
    POST /models/pull          download a model (async → operation)
    GET  /models/runtimes/health

The Core owns download, storage and the compatibility verdict; the CLI only
reports them. `info` is the documented alias of `show` (§2.1 canonical verb
kept). `-o json` passes the Core payload through untouched (§4.2).
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
from interfaces.cli.core.errors import usage_error
from interfaces.cli.registry import register

VERBS = {
    "list": "GET /models",
    "info": "GET /models/{id}",
    "show": "GET /models/{id}",
    "search": "GET /models/search",
    "installed": "GET /models/installed",
    "discover": "GET /models/discover",
    "runtimes": "GET /models/runtimes/health",
    "pull": "POST /models/pull",
}

USAGE = "ethan model <list|info|show|search|installed|discover|runtimes|pull> [args]"

COLUMNS = [
    ("ID", 44, "id"),
    ("NAME", 22, "name"),
    ("CONTEXT", 10, "context_length"),
    ("LOCAL", 8, "is_local"),
    ("PRIVATE", 9, "is_private"),
]

#: Envelope keys the Core may use for this listing.
KEYS = (
    "models",
    "items",
)


def _flag(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "—"


def _rows(payload):
    """Normalise a Core model payload into table rows."""
    if isinstance(payload, dict):
        payload = payload.get("models", payload.get("items", payload))
    if not isinstance(payload, list):
        return None
    return [
        [
            item.get("id") if isinstance(item, dict) else item,
            item.get("name") if isinstance(item, dict) else "",
            item.get("context_length") if isinstance(item, dict) else "",
            _flag(item.get("is_local")) if isinstance(item, dict) else "",
            _flag(item.get("is_private")) if isinstance(item, dict) else "",
        ]
        for item in payload
    ]


def _render_list(payload, *, empty_label: str = "no model") -> int:
    """Table when the payload is a list, raw emission otherwise."""
    rows = _rows(payload)
    if rows is None:
        return emit(payload)
    return table(payload, columns=COLUMNS, keys=KEYS, default_label=empty_label)


@register(
    "model",
    group="core",
    description="Browse Core models and pull local ones",
    usage=USAGE,
)
def cmd_model(args: list[str]) -> int:
    """Manage models through the Core API."""
    verb, rest = subcommand(args, VERBS, command="model", usage=USAGE, default="list")

    if verb in ("list", "installed", "discover"):
        path = "/models" if verb == "list" else f"/models/{verb}"
        return _render_list(api_get(path))

    if verb == "search":
        if not rest:
            raise usage_error("missing <query>", hint="usage: ethan model search <query>")
        from urllib.parse import quote

        return _render_list(api_get(f"/models/search?q={quote(rest[0])}"), empty_label="no match")

    if verb == "runtimes":
        return emit(api_get("/models/runtimes/health"))

    if verb in ("show", "info"):
        model_id = require_id(rest[0] if rest else "", name="id", command="model", usage=USAGE)
        return emit(api_get(f"/models/{model_id}"))

    if verb == "pull":
        model_id = require_id(rest[0] if rest else "", name="id", command="model", usage=USAGE)
        return emit(api_post("/models/pull", {"model_id": model_id}))

    raise usage_error(f"unsupported verb: {verb}", hint=f"usage: {USAGE}")
