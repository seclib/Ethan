"""ETHAN document — Core RAG documents (alias `documents`).

Contract : docs/specs/CLI_CONTRACT.md §8.7 (verbe canonique `document`,
alias `documents`).

Routes verified in `interfaces/api/routers/v1.py` :

    GET    /v1/rag/documents
    POST   /v1/rag/documents
    GET    /v1/rag/documents/{id}
    DELETE /v1/rag/documents/{id}
    POST   /v1/rag/documents/from-file/{file_id}
    GET    /v1/rag/status
    GET    /v1/rag/config
    POST   /v1/rag/retrieve
    POST   /v1/rag/context

Ingestion, chunking, embeddings and retrieval strategies belong to the Core;
this command only calls them. `retrieve` is a query (read-only) while
`ingest` writes a document — the difference matters for `--yes` in scripts.
"""

from __future__ import annotations

from interfaces.cli.core.api import (
    api_delete,
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
    "list": "GET /v1/rag/documents",
    "status": "GET /v1/rag/status",
    "config": "GET /v1/rag/config",
    "show": "GET /v1/rag/documents/{id}",
    "ingest": "POST /v1/rag/documents",
    "delete": "DELETE /v1/rag/documents/{id}",
    "retrieve": "POST /v1/rag/retrieve",
    "context": "POST /v1/rag/context",
}

USAGE = "ethan document <list|status|config|show|ingest|delete|retrieve|context> [args]"

COLUMNS = [
    ("ID", 36, "id"),
    ("TITLE", 30, "title"),
    ("CHUNKS", 8, "chunks"),
    ("SOURCE", 16, "source"),
]

#: Envelope keys the Core may use for this listing.
KEYS = ("documents",)


@register(
    "document",
    group="core",
    description="Ingest and retrieve Core RAG documents",
    usage=USAGE,
)
def cmd_document(args: list[str]) -> int:
    """Manage RAG documents through the Core API."""
    verb, rest = subcommand(args, VERBS, command="document", usage=USAGE, default="list")

    if verb == "list":
        payload = api_get("/v1/rag/documents")
        return table(payload, columns=COLUMNS, keys=KEYS, default_label="no document")

    if verb in ("status", "config"):
        return emit(api_get(f"/v1/rag/{verb}"))

    if verb == "ingest":
        if len(rest) < 2:
            raise usage_error(
                "missing <title>",
                hint="usage: ethan document ingest <title> <content>",
            )
        return emit(
            api_post("/v1/rag/documents", {"title": rest[0], "content": " ".join(rest[1:])})
        )

    if verb in ("retrieve", "context"):
        query = " ".join(rest).strip()
        if not query:
            raise usage_error("missing <query>", hint=f"usage: ethan document {verb} <query>")
        return emit(api_post(f"/v1/rag/{verb}", {"query": query}))

    document_id = require_id(rest[0] if rest else "", name="id", command="document", usage=USAGE)
    if verb == "show":
        return emit(api_get(f"/v1/rag/documents/{document_id}"))
    return emit(api_delete(f"/v1/rag/documents/{document_id}"))


@register(
    "documents",
    group="core",
    description="Alias of 'document'",
    usage=USAGE,
)
def cmd_documents(args: list[str]) -> int:
    """Alias kept for backward compatibility (§2.2)."""
    return cmd_document(args)
