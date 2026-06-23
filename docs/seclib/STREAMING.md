# ETHAN Streaming Output System

## Philosophy

Claude Code teaches us: streaming is better than waiting. tokens appear **smoothly, continuously, without flicker**. The terminal should feel alive.

---

## 1. Rendering Model

### 1.1 In-place line update

```
Before: ⠋ ethan  Processing...
After:  ⠋ ethan  Querying registry...
```

Same line, same indentation, same color. Only text changes.

**Rules**:
- Same cursor position (no line breaks unless the model emits `\n`)
- ANSI escape sequence: `\033[<n>G` (move cursor to column n) or `\r` (carriage return)
- After finishing, print `\n` once

### 1.2 Mode 1: Streaming (preferred)

```python
streamer = Streamer()
streamer.start("Thinking...")

for chunk in response_stream:
    streamer.write(chunk)

streamer.done()
```

Output (`\r` returns cursor to line start):
```
⠋ ethan  Thinking...                         ← initial
⠋ ethan  Querying registry...               ← update
⠋ ethan  Building task plan...              ← update
⠋ ethan  Done                               ← update
                                              ← final \n after done()
```

### 1.3 Mode 2: Buffered (fallback)

If streaming fails (API doesn't support `text/event-stream`):
```python
streamer = Streamer()
streamer.start("Thinking...")

# Blocker: API blocks, no chunks
response_text = send_sync(msg)
streamer.write(response_text)  # single write, looks smooth
streamer.done()
```

### 1.4 Mode 3: Offline (last resort)

Network error:
```
⠋ ethan  Connection lost
✗ Streaming interrupted — falling back to batch result
```

---

## 2. Cancellation (CTRL+C)

```
1. User presses CTRL+C
2. Streamer raises KeyboardInterrupt-safe signal
3. Current line is cleared
4. Partial output is preserved (not rolled back)
5. Streamer enters cancelled state
6. Caller handles cancellation gracefully
```

```
⠋ ethan  Processing...  [CTRL+C]
⠋ ethan  Cancelled
```
(streamer keeps partial text for context; caller decides to retry, ignore, or abort)

---

## 3. Smoothness Guarantees

| Property | Mechanism |
|----------|-----------|
| **No flicker** | Write to same line, same escape sequence, no cursor jump |
| **No tearing** | Flush after every chunk (`sys.stdout.flush()`) |
| **No double-write** | Track `last_len`, clear only extra characters |
| **Stable cursor** | Keep cursor at end of text after every update |

### 3.1 Double-write prevention

```python
class Streamer:
    def write(self, chunk):
        new_text = self.current + chunk
        # Erase only what we previously wrote
        sys.stdout.write("\r" + " " * self._last_len + "\r")
        # Write new text
        sys.stdout.write(new_text)
        self._last_len = len(new_text)
        sys.stdout.flush()
```

### 3.2 Spinner integration

```
  ◐ Thinking...  (animated spinner, rotates every 200ms)
```

Spinner runs in a background thread (or async task). Text is drawn at fixed column after spinner.

---

## 4. State Machine

```
IDLE → STREAMING → DONE
         │         │
         │         └──► ERROR (fallback)
         │
         └──► CANCELLED (CTRL+C)
```

| State | Display | Action |
|-------|---------|--------|
| IDLE | (none) | Ready to stream |
| STREAMING | `⠋ ethan  <accumulated_text>` | Receiving chunks |
| DONE | `⠋ ethan  <full_text>` then newline | Completed |
| CANCELLED | `⠋ ethan  Cancelled` | Interrupted by user |
| FALLBACK | Static prompt → batch text | If stream fails |

---

## 5. Public API

```python
class Streamer:
    def start(self, hint: str = "Thinking...") -> None:
        """Begin stream. Prints initial line with spinner."""
        ...

    def write(self, chunk: str) -> None:
        """Append chunk and re-render smoothly."""
        ...

    def done(self) -> None:
        """Finalize stream. Print final \n."""
        ...

    def cancel(self) -> None:
        """Cancel stream. Print 'Cancelled', preserve context."""
        ...

    def fallback(self, text: str) -> None:
        """If streaming fails, replace with static text."""
        ...
```

---

## 6. Integration Points

| Component | Uses |
|-----------|------|
| `chat.py` | Streamer for assistant responses |
| `cli/commands/run.py` | Streamer for long-running task */
| `cli/commands/exec.py` | Streamer for command output |

---

## 7. Error Recovery

```
Streaming error (network, timeout, protocol)
    │
    ▼
Streamer.fallback(error_message)
    │
    ▼
Show compact error + retry choice
```

```
⠋ ethan  Stream interrupted
✗ Connection lost — retrying in 2s...               [fallback]

✓ Reconnected — resuming stream                      [recovered]
⠋ ethan  Resume querying...
```

---

## 8. Token vs Chunk

**Token-by-token**:
- `for token in llm.stream(...): streamer.write(token)`
- Smoothest, most responsive
- Requires SSE / WebSocket from API

**Chunk**:
- `for chunk in response.iter_content(1024): streamer.write(chunk)`
- Good enough for most cases
- Works with plain HTTP streaming

**Batch**:
- `streamer.write(response_text)`
- Fallback only

---

## 9. Example in chat.py

```python
def send_with_stream(msg, session_id):
    streamer = Streamer()
    streamer.start()

    try:
        for chunk in client.stream(msg, session_id):
            streamer.write(chunk)
        streamer.done()
    except KeyboardInterrupt:
        streamer.cancel()
        return None, "cancelled"
    except Exception as e:
        streamer.fallback(str(e))
        raise

    mem.record(session_id, "assistant", streamer.text)
    return streamer.text, streamer.latency

```

---

## 10. Future: Markdown/Code awareness

```
⠋ ethan  Sure. Here's a Python example:
                                              ← cursor stays here
```python
def hello():
    print("Hello")                          ← code block rendered without flicker
```
```

Requires parser integration (future). Not in MVP.