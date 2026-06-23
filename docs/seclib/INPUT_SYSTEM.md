# ETHAN Input System

## Philosophy

Input is the primary touchpoint. It must feel **native, responsive, and intelligent**. Every keystroke matters. No latency, no surprises. Professional terminal input experience.

---

## 1. Core Requirements

### 1.1 Multi-line Input

- Enter: submit (if single line) or newline (if shift+enter or in multi-line mode)
- Multi-line trigger: `\` at end of line (like bash)
- Preview: show continuation prompt

```
◆  ethan  ◇  idle  ▸ echo "hello \
↳  world"
```

### 1.2 Command Editing

- Full line editing (left/right arrows)
- Word navigation (alt+left/right)
- Home/End support
- Backspace/Delete cross lines

### 1.3 History Navigation

- Up/Down arrows: traverse history
- History persisted per session
- Deduplication: skip sequential duplicates
- Search: Ctrl+R (reverse search)

```
◆  ethan  ◇  idle  ▸ (Ctrl+R)
  [search]: docker build
    → ethan run docker build
```

### 1.4 Autocomplete Suggestions

- TAB: complete to longest common prefix
- Double TAB: show all matches
- Context-aware: suggests based on current input + history

```
◆  ethan  ◇  idle  ▸ ru<TAB>
                                └─► run
```

### 1.5 Paste-safe Input

- Paste trigger: detect bracketed paste mode (`\e[200~`)
- Paste buffer: accumulate until complete
- Submit automatically if buffer contains newlines
- No processing until paste complete

---

## 2. Input States

### 2.1 State Machine

```
IDLE → EDITING → SUBMITTED
  │       │         │
  │       │         └──► PROCESSING
  │       │
  │       ├──► MULTI_LINE
  │       │         │
  │       │         └──► SUBMITTED
  │       │
  │       └──► SEARCH (Ctrl+R)
  │                 │
  │                 └──► EDITING
  │
  └──► HISTORY (Up/Down)
```

### 2.2 Prompts per State

| State | Prompt | Example |
|-------|--------|---------|
| `idle` | `◆ ethan ◇ idle ▸` | Default |
| `editing` | `◆ ethan ◇ idle ▸` | Same as idle |
| `multi` | `↳` | Continuation |
| `search` | `[search]:` | Ctrl+R mode |
| `thinking` | `◆ ethan ◇ thinking ▸` | Processing |

---

## 3. Implementation

### 3.1 Input Handler

```python
class InputHandler:
    def __init__(self, prompt_fn, completer_fn):
        self.prompt_fn = prompt_fn
        self.completer_fn = completer_fn

    def read(self) -> str:
        """Read a line with full editing support."""
        ...

    def read_multiline(self) -> str:
        """Read multiple lines until submit."""
        ...

    def search_history(self, query: str) -> str:
        """Reverse search through history."""
        ...
```

### 3.2 History

```python
class History:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def append(self, text: str):
        """Add to history, deduplicate sequential."""
        ...

    def prev(self) -> str | None:
        """Get previous entry."""
        ...

    def next(self) -> str | None:
        """Get next entry."""
        ...

    def search(self, query: str) -> str | None:
        """Reverse search."""
        ...
```

---

## 4. Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Submit (single line) or newline (multi-line) |
| `Shift+Enter` | Force newline |
| `Ctrl+C` | Cancel current input |
| `Ctrl+D` | Exit (EOF) |
| `Up` | Previous history |
| `Down` | Next history |
| `Left/Right` | Cursor movement |
| `Home` | Start of line |
| `End` | End of line |
| `Ctrl+A` | Start of line |
| `Ctrl+E` | End of line |
| `Ctrl+W` | Delete word backward |
| `Ctrl+U` | Clear line |
| `Ctrl+K` | Delete to end of line |
| `Ctrl+R` | Reverse history search |
| `Tab` | Autocomplete |
| `Esc` | Cancel multi-line / clear search |

---

## 5. Paste Safety

### 5.1 Detection

Bracketed paste mode (most modern terminals):
```
\e[200~  <-- start
<content>
\e[201~  <-- end
```

### 5.2 Handling

```python
def read_with_paste_support(stream):
    buffer = ""
    in_paste = False
    while True:
        chunk = stream.read(1)
        if chunk == "\x1b":  # ESC
            seq = stream.read(2)
            if seq == "[200~":
                in_paste = True
                continue
            elif seq == "[201~":
                in_paste = False
                # Submit if multi-line detected
                if "\n" in buffer:
                    return buffer
                continue
        if in_paste:
            buffer += chunk
        else:
            # Normal input handling
            ...
```

---

## 6. UX Patterns

### 6.1 Multi-line Example

```
◆  ethan  ◇  idle  ▸ cat << EOF
↳  Hello
↳  World
↳  EOF
```

### 6.2 History Search Example

```
◆  ethan  ◇  idle  ▸ (Ctrl+R)
  [search]: docker
    (reverse-i-search)`docker': ethan run docker build
```

### 6.3 Autocomplete Example

```
◆  ethan  ◇  idle  ▸ sta<TAB>
                                └─► status
```

or with multiple matches:

```
◆  ethan  ◇  idle  ▸ st<TAB><TAB>
  → status
  → stop
  → start
```

---

## 7. Constraints

- Max input length: 10,000 characters
- Max multi-line: 100 lines
- History size: 1,000 entries per session
- Search timeout: 5s (return to normal input)

---

## Appendix: Terminal Compatibility

| Feature | xterm | tmux | screen | Windows Terminal |
|---------|-------|------|--------|-----------------|
| Bracketed paste | ✅ | ✅ | ✅ | ✅ |
| Arrow keys | ✅ | ✅ | ✅ | ✅ |
| Ctrl+R | ✅ | ✅ | ✅ | ✅ |
| Multi-line prompt | ✅ | ✅ | ✅ | ✅ |