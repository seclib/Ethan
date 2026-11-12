"""ETHAN config — local CLI configuration and Core configuration domains.

Contract : docs/specs/CLI_CONTRACT.md §8.12.

Two clearly separated scopes, because they have two different owners:

- **local** : the CLI's own preferences (`~/.config/ethan/config.json`) —
  profiles, endpoint, timeout, output. Never holds a secret: tokens live in
  `credentials.json` (0600).
- **core**  : the ETHAN configuration domains owned by the Core
  (`GET /config`, `GET /config/schema`, `GET|PUT /config/{domain}`).

The CLI writes Core configuration ONLY through the Core API, and only for
domains the Core itself declares in its schema. It never edits a file inside
`core/`: the source of truth stays where it belongs (§6.1).
"""

from __future__ import annotations

from interfaces.cli.core.api import ExitCode, api_get, emit, subcommand
from interfaces.cli.core.config import (
    list_profiles,
    load as load_local,
    reset as reset_local,
    set_value as set_local_value,
)
from interfaces.cli.core.errors import usage_error
from interfaces.cli.registry import register

VERBS = {
    "list": "show the local CLI configuration",
    "get": "read a local configuration key",
    "set": "write a supported local configuration key",
    "reset": "restore the local defaults",
    "domains": "GET /config — Core configuration domains",
    "schema": "GET /config/schema — Core configuration schema",
    "core-get": "GET /config/{domain}",
    "core-set": "PUT /config/{domain}",
}

USAGE = "ethan config <list|get|set|reset|domains|schema|core-get|core-set> [args]"

#: Local keys the CLI officially supports (contract §8.12). Anything else is
#: refused: the CLI must not become a free-form editor of its own files.
SUPPORTED_LOCAL_KEYS = frozenset(
    {
        "api.base_url",
        "api.timeout",
        "output",
        "profile",
        "current_profile",
        "logging.max_entries",
        "plugins.user_dir",
        "plugins.enabled",
    }
)

#: Key fragments whose value must never be printed (§6.4).
SECRET_MARKERS = ("token", "api_key", "password", "credential", "secret")


def _is_secret(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in SECRET_MARKERS)


def _mask(value):
    """Recursively mask secret-looking values before printing."""
    if isinstance(value, dict):
        return {
            key: ("***" if _is_secret(str(key)) else _mask(item)) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_mask(item) for item in value]
    return value


def _dig(config: dict, dotted_key: str):
    """Read a dot-separated key from a nested dict."""
    current = config
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _core_domains(schema) -> set[str]:
    """Domain names the Core declares in its own schema."""
    if not isinstance(schema, dict):
        return set()
    properties = schema.get("properties")
    if isinstance(properties, dict):
        return set(properties)
    for value in schema.values():
        if isinstance(value, dict) and isinstance(value.get("properties"), dict):
            return set(value["properties"])
    return set(schema)


def _core_put(domain: str, body: dict):
    """PUT a Core configuration domain through the shared HTTP boundary."""
    from interfaces.cli.core.api import api_put

    return api_put(f"/config/{domain}", body)


@register(
    "config",
    group="system",
    description="Show or edit ETHAN configuration",
    usage=USAGE,
)
def cmd_config(args: list[str]) -> int:
    """Configure the CLI locally, or read/write Core domains."""
    verb, rest = subcommand(args, VERBS, command="config", usage=USAGE, default="list")

    # ── Local CLI configuration ───────────────────────────────────────────
    if verb == "list":
        return emit(
            {"local": _mask(load_local()), "profiles": list_profiles()},
        )

    if verb == "get":
        if not rest:
            raise usage_error("missing <key>", hint="usage: ethan config get <key>")
        key = rest[0]
        if _is_secret(key):
            # Reading a secret is refused outright, not masked and returned.
            raise usage_error(
                f"refusing to read the secret key '{key}'",
                hint="use 'ethan auth status' to inspect the current session",
            )
        value = _dig(load_local(), key)
        print("(not set)" if value is None else value)
        return int(ExitCode.SUCCESS)

    if verb == "set":
        if len(rest) < 2:
            raise usage_error("missing <value>", hint="usage: ethan config set <key> <value>")
        key, value = rest[0], rest[1]
        if key not in SUPPORTED_LOCAL_KEYS:
            raise usage_error(
                f"unsupported configuration key: '{key}'",
                hint=f"supported keys: {', '.join(sorted(SUPPORTED_LOCAL_KEYS))}",
            )
        set_local_value(key, value)
        print(f"config {key} = {value}")
        return int(ExitCode.SUCCESS)

    if verb == "reset":
        reset_local()
        print("config reset to defaults")
        return int(ExitCode.SUCCESS)

    # ── Core configuration (owned by the Core, reached through its API) ──
    if verb == "domains":
        return emit(api_get("/config"))

    if verb == "schema":
        return emit(api_get("/config/schema"))

    if verb == "core-get":
        if not rest:
            raise usage_error("missing <domain>", hint="usage: ethan config core-get <domain>")
        return emit(api_get(f"/config/{rest[0]}"))

    if verb == "core-set":
        if len(rest) < 3:
            raise usage_error(
                "missing <key=value>", hint="usage: ethan config core-set <domain> <key=value>"
            )
        domain = rest[0]
        body: dict = {}
        for pair in rest[1:]:
            key, sep, value = pair.partition("=")
            if not sep:
                raise usage_error(
                    f"invalid field assignment: {pair!r}", hint="expected <key=value>"
                )
            body[key] = value

        # The domain must exist in the Core schema: never invent one.
        domains = _core_domains(api_get("/config/schema"))
        if domains and domain not in domains:
            raise usage_error(
                f"unknown Core configuration domain: '{domain}'",
                hint=f"known domains: {', '.join(sorted(domains))}",
            )
        return emit(_core_put(domain, body))

    raise usage_error(f"unsupported verb: {verb}", hint=f"usage: {USAGE}")
