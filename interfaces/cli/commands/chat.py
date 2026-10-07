"""ETHAN chat — conversation with ETHAN through the Core ChatPipeline.

Routes verified in `interfaces/api/routers/v1.py` :

    POST /v1/chat/completions          one-shot → un unique document JSON
    POST /v1/chat/completions/stream   streaming SSE (mode humain)
    GET  /v1/chat/history              `--resume` (dernière conversation)

C'est EXACTEMENT le mécanisme utilisé par le WebUI
(`interfaces/webui/src/lib/api/chat.ts`) : le CLI transmet `message`,
`model`, `provider_id`, `agent_id`, `chat_id` — la résolution du
modèle/provider/agent, l'historique et la génération appartiennent au
Core (ChatPipeline). Aucune logique LLM n'est implémentée ici (règle
AGENTS : l'affichant ne définit pas ETHAN).

Sorties (§4) : stdout ne porte que la réponse (ou exactement un document
JSON en `-o json`) ; bannière, invite, métadonnées et erreurs vont sur
stderr — le piping reste sûr.
"""

from __future__ import annotations

import json
import sys

from interfaces.cli.core.api import ExitCode, api_get, api_post, api_stream, emit
from interfaces.cli.core.client import get_timeout
from interfaces.cli.core.context import get_context
from interfaces.cli.core.errors import CLIError, format_cli_error, usage_error
from interfaces.cli.registry import register

USAGE = "ethan chat [options] [message…]"

#: Sans `--timeout` explicite, une génération LLM a besoin d'un délai
#: réaliste : le contrat §3.1 (5 s) reste le défaut des appels CRUD, mais
#: chat parle à un modèle — un deadline délibéré (CLI/env/profil) prime.
LLM_TIMEOUT = 120.0

#: Options qui portent une valeur.
_VALUE_OPTS = ("--model", "--provider", "--agent", "--chat-id", "--session")
_OPT_KEYS = {
    "--model": "model",
    "--provider": "provider",
    "--agent": "agent",
    "--chat-id": "chat_id",
    "--session": "chat_id",
}


def _parse(args: list[str]) -> tuple[dict, list[str]]:
    """Split argv into chat options and the free message words.

    Unknown options are USAGE errors (exit 2) evaluated before any
    network call (§5) ; `--` terminates option parsing.
    """
    opts = {
        "model": None,
        "provider": None,
        "agent": None,
        "chat_id": None,
        "resume": False,
        "stream": None,
    }
    words: list[str] = []
    index = 0
    options_done = False
    while index < len(args):
        arg = args[index]
        if options_done or not arg.startswith("-") or arg == "-":
            words.append(arg)
            index += 1
            continue
        if arg == "--":
            options_done = True
            index += 1
            continue
        if arg in ("-h", "--help"):
            raise usage_error(f"usage: {USAGE}", hint="run 'ethan help' for details")
        if arg in ("--resume", "-r"):
            opts["resume"] = True
            index += 1
            continue
        if arg == "--stream":
            opts["stream"] = True
            index += 1
            continue
        if arg == "--no-stream":
            opts["stream"] = False
            index += 1
            continue
        name = arg
        if arg in _VALUE_OPTS:
            if index + 1 >= len(args):
                raise usage_error(f"option {arg} requires a value", hint=f"usage: {arg} <value>")
            value = args[index + 1]
            index += 2
        elif arg.startswith("--") and "=" in arg:
            name, _, value = arg.partition("=")
            if name not in _VALUE_OPTS:
                raise usage_error(f"unknown option: {name}", hint=f"usage: {USAGE}")
            index += 1
        else:
            raise usage_error(f"unknown option: {arg}", hint=f"usage: {USAGE}")
        opts[_OPT_KEYS[name]] = value
    return opts, words


def _payload(message: str, opts: dict, chat_id: str | None) -> dict:
    """Build the Core request — routing fields are INTENTS, not decisions."""
    body: dict = {"message": message}
    if chat_id:
        body["chat_id"] = chat_id
    if opts["model"]:
        body["model"] = opts["model"]
    if opts["provider"]:
        body["provider_id"] = opts["provider"]
    if opts["agent"]:
        body["agent_id"] = opts["agent"]
    return body


def _is_tty(stream) -> bool:
    try:
        return bool(stream.isatty())
    except Exception:  # noqa: BLE001 — detached stream (pytest capture…)
        return False


def _dim(text: str) -> str:
    if not get_context().color:
        return text
    from interfaces.cli.core import colors as clr

    return f"{clr.C.DIM}{text}{clr.C.RESET}"


def _stderr(text: str) -> None:
    print(text, file=sys.stderr)


def _footer(text: str) -> None:
    """Metadata line on stderr, suppressed by `--quiet` (§4.4)."""
    if not get_context().quiet:
        _stderr(_dim(text))


def _chat_id_of(payload) -> str | None:
    if isinstance(payload, dict) and payload.get("chat_id"):
        return str(payload["chat_id"])
    return None


def _print_answer(payload) -> None:
    """Human rendering: stdout carries the answer, nothing else (§4)."""
    if not isinstance(payload, dict):
        print(payload)
        return
    text = payload.get("message") or payload.get("response") or ""
    if text:
        print(text)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    meta = payload.get("metadata") or {}
    parts: list[str] = []
    if payload.get("chat_id"):
        parts.append(str(payload["chat_id"]))
    route = "/".join(str(meta[key]) for key in ("provider", "model") if meta.get(key))
    if route:
        parts.append(route)
    if parts:
        _footer(f"◇ chat {' · '.join(parts)}")


def _repaint(previous: str, new: str) -> None:
    """TTY-only: clear the rendered block and repaint after a replace (§4)."""
    if not previous:
        sys.stdout.write(new)
        sys.stdout.flush()
        return
    out = ["\r\x1b[2K"]
    for _ in range(previous.count("\n")):
        out.append("\x1b[1A\r\x1b[2K")
    sys.stdout.write("".join(out) + new)
    sys.stdout.flush()


def _stream(body: dict, deadline: float, *, live: bool) -> tuple[int, str | None]:
    """Consume the Core SSE stream; returns (exit code, chat_id).

    On a TTY the tokens are rendered live. When stdout is a pipe the
    answer is buffered and printed once at the end, so piping never
    yields a half-written reply after a mid-stream failure (§4).
    """
    parts: list[str] = []
    rendered = ""
    chat_id: str | None = None
    for event in api_stream("/v1/chat/completions/stream", body, timeout=deadline):
        etype = event.get("type")
        if etype == "content":
            chunk = str(event.get("content", ""))
            if chunk:
                parts.append(chunk)
                if live:
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
                    rendered += chunk
        elif etype == "content_replace":
            replacement = str(event.get("content", ""))
            parts = [replacement]
            if live:
                _repaint(rendered, replacement)
                rendered = replacement
        elif etype == "tool_call":
            _stderr(_dim(f"◇ tool {event.get('tool', '?')}"))
        elif etype == "tool_result":
            _stderr(_dim(f"◇ tool {event.get('tool', '?')}: {event.get('status', '')}"))
        elif etype == "done":
            chat_id = event.get("chat_id") or chat_id
        elif etype == "error":
            if live:
                sys.stdout.write("\n")
                sys.stdout.flush()
            raise CLIError(
                f"LLM error: {event.get('error', 'generation failed')}",
                code="CLI-LLM",
                context="the Core chat pipeline reported a generation failure",
                hint="ethan provider test <id> · ethan status",
                exit_code=int(ExitCode.OPERATION_FAILED),
            )
    if live:
        sys.stdout.write("\n")
        sys.stdout.flush()
    elif parts:
        print("".join(parts))
    if chat_id:
        _footer(f"◇ chat {chat_id}")
    return int(ExitCode.SUCCESS), chat_id


def _last_chat_id(deadline: float) -> str | None:
    """Latest conversation of the user, straight from the Core ChatStore."""
    history = api_get("/v1/chat/history?limit=1", timeout=deadline)
    if isinstance(history, list) and history:
        last = history[-1]
        if isinstance(last, dict):
            cid = last.get("chat_id") or last.get("id")
            return str(cid) if cid else None
    return None


def _ask_once(message: str, opts: dict, chat_id: str | None, deadline: float) -> tuple:
    """Send one message through the Core; returns (exit code, chat_id).

    JSON mode always uses the non-streaming route so stdout carries
    exactly one document (§4.2). In human mode streaming is the default
    on a TTY and can be forced/removed with `--stream` / `--no-stream`.
    """
    ctx = get_context()
    body = _payload(message, opts, chat_id)

    if ctx.is_json:
        payload = api_post("/v1/chat/completions", body, timeout=deadline)
        return emit(payload), _chat_id_of(payload)

    want_stream = opts["stream"]
    if want_stream is None:
        want_stream = _is_tty(sys.stdout)
    if want_stream:
        return _stream(body, deadline, live=_is_tty(sys.stdout))

    payload = api_post("/v1/chat/completions", body, timeout=deadline)
    _print_answer(payload)
    return int(ExitCode.SUCCESS), _chat_id_of(payload)


def _repl(opts: dict, chat_id: str | None, deadline: float) -> int:
    """Interactive loop: every line is one Core exchange (same mechanism).

    The conversation history lives in the Core ChatStore (chat_id kept
    across turns) — the CLI stores no session state of its own.
    """
    interactive = _is_tty(sys.stdin)
    cid = chat_id
    if interactive:
        _stderr(_dim("ETHAN chat — Core ChatPipeline"))
        _stderr(_dim("Ctrl+D or /exit to quit · /help · /reset"))
    while True:
        if interactive:
            sys.stderr.write("you> ")
            sys.stderr.flush()
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            # Ctrl+C at the prompt: clean stop, exit 0 (REPL convention).
            sys.stderr.write("\n")
            break
        if not line:
            if interactive:
                _stderr(_dim("bye"))
            break
        text = line.strip()
        if not text:
            continue
        if text in ("/exit", "/quit", "/q"):
            break
        if text == "/help":
            _stderr("commands: /exit /quit /help /reset")
            continue
        if text == "/reset":
            cid = None
            _stderr("new conversation (chat_id cleared)")
            continue
        if text.startswith("/"):
            _stderr(f"unknown command: {text} — /help")
            continue
        try:
            _, cid = _ask_once(text, opts, cid, deadline)
        except CLIError as err:
            # A failure must not kill the interactive session: it is
            # rendered on stderr (never stdout) and the loop continues.
            _stderr(format_cli_error(err, as_json=False))
    return int(ExitCode.SUCCESS)


@register(
    "chat",
    group="core",
    description="Chat with ETHAN — model/provider/agent resolved by the Core",
    usage=USAGE,
)
def cmd_chat(args: list[str]) -> int:
    """One-shot or interactive chat — always via the Core ChatPipeline."""
    opts, words = _parse(args)
    ctx = get_context()
    if ctx.is_json and not words:
        raise usage_error(
            "chat without a message does not support JSON output",
            hint="pass a message, or use 'ethan repl' for the interactive REPL",
        )

    deadline = get_timeout(default=LLM_TIMEOUT)
    chat_id = opts["chat_id"]
    if opts["resume"] and not chat_id:
        chat_id = _last_chat_id(deadline)

    message = " ".join(words).strip()
    if message:
        code, _ = _ask_once(message, opts, chat_id, deadline)
        return code
    return _repl(opts, chat_id, deadline)


__all__ = ["cmd_chat"]
