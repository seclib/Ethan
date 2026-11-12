"""ETHAN application — Core application catalogue, registry and runtime.

Thin pass-through to the Core application routes (verified in
`interfaces/api/routers/applications.py`) :

    GET    /applications
    GET    /applications/{app_id}
    POST   /applications/refresh
    GET    /applications/registered
    GET    /applications/{app_id}/runtime
    POST   /applications/{app_id}/start
    POST   /applications/{app_id}/stop
    GET    /application-capabilities
    GET    /application-integration/catalog
    GET    /application-manifests

The CLI invents nothing: discovery, validation and runtime control stay in
the Core (ApplicationManager / `_application_runtime_service`).
"""

from __future__ import annotations

from interfaces.cli.core.api import (
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
    "list": "GET /applications",
    "show": "GET /applications/{app_id}",
    "refresh": "POST /applications/refresh",
    "registered": "GET /applications/registered",
    "runtime": "GET /applications/{app_id}/runtime",
    "start": "POST /applications/{app_id}/start",
    "stop": "POST /applications/{app_id}/stop",
    "capabilities": "GET /application-capabilities",
    "catalog": "GET /application-integration/catalog",
    "validate": "POST /application-capabilities/validate",
    "register": "POST /application-capabilities",
    "bind": "POST /application-capabilities/{capability_id}/bind",
    "activate": "POST /application-capabilities/{capability_id}/activate",
    "invoke": "POST /application-capabilities/{capability_id}/invoke",
    "manifests": "GET /application-manifests",
}

USAGE = "ethan application <list|show|refresh|registered|runtime|start|stop|capabilities|catalog|manifests> [args]"

COLUMNS = [
    ("APP_ID", 24, "app_id"),
    ("SOURCE", 14, "source"),
    ("VALIDATED", 10, "validated"),
    ("INSTANCE", 20, "instance_id"),
]

KEYS = ("applications",)


def _show(rest: list[str]) -> int:
    app_id = require_id(rest[0] if rest else "", name="app_id", command="application", usage=USAGE)
    return emit(api_get(f"/v1/applications/{app_id}"))


def _runtime(rest: list[str]) -> int:
    app_id = require_id(rest[0] if rest else "", name="app_id", command="application", usage=USAGE)
    return emit(api_get(f"/v1/applications/{app_id}/runtime"))


def _start(rest: list[str]) -> int:
    app_id = require_id(rest[0] if rest else "", name="app_id", command="application", usage=USAGE)
    return emit(api_post(f"/v1/applications/{app_id}/start", timeout=30.0))


def _stop(rest: list[str]) -> int:
    app_id = require_id(rest[0] if rest else "", name="app_id", command="application", usage=USAGE)
    return emit(api_post(f"/v1/applications/{app_id}/stop", timeout=30.0))


@register(
    "application",
    group="core",
    description="Gerer le catalogue et le runtime des applications ETHAN",
    usage=USAGE,
)
def cmd_application(args: list[str]) -> int:
    verb, rest = subcommand(args, VERBS, command="application", usage=USAGE, default="list")

    if verb == "list":
        payload = api_get("/v1/applications")
        items = payload if isinstance(payload, list) else payload.get("applications", payload.get("items", []))
        return table(items, columns=COLUMNS, keys=KEYS, default_label="no application")

    if verb == "show":
        return _show(rest)

    if verb == "refresh":
        return emit(api_post("/v1/applications/refresh"))

    if verb == "registered":
        payload = api_get("/v1/applications/registered")
        items = payload if isinstance(payload, list) else payload.get("applications", payload.get("items", []))
        return table(items, columns=COLUMNS, keys=KEYS, default_label="no registered application")

    if verb == "runtime":
        return _runtime(rest)

    if verb == "start":
        return _start(rest)

    if verb == "stop":
        return _stop(rest)

    if verb == "capabilities":
        payload = api_get("/v1/application-capabilities")
        items = payload if isinstance(payload, list) else payload.get("capabilities", payload.get("items", []))
        return emit(items)

    if verb == "catalog":
        return emit(api_get("/v1/application-integration/catalog"))

    if verb == "manifests":
        return emit(api_get("/v1/application-manifests"))

    if verb == "validate":
        import json as _json
        import sys as _sys
        raw = _sys.stdin.read() if not rest else " ".join(rest)
        try:
            payload = _json.loads(raw)
        except Exception:
            raise usage_error("invalid JSON payload", hint=USAGE)
        return emit(api_post("/v1/application-capabilities/validate", payload))

    if verb == "register":
        import json as _json
        import sys as _sys
        raw = _sys.stdin.read() if not rest else " ".join(rest)
        try:
            payload = _json.loads(raw)
        except Exception:
            raise usage_error("invalid JSON payload", hint=USAGE)
        if not isinstance(payload, dict):
            raise usage_error("payload must be a JSON object", hint=USAGE)
        payload.setdefault("approved", True)
        return emit(api_post("/v1/application-capabilities", payload))

    if verb == "bind":
        cap_id = require_id(rest[0] if rest else "", name="capability_id", command="application", usage=USAGE)
        app_id = None
        alias = ""
        approved = False
        activated = False
        i = 1
        while i < len(rest):
            if rest[i] == "--app" and i + 1 < len(rest):
                app_id = rest[i + 1]
                i += 2
                continue
            if rest[i] == "--alias" and i + 1 < len(rest):
                alias = rest[i + 1]
                i += 2
                continue
            if rest[i] == "--approved":
                approved = True
                i += 1
                continue
            if rest[i] == "--activate":
                activated = True
                i += 1
                continue
            i += 1
        if not app_id:
            raise usage_error("missing --app <app_id>", hint=USAGE)
        body = {"application_id": app_id, "implementation_alias": alias, "approved": approved, "activated": activated}
        return emit(api_post(f"/v1/application-capabilities/{cap_id}/bind", body))

    if verb == "activate":
        cap_id = require_id(rest[0] if rest else "", name="capability_id", command="application", usage=USAGE)
        app_id = None
        activated = True
        i = 1
        while i < len(rest):
            if rest[i] == "--app" and i + 1 < len(rest):
                app_id = rest[i + 1]
                i += 2
                continue
            if rest[i] == "--deactivate":
                activated = False
                i += 1
                continue
            i += 1
        if not app_id:
            raise usage_error("missing --app <app_id>", hint=USAGE)
        body = {"application_id": app_id, "activated": activated}
        return emit(api_post(f"/v1/application-capabilities/{cap_id}/activate", body))

    if verb == "invoke":
        cap_id = require_id(rest[0] if rest else "", name="capability_id", command="application", usage=USAGE)
        app_id = None
        payload = {}
        i = 1
        while i < len(rest):
            if rest[i] == "--app" and i + 1 < len(rest):
                app_id = rest[i + 1]
                i += 2
                continue
            if rest[i].startswith("--"):
                key = rest[i].lstrip("-")
                if i + 1 < len(rest):
                    payload[key] = rest[i + 1]
                    i += 2
                    continue
            i += 1
        if not app_id:
            raise usage_error("missing --app <app_id>", hint=USAGE)
        body = {"application_id": app_id, **payload}
        return emit(api_post(f"/v1/application-capabilities/{cap_id}/invoke", body))

    raise usage_error(f"unknown application subcommand: {verb}", hint=USAGE)
