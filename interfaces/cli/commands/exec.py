"""ETHAN exec — request a controlled local system command from the Core.

This command never invokes a host executable itself.  It creates an operation
through the Core API, displays its human-approval scope, and only renders the
result the Core returns.  This keeps ``ollama list`` distinct from an ETHAN
domain command such as ``ethan model list``.
"""

from __future__ import annotations

import sys
import time

from interfaces.cli.core.api import api_get, api_post, emit
from interfaces.cli.core.context import get_context
from interfaces.cli.core.errors import CLIError, usage_error
from interfaces.cli.core.exit_codes import ExitCode
from interfaces.cli.registry import register

USAGE = "ethan exec <catalogue|pending|approve|cancel|command> [args] [--cwd DIR] [--no-wait]"
POLL_SECONDS = 0.25
TERMINAL = frozenset({"COMPLETED", "REFUSED", "TIMED_OUT", "CANCELLED", "ERROR"})


def _option(args: list[str], name: str) -> tuple[str | None, list[str]]:
    values = list(args)
    if name not in values:
        return None, values
    index = values.index(name)
    if index + 1 >= len(values):
        raise usage_error(f"option {name} requires a value", hint=f"usage: {USAGE}")
    value = values[index + 1]
    del values[index : index + 2]
    return value, values


def _wait(operation: dict) -> dict:
    operation_id = str(operation.get("id", ""))
    if not operation_id:
        raise CLIError("Core returned no operation id", code="CLI-EXEC")
    ctx = get_context()
    deadline = time.monotonic() + max(1.0, ctx.timeout)
    announced = False
    while str(operation.get("status", "")) not in TERMINAL:
        if not announced and not ctx.quiet:
            print(
                f"Awaiting human approval for {operation_id}. "
                "An administrator must review the command scope.",
                file=sys.stderr,
            )
            announced = True
        if time.monotonic() >= deadline:
            raise CLIError(
                f"operation {operation_id} is still pending",
                code="CLI-EXEC-WAIT",
                hint=f"check later: ethan exec operation {operation_id}",
                exit_code=int(ExitCode.TIMEOUT),
            )
        time.sleep(POLL_SECONDS)
        operation = api_get(f"/v1/system/exec/operations/{operation_id}")
    return operation


def _exit_code(operation: dict) -> int:
    status = str(operation.get("status", ""))
    if status == "COMPLETED":
        return int(
            ExitCode.SUCCESS if operation.get("exit_code") == 0 else ExitCode.OPERATION_FAILED
        )
    if status == "TIMED_OUT":
        return int(ExitCode.TIMEOUT)
    if status == "CANCELLED":
        return int(ExitCode.INTERRUPTED)
    return int(ExitCode.OPERATION_FAILED)


@register(
    "exec",
    group="system",
    description="Request an approved, non-shell local system command",
    usage=USAGE,
)
def cmd_exec(args: list[str]) -> int:
    """Use `ethan exec <tool> …`; only the Core may execute the tool."""
    if not args or args[0] in {"-h", "--help"}:
        print(USAGE)
        print("Examples: ethan exec ollama list | ethan exec git status --short")
        return int(ExitCode.SUCCESS)

    verb = args[0]
    if verb == "catalogue":
        return emit(api_get("/v1/system/exec/catalogue"))
    if verb == "pending":
        return emit(api_get("/internal/approval/pending"))
    if verb == "approve":
        if len(args) < 2:
            raise usage_error(
                "missing <approval-id>", hint="usage: ethan exec approve <approval-id>"
            )
        return emit(
            api_post("/internal/approval/resolve", {"request_id": args[1], "approved": True})
        )
    if verb == "reject":
        if len(args) < 2:
            raise usage_error(
                "missing <approval-id>", hint="usage: ethan exec reject <approval-id>"
            )
        return emit(
            api_post("/internal/approval/resolve", {"request_id": args[1], "approved": False})
        )
    if verb == "operation":
        if len(args) < 2:
            raise usage_error(
                "missing <operation-id>", hint="usage: ethan exec operation <operation-id>"
            )
        return emit(api_get(f"/v1/system/exec/operations/{args[1]}"))
    if verb == "cancel":
        if len(args) < 2:
            raise usage_error(
                "missing <operation-id>", hint="usage: ethan exec cancel <operation-id>"
            )
        return emit(api_post(f"/v1/system/exec/operations/{args[1]}/cancel", {}))

    cwd, command_args = _option(args[1:], "--cwd")
    no_wait = "--no-wait" in command_args
    command_args = [arg for arg in command_args if arg != "--no-wait"]
    ctx = get_context()
    operation = api_post(
        "/v1/system/exec/operations",
        {
            "command": verb,
            "args": command_args,
            "cwd": cwd,
            "timeout_seconds": ctx.timeout,
        },
    )
    if no_wait:
        return emit(operation)
    try:
        operation = _wait(operation)
    except KeyboardInterrupt:
        operation_id = operation.get("id") if isinstance(operation, dict) else None
        if operation_id:
            try:
                api_post(f"/v1/system/exec/operations/{operation_id}/cancel", {})
            except Exception as exc:  # noqa: BLE001 - main maps the original interrupt to 130
                get_context().debug(f"could not cancel interrupted operation: {exc}")
        raise
    emit(operation)
    return _exit_code(operation)
