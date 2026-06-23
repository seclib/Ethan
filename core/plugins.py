"""ETHAN Plugin Architecture — formal contract definition.

A plugin is a self-contained module with declared metadata, capabilities,
commands, memory hooks, and event subscriptions.

Discovery paths (in order):
  1. Built-in:   cli/plugins/<name>/
  2. User:       ~/.local/share/ethan/plugins/<name>/
  3. System:     /etc/ethan/plugins/<name>/        (if exists)

Isolation:
  - Each plugin runs in its own Python process
  - Plugins communicate via NATS only (no direct imports)
  - Plugin crash does not affect kernel

Hot-loading:
  - plugins/ directory is watched for changes
  - New plugins are loaded on the fly
  - Removed plugins are unregistered
  - No restart required
"""

ETHAN_PLUGIN_API = "2"

# Full plugin metadata schema
ETHAN_PLUGIN_SCHEMA = {
    "name": "string (required)",
    "version": "semver (required)",
    "api_version": "string (required, must match ETHAN_PLUGIN_API)",
    "description": "string (optional)",
    "author": "string (optional)",
    "license": "string (optional)",

    # 1. Capability declarations
    "capabilities": [
        {
            "name": "string",
            "version": "semver",
            "inputs": ["event.type"],
            "outputs": ["event.type"],
            "state_reads": ["redis:key:*"],
            "state_writes": ["redis:key:*"],
            "dependencies": [],
            "shared": False,
        }
    ],

    # 2. CLI commands
    "commands": {
        "command_name": {
            "help": "description",
            "handler": "function_name",  # in plugin.py
            "args": [{"name": "...", "type": "str", "help": "..."}],
        }
    },

    # 3. Memory hooks
    "memory_hooks": {
        "on_store": "function_name",     # called before store
        "on_recall": "function_name",    # called after recall
        "on_delete": "function_name",    # called before delete
        "on_semantic_query": "function_name",
    },

    # 4. Event subscriptions (NATS)
    "subscriptions": {
        "ethan.intent.user": "handle_intent",
        "ethan.planner.plan.created": "handle_plan",
        "ethan.executor.task.completed": "handle_result",
    },

    # 5. Dependencies
    "dependencies": [],
}

# Example minimal plugin.py
EXAMPLE_PLUGIN = """
'''Example plugin.'''
ETHAN_PLUGIN = {
    "name": "my-plugin",
    "version": "1.0.0",
    "api_version": "2",
    "description": "Does something useful",
    "capabilities": [
        {
            "name": "myplugin.action",
            "version": "1.0.0",
            "module": "my-plugin",
            "inputs": ["myplugin.action.request"],
            "outputs": ["myplugin.action.complete"],
            "state_reads": [],
            "state_writes": [],
            "dependencies": [],
            "shared": False,
        }
    ],
    "commands": {
        "myaction": {
            "help": "Run my action",
            "handler": "cmd_myaction",
            "args": [{"name": "arg", "type": "str", "help": "some argument"}],
        }
    },
    "memory_hooks": {},
    "subscriptions": {
        "myplugin.action.request": "handle_action",
    },
    "dependencies": [],
}

def cmd_myaction(args):
    print("myaction:", args)

def handle_action(event):
    print("got event:", event)
"""