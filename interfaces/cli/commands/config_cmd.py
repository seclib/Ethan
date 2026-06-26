"""Configuration management command.

ethan config [show|edit|set|get] [key] [value]
"""

import os
from ethan.ui.colors import style


def manage(config: dict, args) -> int:
    """Manage configuration."""
    action = args.action or "show"

    if action == "show":
        import yaml
        print(yaml.dump(config, default_flow_style=False))

    elif action == "get" and args.key:
        keys = args.key.split(".")
        value = config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, None)
            else:
                value = None
                break
        if value is not None:
            print(value)
        else:
            print(style.error(f"Key not found: {args.key}"))
            return 1

    elif action == "set" and args.key and args.value:
        keys = args.key.split(".")
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = args.value

        # Save
        from ethan.config import save_config
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        path = os.path.join(xdg_config, "ethan", "config.yaml")
        save_config(config, path)
        print(style.success(f"Config saved to {path}"))

    elif action == "edit":
        import subprocess
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        path = os.path.join(xdg_config, "ethan", "config.yaml")
        editor = os.environ.get("EDITOR", "nano")
        subprocess.call([editor, path])

    return 0