"""ETHAN knowledge — Core knowledge graph and collections.

Contract : docs/specs/CLI_CONTRACT.md §8.6.

Routes verified in `interfaces/api/routers/v1.py` :

    GET    /v1/knowledge
    POST   /v1/knowledge
    GET    /v1/knowledge/search
    GET    /v1/knowledge/{id}
    PUT    /v1/knowledge/{id}
    DELETE /v1/knowledge/{id}
    GET    /v1/knowledge/collections
    POST   /v1/knowledge/collections
    GET    /v1/knowledge/collections/{id}
    GET    /v1/knowledge/collections/{id}/documents
    POST   /v1/knowledge/collections/{id}/retrieve
    POST   /v1/knowledge/collections/{id}/reindex

The RAG pipeline and the embedding backend belong to the Core. This command
only queries and mutates them through their API.
"""

from __future__ import annotations

from urllib.parse import quote

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
    "list": "GET /v1/knowledge",
    "search": "GET /v1/knowledge/search",
    "show": "GET /v1/knowledge/{id}",
    "create": "POST /v1/knowledge",
    "update": "PUT /v1/knowledge/{id}",
    "delete": "DELETE /v1/knowledge/{id}",
    "collections": "GET /v1/knowledge/collections",
    "collection": "GET /v1/knowledge/collections/{id}",
    "collection-update": "PUT /v1/knowledge/collections/{id}",
    "collection-move": "POST /v1/knowledge/collections/{id}/move",
    "collection-delete": "DELETE /v1/knowledge/collections/{id}",
    "documents": "GET /v1/knowledge/collections/{id}/documents",
    "document-add": "POST /v1/knowledge/collections/{id}/documents",
    "document-delete": "DELETE /v1/knowledge/collections/{id}/documents/{doc_id}",
    "retrieve": "POST /v1/knowledge/collections/{id}/retrieve",
    "retrieve-multi": "POST /v1/knowledge/collections/retrieve-multi",
    "reindex": "POST /v1/knowledge/collections/{id}/reindex",
    "connect": "POST /v1/knowledge/{id}/connections",
    "import-status": "GET /v1/knowledge/imports/{job_id}",
}

USAGE = "ethan knowledge <list|search|show|create|update|delete|collections|collection|collection-update|collection-move|collection-delete|documents|document-add|document-delete|retrieve|retrieve-multi|reindex|connect|import|import-status> [args]"

KNOWLEDGE_COLUMNS = [
    ("ID", 32, "id"),
    ("LABEL", 28, "label"),
    ("TYPE", 14, "type"),
]

#: Envelope keys the Core may use for each listing.
KEYS = ("knowledge", "items")
COLLECTION_KEYS = ("collections", "items")
DOCUMENT_KEYS = ("documents", "items")

COLLECTION_COLUMNS = [
    ("ID", 32, "id"),
    ("NAME", 28, "name"),
    ("DOCUMENTS", 10, "document_count"),
]

DOCUMENT_COLUMNS = [
    ("ID", 36, "id"),
    ("TITLE", 30, "title"),
    ("CHUNKS", 8, "chunks"),
]


@register(
    "knowledge",
    group="core",
    description="Search and curate Core knowledge",
    usage=USAGE,
)
def cmd_knowledge(args: list[str]) -> int:
    """Manage Core knowledge through the API."""
    from interfaces.cli.core.context import get_context

    ctx = get_context()
    # `--json` stays accepted as an alias of `-o json` (§2.2).
    json_mode = ctx.is_json or "--json" in args

    verb, rest = subcommand(args, VERBS, command="knowledge", usage=USAGE, default="list")

    if verb == "list":
        payload = api_get("/v1/knowledge")
        return table(
            payload,
            columns=KNOWLEDGE_COLUMNS,
            keys=KEYS,
            default_label="no knowledge entry",
        )

    if verb == "search":
        query = " ".join(rest).strip()
        if not query:
            raise usage_error("missing <query>", hint="usage: ethan knowledge search <query>")
        return emit(api_get(f"/v1/knowledge/search?q={quote(query)}"))

    if verb == "create":
        if len(rest) < 2:
            raise usage_error(
                "missing <label>", hint="usage: ethan knowledge create <label> <content>"
            )
        return emit(api_post("/v1/knowledge", {"label": rest[0], "content": " ".join(rest[1:])}))

    if verb == "collections":
        payload = api_get("/v1/knowledge/collections")
        return table(
            payload,
            columns=COLLECTION_COLUMNS,
            keys=COLLECTION_KEYS,
            default_label="no collection",
        )

    knowledge_id = require_id(rest[0] if rest else "", name="id", command="knowledge", usage=USAGE)

    if verb == "show":
        return emit(api_get(f"/v1/knowledge/{knowledge_id}"))

    if verb == "update":
        if len(rest) < 2:
            raise usage_error(
                "missing <field=value>",
                hint="usage: ethan knowledge update <id> <field=value>",
            )
        body: dict = {}
        for pair in rest[1:]:
            key, sep, value = pair.partition("=")
            if not sep:
                raise usage_error(
                    f"invalid field assignment: {pair!r}", hint="expected <field=value>"
                )
            body[key] = value
        return emit(api_put(f"/v1/knowledge/{knowledge_id}", body))

    if verb == "delete":
        return emit(api_delete(f"/v1/knowledge/{knowledge_id}"))

    if verb == "collection":
        return emit(api_get(f"/v1/knowledge/collections/{knowledge_id}"))

    if verb == "documents":
        payload = api_get(f"/v1/knowledge/collections/{knowledge_id}/documents")
        return table(
            payload,
            columns=DOCUMENT_COLUMNS,
            keys=DOCUMENT_KEYS,
            default_label="no document",
        )

    if verb == "retrieve":
        if len(rest) < 2:
            raise usage_error(
                "missing <query>",
                hint="usage: ethan knowledge retrieve <collection-id> <query>",
            )
        return emit(
            api_post(
                f"/v1/knowledge/collections/{knowledge_id}/retrieve",
                {"query": " ".join(rest[1:])},
            )
        )

    if verb == "reindex":
        return emit(api_post(f"/v1/knowledge/collections/{knowledge_id}/reindex", {}))

    if verb == "collection-update":
        if len(rest) < 2:
            raise usage_error("missing <field=value>", hint=USAGE)
        body = {}
        for pair in rest[1:]:
            key, sep, value = pair.partition("=")
            if not sep:
                raise usage_error(f"invalid field assignment: {pair!r}", hint="expected <field=value>")
            body[key] = value
        return emit(api_put(f"/v1/knowledge/collections/{knowledge_id}", body))

    if verb == "collection-move":
        target = require_id(rest[1] if len(rest) > 1 else "", name="target_collection", command="knowledge", usage=USAGE)
        return emit(api_post(f"/v1/knowledge/collections/{knowledge_id}/move", {"target": target}))

    if verb == "collection-delete":
        return emit(api_delete(f"/v1/knowledge/{knowledge_id}"))

    if verb == "document-add":
        if len(rest) < 2:
            raise usage_error("missing <title>", hint="usage: ethan knowledge document-add <collection-id> <title> [content]")
        title = rest[1]
        content = " ".join(rest[2:]) if len(rest) > 2 else ""
        return emit(api_post(f"/v1/knowledge/collections/{knowledge_id}/documents", {"title": title, "content": content}))

    if verb == "document-delete":
        doc_id = require_id(rest[1] if len(rest) > 1 else "", name="doc_id", command="knowledge", usage=USAGE)
        return emit(api_delete(f"/v1/knowledge/collections/{knowledge_id}/documents/{doc_id}"))

    if verb == "retrieve-multi":
        body = {"query": " ".join(rest)} if rest else {}
        return emit(api_post("/v1/knowledge/collections/retrieve-multi", body))

    if verb == "connect":
        if len(rest) < 2:
            raise usage_error("missing <target_id>", hint="usage: ethan knowledge connect <id> <target_id>")
        return emit(api_post(f"/v1/knowledge/{knowledge_id}/connections", {"target_id": rest[1]}))

    if verb == "import-status":
        job_id = require_id(rest[0] if rest else "", name="job_id", command="knowledge", usage=USAGE)
        return emit(api_get(f"/v1/knowledge/imports/{job_id}"))

    raise usage_error(f"unsupported verb: {verb}", hint=f"usage: {USAGE}")