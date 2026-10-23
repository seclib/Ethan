"""ETHAN approval — Human Root of Trust approvals (ADMIN).

Routes (Core, interfaces/api/routers/internal.py) :

    GET  /internal/approval/pending
    POST /internal/approval/resolve

Le Core décide (ApprovalEngine + HumanRoot + audit) ; le CLI ne fait
qu'afficher et transmettre la décision humaine.
"""

from __future__ import annotations

from interfaces.cli.core.api import (
    ExitCode,
    api_get,
    api_post,
    emit,
    require_id,
    subcommand,
    table,
)
from interfaces.cli.registry import register

VERBS = {
    "pending": "GET /internal/approval/pending",
    "approve": "POST /internal/approval/resolve (approved=true)",
    "reject": "POST /internal/approval/resolve (approved=false)",
}

USAGE = "ethan approval <pending|approve|reject> [request_id] [--reason TEXT]"

COLUMNS = [
    ("REQUEST", 36, "request_id"),
    ("CATEGORY", 20, "category"),
    ("TITLE", 44, "title"),
]

KEYS = ("items", "approvals", "pending")


def _reason_of(args: list[str]) -> str:
    if "--reason" in args:
        idx = args.index("--reason")
        if idx + 1 < len(args):
            return args[idx + 1]
    return ""


@register(
    "approval",
    group="core",
    description="Review Human Root of Trust approvals",
    usage=USAGE,
)
def cmd_approval(args: list[str]) -> int:
    """Liste et résout les approbations HROT via l'API Core."""
    verb, rest = subcommand(args, VERBS, command="approval", usage=USAGE, default="pending")

    if verb == "pending":
        payload = api_get("/internal/approval/pending")
        return table(payload, columns=COLUMNS, keys=KEYS, default_label="no pending approval")

    request_id = require_id(
        rest[0] if rest and not rest[0].startswith("--") else "",
        name="request_id",
        command="approval",
        usage=f"ethan approval {verb} <request_id> [--reason TEXT]",
    )
    payload = api_post(
        "/internal/approval/resolve",
        {
            "request_id": request_id,
            "approved": verb == "approve",
            "reason": _reason_of(rest),
        },
    )
    emit(payload)
    resolved = payload.get("resolved") if isinstance(payload, dict) else None
    if resolved is False:
        return int(ExitCode.OPERATION_FAILED)
    return int(ExitCode.SUCCESS)
