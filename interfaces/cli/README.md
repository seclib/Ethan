# ETHAN CLI — Terminal Interface

Terminal interface for ETHAN Cognitive Runtime, inspired by Claude Code and Gemini CLI.

## Features

- **Clean terminal UI** — minimal, focused interface
- **Streaming output** — real-time token display
- **Session management** — persistent conversation history
- **Minimal commands** — `/exit`, `/clear`, `/status`, `/help`
- **Thin client** — no AI logic, communicates only via Runtime

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ETHAN CLI (Python)                            │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │   REPL        │  │   Command     │  │   Session Manager        │   │
│  │   Loop        │  │   Parser      │  │   (history, state)       │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────────────┘   │
│         │                 │                    │                     │
│         └────────┬────────┘                    │                     │
│                  │                             │                     │
│         ┌────────▼────────┐                    │                     │
│         │   Runtime        │                    │                     │
│         │   Client         │                    │                     │
│         │   (socket/HTTP)  │                    │                     │
│         └────────┬────────┘                    │                     │
│                  │                             │                     │
│         ┌────────┼────────────┬───────────────┘                     │
│         │        │            │                                      │
│  ┌──────▼──┐ ┌──▼────┐ ┌─────▼──────┐                               │
│  │ Output   │ │Input  │ │  Command    │                               │
│  │ Renderer │ │Handler│ │  Registry   │                               │
│  └─────────┘ └───────┘ └────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 20 | Entry point |
| `repl.py` | 150 | REPL loop |
| `client.py` | 120 | Runtime client (socket + HTTP) |
| `session.py` | 100 | Session management |
| `config.py` | 60 | Configuration |
| `commands/parser.py` | 50 | Command parsing |
| `commands/handler.py` | 100 | Command implementations |
| `ui/prompt.py` | 20 | Prompt formatting |
| `ui/renderer.py` | 40 | Output rendering |
| **Total** | **660** | **Complete** |

## Usage

```bash
# Start CLI
python3 -m interfaces.cli.main

# Or directly
python3 interfaces/cli/main.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/exit`, `/quit` | Exit CLI |
| `/clear` | Clear screen |
| `/status` | Show Runtime status |
| `/session` | Show session info |
| `/history` | Show recent messages |
| `/help` | Show help |

## Communication

The CLI communicates with ETHAN Runtime via:

1. **Unix socket** (primary): `/run/ethan/runtime.sock`
2. **HTTP** (fallback): `http://localhost:8002`

Protocol: JSON + newline

## Session Storage

Sessions are stored in: `~/.local/share/ethan/sessions/`

Format: JSON, one file per session

## Configuration

Config file: `~/.config/ethan/config.json`

```json
{
  "runtime_socket": "/run/ethan/runtime.sock",
  "runtime_http": "http://localhost:8002",
  "timeout": 30,
  "streaming": true
}
```

## Key Properties

- ✅ **Thin client** — no AI logic
- ✅ **Clean UI** — minimal, Claude Code-inspired
- ✅ **Streaming** — real-time token display
- ✅ **Session persistence** — history saved automatically
- ✅ **Minimal commands** — /exit, /clear, /status, /help
- ✅ **Unix-native** — socket communication
- ✅ **Fallback** — HTTP if socket unavailable