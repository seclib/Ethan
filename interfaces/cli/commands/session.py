"""ETHAN session — Core chat sessions (list, show, create, update, delete, messages).

Thin pass-through to the Core chat/session routes (verified in
`interfaces/api/routers/domains.py`) :

    GET    /chats
    POST   /chats
    GET    /chats/{chat_id}
    PUT    /chats/{chat_id}
    DELETE /chats/{chat_id}
    GET    /chats/{chat_id}/messages
    POST   /chats/{chat_id}/messages
    POST   /chats/{chat_id}/share
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
from interfaces.cli.core.context import get_context
from interfaces.cli.core.errors import usage_error
from interfaces.cli.registry import register

VERBS = {
    "list": "GET /chats",
    "show": "GET /chats/{chat_id}",
    "create": "POST /chats",
    "update": "PUT /chats/{chat_id}",
    "delete": "DELETE /chats/{chat_id}",
    "messages": "GET /chats/{chat_id}/messages",
    "add": "POST /chats/{chat_id}/messages",
    "share": "POST /chats/{chat_id}/share",
}

USAGE = "ethan session <list|show|create|update|delete|messages|add|share> [args]"

COLUMNS = [
    ("ID", 30, "id"),
    ("TITLE", 30, "title"),
    ("UPDATED", 20, "updated_at"),
]

KEYS = ("chats",)


def cmd_session(args):
    from interfaces.cli.core.context import get_context

    ctx = get_context()
    # `--json` stays accepted as an alias of `-o json` (§2.2).
    json_mode = ctx.is_json or "--json" in args

    verb, rest = subcommand(args, VERBS, command="session", usage=USAGE, default="list")

    if verb == "list":
        params = {}
        i = 0
        while i < len(rest):
            if rest[i] == "--archived":
                params["archived"] = "true"
                i += 1
                continue
            if rest[i] == "--folder" and i + 1 < len(rest):
                params["folder_id"] = rest[i + 1]
                i += 2
                continue
            if rest[i] == "--project" and i + 1 < len(rest):
                params["project_id"] = rest[i + 1]
                i += 2
                continue
            if rest[i] == "--unassigned":
                params["unassigned"] = "true"
                i += 1
                continue
            i += 1
        payload = api_get("/chats", params=params if params else None)
        items = payload if isinstance(payload, list) else payload.get("chats", payload.get("items", []))
        if json_mode:
            return emit(items)
        return table(items, columns=COLUMNS, keys=KEYS, default_label="no session")

    if verb == "show":
        chat_id = require_id(rest[0] if rest else "", name="chat_id", command="session", usage=USAGE)
        return emit(api_get(f"/chats/{chat_id}"))

    if verb == "create":
        title = " ".join(rest) if rest else ""
        return emit(api_post("/chats", {"title": title}))

    if verb == "update":
        chat_id = require_id(rest[0] if rest else "", name="chat_id", command="session", usage=USAGE)
        title = " ".join(rest[1:]) if len(rest) > 1 else None
        payload = {}
        if title is not None:
            payload["title"] = title
        return emit(api_put(f"/chats/{chat_id}", payload))

    if verb == "delete":
        chat_id = require_id(rest[0] if rest else "", name="chat_id", command="session", usage=USAGE)
        return emit(api_delete(f"/chats/{chat_id}"))

    if verb == "messages":
        chat_id = require_id(rest[0] if rest else "", name="chat_id", command="session", usage=USAGE)
        return emit(api_get(f"/chats/{chat_id}/messages"))

    if verb == "add":
        chat_id = require_id(rest[0] if rest else "", name="chat_id", command="session", usage=USAGE)
        content = " ".join(rest[1:]) if len(rest) > 1 else ""
        role = "user"
        return emit(api_post(f"/chats/{chat_id}/messages", {"role": role, "content": content}))

    if verb == "share":
        chat_id = require_id(rest[0] if rest else "", name="chat_id", command="session", usage=USAGE)
        return emit(api_post(f"/chats/{chat_id}/share"))

    raise usage_error(f"unknown session subcommand: {verb}", hint=USAGE)