"""ETHAN version command.

Source unique de vérité : `docs/specs/CLI_CONTRACT.md` §8.18.
- Mode humain : ethan <version>
- Mode json : {"cli": "...", "contract": "1.0", "core": null|str, "api_url": "..."}
"""

from __future__ import annotations

import json

from interfaces.cli._version import __version__
from interfaces.cli.core.client import get_core_version
from interfaces.cli.core.context import get_context
from interfaces.cli.registry import register


@register("version", group="system", description="Show version")
def cmd_version(args: list[str]) -> int:
    """Show ETHAN CLI version and contract info."""
    ctx = get_context()
    as_json = (
        ctx.output == "json"
        or "-o" in args
        or "--output" in args
        or any(a.startswith(("-o=", "--output=")) for a in args)
    )

    if as_json:
        payload = {
            "cli": __version__,
            "contract": "1.0",
            "core": get_core_version(),
            "api_url": ctx.api_url,
        }
        print(json.dumps(payload, indent=2))
        return 0

    core = get_core_version()
    suffix = f" (core {core})" if core else ""
    print(f"ETHAN CLI v{__version__}{suffix}")
    return 0
