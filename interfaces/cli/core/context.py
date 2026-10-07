"""ETHAN CLI — global execution context.

Single source of truth for the global options of
`docs/specs/CLI_CONTRACT.md` §3.1: output format, verbosity, colour,
timeout, profile, API endpoint, confirmation and token.

Every command reads its execution parameters from this context instead of
re-parsing `sys.argv`: global options are parsed exactly once, in `main()`,
so two commands can never disagree about `--output json` or about the client
deadline (§5: `usage` is evaluated before any network call).

The context is also what makes the CLI scriptable (§4.2): in JSON mode
`stdout` carries exactly one JSON document and nothing else.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

from interfaces.cli.core.errors import CLIError, usage_error

#: Default client deadline (seconds) for regular API calls — contract §3.1.
DEFAULT_TIMEOUT = 5.0
#: Diagnostics (`doctor`) get a longer default — contract §3.1.
DIAGNOSTIC_TIMEOUT = 30.0

OUTPUT_FORMATS = ("human", "json")

#: Options that must never be silently ignored (contract §3.1).
#: `--dry-run` is RESERVED: using it is a usage error (exit 2), never a no-op.
RESERVED_OPTIONS = ("--dry-run",)

#: Short flags accepted as a cluster (-vq, -vv, -yq …).
_SHORT_FLAGS = frozenset("hVqvy")

#: Options that consume the following argv token as their value.
_VALUE_OPTIONS = (
    "-o",
    "--output",
    "--profile",
    "--api-url",
    "--timeout",
    "--token",
)


def _is_tty(stream) -> bool:
    """True when `stream` is an interactive terminal."""
    try:
        return bool(stream.isatty())
    except Exception:  # noqa: BLE001 — detached stream (pytest capture…)
        return False


def color_enabled(*, no_color_flag: bool = False, output: str = "human") -> bool:
    """Colour policy (contract §3.2).

    Priority: ``--no-color`` > ``NO_COLOR`` > TTY detection. Colour is never
    emitted in JSON mode, because machine output must stay byte-stable.
    """
    if no_color_flag or os.environ.get("NO_COLOR"):
        return False
    if output == "json":
        return False
    return _is_tty(sys.stdout)


@dataclass
class CLIContext:
    """Execution context of a single CLI invocation.

    Holds both the resolved global options (§3.1) and the command that was
    selected, so a handler receives exactly the arguments that belong to it.
    """

    # ── Global options (contract §3.1) ─────────────────────────────────
    output: str = "human"
    quiet: bool = False
    verbose: int = 0
    color: bool = False
    profile: str | None = None
    api_url: str = ""
    timeout: float = DEFAULT_TIMEOUT
    #: True when the deadline came from an explicit `--timeout` — lets a
    #: command (e.g. `chat`) offer a larger default for slow Core subsystems
    #: without silently overriding a deliberate user/profile/env deadline.
    timeout_explicit: bool = False
    assume_yes: bool = False
    token: str | None = None
    #: True when the token came from `--token` (discouraged → stderr warning).
    cli_token_explicit: bool = False

    # ── Flags and selection ───────────────────────────────────────────
    is_help: bool = False
    is_version: bool = False
    #: True when `--dry-run` was passed (reserved → exit 2, never a no-op).
    dry_run: bool = False

    command: str | None = None
    args: list[str] = field(default_factory=list)
    #: Non-fatal warnings collected while parsing, flushed to stderr.
    warnings: list[str] = field(default_factory=list)

    @property
    def is_json(self) -> bool:
        """True when stdout must carry exactly one JSON document (§4.2)."""
        return self.output == "json"

    def debug(self, message: str) -> None:
        """Emit a `-v` diagnostic on **stderr** (never on stdout)."""
        if self.verbose:
            print(f"[ethan] {message}", file=sys.stderr)

    def warn(self, message: str) -> None:
        """Emit a warning on stderr, suppressed by ``--quiet`` (§4.4)."""
        if not self.quiet:
            print(f"warning: {message}", file=sys.stderr)

    def emit_json(self, payload) -> None:
        """Write exactly one JSON document on stdout (contract §4.2).

        The Core response is passed through faithfully: the CLI renames,
        masks and invents no business field.
        """
        import json

        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def emit_error(self, err: CLIError) -> None:
        """Render an error on **stderr** in the active output mode (§4.3)."""
        from interfaces.cli.core.errors import format_cli_error

        print(format_cli_error(err, as_json=self.is_json), file=sys.stderr)


# Process-wide context. A default instance keeps the CLI usable from tests and
# from handlers imported directly, without a parsed argv.
_context = CLIContext(color=color_enabled())


def get_context() -> CLIContext:
    """Return the active CLI context (never None)."""
    return _context


def set_context(ctx: CLIContext) -> CLIContext:
    """Install a new context (used by `main()` and by tests)."""
    global _context
    _context = ctx
    return _context


def reset_context() -> CLIContext:
    """Rebuild the context from environment variables only (no argv)."""
    global _context
    _context = CLIContext(
        output=os.environ.get("ETHAN_OUTPUT") or "human",
        profile=os.environ.get("ETHAN_PROFILE"),
        api_url=os.environ.get("ETHAN_API") or os.environ.get("ETHAN_API_URL") or "",
    )
    if os.environ.get("ETHAN_TIMEOUT"):
        try:
            _context.timeout = float(os.environ["ETHAN_TIMEOUT"])
        except ValueError:
            pass
    _context.color = color_enabled(output=_context.output)
    return _context


def _parse_timeout(raw: str) -> float:
    """Validate a ``--timeout`` value; an invalid value is a usage error."""
    try:
        value = float(raw)
    except ValueError:
        raise usage_error(
            f"invalid --timeout value: {raw!r}",
            hint="--timeout expects a positive number of seconds",
        ) from None
    if value <= 0:
        raise usage_error(
            f"invalid --timeout value: {raw!r}",
            hint="--timeout expects a positive number of seconds",
        )
    return value


def parse_global_options(argv: list[str] | None = None) -> CLIContext:
    """Parse the global options and select the command (contract §3.1).

    Global options are accepted **before or after** the command family, so
    they are collected from the whole argument list and removed; whatever
    remains is the command name plus its own arguments.

    ``--dry-run`` is RESERVED (§3.1, §10.3): it is recorded here and refused
    by `main()` with exit 2, so it can never become a silent no-op.

    Args:
        argv: argument list without the program name. Defaults to
            ``sys.argv[1:]``.

    Returns:
        A fully populated :class:`CLIContext`.

    Raises:
        CLIError: exit code 2 for an invalid value or a missing option value.
            Unknown options are *not* raised here — an unknown option placed
            after the family may belong to the command, which rejects it with
            the same exit code.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    ctx = reset_context()

    verbose_flags = 0
    no_color = False
    command: str | None = None
    rest: list[str] = []

    index = 0
    while index < len(args):
        arg = args[index]

        if arg in ("-h", "--help"):
            ctx.is_help = True
            index += 1
            continue

        if arg in ("-V", "--version"):
            ctx.is_version = True
            index += 1
            continue

        if arg in ("-q", "--quiet"):
            ctx.quiet = True
            index += 1
            continue

        if arg == "-v":
            verbose_flags += 1
            index += 1
            continue

        if arg == "--verbose":
            verbose_flags += 2
            index += 1
            continue

        if arg == "--no-color":
            no_color = True
            index += 1
            continue

        if arg in ("-y", "--yes"):
            ctx.assume_yes = True
            index += 1
            continue

        if arg == "--dry-run":
            ctx.dry_run = True
            index += 1
            continue

        # Short flags may be clustered: -vq, -vv, -yq …
        if (
            arg.startswith("-")
            and not arg.startswith("--")
            and len(arg) > 2
            and all(ch in _SHORT_FLAGS for ch in arg[1:])
        ):
            for flag in arg[1:]:
                if flag == "h":
                    ctx.is_help = True
                elif flag == "V":
                    ctx.is_version = True
                elif flag == "q":
                    ctx.quiet = True
                elif flag == "v":
                    verbose_flags += 1
                elif flag == "y":
                    ctx.assume_yes = True
            index += 1
            continue

        # Long form with '=' : --output=json, --profile=dev, --timeout=30 …
        # The slot is expanded in place into (name, value) so the regular
        # branch below consumes it: `index` already points at `name`.
        if arg.startswith("--") and "=" in arg:
            name, _, value = arg.partition("=")
            if name in _VALUE_OPTIONS:
                args[index : index + 1] = [name, value]
                continue

        if arg in _VALUE_OPTIONS:
            if index + 1 >= len(args):
                raise usage_error(f"option {arg} requires a value", hint=f"usage: {arg} <value>")
            value = args[index + 1]
            index += 2

            if arg in ("-o", "--output"):
                if value not in OUTPUT_FORMATS:
                    raise usage_error(
                        f"invalid --output value: {value!r}",
                        hint="expected 'human' or 'json'",
                    )
                ctx.output = value
            elif arg == "--profile":
                ctx.profile = value
            elif arg == "--api-url":
                ctx.api_url = value
            elif arg == "--timeout":
                ctx.timeout = _parse_timeout(value)
                ctx.timeout_explicit = True
            elif arg == "--token":
                ctx.token = value
                ctx.cli_token_explicit = True
                ctx.warnings.append("--token is visible in the process list; prefer ETHAN_TOKEN")
            continue

        if command is None and not arg.startswith("-"):
            command = arg
            rest.append(arg)
            index += 1
            continue

        # Anything else belongs to the command and is forwarded untouched.
        rest.append(arg)
        index += 1

    ctx.verbose = verbose_flags
    # Colour depends on the output mode and on --no-color: resolved last.
    ctx.color = color_enabled(no_color_flag=no_color, output=ctx.output)

    if command is not None:
        ctx.command = command
        ctx.args = rest[1:]
    else:
        # `ethan` alone ≡ `ethan help` (contract §2.1); stray leading options
        # are still forwarded so `ethan --json`-style misuse is reported.
        ctx.command = None
        ctx.args = rest

    # Warnings go to stderr, never to stdout (contract §3.3).
    for warning in ctx.warnings:
        print(f"warning: {warning}", file=sys.stderr)

    return ctx


__all__ = [
    "DEFAULT_TIMEOUT",
    "DIAGNOSTIC_TIMEOUT",
    "CLIContext",
    "color_enabled",
    "get_context",
    "parse_global_options",
    "reset_context",
    "set_context",
]
