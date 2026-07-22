"""CLI command: ethan plugin <validate|list|info> [path]"""
from __future__ import annotations

import json
from pathlib import Path

from interfaces.cli.core import colors as clr
from interfaces.cli.registry import register
from plugins.loader import PluginLoader
from plugins.validator import PluginValidator


@register(
    "plugin",
    group="core",
    description="Gerer et valider les plugins ETHAN",
    usage="ethan plugin <validate|list|info> [path]",
)
def cmd_plugin(args: list[str]) -> int:
    if not args:
        print(f"{clr.C.CYAN}Usage:{clr.C.RESET} ethan plugin <validate|list|info> [path]")
        return 0

    action = args[0].lower()
    loader = PluginLoader()
    validator = PluginValidator()

    if action == "list":
        plugins = loader.list()
        if not plugins:
            print(f"{clr.C.YELLOW}Aucun plugin charge{clr.C.RESET}")
            return 0
        for p in plugins:
            print(f"  {clr.C.GREEN}{p.name}{clr.C.RESET} v{p.version} (api={p.api_version})")
        return 0

    if action == "info":
        name = args[1] if len(args) > 1 else ""
        meta = loader.get(name)
        if not meta:
            print(f"{clr.C.RED}Plugin '{name}' introuvable{clr.C.RESET}")
            return 1
        print(json.dumps({
            "name": meta.name,
            "version": meta.version,
            "api_version": meta.api_version,
            "description": meta.description,
            "author": meta.author,
            "license": meta.license,
            "permissions": meta.permissions,
            "capabilities": meta.capabilities,
            "commands": list(meta.commands.keys()),
            "subscriptions": list(meta.subscriptions.keys()),
        }, indent=2))
        return 0

    if action == "validate":
        path = Path(args[1]) if len(args) > 1 else Path.cwd()
        if not path.is_dir():
            print(f"{clr.C.RED}Chemin invalide : {path}{clr.C.RESET}")
            return 1
        manifest_path = path / "manifest.json"
        if not manifest_path.exists():
            print(f"{clr.C.RED}manifest.json introuvable dans : {path}{clr.C.RESET}")
            return 1
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as e:
            print(f"{clr.C.RED}manifest.json invalide : {e}{clr.C.RESET}")
            return 1
        result = validator.validate(path, manifest)
        if result.valid:
            print(f"{clr.C.GREEN}OK Plugin valide : {manifest.get('name', '?')}{clr.C.RESET}")
            return 0
        else:
            print(f"{clr.C.RED}FAIL Validation echouee : {result.error}{clr.C.RESET}")
            return 1

    print(f"{clr.C.RED}Action inconnue : {action}{clr.C.RESET}")
    return 1
