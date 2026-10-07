#!/usr/bin/env python3
"""ETHAN CLI — Official Terminal Interface for ETHAN Cognitive Runtime.

Contrat officiel : docs/specs/CLI_CONTRACT.md.
Règle d'or AGENTS.md : Le CLI est une interface ; il ne contient aucune logique métier.

Usage:
  ethan [options globales] <famille> [<verbe>] [arguments]
  ethan --help
  ethan --version
  ethan -o json version
"""

from __future__ import annotations

import json
import sys

from interfaces.cli._version import __version__
from interfaces.cli.core import colors as clr
from interfaces.cli.core.context import CLIContext, parse_global_options, set_context
from interfaces.cli.core.errors import (
    CLIError,
    api_error,
    connection_error,
    format_cli_error,
    timeout_error,
    usage_error,
)
from interfaces.cli.core.exit_codes import ExitCode, normalize_exit
from interfaces.cli.registry import Registry, discover_commands


def _print_error(err: CLIError, ctx: CLIContext) -> None:
    """Print error to stderr formatted as JSON or human per contract §4.3."""
    as_json = ctx.output == "json"
    formatted = format_cli_error(err, as_json=as_json)
    print(formatted, file=sys.stderr)


def _show_version(ctx: CLIContext) -> None:
    """Show version per contract §8.18."""
    from interfaces.cli.core.client import get_core_version

    if ctx.output == "json":
        payload = {
            "cli": __version__,
            "contract": "1.0",
            "core": get_core_version(),
            "api_url": ctx.api_url,
        }
        print(json.dumps(payload, indent=2))
    else:
        core = get_core_version()
        suffix = f" (core {core})" if core else ""
        print(f"ETHAN CLI v{__version__}{suffix}")


def _bootstrap_context() -> CLIContext:
    """Ambient context used to report an error raised while parsing argv.

    Global options are resolved from the environment only: the very option
    that failed to parse must not be reused to format the error.
    """
    from interfaces.cli.core.context import reset_context

    return reset_context()


def main() -> None:
    """Main CLI entry point."""
    # 1. Discover registered builtin commands
    discover_commands()
    registry = Registry()

    # 2. Parse global options and resolve execution context.
    #    A malformed option value is a USAGE error (exit 2) evaluated before
    #    any network call (§5): it is reported like any other CLI error, never
    #    as a raw traceback.
    try:
        context = parse_global_options()
    except CLIError as err:
        # The context is not usable yet, so render with the ambient defaults.
        _print_error(err, _bootstrap_context())
        sys.exit(err.exit_code)
    set_context(context)

    # 3. Check reserved options (contract §3.1 & §10.3)
    if context.dry_run:
        err = usage_error("Option '--dry-run' is reserved and not yet implemented.")
        _print_error(err, context)
        sys.exit(int(ExitCode.USAGE))

    # 4. Check version flag/command: ethan -V, ethan --version, ethan version
    if context.is_version or context.command in ("version", "--version", "-V"):
        _show_version(context)
        sys.exit(int(ExitCode.SUCCESS))

    # 5. Check global help: ethan, ethan -h, ethan --help, ethan help
    if not context.command or context.command in ("--help", "-h", "help") or context.is_help:
        # Check if asking help for a specific command: ethan help <cmd>
        if context.command == "help" and context.args:
            subcmd = context.args[0]
            handler = registry.commands.get(subcmd)
            if handler is None:
                from interfaces.cli.core.ux import UX

                suggestion = UX.suggest_command(subcmd, sorted(registry.commands))
                hint = (
                    f"Did you mean: {suggestion}?"
                    if suggestion
                    else "Run 'ethan help' for the command list."
                )
                err = usage_error(f"Unknown command: {subcmd}", hint=hint)
                _print_error(err, context)
                sys.exit(int(ExitCode.USAGE))
            # Invoke command handler with --help
            try:
                res = handler(["--help"])
                sys.exit(normalize_exit(res))
            except Exception:
                sys.exit(0)

        # Main help output
        _show_help(registry)
        sys.exit(int(ExitCode.SUCCESS))

    # 6. Check interactive REPL
    if context.command == "repl":
        if context.output == "json":
            err = usage_error("REPL mode is not supported with --output json.")
            _print_error(err, context)
            sys.exit(int(ExitCode.USAGE))

        from interfaces.cli.repl import repl_loop

        try:
            repl_loop()
            sys.exit(int(ExitCode.SUCCESS))
        except KeyboardInterrupt:
            if not context.quiet:
                print(f"\n{clr.C.GREEN}◆ Goodbye{clr.C.RESET}")
            sys.exit(int(ExitCode.SUCCESS))
        except Exception as e:
            err = CLIError(f"REPL failed: {e}", exit_code=int(ExitCode.OPERATION_FAILED))
            _print_error(err, context)
            sys.exit(int(ExitCode.OPERATION_FAILED))

    # 7. Resolve command handler
    handler = registry.commands.get(context.command)
    if handler is None:
        from interfaces.cli.core.ux import UX

        suggestion = UX.suggest_command(context.command, sorted(registry.commands))
        hint = (
            f"Did you mean: {suggestion}?"
            if suggestion
            else "Run 'ethan help' for the command list."
        )
        err = usage_error(f"Unknown command: {context.command}", hint=hint)
        _print_error(err, context)
        sys.exit(int(ExitCode.USAGE))

    # 8. Dispatch handler with contract exception handling (no raw tracebacks)
    try:
        exit_code = handler(context.args)
        sys.exit(normalize_exit(exit_code))
    except KeyboardInterrupt:
        if not context.quiet and context.output != "json":
            print(f"\n{clr.C.CYAN}◇ Interrupted{clr.C.RESET}", file=sys.stderr)
        sys.exit(int(ExitCode.INTERRUPTED))
    except CLIError as e:
        _print_error(e, context)
        sys.exit(e.exit_code)
    except ConnectionError as e:
        err = connection_error(str(e))
        _print_error(err, context)
        sys.exit(int(ExitCode.UNAVAILABLE))
    except TimeoutError as e:
        err = timeout_error(context.timeout, hint=str(e))
        _print_error(err, context)
        sys.exit(int(ExitCode.TIMEOUT))
    except Exception as e:
        status = getattr(e, "status", None)
        detail = str(e)
        if status == 401 or "API 401" in detail:
            err = api_error(401, detail, hint="ethan auth login")
            _print_error(err, context)
            sys.exit(int(ExitCode.AUTH))
        elif status == 403 or "API 403" in detail:
            err = api_error(403, detail)
            _print_error(err, context)
            sys.exit(int(ExitCode.FORBIDDEN))
        elif "connection refused" in detail.lower() or "unreachable" in detail.lower():
            err = connection_error(detail)
            _print_error(err, context)
            sys.exit(int(ExitCode.UNAVAILABLE))
        elif "timed out" in detail.lower():
            err = timeout_error(context.timeout)
            _print_error(err, context)
            sys.exit(int(ExitCode.TIMEOUT))
        else:
            err = CLIError(
                f"Command '{context.command}' failed: {detail}",
                code="CLI-FAILED",
                exit_code=int(ExitCode.OPERATION_FAILED),
            )
            _print_error(err, context)
            if context.verbose >= 2:
                import traceback

                traceback.print_exc(file=sys.stderr)
            sys.exit(int(ExitCode.OPERATION_FAILED))


def _show_help(registry: Registry) -> None:
    """Display formatted help grouped by category per contract §8.18."""
    from interfaces.cli.core.context import get_context

    use_color = get_context().color
    bold = clr.C.BOLD if use_color else ""
    cyan = clr.C.CYAN if use_color else ""
    dim = clr.C.DIM if use_color else ""
    reset = clr.C.RESET if use_color else ""
    print()
    print(f"{bold}{cyan}◆ ETHAN CLI{reset}  {dim}Cognitive OS Terminal{reset}")
    print()

    groups: dict[str, list[tuple[str, str]]] = {}
    for name, handler in sorted(registry.commands.items()):
        meta = getattr(handler, "__meta__", None)
        if meta is None:
            try:
                from interfaces.cli.core.discovery import registry as disc

                cmd = disc.get(name)
                meta = (
                    {
                        "group": getattr(cmd, "group", "other"),
                        "description": getattr(cmd, "description", ""),
                    }
                    if cmd
                    else {}
                )
            except Exception:
                meta = {}
        group = meta.get("group") or "other"
        desc = meta.get("description") or ""
        groups.setdefault(group, []).append((name, desc))

    group_order = ["infra", "core", "system"]
    labels = {
        "infra": "Infrastructure",
        "core": "Cognitive",
        "system": "System",
        "other": "Other",
    }
    ordered = [g for g in group_order if g in groups]
    ordered += sorted(g for g in groups if g not in group_order)

    for group_name in ordered:
        label = labels.get(group_name, group_name.capitalize())
        print(f"  {bold}{label}{reset}")
        for name, desc in groups[group_name]:
            print(f"    {cyan}{name:<16}{reset} {desc}")
        print()

    print(f"  {dim}Usage: ethan [options] <command> [args]{reset}")
    print(
        f"  {dim}Global options: -o json|human, -q, -v, --no-color, --timeout <sec>, --api-url <url>{reset}"
    )
    print()


if __name__ == "__main__":
    main()
