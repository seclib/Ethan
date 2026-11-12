"""Client TUI ETHAN — projection typée des contrats Core.

Ce module est la **seule** frontière HTTP utilisée par le TUI. Il ne
réimplémente aucun agent, modèle, outil, session ou permission : il ne fait
que lire et envoyer les données du Core via `interfaces.cli.core.client`
(`request_json`, `stream_sse`), puis les projeter dans les dataclasses de
`interfaces.cli.tui.models`.

Toute erreur de transport est propagée sous forme de `CLIError` (mêmes
codes de retour que le CLI, contrat §5).
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Iterator

from interfaces.cli.core.client import get_timeout, request_json, stream_sse
from interfaces.cli.core.errors import CLIError
from interfaces.cli.tui.models import (
    Agent,
    ApprovalItem,
    ChatMessage,
    ChatSummary,
    DoneEvent,
    ErrorEvent,
    JSONValue,
    PermissionRequestEvent,
    PermissionResolvedEvent,
    Model,
    Provider,
    StreamError,
    StreamEvent,
    Tool,
    ToolCallEvent,
    ToolResultEvent,
    ContentEvent,
    ContentReplaceEvent,
)


# ── Helpers de projection ──────────────────────────────────────────────


def _as_dict(value: object) -> dict[str, JSONValue]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, JSONValue] = {}
    for key, item in value.items():
        result[str(key)] = item  # type: ignore[assignment]
    return result


def _as_list(value: object) -> list[JSONValue]:
    if not isinstance(value, list):
        return []
    return list(value)


def _as_str(value: object, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _as_int(value: object, default: int = 0) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _as_bool(value: object, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _extract_list(payload: object, keys: tuple[str, ...]) -> list[JSONValue]:
    """Extrait une liste depuis un payload Core (liste nue ou enveloppe)."""
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return list(value)
    return []


def _parse_agent(raw: JSONValue) -> Agent:
    data = _as_dict(raw)
    return Agent(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")) or _as_str(data.get("id")),
        description=_as_str(data.get("description")),
        model=_as_str(data.get("model")),
        provider=_as_str(data.get("provider")),
        status=_as_str(data.get("status")),
        tool_ids=tuple(_as_str(item) for item in _as_list(data.get("tool_ids"))),
        skill_ids=tuple(_as_str(item) for item in _as_list(data.get("skill_ids"))),
    )


def _parse_model(raw: JSONValue) -> Model:
    data = _as_dict(raw)
    return Model(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")) or _as_str(data.get("id")),
        provider=_as_str(data.get("provider")),
        context_length=_as_int(data.get("context_length")),
        is_available=_as_bool(data.get("is_available"), True),
        capabilities=tuple(_as_str(item) for item in _as_list(data.get("capabilities"))),
    )


def _parse_provider(raw: JSONValue) -> Provider:
    data = _as_dict(raw)
    return Provider(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")) or _as_str(data.get("id")),
        type=_as_str(data.get("type")),
        enabled=_as_bool(data.get("enabled")),
        status=_as_str(data.get("status")),
        is_default=_as_bool(data.get("is_default")),
        default_model=_as_str(data.get("default_model")),
        models=tuple(_as_str(item) for item in _as_list(data.get("models"))),
    )


def _parse_tool(raw: JSONValue) -> Tool:
    data = _as_dict(raw)
    return Tool(
        id=_as_str(data.get("id")),
        name=_as_str(data.get("name")) or _as_str(data.get("id")),
        description=_as_str(data.get("description")),
        category=_as_str(data.get("category")),
        provider=_as_str(data.get("provider")),
        risk_level=_as_str(data.get("risk_level"), "low"),
        is_available=_as_bool(data.get("is_available"), True),
        parameters=_as_dict(data.get("parameters")),
    )


def _parse_chat_summary(raw: JSONValue) -> ChatSummary:
    data = _as_dict(raw)
    messages = _as_list(data.get("messages"))
    return ChatSummary(
        id=_as_str(data.get("id")),
        title=_as_str(data.get("title")),
        updated_at=_as_str(data.get("updated_at")),
        created_at=_as_str(data.get("created_at")),
        message_count=len(messages),
    )


def _parse_chat_message(raw: JSONValue) -> ChatMessage:
    data = _as_dict(raw)
    return ChatMessage(
        id=_as_str(data.get("id")),
        role=_as_str(data.get("role")),
        content=_as_str(data.get("content")) or _as_str(data.get("message")),
        created_at=_as_str(data.get("created_at")),
        status=_as_str(data.get("status")),
        tool_calls=tuple(_as_list(data.get("tool_calls"))),
    )


def _parse_approval(raw: JSONValue, kind: str) -> ApprovalItem | None:
    data = _as_dict(raw)
    item_id = _as_str(data.get("id")) or _as_str(data.get("approval_id")) or _as_str(data.get("request_id"))
    if not item_id:
        return None
    title = _as_str(data.get("title")) or _as_str(data.get("operation")) or _as_str(data.get("summary"))
    return ApprovalItem(
        id=item_id,
        kind=kind,
        title=title or item_id,
        category=_as_str(data.get("category")),
        description=_as_str(data.get("description")),
        status=_as_str(data.get("status")),
        source=_as_str(data.get("source")),
        requester=_as_str(data.get("requester")) or _as_str(data.get("source_id")),
        expires_at=_as_str(data.get("expires_at")),
        details=_as_dict(data.get("details")) or _as_dict(data.get("parameters")),
    )


def parse_stream_event(raw: object) -> StreamEvent | None:
    """Projette un événement SSE Core en dataclass typée (ou None si inconnu)."""
    data = _as_dict(raw)
    etype = _as_str(data.get("type"))
    chat_id_raw = data.get("chat_id")
    chat_id = chat_id_raw if isinstance(chat_id_raw, str) else None

    if etype == "content":
        return ContentEvent(type=etype, chat_id=chat_id, content=_as_str(data.get("content")))
    if etype == "content_replace":
        return ContentReplaceEvent(type=etype, chat_id=chat_id, content=_as_str(data.get("content")))
    if etype == "tool_call":
        params = _as_dict(data.get("params"))
        return ToolCallEvent(type=etype, chat_id=chat_id, tool=_as_str(data.get("tool")), params=params)
    if etype == "tool_result":
        return ToolResultEvent(
            type=etype,
            chat_id=chat_id,
            tool=_as_str(data.get("tool")),
            status=_as_str(data.get("status")),
            output=_as_str(data.get("output")),
        )
    if etype == "done":
        mid_raw = data.get("message_id")
        message_id = mid_raw if isinstance(mid_raw, str) else None
        return DoneEvent(type=etype, chat_id=chat_id, message_id=message_id)
    if etype == "error":
        return ErrorEvent(type=etype, error=_as_str(data.get("error")))
    if etype == "permission_request":
        try:
            timeout_val = int(data.get("timeout_seconds", 300))
        except (TypeError, ValueError):
            timeout_val = 300
        return PermissionRequestEvent(
            type=etype,
            chat_id=chat_id,
            request_id=_as_str(data.get("request_id")),
            tool=_as_str(data.get("tool")),
            params=_as_dict(data.get("params")),
            reason=_as_str(data.get("reason")),
            timeout_seconds=timeout_val,
        )
    if etype == "permission_resolved":
        return PermissionResolvedEvent(
            type=etype,
            chat_id=chat_id,
            request_id=_as_str(data.get("request_id")),
            tool=_as_str(data.get("tool")),
            approved=bool(data.get("approved", False)),
        )
    return None


# ── Client ─────────────────────────────────────────────────────────────


class TuiCoreClient:
    """Client TUI : lit et envoie les données Core via la frontière HTTP unique."""

    def __init__(self, *, timeout: float | None = None, abort_event: threading.Event | None = None) -> None:
        self._timeout = timeout if timeout is not None else get_timeout(default=120.0)
        self._abort = abort_event if abort_event is not None else threading.Event()

    # ── Santé ─────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """True si le Core répond sur /v1/version (lecture seule, sans auth)."""
        try:
            payload = request_json("GET", "/v1/version", timeout=2.0)
            return isinstance(payload, dict)
        except CLIError:
            return False
        except Exception:  # noqa: BLE001 — toute erreur réseau = indisponible
            return False

    def get_state(self) -> dict[str, JSONValue]:
        try:
            payload = request_json("GET", "/v1/state", timeout=self._timeout)
            return _as_dict(payload)
        except CLIError:
            return {}

    # ── Agents ─────────────────────────────────────────────────────────

    def list_agents(self) -> list[Agent]:
        payload = request_json("GET", "/v1/agents", timeout=self._timeout)
        return [_parse_agent(item) for item in _extract_list(payload, ("agents", "items"))]

    # ── Modèles ────────────────────────────────────────────────────────

    def list_models(self) -> list[Model]:
        payload = request_json("GET", "/models", timeout=self._timeout)
        return [_parse_model(item) for item in _extract_list(payload, ("models", "items"))]

    # ── Providers ──────────────────────────────────────────────────────

    def list_providers(self) -> list[Provider]:
        payload = request_json("GET", "/providers", timeout=self._timeout)
        return [_parse_provider(item) for item in _extract_list(payload, ("providers", "items"))]

    # ── Outils ─────────────────────────────────────────────────────────

    def list_tools(self) -> list[Tool]:
        payload = request_json("GET", "/v1/tools", timeout=self._timeout)
        return [_parse_tool(item) for item in _extract_list(payload, ("tools", "items"))]

    # ── Conversations ──────────────────────────────────────────────────

    def list_chats(self) -> list[ChatSummary]:
        payload = request_json("GET", "/chats", timeout=self._timeout)
        return [_parse_chat_summary(item) for item in _extract_list(payload, ("chats", "items"))]

    def get_chat_messages(self, chat_id: str) -> list[ChatMessage]:
        payload = request_json("GET", f"/chats/{chat_id}/messages", timeout=self._timeout)
        return [_parse_chat_message(item) for item in _extract_list(payload, ("messages", "items"))]

    def create_chat(self, title: str) -> ChatSummary:
        payload = request_json("POST", "/chats", {"title": title}, timeout=self._timeout)
        data = _as_dict(payload)
        if not _as_str(data.get("id")):
            # Fallback : le Core renvoie parfois l'enveloppe complète.
            return _parse_chat_summary(payload)  # type: ignore[arg-type]
        return _parse_chat_summary(payload)  # type: ignore[arg-type]

    # ── HROT / approbations ────────────────────────────────────────────

    def list_pending_approvals(self) -> list[ApprovalItem]:
        try:
            payload = request_json("GET", "/internal/approval/pending", timeout=self._timeout)
        except CLIError:
            return []
        items = _extract_list(payload, ("pending", "items"))
        result: list[ApprovalItem] = []
        for item in items:
            parsed = _parse_approval(item, "approval")
            if parsed is not None:
                result.append(parsed)
        return result

    def resolve_approval(self, request_id: str, approved: bool, reason: str = "") -> bool:
        try:
            request_json(
                "POST",
                "/internal/approval/resolve",
                {"request_id": request_id, "approved": approved, "reason": reason},
                timeout=self._timeout,
            )
            return True
        except CLIError:
            return False

    def list_pending_hrot(self) -> list[ApprovalItem]:
        try:
            payload = request_json("GET", "/internal/hrot/pending", timeout=self._timeout)
        except CLIError:
            return []
        items = _extract_list(payload, ("pending", "items"))
        result: list[ApprovalItem] = []
        for item in items:
            parsed = _parse_approval(item, "hrot")
            if parsed is not None:
                result.append(parsed)
        return result

    def resolve_hrot(self, approval_id: str, approved: bool, reason: str = "") -> bool:
        try:
            request_json(
                "POST",
                f"/internal/hrot/requests/{approval_id}/resolve",
                {"approved": approved, "reason": reason},
                timeout=self._timeout,
            )
            return True
        except CLIError:
            return False

    # ── Flux ───────────────────────────────────────────────────────────

    def send_stream(self, payload: dict[str, JSONValue]) -> Iterator[StreamEvent]:
        """Consomme le flux SSE Core et projette chaque événement."""
        for raw in stream_sse(
            "/v1/chat/completions/stream",
            payload,
            timeout=self._timeout,
            abort_event=self._abort,
        ):
            event = parse_stream_event(raw)
            if event is not None:
                yield event

    def abort_stream(self) -> None:
        """Signale l'arrêt du flux en cours."""
        self._abort.set()

    def reset_abort(self) -> None:
        """Réarme le signal d'arrêt."""
        self._abort.clear()


def run_stream_worker(
    client: TuiCoreClient,
    payload: dict[str, JSONValue],
    queue_: "queue.Queue[StreamEvent | StreamError | None]",
) -> None:
    """Thread worker : pousse les événements de flux dans une file."""

    try:
        for event in client.send_stream(payload):
            queue_.put(event)
    except CLIError as err:
        queue_.put(StreamError(message=str(err), exit_code=err.exit_code, status=err.status))
    except Exception as err:  # noqa: BLE001 — le TUI doit survivre
        queue_.put(StreamError(message=str(err)))
    finally:
        queue_.put(None)


__all__ = [
    "TuiCoreClient",
    "run_stream_worker",
]
