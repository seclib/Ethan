# ETHAN CLI Discovery System

## Philosophy

A modern CLI must help users discover features without documentation. Group, suggest, and guide. Like `gh`, `docker`, or `kubectl`.

---

## 1. `ethan help` Design

### 1.1 Top-Level Help (grouped)

```
◆ ETHAN — Cognitive Runtime CLI

  Core
    chat       Interactive AI chat
    run        Execute via capabilities
    status     Show system state
    logs       Tail system logs
    help       Show help

  Advanced
    plugin     Manage plugins
    shell      Open ethan-shell
    config     Edit configuration
    daemon     Control background daemon

  Plugins (3 installed)
    security   Security scanner
    twitter    Twitter bot
    browser    Browser automation

  Global flags:
    -v, --version    Show version
    -h, --help       Show this help
    --debug          Show debug output

  Quick start:
    ethan chat                 Start AI chat
    ethan run docker build     Execute command
    ethan status               Show system state
```

### 1.2 Topic Help

```
◆ ethan chat — interactive AI chat

  Usage:
    ethan chat              Start new session
    ethan chat --resume     Resume last session

  Flags:
    -r, --resume            Resume previous session
    -h, --help              Show this help
```

### 1.3 Grouping Rules

| Group | Visibility | Commands |
|-------|-----------|----------|
| **Core** | Always shown | chat, run, status, logs, help |
| **Advanced** | Always shown | plugin, shell, config, daemon |
| **Plugins** | Shown if plugins installed | dynamic per plugin |
| **Flags** | Always shown | --version, --help, --debug |

---

## 2. Fuzzy Suggestions ("Did you mean...")

### 2.1 Triggers

- Unknown command: `ethan strat` → suggest `ethan status`
- Unknown subcommand: `ethan plugin add` → suggest `ethan plugin install`
- Typo in flag: `ethan chat --resme` → suggest `--resume`

### 2.2 Algorithm

1. Load all known commands into a list (core + advanced + plugins)
2. Calculate Levenshtein distance between input and each command
3. If distance <= 2 (short) or <= 3 (long), show suggestion
4. Rank by: distance, then alphabetical
5. Show top 3 matches

### 2.3 Examples

```
Input:  ethan staatus
Output: ✗ Unknown command: 'staatus'
        → Did you mean? ethan status

Input:  ethan plugun list
Output: ✗ Unknown command: 'plugun'
        → Did you mean? ethan plugin list

Input:  ethan shel
Output: ✗ No command found for 'shel'
        → Did you mean? ethan shell
```

---

## 3. Command Registration

### 3.1 Structure

```python
class Command:
    name: str          # "chat"
    group: str         # "core", "advanced", "plugin:security"
    description: str   # "Interactive AI chat"
    usage: str         # "ethan chat [--resume]"
    examples: list[str]  # ["ethan chat", "ethan chat --resume"]
    aliases: list[str]   # ["c", "ch"]
```

### 3.2 Registry

```python
registry = {
    "chat": Command("chat", "core", ...),
    "run": Command("run", "core", ...),
    "status": Command("status", "core", ...),
    "plugin": Command("plugin", "advanced", ...),
    "security.scan": Command("scan", "plugin:security", ...),
}
```

---

## 4. Discovery Features

### 4.1 Autocomplete (TAB)

```
◆  ethan  ◇  idle  ▸ pl<TAB>
                                └─► Autocomplete to: plugin
```

Single TAB: complete to longest common prefix.
Double TAB: show all matches.

### 4.2 Suggestions on Pause

After user stops typing for 200ms:

```
◆  ethan  ◇  idle  ▸ ru

  Did you mean?
  → ethan run
  → ethan shell
  → ethan status
```

### 4.3 Contextual Suggestions

```
After: ethan plugin
Suggest: install, list, remove, info
```

---

## 5. Implementation

### 5.1 Discovery Module

File: `cli/core/discovery.py`

```python
class CommandRegistry:
    def register(self, cmd: Command) -> None
    def get(self, name: str) -> Command | None
    def list(self, group: str | None = None) -> list[Command]
    def suggest(self, input: str, limit: int = 3) -> list[Command]
    def autocomplete(self, prefix: str) -> list[str]
```

### 5.2 Help Command

File: `cli/commands/help.py`

```python
@register("help")
def cmd_help(args):
    topic = args[0] if args else None
    if topic:
        show_topic_help(topic)
    else:
        show_top_level_help()
```

### 5.3 Integration

- All commands register themselves on import
- `ethan help` queries registry
- Unknown command handler queries `suggest()`
- Autocomplete queries `autocomplete()`

---

## 6. UX Patterns

| Pattern | Example |
|---------|---------|
| Unknown command | `✗ Unknown command: 'strat' → Did you mean? ethan status` |
| Unknown flag | `✗ Unknown flag: --resme → Did you mean? --resume` |
| No match | `✗ No suggestions found → Try: ethan help` |
| Multiple matches | `? Multiple matches: ethan plugin, ethan plugin list, ethan plugin install` |

---

## 7. Anti-Patterns

| Avoid | Reason |
|-------|--------|
| Alphabetical command list | Group by frequency/role |
| One big help page | Grouped, scannable |
| No examples | Users learn by example |
| Hidden plugins | Make them visible in help |
| Case-sensitive matching | Normalize to lowercase |
| Too many suggestions | Max 3, ranked by relevance |

---

## Appendix A: Command Groups Reference

```
Core:        chat, run, status, logs, help
Advanced:    plugin, shell, config, daemon
Global:      --version, --help, --debug
Plugins:     dynamic (loaded at runtime)