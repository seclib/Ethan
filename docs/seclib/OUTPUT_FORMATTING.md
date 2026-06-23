# ETHAN Output Formatting System

## Philosophy

Output is communication, not decoration. Every character must serve a purpose. Readable, structured, minimal noise. Terminal-safe first.

---

## 1. Foundations

### 1.1 Design Principles

| Principle | Rule |
|-----------|------|
| **Terminal-safe** | No 24-bit color, no background fills, no Unicode combining |
| **Scannable** | Headers, bullets, spacing make structure obvious at a glance |
| **Consistent** | Same concepts always look the same |
| **Minimal** | Remove decorative elements; keep only functional whitespace |
| **Resilient** | Degrade gracefully on width < 80 columns |

### 1.2 Anatomy of an Output Block

```
┌─ Header ─────────────────────────────────────────┐
│ ◆  Section Title                                  │
│                                                   │
│   ✓  success line                                 │
│   →  list item                                    │
│       code example here                           │
│                                                   │
│ ─ footer ──────────────────────────────────────── │
│   ⏱ 2.3s                                          │
└───────────────────────────────────────────────────┘
```

---

## 2. Headers

### 2.1 Section Header

```python
def section(title: str, subtitle: str = "") -> str:
    return f"{C.BLUE}{I.SECTION} {title}{C.RESET}  {C.DIM}{subtitle}{C.RESET}"
```

```
◆ Result    [POST /v1/message 201]
```

### 2.2 Sub-header

```python
def subheader(text: str) -> str:
    return f"{C.BOLD}{text}{C.RESET}"
```

```
Properties
```

### 2.3 Divider

```python
DIVIDER = f"{C.DIM}{'─' * 40}{C.RESET}"
```

```
─────────────────────────────────────────────
```

---

## 3. Success / Warning / Error States

### 3.1 Success (green)

```
✓  Deployed 3 services
```

```python
def success(msg: str) -> str:
    return f"  {C.GREEN}{I.CHECK} {msg}{C.RESET}"
```

### 3.2 Warning (yellow)

```
⚠  Disk space low (12% free)
```

```python
def warning(msg: str) -> str:
    return f"  {C.YELLOW}{I.WARN} {msg}{C.RESET}"
```

### 3.3 Error (red, structured)

```
✗ Connection refused
  → host: localhost:4222
  → try: ethan daemon start
```

```python
def error(title: str, context: str = "", suggestion: str = "") -> str:
    parts = [f"  {C.RED}{I.CROSS} {title}{C.RESET}"]
    if context:
        parts.append(f"    {C.DIM}{I.ARROW} {context}{C.RESET}")
    if suggestion:
        parts.append(f"    {C.CYAN}{I.ARROW} {suggestion}{C.RESET}")
    return "\n".join(parts)
```

### 3.4 Info (cyan)

```
ℹ  Running diagnostics...
```

```python
def info(msg: str) -> str:
    return f"  {C.CYAN}{I.INFO} {msg}{C.RESET}"
```

---

## 4. Code Blocks

### 4.1 Inline Code

```
Use `docker build` to create an image.
```

```python
def inline_code(text: str) -> str:
    return f"{C.CYAN}`{text}`{C.RESET}"
```

### 4.2 Fenced Code Block (terminal-safe)

````
    ┌─ Python ─────────────────────────────────┐
    │ def hello():                             │
    │     print("Hello, World!")               │
    └──────────────────────────────────────────┘
````

```python
def code_block(language: str, code: str) -> str:
    lines = code.strip().split("\n")
    header = f"{C.DIM}┌─ {language} {'─' * max(0, 40 - len(language))}┐{C.RESET}"
    footer = f"{C.DIM}└{'─' * 40}┘{C.RESET}"
    body = "\n".join(f"    {C.WHITE}{line}{C.RESET}" for line in lines)
    return f"{header}\n{body}\n{footer}"
```

**Rules**:
- Max width 42 chars (inner content)
- Language label in header
- 4-space outer indent
- No syntax highlighting (Just White on Dim border)
- Truncate lines > 40 with `…`

### 4.3 Multi-line Output

```
  output line 1
  output line 2
  output line 3
```

```python
def output_lines(lines: list[str]) -> str:
    return "\n".join(f"  {C.DIM}{line}{C.RESET}" for line in lines)
```

---

## 5. Tables (terminal-safe)

### 5.1 Simple Table

```
  Name           Status    Port
  ─────────────────────────────
  api-gateway   ● ONLINE  8080
  user-service  ● ONLINE  3000
  db            ○ OFFLINE -
```

```python
def table(headers: list[str], rows: list[list[str]], status_col: int = -1) -> str:
    col_widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    # Header
    out = [f"  {'  '.join(h.ljust(w) for h, w in zip(headers, col_widths))}"]
    # Divider
    out.append(f"  {'  '.join('─' * w for w in col_widths)}")
    # Rows
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell = str(cell)
            if i == status_col:
                # Status column: preserve Unicode icons
                cells.append(cell.ljust(col_widths[i]))
            else:
                cells.append(cell.ljust(col_widths[i]))
        out.append(f"  {'  '.join(cells)}")
    return "\n".join(out)
```

### 5.2 Status Icons in Tables

| Icon | Meaning | Color |
|------|---------|-------|
| `● ONLINE` | Running, healthy | Green |
| `○ OFFLINE` | Stopped | Dim |
| `◐ DEGRADED` | Partial failure | Yellow |
| `✗ ERROR` | Crashed | Red |

### 5.3 Table Rules

- Column separator: 2 spaces
- Header divider: `─` repeated per column width
- No vertical borders (too noisy)
- Max 6 columns (beyond that: use `key: value` pairs instead)
- Truncate cells > max_width with `…`

---

## 6. Lists

### 6.1 Unordered List

```
  → first item
  → second item
    with continuation
  → third item
```

### 6.2 Numbered List

```
  1.  first step
  2.  second step
  3.  third step
```

```python
def numbered_list(items: list[str], start: int = 1) -> str:
    width = len(str(len(items) + start))
    return "\n".join(
        f"  {str(i).rjust(width)}.  {item}" for i, item in enumerate(items, start=start)
    )
```

### 6.3 Definition List (key: value)

```
  name:      my-service
  version:   1.2.0
  status:    ● ONLINE
```

```python
def definition_list(pairs: dict[str, str]) -> str:
    max_key = max(len(k) for k in pairs) if pairs else 0
    return "\n".join(
        f"  {k.ljust(max_key)}:  {v}" for k, v in pairs.items()
    )
```

---

## 7. Metadata & Timing

### 7.1 Timing Footer

```
  ⏱ 2.3s
  @ 2026-06-23T20:00:00Z
```

```python
def timing(duration: float, timestamp: str = "") -> str:
    parts = [f"{C.DIM}{I.TIMER} {duration:.1f}s{C.RESET}"]
    if timestamp:
        parts.append(f"{C.DIM}@ {timestamp}{C.RESET}")
    return f"  {'  '.join(parts)}"
```

### 7.2 Counters

```
  3 services  |  2 warnings  |  0 errors
```

```python
def counters(**kwargs: int) -> str:
    parts = [f"{v} {k}" for k, v in kwargs.items()]
    return f"  {C.DIM}{'  |  '.join(parts)}{C.RESET}"
```

---

## 8. Spinner & Progress

### 8.1 Animated Spinner

```
  ◐ Loading...
```

Rotates through `◐◓◑◒`. Use `Streamer` from `core/streaming.py`.

### 8.2 Progress Bar

```
  [████████░░░░]  67%  (3/5 plugins installed)
```

```python
def progress(current: int, total: int, width: int = 12, label: str = "") -> str:
    filled = int(width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * current / total) if total > 0 else 0
    suffix = f"  {pct}%"
    if label:
        suffix += f"  ({label})"
    return f"  [{C.CYAN}{bar}{C.RESET}]{suffix}"
```

---

## 9. Combining Blocks

### 9.1 Full Example

```python
print()
print(section("Deploy Result", "POST /v1/deploy"))
print()
print(success("Deployed 3 services"))
print(warning("API health check pending"))
print(error("DB connection slow", "latency 1.2s", "check network"))
print()
print(subheader("Services"))
print(table(
    ["Name", "Status", "Port"],
    [
        ["api-gateway", "● ONLINE", "8080"],
        ["user-service", "● ONLINE", "3000"],
        ["db", "○ OFFLINE", "-"],
    ],
    status_col=1
))
print()
print(timing(2.3, "2026-06-23T20:00:00Z"))
print(counters(services=3, warnings=2, errors=0))
print()
print(code_block("bash", "ethan logs --follow"))
print(divider())
```

### 9.2 Block Spacing

- 1 blank line before a section
- 0 blank lines inside a section (between elements)
- 1 blank line after a section
- 4-space indent for nested content

---

## 10. Graceful Degradation

| Condition | Adaptation |
|-----------|-------------|
| Width < 80 | Wrap long cells, reduce progress bar to 8 chars |
| No color support | Strip ANSI, show `[OK]` instead of `✓` |
| No Unicode | Replace `─◆●○✗⚠` with ASCII `-*ox!` |
| Piped output | Remove spinner/animation, keep structure |

```python
def section(title, subtitle=""):
    if not sys.stdout.isatty():
        return f"[SECTION] {title}"
    return f"{C.BLUE}{I.SECTION}{C.RESET} {title}"