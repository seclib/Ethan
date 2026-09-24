"""ETHAN plugin — validate, install, remove, list, info (commande unifiée).

Fusion des anciennes commandes en conflit `plugin` (plugin.py +
plugin_cmd.py) et retrait de `plugins.py` (rouge : import COMMANDS
inexistant) — Phase 4 « doublons CLI ».

La validation est la capacité Core ``core.plugins.validator``
(P1-PLUGIN-01) ; l'installation passe par ``plugin_manager`` (avec
contrôle AST Core avant exécution).
"""

from __future__ import annotations

import json
from pathlib import Path

from core.plugins.validator import PluginValidator
from interfaces.cli.core import colors as clr
from interfaces.cli.core.ux import UX
from interfaces.cli.plugin_manager import install, list_installed, remove
from interfaces.cli.registry import register
from plugins.loader import PluginLoader

KNOWN_PLUGIN_SUBS = ["validate", "install", "remove", "list", "info"]


@register(
    "plugin",
    group="core",
    description="Gerer et valider les plugins ETHAN",
    usage="ethan plugin <validate|install|remove|list|info> [args]",
)
def cmd_plugin(args):
    """Dispatch des sous-commandes plugin."""
    if not args:
        print(
            f"{clr.C.CYAN}Usage:{clr.C.RESET} "
            "ethan plugin <validate|install|remove|list|info> [args]"
        )
        return 1
    sub = args[0].lower()
    sub_args = args[1:]

    if sub == "validate":
        return _validate(sub_args)
    if sub == "info":
        return _info(sub_args)
    if sub == "list":
        return _list()
    if sub == "install":
        if not sub_args:
            print(f"{clr.C.RED}Usage:{clr.C.RESET} ethan plugin install <path|git-url>")
            return 1
        return 0 if install(sub_args[0]) else 1
    if sub == "remove":
        if not sub_args:
            print(f"{clr.C.RED}Usage:{clr.C.RESET} ethan plugin remove <name>")
            return 1
        return 0 if remove(sub_args[0]) else 1

    suggestion = UX.suggest_command(sub, KNOWN_PLUGIN_SUBS)
    msg = (
        f"Did you mean? {suggestion}"
        if suggestion
        else "try: ethan plugin <validate|install|remove|list|info>"
    )
    print(f"Unknown subcommand: {sub}\n  {msg}")
    return 1


def _validate(args: list[str]) -> int:
    """Validation Core : manifest (schéma legacy ou Core) puis code (AST)."""
    path = Path(args[0]) if args else Path.cwd()
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
    result = PluginValidator().validate(path, manifest)
    if result.valid:
        print(f"{clr.C.GREEN}OK Plugin valide : {manifest.get('name', '?')}{clr.C.RESET}")
        return 0
    print(f"{clr.C.RED}FAIL Validation echouee : {result.error}{clr.C.RESET}")
    return 1


def _info(args: list[str]) -> int:
    """Détaille un plugin via le loader legacy (meta structurée)."""
    name = args[0] if args else ""
    if not name:
        print(f"{clr.C.RED}Usage:{clr.C.RESET} ethan plugin info <name>")
        return 1
    loader = PluginLoader()
    meta = loader.load(name) or loader.get(name)
    if meta is None:
        print(f"{clr.C.RED}Plugin '{name}' introuvable{clr.C.RESET}")
        return 1
    print(
        json.dumps(
            {
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
            },
            indent=2,
        )
    )
    return 0


def _list() -> int:
    """Liste les plugins utilisateurs installés (source unique : plugin_manager)."""
    plugins = list_installed()
    if not plugins:
        print(f"{clr.C.YELLOW}Aucun plugin installe{clr.C.RESET}")
        return 0
    for p in plugins:
        print(
            f"  {clr.C.GREEN}{p.get('name', '?')}{clr.C.RESET} "
            f"v{p.get('version', '?')} (api={p.get('api_version', '?')})"
        )
    return 0
