# ETHAN CLI Brand Feel

## Philosophy

ETHAN is not a toy. It is a **precision instrument** for developers who think in code. The UI must reflect that: calm, confident, intelligent. Every element earns its place. Nothing is decorative.

---

## 1. Core Adjectives

| Adjective | Manifestation |
|-----------|---------------|
| **Calm** | No flashing, no urgency, soothing blue/cyan palette, steady spinner |
| **Precise** | Monospace alignment, consistent 2-space indent, exact spacing |
| **Intelligent** | Smart suggestions, context awareness, proactive hints |
| **Non-noisy** | One status per line, minimal icons, dim metadata |
| **Developer-focused** | Keyboard-driven, respects terminal norms, no hand-holding |

---

## 2. Visual Identity

### 2.1 Color Temperature

```
Primary:   Blue  →  Trust, intelligence, calm
Secondary: Cyan  →  Information, data, neutral
Success:   Green →  Confirmation, ready
Warning:   Yellow →  Attention, not alarm
Error:     Red   →  Failure, clear but not aggressive
Thinking:  Purple →  Cognitive process, meta
Neutral:   Dim   →  Recedes, supports primary content
```

**Rule**: No more than 2 colors on any line. Primary + neutral, or neutral + accent.

### 2.2 Icon Budget

ETHAN uses a strict icon vocabulary. No ad-hoc symbols.

| Icon | ASCII Fallback | Use Count |
|------|---------------|-----------|
| `◆` | `*` | Brand marker only |
| `✓` | `[OK]` | Success confirmation |
| `✗` | `[!!]` | Error state |
| `⚠` | `[!!]` | Warning state |
| `ℹ` | `[i]` | Info hint |
| `→` | `->` | List items, suggestions |
| `⏱` | `t=` | Timing metadata |
| `●` / `○` | `*` / `o` | Online/offline status |
| `▸` | `>` | Input prompt cursor |
| `◐◓◑◒` | `-\|/` | Spinner frames |

**Max 3 icons per screen section** (not counting list items).

### 2.3 Typography

- Font: system monospace (no custom fonts)
- Weight: regular + bold only (no italics, no underline)
- Size: inherited from terminal
- Alignment: left-aligned, consistent indent (2 spaces)
- Line height: single-spaced (no blank lines within sections)

---

## 3. Tone of Voice

### 3.1 Principles

| Principle | Example |
|-----------|---------|
| **Direct** | "API unreachable" not "There seems to be an issue" |
| **Actionable** | Every error ends with a next step |
| **Calm** | "Timeout" not "CRITICAL FAILURE" |
| **Concise** | One idea per line |
| **Specific** | "exit code 1" not "something went wrong" |

### 3.2 Word Choice

| Use | Avoid |
|-----|-------|
| Clear, specific terms | Vague jargon |
| Action verbs | Passive voice |
| "try:" | "You should probably" |
| "Failed" | "Unsuccessfully" |
| "Cancelled" | "Aborted" |

---

## 4. Interaction Design

### 4.1 Response Time Standards

| Action | Target | Feedback |
|--------|--------|----------|
| Command parse | < 50ms | Immediate prompt return |
| API call | < 2s | Typing indicator `ⓘ ethan` |
| Long operation | > 2s | Spinner + hint |
| Streaming LLM | variable | Token-by-token render |

### 4.2 Feedback Rules

1. **Always show progress** if wait > 500ms
2. **Never block without indication**
3. **Confirm success** with `✓` (not silence)
4. **Explain failure** with `✗` + context + fix
5. **Never repeat** the same hint twice in a session

### 4.3 Keyboard-First

- `TAB` : autocomplete
- `↑↓` : history
- `CTRL+C` : cancel (always works)
- `CTRL+D` : exit
- `/` : built-in commands (no prefix needed in chat)

---

## 5. Output Discipline

### 5.1 Noise Budget

Per interaction:
- Max 1 section header
- Max 3 status lines
- Max 5 list items
- Max 1 timing footer
- No decorative ASCII art
- No banner ads (even for ETHAN itself)

### 5.2 Density Control

| Screen State | Max Lines | Max Colors |
|--------------|-----------|------------|
| Idle prompt | 1 | 2 |
| Success response | 5 | 3 |
| Error response | 4 | 3 |
| Help screen | 20 | 2 |
| Streaming output | dynamic | 1 (text color only) |

### 5.3 Verbosity Levels

| Flag | Behavior |
|------|----------|
| (default) | Minimal output, status only |
| `--verbose` | Show timing, context details |
| `--debug` | Include stack traces on errors |
| `--quiet` | Errors only, no success confirmations |

---

## 6. Emotional Design

### 6.1 How ETHAN Feels

```
User opens terminal
    │
    ▼
Prompt: ◆ ethan ◇ idle ▸
    → Calm, ready, no flashing
    │
    ▼
User runs command
    │
    ▼
⠋ Working... (or streaming tokens)
    → Responsive, alive, predictable
    │
    ▼
Result:
  ✓ Done (1.2s)
  → Satisfying, precise
    │
    ▼
Error:
  ✗ Something failed
    → Helpful, not blaming
```

### 6.2 Anti-Feel

| What Users Hate | ETHAN Does Not Do |
|-----------------|-------------------|
| Screaming colors | Max 2 colors per line |
| Wall of text | Strict line budgets |
| Unknown unknowns | Always suggest next action |
| Mysterious hangs | Always show spinner/progress |
| Preachy errors | Calm, actionable, specific |

---

## 7. Implementation Rules

### 7.1 Code-Level Discipline

```python
# Good: direct, structured
print(clr.success("Deployed"))

# Bad: verbose, emotional
print(clr.success("🎉 Amazing! Your deployment was successfully completed!"))
```

### 7.2 Icon Usage

```python
# Good: 1 icon per status line
print(clr.success("Done"))

# Bad: multiple icons, excessive decoration
print("🎉 ✅ 🚀 Deployment completed successfully! 🎊")
```

### 7.3 Spacing

```python
# Good: 1 blank line between sections
print()
print(clr.section("Result"))
print(clr.success("Done"))

# Bad: excessive whitespace
print()
print()
print(clr.section("Result"))
print()
print(clr.success("Done"))
print()
```

---

## 8. Developer Ergonomics

### 8.1 Copy-Paste Friendly

- No ANSI codes in structured output (disable with `NO_COLOR=1`)
- JSON output always clean (no ANSI)
- Logs in structured format (JSON lines)

### 8.2 Scriptable

- Exit codes: 0 = success, 1 = error, 2 = usage error
- `--json` flag for machine-readable output
- `--quiet` for CI pipelines

---

## Appendix: Brand Checklist

Before shipping any UI change, check:

- [ ] Max 2 colors per line
- [ ] Max 3 icons per section
- [ ] No emojis outside defined icon set
- [ ] No decorative ASCII art
- [ ] Every error has a suggestion
- [ ] Every wait has feedback
- [ ] No hint repeated twice
- [ ] Exit codes correct
- [ ] JSON output clean
- [ ] Respects `NO_COLOR=1`