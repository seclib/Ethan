# ETHAN Plugin Format Specification v2

## 1. Plugin Directory Structure

```
<plugin-name>/
├── manifest.json          # Plugin metadata (required)
├── plugin.py              # Entry point (required)
├── requirements.txt       # Python dependencies (optional)
├── assets/                # Static files (optional)
│   ├── icon.png
│   └── help.md
└── tests/                 # Plugin tests (optional)
    └── test_plugin.py
```

---

## 2. manifest.json

### 2.1 Schema

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "api_version": "2",
  "description": "Plugin description",
  "author": "Author name",
  "license": "MIT",

  "capabilities": [],
  "commands": {},
  "memory_hooks": {},
  "subscriptions": {},
  "permissions": [],

  "dependencies": {
    "python": ">=3.10",
    "pip": ["requests>=2.0"]
  }
}
```

### 2.2 Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | yes | Unique plugin name, lowercase, hyphen-separated |
| `version` | `string` | yes | Semantic version (semver) |
| `api_version` | `string` | yes | Must match ETHAN core API version (`"2"`) |
| `description` | `string` | no | Human-readable description |
| `author` | `string` | no | Plugin author |
| `license` | `string` | no | SPDX license identifier (e.g. `MIT`, `Apache-2.0`) |
| `capabilities` | `array` | no | Capability declarations |
| `commands` | `object` | no | CLI command declarations |
| `memory_hooks` | `object` | no | Memory hook declarations |
| `subscriptions` | `object` | no | NATS event subscriptions |
| `permissions` | `array` | no | Required permissions |
| `dependencies` | `object` | no | System and pip dependencies |

---

## 3. Entry Point (`plugin.py`)

### 3.1 Execution

The entry point is loaded once at plugin activation. It must define `ETHAN_PLUGIN` with metadata matching `manifest.json`.

```python
ETHAN_PLUGIN = {
    "name": "my-plugin",
    "version": "1.0.0",
    "api_version": "2",
    "capabilities": [],
    "commands": {},
    "subscriptions": {},
}

def cmd_myaction(args):
    """Handler for 'myaction' CLI command."""
    print("executing myaction:", args)

def handle_intent(event):
    """Handler for 'ethan.intent.user' event."""
    pass
```

### 3.2 Handler Resolution

- **CLI commands**: function named in `commands.<name>.handler` is called with `(args)`
- **Event subscriptions**: function named in `subscriptions.<subject>` is called with `(event_dict)`
- **Memory hooks**: function named in `memory_hooks.<hook>` is called with `(data_dict)`

All handler functions are resolved from the `plugin.py` module scope.

---

## 4. Capabilities

### 4.1 Capability Object

```json
{
  "name": "myplugin.action",
  "version": "1.0.0",
  "module": "my-plugin",
  "description": "Performs the plugin action",
  "inputs": ["myplugin.action.request"],
  "outputs": ["myplugin.action.complete", "myplugin.action.error"],
  "state_reads": ["myplugin:config"],
  "state_writes": ["myplugin:history"],
  "dependencies": ["filesystem.read"],
  "shared": false
}
```

### 4.2 Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | yes | Namespaced: `<plugin>.<action>` |
| `version` | `string` | yes | Semver of this capability |
| `module` | `string` | yes | Plugin name (owner) |
| `description` | `string` | no | What this capability does |
| `inputs` | `array[string]` | no | Event types consumed |
| `outputs` | `array[string]` | no | Event types produced |
| `state_reads` | `array[string]` | no | Redis/state keys read |
| `state_writes` | `array[string]` | no | Redis/state keys written |
| `dependencies` | `array[string]` | no | Required capabilities from other modules |
| `shared` | `boolean` | no | Allow other plugins to write same state keys |

### 4.3 Capability Registration Flow

```
Plugin loaded → manifest parsed → capabilities extracted
    │
    ▼
Registry.validate(capabilities) → check write conflicts, dependencies
    │
    ▼
Registry.Register(capability) → stored in capability registry
    │
    ▼
Planner can now query and assign this capability
```

---

## 5. CLI Commands

### 5.1 Command Object

```json
{
  "myaction": {
    "help": "Run the plugin action",
    "handler": "cmd_myaction",
    "args": [
      {"name": "input", "type": "str", "help": "Input text"}
    ]
  }
}
```

### 5.2 Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `help` | `string` | yes | Short description for `--help` |
| `handler` | `string` | yes | Function name in `plugin.py` |
| `args` | `array` | no | Positional arguments |
| `args[].name` | `string` | yes | Argument name |
| `args[].type` | `string` | yes | `str`, `int`, `bool`, or `float` |
| `args[].help` | `string` | yes | Argument description |

### 5.3 Registration Flow

```
Plugin loaded → commands extracted
    │
    ▼
CLI Registry → register("myaction") → cmd_myaction
    │
    ▼
"ethan myaction <args>" → dispatches to plugin handler
```

---

## 6. Permissions Model

### 6.1 Permission Levels

| Level | Label | Description |
|-------|-------|-------------|
| 0 | `none` | No access to system resources |
| 1 | `read` | Read state, read files |
| 2 | `write` | Write state, write files |
| 3 | `execute` | Execute commands, call APIs |
| 4 | `admin` | Full system access |

### 6.2 Permission Declaration

In `manifest.json`:

```json
{
  "permissions": [
    "state:read:myplugin:*",
    "state:write:myplugin:history",
    "filesystem:read:/tmp/*",
    "network:request:https://api.example.com"
  ]
}
```

### 6.3 Permission Patterns

```
state:read:<namespace>:<key-pattern>
state:write:<namespace>:<key-pattern>
filesystem:read:<path-pattern>
filesystem:write:<path-pattern>
network:request:<url-pattern>
execute:<command-pattern>
```

Patterns support glob-style wildcards:
- `*` — match any segment
- `**` — match any depth
- `myplugin:*` — all myplugin-related keys

### 6.4 Enforcement

```
Permission check at:
- State access (read/write)
- Filesystem access
- Network calls
- Command execution

Violation → RuntimeError logged, operation denied
No enforcement done in Python — enforced at kernel level
```

---

## 7. Memory Hooks

### 7.1 Hook Types

| Hook | Trigger | Handler Signature |
|------|---------|-------------------|
| `on_store` | Before storing an event | `handler(record: dict) -> dict` |
| `on_recall` | After recalling events | `handler(events: list[dict]) -> list[dict]` |
| `on_delete` | Before deleting record | `handler(record_id: str) -> bool` |
| `on_semantic_query` | Before semantic search | `handler(query: str) -> str` |

### 7.2 Example

```python
ETHAN_PLUGIN = {
    "memory_hooks": {
        "on_store": "enrich_before_store",
        "on_recall": "filter_results",
    },
}

def enrich_before_store(record):
    record["plugin_tag"] = "my-plugin"
    return record

def filter_results(events):
    return [e for e in events if e.get("status") != "internal"]
```

---

## 8. Event Subscriptions

### 8.1 Subscription Object

```json
{
  "subscriptions": {
    "ethan.intent.user": "handle_intent",
    "ethan.planner.plan.created": "on_plan",
    "ethan.executor.task.completed": "on_task_done"
  }
}
```

### 8.2 Rules

- Subject patterns follow NATS convention
- Dot-separated, wildcards `*` and `>` supported
- Handler receives event `dict` as argument
- Handler runs in plugin process, not kernel

---

## 9. Version Resolution

| Case | Behavior |
|------|----------|
| Same plugin name, same version | First found wins (priority: built-in > user > system) |
| Same plugin name, different version | Higher version wins |
| Missing `api_version` | Plugin rejected |
| `api_version` mismatch | Plugin rejected |
| Missing `manifest.json` | Plugin rejected |

Priority order when same version: **built-in → user → system**.

---

## 10. Example: Complete Plugin

### 10.1 Directory

```
hello-plugin/
├── manifest.json
├── plugin.py
└── assets/
    └── icon.png
```

### 10.2 manifest.json

```json
{
  "name": "hello-plugin",
  "version": "1.0.0",
  "api_version": "2",
  "description": "Example hello world plugin",
  "author": "ETHAN Team",
  "license": "MIT",
  "capabilities": [
    {
      "name": "hello.greet",
      "version": "1.0.0",
      "module": "hello-plugin",
      "inputs": ["hello.greet.request"],
      "outputs": ["hello.greet.complete"],
      "state_reads": [],
      "state_writes": [],
      "dependencies": [],
      "shared": false
    }
  ],
  "commands": {
    "hello": {
      "help": "Say hello",
      "handler": "cmd_hello",
      "args": [
        {"name": "name", "type": "str", "help": "Who to greet"}
      ]
    }
  },
  "subscriptions": {
    "ethan.intent.user": "on_intent"
  },
  "memory_hooks": {},
  "permissions": ["state:read:hello:*"],
  "dependencies": {}
}
```

### 10.3 plugin.py

```python
"""ETHAN Plugin: hello-plugin — example minimal plugin."""
ETHAN_PLUGIN = {
    "name": "hello-plugin",
    "version": "1.0.0",
    "api_version": "2",
    "capabilities": [
        {
            "name": "hello.greet",
            "version": "1.0.0",
            "module": "hello-plugin",
            "inputs": ["hello.greet.request"],
            "outputs": ["hello.greet.complete"],
        }
    ],
    "commands": {
        "hello": {
            "help": "Say hello",
            "handler": "cmd_hello",
            "args": [{"name": "name", "type": "str", "help": "Who to greet"}],
        }
    },
    "subscriptions": {},
}

def cmd_hello(args):
    print(f"Hello, {args[0]}!")
```

---

## Appendix A: Schema Validation Rules

1. `manifest.json` must be valid JSON
2. `manifest.json` must contain all required fields
3. `manifest.json` capabilities must match `ETHAN_PLUGIN` capabilities
4. `api_version` must equal core API version
5. No duplicate capability names within the same plugin
6. No duplicate command names within the same plugin
7. Command handler functions must exist in `plugin.py`
8. Subscription handler functions must exist in `plugin.py`
9. Permission patterns must follow defined format
10. `dependencies.python` version must satisfy current runtime



---

## Appendix B: Changelog (Plugin API)

| Version | Changes |
|---------|---------|
| 1 | Initial plugin API |
| 2 | Added `permissions`, `memory_hooks`; renamed `handlers` → `subscriptions` |