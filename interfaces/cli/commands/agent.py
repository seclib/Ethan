"""ETHAN agent — Core agent definitions and lifecycle.

Contract : docs/specs/CLI_CONTRACT.md §8.3 (verbe canonique `agent`,
alias `agents`).

Every verb is a thin pass-through to a Core route that already exists
(verified in `interfaces/api/routers/v1.py`) :

    GET    /v1/agents
    POST   /v1/agents
    GET    /v1/agents/{id}                 (`show`, alias documented `info`)
    GET    /v1/agents/{id}/resources
    PUT    /v1/agents/{id}
    DELETE /v1/agents/{id}
    POST   /v1/agents/{id}/execute         (`run`, alias `execute`)
    GET    /v1/agents/{id}/executions

`run` uses EXACTLY the same Core mechanism as the WebUI
(`interfaces/webui/src/lib/api/agents.ts`): `POST …/execute` with the
`task` body key. The Core owns agent state, capabilities and permissions
(an `AGENTS`/`EXECUTE` permission missing yields HTTP 403 → exit 4).
The CLI invents nothing.
"""

from __future__ import annotations

from pathlib import Path

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
from interfaces.cli.core.errors import CLIError, usage_error
from interfaces.cli.registry import register

VERBS = {
    "list": "GET /v1/agents",
    "show": "GET /v1/agents/{id}",
    "info": "GET /v1/agents/{id}",
    "create": "POST /v1/agents",
    "update": "PUT /v1/agents/{id}",
    "delete": "DELETE /v1/agents/{id}",
    "run": "POST /v1/agents/{id}/execute",
    "execute": "POST /v1/agents/{id}/execute",
    "resources": "GET /v1/agents/{id}/resources",
    "executions": "GET /v1/agents/{id}/executions",
}

USAGE = "ethan agent <list|info|show|create|update|delete|run|resources|executions> [args]"

COLUMNS = [
    ("ID", 28, "id"),
    ("NAME", 20, "name"),
    ("STATUS", 12, "status"),
    ("CAPABILITIES", 30, "capabilities"),
]

#: Envelope keys the Core may use for this listing.
KEYS = ("agents",)


def _status_of(item: dict) -> str:
    """Agent lifecycle state, read from whichever field Core exposes."""
    for field in ("status", "state"):
        if item.get(field):
            return str(item[field])
    return "unknown"


def _run(rest: list[str]) -> int:
    """`ethan agent run <id> --input <texte|@fichier>` (contract §8.3).

    Same Core route and body key (`task`) as the WebUI execution button
    (`interfaces/webui/src/lib/api/agents.ts`) — the CLI never executes
    an agent itself. `execute` remains a documented synonym (positional
    input accepted).
    """
    agent_id = require_id(rest[0] if rest else "", name="id", command="agent", usage=USAGE)
    tokens = rest[1:]

    inline: str | None = None
    words: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--input":
            if index + 1 >= len(tokens):
                raise usage_error(
                    "option --input requires a value",
                    hint="usage: ethan agent run <id> --input <texte|@fichier>",
                )
            inline = tokens[index + 1]
            index += 2
            continue
        if token.startswith("--input="):
            inline = token.partition("=")[2]
            index += 1
            continue
        if token in ("-h", "--help"):
            raise usage_error(f"usage: {USAGE}", hint="run 'ethan help' for details")
        if token.startswith("-") and token != "-":
            raise usage_error(f"unknown option: {token}", hint=f"usage: {USAGE}")
        words.append(token)
        index += 1

    source = inline if inline is not None else " ".join(words)
    if not source.strip():
        raise usage_error(
            "missing input",
            hint="usage: ethan agent run <id> --input <texte|@fichier>",
        )
    if source.startswith("@"):
        path = source[1:]
        try:
            source = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise CLIError(
                f"cannot read input file: {path}",
                code="CLI-INPUT",
                context=str(exc),
                hint="check the path and permissions",
                exit_code=int(ExitCode.OPERATION_FAILED),
            ) from exc
        if not source.strip():
            raise usage_error("input file is empty", hint=f"{path} holds no text")

    return emit(api_post(f"/v1/agents/{agent_id}/execute", {"task": source}))


@register(
    "agent",
    group="core",
    description="Manage Core agent definitions and lifecycle",
    usage=USAGE,
)
def cmd_agent(args: list[str]) -> int:
    """Manage agents through the Core API."""
    verb, rest = subcommand(args, VERBS, command="agent", usage=USAGE, default="list")

    if verb == "list":
        payload = api_get("/v1/agents")
        return table(payload, columns=COLUMNS, keys=KEYS, default_label="no agent")

    if verb in ("show", "info"):
        agent_id = require_id(rest[0] if rest else "", name="id", command="agent", usage=USAGE)
        return emit(api_get(f"/v1/agents/{agent_id}"))

    if verb == "create":
        if len(rest) < 2:
            raise usage_error("missing <name>", hint="usage: ethan agent create <name>")
        payload = api_post("/v1/agents", {"name": rest[0], "capabilities": rest[1:]})
        return emit(payload)

    if verb in ("run", "execute"):
        return _run(rest)

    if verb == "resources":
        agent_id = require_id(rest[0] if rest else "", name="id", command="agent", usage=USAGE)
        return emit(api_get(f"/v1/agents/{agent_id}/resources"))

    agent_id = require_id(rest[0] if rest else "", name="id", command="agent", usage=USAGE)

    if verb == "update":
        if len(rest) < 2:
            raise usage_error(
                "missing <field=value>", hint="usage: ethan agent update <id> <field=value>"
            )
        body: dict = {}
        for pair in rest[1:]:
            key, sep, value = pair.partition("=")
            if not sep:
                raise usage_error(
                    f"invalid field assignment: {pair!r}",
                    hint="expected <field=value>",
                )
            body[key] = value
        return emit(api_put(f"/v1/agents/{agent_id}", body))

    if verb == "delete":
        return emit(api_delete(f"/v1/agents/{agent_id}"))

    if verb == "executions":
        return emit(api_get(f"/v1/agents/{agent_id}/executions"))

    raise usage_error(f"unsupported verb: {verb}", hint=f"usage: {USAGE}")


@register(
    "agents",
    group="core",
    description="Alias of 'agent'",
    usage=USAGE,
)
def cmd_agents(args: list[str]) -> int:
    """Alias kept for backward compatibility (§2.2)."""
    return cmd_agent(args)


__all__ = ["ExitCode", "cmd_agent", "cmd_agents"]
