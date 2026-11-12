# ETHAN CLI Test Suite — Plan & Structure

## 1. Overview

Comprehensive test suite for the ETHAN CLI (`cli/`), covering all 12 commands, 10 core modules, API integration, failure modes, and timeout handling.

---

## 2. Test Architecture

```
tests/cli/ethan/
├── TEST_PLAN.md                          # This file
├── conftest.py                           # Shared fixtures, mocks, helpers
├── helpers.py                            # Test utilities (mock server, fixtures)
├── unit/
│   ├── test_registry.py                  # Registry & dispatch logic
│   ├── test_entrypoint.py                # cli/ethan entry point
│   ├── test_client.py                    # HTTP client (send, alive, get_state)
│   ├── test_colors.py                    # Color system & formatters
│   ├── test_config.py                    # Configuration loading & merging
│   ├── test_daemon.py                    # Daemon lifecycle (start/stop/status)
│   ├── test_errors.py                    # Error system (EthanError, format)
│   ├── test_intent.py                    # Prompt intelligence classifier
│   ├── test_loading.py                   # Spinner, StepProgress, Thinker
│   ├── test_logging.py                   # Structured logging
│   ├── test_memory.py                    # Local memory & sessions
│   ├── test_streaming.py                 # Streaming output
│   ├── test_ux.py                        # UX helpers (suggest, help, smart errors)
│   ├── test_first_run.py                 # First-run detection & welcome
│   ├── test_discovery.py                 # Command registry & discovery
├── commands/
│   ├── test_chat.py                      # ethan chat
│   ├── test_status.py                    # ethan status
│   ├── test_logs.py                      # ethan logs
│   ├── test_memory_cmd.py                # ethan memory
│   ├── test_daemon_cmd.py                # ethan daemon
│   ├── test_suggest.py                   # ethan suggest
│   ├── test_run.py                       # ethan run
│   ├── test_cfg.py                       # ethan config
│   ├── test_plugin.py                    # ethan plugin
│   ├── test_help.py                      # ethan help
│   ├── test_think.py                     # ethan think
│   ├── test_service.py                   # ethan service
├── integration/
│   ├── test_api_integration.py           # Real/mocked API calls
│   ├── test_timeout_handling.py          # Timeout scenarios
│   ├── test_failure_scenarios.py         # All failure modes
│   ├── test_invalid_commands.py          # Unknown commands & typos
└── README.md                             # How to run & interpret tests
```

---

## 3. Test Categories

### 3.1 Unit Tests

| Module | File | Test Count | Key Scenarios |
|--------|------|-----------|---------------|
| **registry** | `test_registry.py` | 12 | `@register` decorator, `COMMANDS` dict, `dispatch()` with valid/invalid/empty args, `discover_commands()` dir scan, `_load_module()` for .py/dir/plugin.py, exception handling in dispatch |
| **entrypoint** | `test_entrypoint.py` | 6 | `--help` → help cmd, unknown command → `run` fallback, `version` command, empty argv → help, flag passthrough |
| **client** | `test_client.py` | 8 | `send()` with/without session_id, response parsing, `alive()` on 200/error/exception, `get_state()` returns dict/None, timeout propagation, error response handling |
| **colors** | `test_colors.py` | 18 | All formatters (`section`, `success`, `error`, `warn`, `info`, `item`, `wrap`, `metadata`, `online`, `offline`, `prompt`), all states, `progress_bar()` at 0%/50%/100%, table rendering, definition_list, timing, counters |
| **config** | `test_config.py` | 14 | Default values, file loading, `_deep_merge()` with nested dicts, env var override (`ETHAN_` prefix), `get()` dot notation, `set_value()` updates, `reset()` restores defaults, missing file handling |
| **daemon** | `test_daemon.py` | 10 | `_pid_write/read/remove`, `_is_running()` true/false/None, `_fetch_state()` success/failure, `_cache_write/read`, `cmd_start()` already running, `cmd_stop()` not running/force kill, `cmd_status()` running/stopped/with cache |
| **errors** | `test_errors.py` | 12 | `EthanError` constructor, `format_error()` with EthanError/Exception, debug mode traceback, `error()` quick formatting, all 10 error constructors (api_unreachable, capability_not_found, execution_failed, timeout, permission_denied, unknown_command, missing_argument, invalid_session, file_not_found, empty_input) |
| **intent** | `test_intent.py` | 16 | `classify()` empty/command/smart_cmd/intent/default chat, all intent patterns (fix, check, run, deploy, logs, status, help), confidence levels, `suggest_next()` for intents/smart_cmd/status, `autocomplete()` prefix/history, `confidence_label()` |
| **loading** | `test_loading.py` | 9 | `Spinner` start/stop/cancel, all 6 styles, thread lifecycle, `StepProgress` begin/step/complete/fail, `Thinker` begin/update/done/cancel |
| **logging** | `test_logging.py` | 8 | `log()` writes entry, `_load/_save` with MAX_ENTRIES cap, `query_last()` ordering, `query_errors()` filters ok, `query_text()` search, error handling on corrupt file |
| **memory** | `test_memory.py` | 16 | `record()` stores entry, `recent()` ordering, `frequent()` counts, `suggest_prefix()` matching, session lifecycle (new/resume/save), `get_history()` session filter, `get_session_info()` metadata, `get_context_usage()`, `reset_context()` |
| **streaming** | `test_streaming.py` | 8 | `Streamer` start/write/done/cancel, thread safety, `fallback()` on error, spinner animation, cancelled state |
| **ux** | `test_ux.py` | 10 | `levenshtein()` distances, `suggest_command()` with difflib/fallback, all 6 `smart_error()` kinds, `show_help()` with/without topic |
| **first_run** | `test_first_run.py` | 5 | `is_first_run()` true/false, `mark_installed()` creates marker, `show_welcome()` output, `show_system_check()` with API up/down, `maybe_show_first_run()` conditional |
| **discovery** | `test_discovery.py` | 8 | `CommandRegistry.register/get/list_commands`, group filtering, `suggest()` fuzzy matching, `autocomplete()` prefix, core/advanced command registration |

**Unit total: ~160 tests**

---

### 3.2 Command Tests

| Command | File | Test Count | Key Scenarios |
|---------|------|-----------|---------------|
| **chat** | `test_chat.py` | 14 | New session, resume session, all 7 slash commands (`/exit`, `/q`, `/resume`, `/history`, `/reset`, `/new`, `/session`, `/ctx`), unknown `/cmd` fallback, API unreachable, send success/error, memory hint display, suggestion display |
| **status** | `test_status.py` | 6 | API online → state fields, API offline → "OFFLINE", partial state, empty state, full vs minimal state |
| **logs** | `test_logs.py` | 8 | Default (last 20), `--last N`, `--errors`, text search, no results, empty log, error in output |
| **memory** | `test_memory_cmd.py` | 6 | Default (recent), `recent N`, `frequent`, `frequent N`, no history, invalid subcommand → usage |
| **daemon** | `test_daemon_cmd.py` | 6 | `start` dispatches, `stop` dispatches, `status` dispatches, no args → usage, invalid subcommand, args passthrough |
| **suggest** | `test_suggest.py` | 6 | Default (recent + frequent), prefix match, no history, no matches, empty prefix |
| **run** | `test_run.py` | 4 | Command execution, capability routing, error propagation, empty command |
| **cfg** | `test_cfg.py` | 6 | Get value, set value, show all, reset, invalid key, nested key access |
| **plugin** | `test_plugin.py` | 6 | List plugins, install plugin, remove plugin, unknown subcommand, missing argument |
| **help** | `test_help.py` | 6 | Default help, topic-specific help, unknown topic, all topics listed |
| **think** | `test_think.py` | 4 | Think mode toggle, with/without context, state display |
| **service** | `test_service.py` | 4 | Service status, start, stop, error handling |

**Command total: ~70 tests**

---

### 3.3 Integration Tests

| Suite | File | Test Count | Key Scenarios |
|-------|------|-----------|---------------|
| **API Integration** | `test_api_integration.py` | 8 | send() with mocked HTTP, alive() with 200/4xx/5xx/connection refused, get_state() returns dict, request timeout, response error field, session_id passthrough, base URL from env |
| **Timeout Handling** | `test_timeout_handling.py` | 8 | client.send() timeout, client.alive() timeout, daemon._fetch_state() timeout, streaming timeout, StepProgress timeout, intentional 10s timeout error, configurable timeout, timeout error formatting |
| **Failure Scenarios** | `test_failure_scenarios.py` | 12 | API unreachable (all commands), corrupt config file, memory file corrupt, daemon PID file corrupt, incomplete state response, network disconnected, permission denied (config dir, memory dir, log dir), disk full simulation, plugin load failure |
| **Invalid Commands** | `test_invalid_commands.py` | 8 | Unknown command → error, typo (chatt → suggestion?), empty command, --help on subcommand, missing required arg, extra args ignored, /unknown in chat, `run` with no args |

**Integration total: ~36 tests**

---

### 3.4 Failure Scenario Matrix

| Failure Type | Module | Expected Behavior | Coverage |
|-------------|--------|------------------|----------|
| API down | client, chat, status, daemon | Graceful offline message, retry hint | `test_client.py`, `test_chat.py`, `test_status.py` |
| API timeout | client | TimeoutError, SYS-002 code | `test_timeout_handling.py` |
| Corrupt config | config | Fallback to defaults | `test_config.py` |
| Corrupt memory | memory | Fallback to empty array | `test_memory.py` |
| Corrupt log file | logging | Fallback to empty array | `test_logging.py` |
| Permission denied | daemon, config, memory | PermissionError caught | `test_daemon.py`, `test_config.py` |
| Invalid command | dispatch | CMD-001 error + suggestion | `test_registry.py` |
| Empty input | chat, intent | INP-001, classify returns chat 0.0 | `test_chat.py`, `test_intent.py` |
| Session not found | memory | New session created | `test_memory.py` |
| File not found | first_run, discovery | Graceful skip | `test_first_run.py`, `test_registry.py` |

### 3.5 Edge Cases

| Edge Case | Tests |
|-----------|-------|
| Empty history (recent/frequent/suggest) | `test_memory.py`, `test_suggest.py` |
| MAX_ENTRIES rollover | `test_memory.py`, `test_logging.py` |
| Unicode in commands/messages | `test_chat.py`, `test_logging.py` |
| Rapid session create/resume | `test_memory.py` |
| Concurrent spinner/streamer start | `test_loading.py`, `test_streaming.py` |
| Deeply nested config keys | `test_config.py` |
| Env vars with mixed case | `test_config.py` |
| Empty argv in dispatch | `test_registry.py` |
| Very long command names | `test_registry.py` |
| All ANSI codes stripped in tests | all formatter tests |

---

## 4. Fixtures & Helpers (conftest.py)

```python
# Shared fixtures for ETHAN CLI tests

@pytest.fixture
def mock_api_server():
    """Start a local mock HTTP server for API testing."""

@pytest.fixture
def tmp_ethan_dir(tmp_path):
    """Isolated ~/.ethan directory."""

@pytest.fixture
def mock_client_send():
    """Mock cli.core.client.send() to return controlled responses."""

@pytest.fixture
def mock_client_alive():
    """Mock cli.core.client.alive() to simulate API state."""

@pytest.fixture
def captured_output():
    """Capture stdout for assertion."""

@pytest.fixture
def registered_commands():
    """Register known test commands in the global COMMANDS dict."""

@pytest.fixture
def clear_registry():
    """Clear COMMANDS dict between tests."""
```

---

## 5. Running Tests

```bash
# All ETHAN CLI tests
pytest tests/cli/ethan/ -v

# Unit tests only
pytest tests/cli/ethan/unit/ -v

# Command tests only
pytest tests/cli/ethan/commands/ -v

# Integration tests only
pytest tests/cli/ethan/integration/ -v

# Specific test file
pytest tests/cli/ethan/unit/test_registry.py -v

# With coverage
pytest tests/cli/ethan/ --cov=cli --cov-report=term-missing -v

# Parallel execution
pytest tests/cli/ethan/ -n auto -v
```

---

## 6. Coverage Targets

| Module | Target Coverage | Critical Paths |
|--------|----------------|----------------|
| `cli/__init__.py` | 100% | Discovery, dispatch |
| `cli/ethan` | 100% | Entry point, arg parsing |
| `cli/registry.py` | 95% | Register, dispatch, discover |
| `cli/core/client.py` | 100% | send, alive, get_state |
| `cli/core/colors.py` | 95% | All formatters |
| `cli/core/config.py` | 95% | Load, merge, get, set |
| `cli/core/daemon.py` | 90% | Start, stop, status, cache |
| `cli/core/errors.py` | 100% | All error constructors |
| `cli/core/intent.py` | 95% | Classify, suggest, autocomplete |
| `cli/core/loading.py` | 90% | Spinner, Steps, Thinker |
| `cli/core/logging.py` | 95% | Log, query, error handling |
| `cli/core/memory.py` | 95% | Store, retrieve, sessions |
| `cli/core/streaming.py` | 90% | Stream, cancel, fallback |
| `cli/core/ux.py` | 95% | Suggest, help, smart errors |
| `cli/core/first_run.py` | 100% | Detection, welcome, install |
| `cli/core/discovery.py` | 95% | Registry, suggest, autocomplete |
| Each command file | 90%+ | All subcommands, edge cases |

**Overall target: ≥93% line coverage of `cli/`**

---

## 7. Mock Strategy

| External Dependency | Mocking Approach |
|--------------------|-----------------|
| HTTP API (`urlopen`) | `unittest.mock.patch('urllib.request.urlopen')` |
| File system | `tmp_path` fixture (pytest built-in) |
| `os.kill` | Mocked via `unittest.mock.patch` |
| `os.fork` | Mocked (never actually fork in tests) |
| `threading.Thread` | Real threads allowed (short-lived daemon threads) |
| Environment variables | `monkeypatch.setenv` / `monkeypatch.delenv` |
| `~/.ethan` | Redirected to `tmp_path` via `monkeypatch` |
| `~/.config/ethan` | Redirected to `tmp_path` via `monkeypatch` |

---

## 8. Test File Template

```python
"""Tests for cli/commands/<command>.py."""
from __future__ import annotations

from unittest import mock
from cli.registry import COMMANDS


def test_command_basic():
    """Default invocation shows expected output."""
    cmd = COMMANDS["<command>"]
    result = cmd([])
    assert result == 0


def test_command_no_args():
    """Missing args show usage."""
    ...

def test_command_error():
    """Error scenario returns non-zero."""
    ...

def test_command_edge_case():
    """Edge case handling."""
    ...
```

---

## 9. Acceptance Criteria

- [ ] All unit tests pass in isolation
- [ ] All command tests pass with mocked dependencies
- [ ] Integration tests cover API interaction patterns
- [ ] Timeout handling validated for all network operations
- [ ] Every failure scenario produces a human-readable error
- [ ] Invalid commands are caught with suggestions
- [ ] Coverage ≥93% on `cli/` module
- [ ] Tests run in <10 seconds (no real network calls)
- [ ] No test uses actual filesystem outside `tmp_path`