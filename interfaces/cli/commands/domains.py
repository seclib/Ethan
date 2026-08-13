"""CLI gateway for Core-owned agents, missions, knowledge and RAG documents."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from interfaces.cli.registry import register


def _request(method: str, path: str, payload: dict | None = None):
    """Call the public API boundary; never duplicate Core logic in the CLI."""
    base_url = os.environ.get("ETHAN_API", "http://localhost:8000").rstrip("/")
    headers = {"Accept": "application/json"}
    token = os.environ.get("ETHAN_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    request = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            message = json.loads(body).get("detail", body)
        except json.JSONDecodeError:
            message = body
        raise RuntimeError(f"API {exc.code}: {message}") from exc
    except URLError as exc:
        raise RuntimeError(f"ETHAN API unavailable: {exc.reason}") from exc


def _print(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


@register(
    "agents",
    description="Manage Core agent definitions and lifecycle",
    usage="ethan agents [list|create|start|pause|stop|executions]",
)
def cmd_agents(args: list[str]) -> int:
    """Manage agents through the Core HTTP gateway."""
    action = args[0] if args else "list"
    if action == "list":
        _print(_request("GET", "/v1/agents"))
    elif action == "create" and len(args) >= 2:
        _print(_request("POST", "/v1/agents", {"name": args[1], "capabilities": args[2:]}))
    elif action in {"start", "pause", "stop"} and len(args) == 2:
        status = {"start": "running", "pause": "paused", "stop": "stopped"}[action]
        _print(_request("PUT", f"/v1/agents/{args[1]}", {"status": status}))
    elif action == "executions" and len(args) == 2:
        _print(_request("GET", f"/v1/agents/{args[1]}/executions"))
    else:
        print("usage: ethan agents [list|create <name> [capability...]|start|pause|stop|executions <id>]")
        return 1
    return 0


@register(
    "missions",
    description="Manage long-running Core missions",
    usage="ethan missions [list|create|show|verify|approve]",
)
def cmd_missions(args: list[str]) -> int:
    """Manage missions through the Core HTTP gateway."""
    action = args[0] if args else "list"
    if action == "list":
        _print(_request("GET", "/v1/missions"))
    elif action == "create" and len(args) >= 2:
        _print(_request("POST", "/v1/missions", {"title": " ".join(args[1:])}))
    elif action == "show" and len(args) == 2:
        _print(_request("GET", f"/v1/missions/{args[1]}"))
    elif action in {"verify", "approve"} and len(args) == 3:
        _print(_request("POST", f"/v1/missions/{args[1]}/steps/{args[2]}/{action}"))
    else:
        print("usage: ethan missions [list|create <title>|show <id>|verify <mission> <step>|approve <mission> <step>]")
        return 1
    return 0


@register(
    "knowledge",
    description="Search and create persistent Core knowledge",
    usage="ethan knowledge [list|search|create]",
)
def cmd_knowledge(args: list[str]) -> int:
    """Manage the Core knowledge graph through the API boundary."""
    action = args[0] if args else "list"
    if action == "list":
        _print(_request("GET", "/v1/knowledge"))
    elif action == "search" and len(args) >= 2:
        from urllib.parse import quote

        _print(_request("GET", f"/v1/knowledge/search?q={quote(' '.join(args[1:]))}"))
    elif action == "create" and len(args) >= 2:
        _print(_request("POST", "/v1/knowledge", {"label": args[1], "content": " ".join(args[2:])}))
    else:
        print("usage: ethan knowledge [list|search <query>|create <label> [content]]")
        return 1
    return 0


@register(
    "documents",
    description="Ingest and retrieve Core RAG documents",
    usage="ethan documents [list|ingest|search|context]",
)
def cmd_documents(args: list[str]) -> int:
    """Use the RAG pipeline through its API boundary."""
    action = args[0] if args else "list"
    if action == "list":
        _print(_request("GET", "/v1/rag/documents"))
    elif action == "ingest" and len(args) >= 3:
        _print(
            _request(
                "POST",
                "/v1/rag/documents",
                {"title": args[1], "content": " ".join(args[2:])},
            )
        )
    elif action == "search" and len(args) >= 2:
        _print(_request("POST", "/v1/rag/retrieve", {"query": " ".join(args[1:])}))
    elif action == "context" and len(args) >= 2:
        _print(_request("POST", "/v1/rag/context", {"query": " ".join(args[1:])}))
    else:
        print("usage: ethan documents [list|ingest <title> <content>|search <query>|context <query>]")
        return 1
    return 0
