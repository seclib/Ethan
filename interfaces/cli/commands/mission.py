"""ETHAN mission — long-running Core missions.

Contract : docs/specs/CLI_CONTRACT.md §8.4 (verbe canonique `mission`,
alias `missions`).

Routes verified in `interfaces/api/routers/v1.py` :

    GET    /v1/missions
    POST   /v1/missions
    GET    /v1/missions/{id}
    PUT    /v1/missions/{id}
    DELETE /v1/missions/{id}
    POST   /v1/missions/{id}/steps/{step}/verify
    POST   /v1/missions/{id}/steps/{step}/approve

The Planner, the steps and their verification belong to the Core. Step
verification and approval yield exit 0 for `verified`/`approved` and exit 1
otherwise (§8.4).
"""

from __future__ import annotations

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
    "list": "GET /v1/missions",
    "show": "GET /v1/missions/{id}",
    "create": "POST /v1/missions",
    "update": "PUT /v1/missions/{id}",
    "delete": "DELETE /v1/missions/{id}",
    "verify": "POST /v1/missions/{id}/steps/{step}/verify",
    "approve": "POST /v1/missions/{id}/steps/{step}/approve",
}

USAGE = "ethan mission <list|show|create|update|delete|verify|approve> [args]"

COLUMNS = [
    ("ID", 32, "id"),
    ("TITLE", 34, "title"),
    ("STATUS", 14, "status"),
]

#: Envelope keys the Core may use for this listing.
KEYS = ("missions",)

#: Core outcomes that make a verify/approve operation a success (§8.4).
_OK_OUTCOMES = frozenset({"verified", "approved", "ok", "success"})


def _status_of(item: dict) -> str:
    for field in ("status", "state"):
        if item.get(field):
            return str(item[field])
    return "unknown"


@register(
    "mission",
    group="core",
    description="Manage long-running Core missions",
    usage=USAGE,
)
def cmd_mission(args: list[str]) -> int:
    """Manage missions through the Core API."""
    verb, rest = subcommand(args, VERBS, command="mission", usage=USAGE, default="list")

    if verb == "list":
        payload = api_get("/v1/missions")
        return table(payload, columns=COLUMNS, keys=KEYS, default_label="no mission")

    if verb == "create":
        title = " ".join(rest).strip()
        if not title:
            raise usage_error("missing <title>", hint="usage: ethan mission create <title>")
        return emit(api_post("/v1/missions", {"title": title}))

    mission_id = require_id(rest[0] if rest else "", name="id", command="mission", usage=USAGE)

    if verb == "show":
        return emit(api_get(f"/v1/missions/{mission_id}"))

    if verb == "update":
        if len(rest) < 2:
            raise usage_error(
                "missing <field=value>",
                hint="usage: ethan mission update <id> <field=value>",
            )
        body: dict = {}
        for pair in rest[1:]:
            key, sep, value = pair.partition("=")
            if not sep:
                raise usage_error(
                    f"invalid field assignment: {pair!r}", hint="expected <field=value>"
                )
            body[key] = value
        return emit(api_put(f"/v1/missions/{mission_id}", body))

    if verb == "delete":
        return emit(api_delete(f"/v1/missions/{mission_id}"))

    step = require_id(
        rest[1] if len(rest) > 1 else "",
        name="step",
        command="mission",
        usage=f"ethan mission {verb} <mission-id> <step-id>",
    )
    payload = api_post(f"/v1/missions/{mission_id}/steps/{step}/{verb}", {})
    emit(payload)
    # The Core decides the outcome; a rejected step is an operation failure
    # (exit 1), not a CLI error (contract §8.4).
    outcome = None
    if isinstance(payload, dict):
        outcome = payload.get("result") or payload.get("outcome") or payload.get("status")
    if isinstance(outcome, str) and outcome.lower() not in _OK_OUTCOMES:
        return int(ExitCode.OPERATION_FAILED)
    return int(ExitCode.SUCCESS)


@register(
    "missions",
    group="core",
    description="Alias of 'mission'",
    usage=USAGE,
)
def cmd_missions(args: list[str]) -> int:
    """Alias kept for backward compatibility (§2.2)."""
    return cmd_mission(args)
