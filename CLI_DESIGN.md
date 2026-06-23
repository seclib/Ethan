# ETHAN CLI Visual Identity

## Philosophy

ETHAN CLI is not a terminal prompt — it is a **cognitive terminal interface**. Every character must feel intentional. No clutter. No noise. Premium developer tool.

---

## 1. Color System

### 1.1 Palette (16 ANSI, terminal-safe)

```
ETHAN Blue      \033[38;5;39m  │ Primary accent, brand identity
ETHAN Cyan      \033[38;5;44m  │ Information, data, neutral context
ETHAN Green     \033[38;5;42m  │ Success, confirmation, ready state
ETHAN Yellow    \033[38;5;220m │ Warnings, attention required
ETHAN Red       \033[38;5;196m │ Errors, failures, critical
ETHAN Purple    \033[38;5;135m │ Thinking, reasoning, meta
ETHAN Dim       \033[38;5;245m │ Secondary text, metadata, timestamps
ETHAN White     \033[38;5;255m │ Primary text
ETHAN Bold      \033[1m        │ Only for emphasis, never for decoration
ETHAN Reset     \033[0m        │ Back to terminal default
```

### 1.2 Usage Rules

| Element | Color | Why |
|---------|-------|-----|
| Brand prefix `◆` | Blue | Primary identity marker |
| Prompts `>` | Blue | Active input state |
| Status indicators | Green / Yellow / Red | At-a-glance system state |
| Thinking indicator | Purple | Active cognitive processing |
| Timestamps | Dim | Present but not distracting |
| Errors | Red + Bold | Cannot be missed |
| Success confirmations | Green on new line | Positive reinforcement |
| User input | White | Neutral, readable |
| System output | Cyan | Differentiated from user text |
| File paths | Cyan + Dim | Technical but secondary |

### 1.3 What NOT to do

- No blinking text
- No background colors (terminal compatibility)
- No more than 2 colors per line
- No color gradients or 24-bit (fails on basic terminals)

---

## 2. Typography & Spacing

### 2.1 Prompt Line

```
◆  ethan  ◇  working  ▸
```

**Anatomy**:
```
◆           — brand marker (blue)
ethan       — system name (bold white)
◇           — separator (dim)
working     — state badge (cyan)
▸           — input cursor (blue)
```

**State badges**:
| State | Badge | Color |
|-------|-------|-------|
| Ready | `idle` | Green |
| Processing | `working` | Cyan |
| Error | `error` | Red |
| Thinking | `thinking` | Purple |
| Autonomous | `auto` | Cyan |

### 2.2 Output Blocks

```
◆  Result                     <- header (blue), blank line before
✓ Deployed 3 services         <- content (white)
  → api-gateway               <- sub-item (cyan, indent 2 spaces)
  → user-service
  → notification
  ⏱ 2.3s                      <- metadata (dim), new line

◆  Error                      <- error header (red)
✗ Connection refused           <- error message (red)
  → host: localhost:4222       <- context (dim)
  → try: ethan daemon start    <- suggestion (cyan)
```

### 2.3 Spacing Rules

- 1 blank line before every `◆` section
- 0 blank lines between bullet items
- 1 blank line after sections (except last)
- 2-space indent for sub-items
- 4-space indent for code/data blocks

### 2.4 Line Width

- Max 120 characters (hard wrap at word boundary)
- Break long lines with `↳  ` (3-space continuation indent)

```
◆  Long output that exceeds the maximum line width and needs to
↳  be wrapped with continuation indent for readability
```

---

## 3. Prompt Modes

### 3.1 Single Command Mode

```
◆  ethan  ◇  idle  ▸ build docker
```

### 3.2 Interactive Chat Mode

```
◆  ethan  ◇  chat  ▸
```

Raw input line. No prefix per message. History accessible with ↑↓.

### 3.3 Streaming Mode (thinking)

```
◆  ethan  ◇  thinking  ▸

  ■  Querying capability registry...
  ■  Found docker.build (v1.0.0)
  ■  Deploying service...
  ✓  Complete (3.2s)
```

Spinner animation on `■` (rotates through `◐◓◑◒` during work).

---

## 4. Output Formatting Rules

### 4.1 Status Messages

```
✓  OK                        # success (green)
✗  FAILED                    # error (red)
⚠  WARNING                   # warning (yellow)
ℹ  INFO                      # info (cyan)
○  OFFLINE                   # offline state (dim)
●  ONLINE                    # online state (green)
◆  SECTION                   # section header (blue)
→  ITEM                      # list item (cyan)
↳  CONTINUATION              # line wrap (dim + indent)
```

### 4.2 Timing & Metadata

Always on the last line of a section, in dim. Format: `⏱ <duration><unit>` or `@ <timestamp>`.

```
◆  Result
✓ System online
  → 3 modules active
  ⏱ 1.2s
```

### 4.3 Structured Data

```json
{
  "key": "value"
}
```

- Preceded by `◆  Data` header
- Syntax-highlighted with minimal color (keys cyan, values white, strings dim)
- Max 20 lines, truncate with `… (+N more)`

### 4.4 Errors

```
◆  Error
✗ <error title>              <- bold red
  → <context>                 <- dim
  → <suggestion>              <- cyan
```

Always include a suggestion line when possible. Never show raw stack traces.

---

## 5. Progress Indicators

### 5.1 Spinner

```
  ◐  Loading...
  ◓
  ◑
  ◒
```

Characters: `◐◓◑◒` — rotates clockwise. Placed at column 0, 2-space indent.

### 5.2 Progress Bar

Only for operations with known total (installing, downloading):

```
  [████████░░░░]  67%  (3/5 plugins installed)
```

- 8 block characters wide
- Filled: `█` (dark), Empty: `░` (dim)
- Percentage on the right
- Description in dim

### 5.3 Stepped Progress

For multi-step operations:

```
◆  Installing plugin
  ✓  Copied files            (0.3s)
  ✓  Installed dependencies   (2.1s)
  ✓  Validated capabilities   (0.1s)
  ✓  Registered commands      (0.0s)
  ✓  Complete                 (2.5s)
```

---

## 6. Special Modes

### 6.1 Thinking Mode

When ETHAN is processing (LLM call, planning), show a purple thinking section:

```
◆  ethan  ◇  thinking  ▸ deploy

  ■  Analyzing intent...
  ■  Decomposing goal into tasks
  ■  Querying docker.build capability
  ✓  Complete
```

The `■` character animates as a spinner during active processing. Results appear in real time.

### 6.2 Confirmation Mode

For destructive operations:

```
◆  Confirm
  Destroy production database? [y/N] ▸
```

- `y` = green confirmation message
- Anything else = red "Cancelled"
- Timeout after 30s = `⚠  Timeout, assuming no`

### 6.3 Suggest Mode (autocomplete)

```
◆  ethan  ◇  idle  ▸ status

  Did you mean?
  → ethan status
  → ethan daemon status
  → ethan service status
```

---

## 7. Theme Implementation

### 7.1 Color Constants

File: `cli/core/colors.py`

```python
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    BLUE    = "\033[38;5;39m"
    CYAN    = "\033[38;5;44m"
    GREEN   = "\033[38;5;42m"
    YELLOW  = "\033[38;5;220m"
    RED     = "\033[38;5;196m"
    PURPLE  = "\033[38;5;135m"
    WHITE   = "\033[38;5;255m"
```

### 7.2 Icon Constants

```python
class I:
    CHECK   = "✓"
    CROSS   = "✗"
    WARN    = "⚠"
    INFO    = "ℹ"
    ARROW   = "→"
    WRAP    = "↳"
    SECTION = "◆"
    SPINNER = ["◐", "◓", "◑", "◒"]
    TIMER   = "⏱"
    DOT     = "●"
    CIRCL   = "○"
    INPUT   = "▸"
```

### 7.3 Formatter Functions

```python
def section(title):
    return f"{C.BLUE}{I.SECTION} {title}{C.RESET}"

def success(msg):
    return f"  {C.GREEN}{I.CHECK} {msg}{C.RESET}"

def error(title, context=None, suggestion=None):
    lines = [f"{C.RED}{I.CROSS} {title}{C.RESET}"]
    if context:
        lines.append(f"  {C.DIM}{I.ARROW} {context}{C.RESET}")
    if suggestion:
        lines.append(f"  {C.CYAN}{I.ARROW} {suggestion}{C.RESET}")
    return "\n".join(lines)

def metadata(text):
    return f"  {C.DIM}{I.TIMER} {text}{C.RESET}"

def prompt(state="idle"):
    color = {"idle": C.GREEN, "working": C.CYAN, "error": C.RED, "thinking": C.PURPLE}
    badge = color.get(state, C.CYAN)
    return f"{C.BLUE}{I.SECTION}{C.RESET}  {C.BOLD}ethan{C.RESET}  {badge}{state}{C.RESET}  {C.BLUE}{I.INPUT}{C.RESET} "
```

---

## 8. Anti-Patterns (forbidden)

| Pattern | Why |
|---------|-----|
| `>>>` prompts | Python REPL, not cognitive runtime |
| `$` prompts | Shell, not ETHAN |
| Bold everywhere | Only for emphasis, never decoration |
| Rainbow colors | Unprofessional, terminal-incompatible |
| Progress bars for unknown durations | Misleading |
| Stack traces shown raw | Use structured error blocks |
| Inconsistent icon spacing | 2-space indent always |