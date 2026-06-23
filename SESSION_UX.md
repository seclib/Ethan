# ETHAN Session UX Model

## Philosophy

Sessions should feel like **continuing a conversation with a colleague** — you know who you're talking to, you remember what was discussed, but you don't need to be reminded constantly. The session UI is **visible but non-intrusive**.

---

## 1. Session ID Display

### 1.1 Minimal Session ID

```
◆  ethan  ◇  chat  ▸
```

The session ID is **not** shown in the prompt. It's only visible on demand (`/session` command) or in the welcome banner.

### 1.2 Welcome Banner

```
◆  ETHAN Chat  ◇  session a1b2c3d4

  Ctrl+D or /exit to quit  •  /help for commands
```

Rules:
- Show on session start
- Show on `/resume`
- Show session ID truncated to 8 chars
- One-line footer with hints

---

## 2. Context Awareness Indicator

### 2.1 Position

The context indicator appears **between the prompt and the input**, or in the prompt badge.

```
◆  ethan  ◇  chat · 12 ctx  ▸
```

or (simpler):

```
◆  ethan  ◇  chat  ▸
```

with `/ctx` showing:

```
◆  Context  ◇  session a1b2c3d4
  Memory: 12 previous interactions
  Context window: 4,096 tokens used / 8,192 max
  Last activity: 2 minutes ago
```

### 2.2 Badge States

| State | Badge | When |
|-------|-------|------|
| `chat` | Blue | Default chat |
| `chat · 12` | Cyan | 12 context items loaded |
| `chat · max` | Yellow | Context window nearly full |
| `chat · new` | Green | Fresh session, no history |

### 2.3 Context Thresholds

| Items | Badge | Action |
|-------|-------|--------|
| 0 | `new` | — |
| 1–10 | (none) | — |
| 11–50 | `· N` | Show count |
| >50 | `· max` | Warn, suggest `/reset` |

---

## 3. Memory Hint

### 3.1 On Resume

```
◆  ETHAN Chat  ◇  session a1b2c3d4

  12 previous interactions restored
```

### 3.2 In Chat (subtle)

When context is loaded, show a one-time hint:

```
  ℹ  Using 12 previous interactions for context
```

Only shown once per session, on first AI response that uses memory.

### 3.3 On Reset

```
◆  Context cleared
  ✓ Session reset — fresh start
```

---

## 4. Context Reset

### 4.1 Commands

| Command | Action |
|---------|--------|
| `/reset` | Clear context, keep session ID |
| `/new` | New session (new ID) |
| `/session` | Show session info |
| `/ctx` | Show context details |

### 4.2 Reset Flow

```
User: /reset
    │
    ▼
Clear memory context for session
    │
    ▼
Show confirmation:
◆  Context cleared
  ✓ Session reset — fresh start
    │
    ▼
New prompt:
◆  ethan  ◇  chat  ▸
```

### 4.3 New Session Flow

```
User: /new
    │
    ▼
Save current session
    │
    ▼
Create new session ID
    │
    ▼
Show banner:
◆  ETHAN Chat  ◇  session xxxx
  ✓ New session started
```

---

## 5. Session Information API

### 5.1 Data Model

```python
@dataclass
class SessionInfo:
    id: str                    # Full UUID
    short_id: str              # 8-char truncated
    created_at: str            # ISO timestamp
    last_activity: str         # ISO timestamp
    message_count: int         # Total messages
    context_items: int         # Memory entries used
    context_tokens: int        # Estimated token usage
    context_max: int           # Max context window
```

### 5.2 Commands

```python
def show_session_info(session_id: str) -> SessionInfo:
    """Return session metadata."""

def get_context_usage(session_id: str) -> tuple[int, int]:
    """Return (used, max) tokens."""

def reset_context(session_id: str) -> None:
    """Clear memory for session."""

def new_session() -> str:
    """Create new session, return new ID."""
```

---

## 6. UX Patterns

### 6.1 Prompt States

```
◆  ethan  ◇  chat  ▸                   # Default
◆  ethan  ◇  chat · 12  ▸              # Context loaded
◆  ethan  ◇  chat · max  ▸             # Context full
◆  ethan  ◇  chat · new  ▸             # Fresh session
◆  ethan  ◇  thinking  ▸               # Processing
```

### 6.2 Context Actions

```
/session    Show session info
/ctx        Show context details
/reset      Clear context
/new        New session
/history    Show recent messages
```

### 6.3 Non-Intrusive Rules

| Rule | Why |
|------|-----|
| No session ID in prompt | Too noisy |
| Show context count only when > 10 | Avoid clutter |
| Show memory hint only once | Don't repeat |
| Show `/ctx` hint only on first context use | Guide without nagging |

---

## 7. Implementation

### 7.1 Memory Module Updates

File: `cli/core/memory.py`

```python
def get_session_info(session_id: str) -> dict:
    """Return session metadata."""

def get_context_usage(session_id: str) -> tuple[int, int]:
    """Return (used, max) context usage."""

def reset_context(session_id: str) -> None:
    """Clear memory context for session."""

def new_session() -> str:
    """Create new session ID."""
```

### 7.2 Chat Integration

```python
# On session start
session_id = mem.new_session()
info = mem.get_session_info(session_id)
show_welcome_banner(info)

# On first response with memory
if mem.get_context_usage(session_id)[0] > 0:
    print(clr.info(f"Using {count} previous interactions for context"))

# On /reset
mem.reset_context(session_id)
print(clr.success("Context cleared — fresh start"))
```

---

## 8. Visual Design

### 8.1 Welcome Banner

```
◆  ETHAN Chat  ◇  session a1b2c3d4

  Ctrl+D or /exit to quit  •  /help for commands
  /reset to clear context  •  /new for fresh session
```

### 8.2 Session Info (`/session`)

```
◆  Session  ◇  a1b2c3d4
  Created:    2026-06-23T20:00:00Z
  Last active: 2 minutes ago
  Messages:   12
  Context:    4,096 / 8,192 tokens (50%)
```

### 8.3 Context Details (`/ctx`)

```
◆  Context  ◇  a1b2c3d4
  Memory:  12 previous interactions
  Tokens:  4,096 used / 8,192 max
  Status:  ● healthy
  Reset:   /reset
```

### 8.4 After Reset

```
◆  Context cleared
  ✓ Fresh start — previous context removed
```

---

## 9. Anti-Patterns

| Avoid | Reason |
|-------|--------|
| Showing full session ID in prompt | Too long, noisy |
| Showing context count always | Clutters prompt |
| Repeating memory hint | Annoying |
| Auto-resetting context | User loses history |
| Hiding session ID completely | User cannot reference it for support |