"""ETHAN skill — Core skill registry.

Contract : docs/specs/CLI_CONTRACT.md §8.5.

Routes verified in `interfaces/api/routers/v1.py` :

    GET    /v1/skills
    POST   /v1/skills
    GET    /v1/skills/search
    GET    /v1/skills/{id}
    PUT    /v1/skills/{id}
    DELETE /v1/skills/{id}
    POST   /v1/skills/{id}/toggle
    POST   /v1/skills/{id}/run

Skill execution belongs to the Core: the CLI forwards the input and prints
the returned result, it does not run the skill itself.
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
    "list": "GET /v1/skills",
    "search": "GET /v1/skills/search",
    "show": "GET /v1/skills/{id}",
    "create": "POST /v1/skills",
    "update": "PUT /v1/skills/{id}",
    "delete": "DELETE /v1/skills/{id}",
    "toggle": "POST /v1/skills/{id}/toggle",
    "run": "POST /v1/skills/{id}/run",
}

USAGE = "ethan skill <list|search|show|create|update|delete|toggle|run> [args]"

COLUMNS = [
    ("ID", 28, "id"),
    ("NAME", 22, "name"),
    ("ENABLED", 8, "enabled"),
    ("SOURCE", 14, "source"),
]

#: Envelope keys the Core may use for this listing.
KEYS = ("skills",)


def _flag(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "—"


@register(
    "skill",
    group="core",
    description="Manage Core skills",
    usage=USAGE,
)
def cmd_skill(args: list[str]) -> int:
    """Manage skills through the Core API."""
    verb, rest = subcommand(args, VERBS, command="skill", usage=USAGE, default="list")

    if verb == "list":
        payload = api_get("/v1/skills")
        return table(payload, columns=COLUMNS, keys=KEYS, default_label="no skill")

    if verb == "search":
        query = " ".join(rest).strip()
        if not query:
            raise usage_error("missing <query>", hint="usage: ethan skill search <query>")
        from urllib.parse import quote

        return emit(api_get(f"/v1/skills/search?q={quote(query)}"))

    if verb == "create":
        if len(rest) < 2:
            raise usage_error("missing <name>", hint="usage: ethan skill create <name>")
        return emit(api_post("/v1/skills", {"name": rest[0], "content": " ".join(rest[1:])}))

    skill_id = require_id(rest[0] if rest else "", name="id", command="skill", usage=USAGE)

    if verb == "show":
        return emit(api_get(f"/v1/skills/{skill_id}"))

    if verb == "update":
        if len(rest) < 2:
            raise usage_error(
                "missing <field=value>", hint="usage: ethan skill update <id> <field=value>"
            )
        body: dict = {}
        for pair in rest[1:]:
            key, sep, value = pair.partition("=")
            if not sep:
                raise usage_error(
                    f"invalid field assignment: {pair!r}", hint="expected <field=value>"
                )
            body[key] = value
        return emit(api_put(f"/v1/skills/{skill_id}", body))

    if verb == "delete":
        return emit(api_delete(f"/v1/skills/{skill_id}"))

    if verb == "toggle":
        return emit(api_post(f"/v1/skills/{skill_id}/toggle"))

    if verb == "run":
        if len(rest) < 2:
            raise usage_error("missing <input>", hint="usage: ethan skill run <id> <input>")
        return emit(api_post(f"/v1/skills/{skill_id}/run", {"input": " ".join(rest[1:])}))

    raise usage_error(f"unsupported verb: {verb}", hint=f"usage: {USAGE}")
