# ETHAN CLI Regression Test System — Framework Design

## Executive Summary

A snapshot-based regression test system that prevents future changes from breaking existing CLI behavior. Uses golden files, command-level comparison, API contract validation, and plugin compatibility checks.

**Core principle**: Capture → Compare → Report. Every CLI interaction has a known-good baseline; deviations are flagged automatically.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REGRESSION TEST FRAMEWORK                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │   SNAPSHOT   │    │  COMPARISON  │    │      REPORTING       │ │
│  │   ENGINE     │───▶│   ENGINE     │───▶│      ENGINE          │ │
│  │              │    │              │    │                      │ │
│  │ - Capture    │    │ - Diff       │    │ - HTML report       │ │
│  │ - Hash       │    │ - Tolerance   │    │ - JUnit XML         │ │
│  │ - Store      │    │ - Threshold   │    │ - CI integration    │ │
│  └──────────────┘    └──────────────┘    └──────────────────────┘ │
│         │                  │                       │               │
│         │                  │                       │               │
│         ▼                  ▼                       ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │   OUTPUT     │    │   API        │    │      PLUGIN          │ │
│  │   NORMALIZE  │    │   CONTRACT   │    │      COMPAT          │ │
│  │              │    │   VALIDATOR  │    │                      │ │
│  │ - Strip ANSI │    │              │    │ - Registry check     │ │
│  │ - Canonical  │    │ - Schema     │    │ - Load all           │ │
│  │   timestamps │    │ - Type check │    │ - Command discovery  │ │
│  └──────────────┘    └──────────────┘    └──────────────────────┘ │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │  GOLDEN      │    │   TEST       │    │      CI/CD           │ │
│  │  FILES       │    │   RUNNER     │    │      GATE            │ │
│  │  (Baseline)  │    │              │    │                      │ │
│  │              │    │ - Pytest     │    │ - GitHub Actions     │ │
│  │ - snapshots/ │    │ - Fixtures   │    │ - Pre-merge check    │ │
│  │   chat.txt   │    │ - Parametrize│    │ - Alerts on fail     │ │
│  │   status.txt │    │              │    │                      │ │
│  └──────────────┘    └──────────────┘    └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. SNAPSHOT ENGINE

**Location**: `tests/cli/ethan/snapshot.py`

**Responsibility**: Capture CLI command outputs as golden files.

```python
class SnapshotEngine:
    """Capture and manage CLI snapshots."""
    
    def __init__(self, snapshot_dir="tests/cli/ethan/snapshots"):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    def capture(self, command: str, argv: list[str], output: str, 
                exit_code: int, metadata: dict = None) -> str:
        """Capture command output and save as snapshot.
        
        Returns: snapshot file path
        """
        # Normalize output
        normalized = self._normalize(output)
        
        # Generate filename: command__args_hash.txt
        args_hash = hashlib.md5(" ".join(argv).encode()).hexdigest()[:8]
        filename = f"{command}__{args_hash}.txt"
        path = self.snapshot_dir / filename
        
        # Write snapshot with metadata header
        snapshot = self._format_snapshot(
            command=command,
            argv=argv,
            output=normalized,
            exit_code=exit_code,
            metadata=metadata or {},
        )
        path.write_text(snapshot)
        return str(path)
    
    def load(self, command: str, argv: list[str]) -> str | None:
        """Load existing snapshot for comparison."""
        args_hash = hashlib.md5(" ".join(argv).encode()).hexdigest()[:8]
        filename = f"{command}__{args_hash}.txt"
        path = self.snapshot_dir / filename
        if path.exists():
            return path.read_text()
        return None
    
    def _normalize(self, output: str) -> str:
        """Normalize output for comparison.
        
        - Strip ANSI color codes
        - Normalize whitespace
        - Replace dynamic timestamps/IDs with placeholders
        - Sort lines if needed
        """
        # Strip ANSI
        output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
        # Normalize line endings
        output = output.replace('\r\n', '\n').replace('\r', '\n')
        # Replace session IDs, timestamps with placeholders
        output = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 
                       '<SESSION_ID>', output)
        output = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', output)
        # Normalize trailing whitespace
        output = "\n".join(line.rstrip() for line in output.split("\n"))
        return output.strip()
    
    def _format_snapshot(self, **kwargs) -> str:
        """Format snapshot with metadata header."""
        header = f"""# SNAPSHOT
# Command: {kwargs['command']} {' '.join(kwargs['argv'])}
# Exit code: {kwargs['exit_code']}
# Captured: <TIMESTAMP>
# Meta: {json.dumps(kwargs.get('metadata', {}))}
# ===

"""
        return header + kwargs['output']
```

---

### 2. COMPARISON ENGINE

**Location**: `tests/cli/ethan/comparator.py`

**Responsibility**: Compare actual output against golden snapshots.

```python
class ComparisonResult:
    """Result of snapshot comparison."""
    def __init__(self, passed: bool, diff: str, missing: list, extra: list):
        self.passed = passed
        self.diff = diff
        self.missing = missing
        self.extra = extra


class Comparator:
    """Compare CLI outputs against golden snapshots."""
    
    def __init__(self, tolerance_lines=0, ignore_patterns=None):
        self.tolerance_lines = tolerance_lines
        self.ignore_patterns = ignore_patterns or []
    
    def compare(self, actual: str, expected: str, 
                context: str = "") -> ComparisonResult:
        """Compare actual vs expected output.
        
        Args:
            actual: Current command output (normalized)
            expected: Golden snapshot content
            context: Command context for error messages
        
        Returns:
            ComparisonResult with pass/fail and details
        """
        actual_lines = actual.split("\n")
        expected_lines = expected.split("\n")
        
        # Apply ignore patterns
        actual_filtered = self._apply_ignore_patterns(actual_lines)
        expected_filtered = self._apply_ignore_patterns(expected_lines)
        
        # Allow line count tolerance
        if self.tolerance_lines > 0:
            if abs(len(actual_filtered) - len(expected_filtered)) <= self.tolerance_lines:
                # Align by content
                actual_filtered = self._align_lines(actual_filtered, expected_filtered)
        
        # Compute diff
        missing, extra = self._compute_diff(actual_filtered, expected_filtered)
        
        passed = len(missing) == 0 and len(extra) == 0
        
        diff_text = ""
        if not passed:
            diff_text = self._format_diff(missing, extra, context)
        
        return ComparisonResult(
            passed=passed,
            diff=diff_text,
            missing=missing,
            extra=extra,
        )
    
    def _apply_ignore_patterns(self, lines: list[str]) -> list[str]:
        """Remove lines matching ignore patterns."""
        filtered = []
        for line in lines:
            skip = False
            for pattern in self.ignore_patterns:
                if re.search(pattern, line):
                    skip = True
                    break
            if not skip:
                filtered.append(line)
        return filtered
    
    def _compute_diff(self, actual: list[str], expected: list[str]) -> tuple[list, list]:
        """Simple line-by-line diff."""
        actual_set = set(actual)
        expected_set = set(expected)
        
        missing = [line for line in expected if line not in actual_set]
        extra = [line for line in actual if line not in expected_set]
        
        return missing, extra
    
    def _format_diff(self, missing: list, extra: list, context: str) -> str:
        """Format diff for human reading."""
        lines = [f"Diff for: {context}", ""]
        
        if missing:
            lines.append("Missing lines (expected but not found):")
            for line in missing:
                lines.append(f"  - {line}")
        
        if extra:
            lines.append("Extra lines (found but not expected):")
            for line in extra:
                lines.append(f"  + {line}")
        
        return "\n".join(lines)
    
    def _align_lines(self, actual: list[str], expected: list[str]) -> list[str]:
        """Truncate longer list to match shorter one."""
        min_len = min(len(actual), len(expected))
        return actual[:min_len]
```

---

### 3. API RESPONSE VALIDATOR

**Location**: `tests/cli/ethan/api_validator.py`

**Responsibility**: Validate API responses against schemas.

```python
from dataclasses import dataclass
from typing import Any


@dataclass
class APISchema:
    """Schema definition for API response."""
    endpoint: str
    method: str
    expected_keys: list[str]
    expected_types: dict[str, type]
    required: bool = True


class APIResponseValidator:
    """Validate API responses against schemas."""
    
    SCHEMAS = {
        "message": APISchema(
            endpoint="/v1/message",
            method="POST",
            expected_keys=["success", "event_id", "goal_id", "message"],
            expected_types={
                "success": bool,
                "event_id": str,
                "goal_id": str,
                "message": str,
            },
        ),
        "state": APISchema(
            endpoint="/v1/state",
            method="GET",
            expected_keys=["mode", "modules_active"],
            expected_types={
                "mode": str,
                "modules_active": list,
            },
        ),
        "health": APISchema(
            endpoint="/v1/health",
            method="GET",
            expected_keys=["status", "service", "nats_connected"],
            expected_types={
                "status": str,
                "service": str,
                "nats_connected": bool,
            },
        ),
    }
    
    def validate(self, endpoint: str, response: dict) -> ValidationResult:
        """Validate response against schema.
        
        Args:
            endpoint: API endpoint (e.g., "/v1/message")
            response: Parsed JSON response
        
        Returns:
            ValidationResult
        """
        schema = self.SCHEMAS.get(endpoint)
        if not schema:
            return ValidationResult(
                valid=False,
                errors=[f"No schema defined for {endpoint}"],
            )
        
        errors = []
        
        # Check required keys
        missing = [k for k in schema.expected_keys if k not in response]
        if missing:
            errors.append(f"Missing keys: {missing}")
        
        # Check types
        for key, expected_type in schema.expected_types.items():
            if key in response and not isinstance(response[key], expected_type):
                actual_type = type(response[key]).__name__
                errors.append(f"Key '{key}': expected {expected_type.__name__}, got {actual_type}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
        )


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
```

---

### 4. PLUGIN COMPATIBILITY CHECKER

**Location**: `tests/cli/ethan/plugin_compat.py`

**Responsibility**: Ensure plugins load correctly and register commands.

```python
class PluginCompatibilityChecker:
    """Check plugin loading and compatibility."""
    
    def __init__(self):
        self.results = []
    
    def check_all(self) -> list[PluginCheckResult]:
        """Check all discoverable plugins.
        
        Returns:
            List of PluginCheckResult
        """
        self.results = []
        
        # Check builtin plugins
        self._check_directory(Path("cli/plugins"))
        
        # Check user plugins
        user_dir = Path.home() / ".local" / "share" / "ethan" / "plugins"
        if user_dir.exists():
            self._check_directory(user_dir)
        
        return self.results
    
    def _check_directory(self, directory: Path):
        """Check all plugins in a directory."""
        if not directory.exists():
            return
        
        for plugin_dir in directory.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            result = self._check_plugin(plugin_dir)
            self.results.append(result)
    
    def _check_plugin(self, plugin_dir: Path) -> PluginCheckResult:
        """Check single plugin."""
        plugin_file = plugin_dir / "plugin.py"
        plugin_name = plugin_dir.name
        
        # Check 1: plugin.py exists
        if not plugin_file.exists():
            return PluginCheckResult(
                plugin=plugin_name,
                loaded=False,
                commands=[],
                errors=["plugin.py not found"],
            )
        
        # Check 2: Can import
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            return PluginCheckResult(
                plugin=plugin_name,
                loaded=False,
                commands=[],
                errors=[f"Import error: {e}"],
            )
        
        # Check 3: Has ETHAN_PLUGIN dict
        if not hasattr(module, "ETHAN_PLUGIN"):
            return PluginCheckResult(
                plugin=plugin_name,
                loaded=False,
                commands=[],
                errors=["Missing ETHAN_PLUGIN dict"],
            )
        
        plugin_info = module.ETHAN_PLUGIN
        
        # Check 4: Valid version
        version = plugin_info.get("version", "?")
        
        # Check 5: Commands are callable
        commands = []
        errors = []
        for cmd_name, cmd_info in plugin_info.get("commands", {}).items():
            handler = cmd_info.get("handler")
            if not callable(handler):
                errors.append(f"Command '{cmd_name}' handler not callable")
            else:
                commands.append(cmd_name)
        
        return PluginCheckResult(
            plugin=plugin_name,
            loaded=True,
            version=version,
            commands=commands,
            errors=errors,
        )


@dataclass
class PluginCheckResult:
    plugin: str
    loaded: bool
    version: str = "?"
    commands: list[str] = None
    errors: list[str] = None
    
    def __post_init__(self):
        if self.commands is None:
            self.commands = []
        if self.errors is None:
            self.errors = []
```

---

## Test Suite Organization

```
tests/cli/ethan/
├── conftest.py                    # Shared fixtures
├── helpers.py                     # Test utilities
├── REGRESSION_TEST_SYSTEM.md      # This file
├── golden/                        # Snapshot directory
│   ├── chat/
│   │   ├── basic_chat.txt
│   │   ├── chat_with_history.txt
│   │   └── chat_empty.txt
│   ├── status/
│   │   ├── online.txt
│   │   └── offline.txt
│   ├── logs/
│   │   ├── logs_default.txt
│   │   └── logs_errors.txt
│   ├── memory/
│   │   ├── memory_recent.txt
│   │   └── memory_frequent.txt
│   ├── daemon/
│   │   ├── daemon_status.txt
│   │   └── daemon_help.txt
│   ├── plugin/
│   │   ├── plugin_list_installed.txt
│   │   └── plugin_help.txt
│   ├── config/
│   │   ├── config_show.txt
│   │   └── config_get_key.txt
│   └── service/
│       ├── service_status.txt
│       └── service_help.txt
├── regression/
│   ├── __init__.py
│   ├── test_snapshot_regression.py  # Snapshot comparison tests
│   ├── test_api_contracts.py        # API schema validation
│   ├── test_plugin_compat.py        # Plugin loading checks
│   └── test_command_matrix.py       # All commands smoke test
├── unit/
│   └── ... (existing tests)
└── integration/
    └── ... (existing tests)
```

---

## Test Implementation

### A. Snapshot Regression Tests

**File**: `tests/cli/ethan/regression/test_snapshot_regression.py`

```python
import pytest
from pathlib import Path
from io import StringIO
from unittest.mock import patch
import sys

from cli.registry import discover_commands, dispatch
from tests.cli.ethan.snapshot import SnapshotEngine
from tests.cli.ethan.comparator import Comparator
from tests.cli.ethan.helpers import capture_output


# Snapshots are stored in tests/cli/ethan/golden/
SNAPSHOT_DIR = Path(__file__).parent.parent / "golden"


@pytest.fixture
def snapshot_engine():
    """Provide snapshot engine."""
    return SnapshotEngine(snapshot_dir=str(SNAPSHOT_DIR))


@pytest.fixture
def comparator():
    """Provide comparison engine with tolerance."""
    return Comparator(tolerance_lines=2)


class TestChatSnapshots:
    """Snapshot tests for chat command."""
    
    def test_chat_help_output(self, snapshot_engine, comparator):
        """Chat command help should match snapshot."""
        exit_code, output = capture_output(["chat", "--help"])
        
        result = comparator.compare(output, expected, "chat --help")
        assert result.passed, result.diff
    
    def test_chat_empty_session(self, snapshot_engine, comparator):
        """Chat with no history should show welcome only."""
        exit_code, output = capture_output(["chat", "--no-interactive"])
        
        result = comparator.compare(output, expected, "chat --no-interactive")
        assert result.passed, result.diff


class TestStatusSnapshots:
    """Snapshot tests for status command."""
    
    def test_status_offline(self, snapshot_engine, comparator, mock_api_offline):
        """Status output when API is offline."""
        exit_code, output = capture_output(["status"])
        
        # Load expected offline snapshot
        expected = (SNAPSHOT_DIR / "status" / "offline.txt").read_text()
        # Extract output section (skip header)
        expected_output = "\n".join(
            line for line in expected.split("\n") 
            if not line.startswith("#")
        ).strip()
        
        result = comparator.compare(output.strip(), expected_output, "status offline")
        assert result.passed, result.diff


class TestLogsSnapshots:
    """Snapshot tests for logs command."""
    
    def test_logs_default(self, snapshot_engine, comparator, mock_logs_empty):
        """Logs command with no entries."""
        exit_code, output = capture_output(["logs"])
        
        expected = (SNAPSHOT_DIR / "logs" / "logs_default.txt").read_text()
        expected_output = "\n".join(
            line for line in expected.split("\n")
            if not line.startswith("#")
        ).strip()
        
        result = comparator.compare(output.strip(), expected_output, "logs default")
        assert result.passed, result.diff


class TestMemorySnapshots:
    """Snapshot tests for memory command."""
    
    def test_memory_recent_empty(self, snapshot_engine, comparator, mock_memory_empty):
        """Memory recent with no history."""
        exit_code, output = capture_output(["memory", "recent"])
        
        expected = (SNAPSHOT_DIR / "memory" / "memory_recent.txt").read_text()
        expected_output = "\n".join(
            line for line in expected.split("\n")
            if not line.startswith("#")
        ).strip()
        
        result = comparator.compare(output.strip(), expected_output, "memory recent")
        assert result.passed, result.diff


class TestPluginSnapshots:
    """Snapshot tests for plugin command."""
    
    def test_plugin_list_no_plugins(self, snapshot_engine, comparator, mock_no_user_plugins):
        """Plugin list when no user plugins installed."""
        exit_code, output = capture_output(["plugin", "list"])
        
        expected = (SNAPSHOT_DIR / "plugin" / "plugin_list_installed.txt").read_text()
        expected_output = "\n".join(
            line for line in expected.split("\n")
            if not line.startswith("#")
        ).strip()
        
        result = comparator.compare(output.strip(), expected_output, "plugin list")
        assert result.passed, result.diff


class TestConfigSnapshots:
    """Snapshot tests for config command."""
    
    def test_config_show_defaults(self, snapshot_engine, comparator, mock_config_defaults):
        """Config show with default values."""
        exit_code, output = capture_output(["config"])
        
        expected = (SNAPSHOT_DIR / "config" / "config_show.txt").read_text()
        expected_output = "\n".join(
            line for line in expected.split("\n")
            if not line.startswith("#")
        ).strip()
        
        result = comparator.compare(output.strip(), expected_output, "config show")
        assert result.passed, result.diff
```

---

### B. API Contract Validation Tests

**File**: `tests/cli/ethan/regression/test_api_contracts.py`

```python
import pytest
from unittest.mock import Mock, patch
from tests.cli.ethan.api_validator import APIResponseValidator


class TestMessageAPI:
    """Validate /v1/message API contract."""
    
    @pytest.fixture
    def validator(self):
        return APIResponseValidator()
    
    def test_message_response_schema(self, validator):
        """POST /v1/message should return expected schema."""
        response = {
            "success": True,
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "goal_id": "",
            "message": "Event emitted into cognitive system",
        }
        
        result = validator.validate("/v1/message", response)
        assert result.valid, f"Schema validation failed: {result.errors}"
    
    def test_message_response_types(self, validator):
        """Response values should have correct types."""
        response = {
            "success": "true",  # Wrong: should be bool
            "event_id": 12345,  # Wrong: should be str
            "goal_id": "",
            "message": "ok",
        }
        
        result = validator.validate("/v1/message", response)
        assert not result.valid
        assert "success" in str(result.errors)
        assert "event_id" in str(result.errors)


class TestHealthAPI:
    """Validate /v1/health API contract."""
    
    @pytest.fixture
    def validator(self):
        return APIResponseValidator()
    
    def test_health_response_schema(self, validator):
        """GET /v1/health should return expected schema."""
        response = {
            "status": "ok",
            "service": "api-gateway",
            "nats_connected": True,
        }
        
        result = validator.validate("/v1/health", response)
        assert result.valid, f"Schema validation failed: {result.errors}"


class TestStateAPI:
    """Validate /v1/state API contract."""
    
    @pytest.fixture
    def validator(self):
        return APIResponseValidator()
    
    def test_state_response_schema(self, validator):
        """GET /v1/state should return expected schema."""
        response = {
            "mode": "idle",
            "modules_active": ["cli", "api"],
        }
        
        result = validator.validate("/v1/state", response)
        assert result.valid, f"Schema validation failed: {result.errors}"
```

---

### C. Plugin Compatibility Tests

**File**: `tests/cli/ethan/regression/test_plugin_compat.py`

```python
import pytest
import importlib.util
from pathlib import Path
from tests.cli.ethan.plugin_compat import PluginCompatibilityChecker


class TestPluginRegistry:
    """Ensure all plugins load and register correctly."""
    
    @pytest.fixture
    def checker(self):
        return PluginCompatibilityChecker()
    
    def test_all_plugins_load(self, checker):
        """All plugins should load without errors."""
        results = checker.check_all()
        
        failed = [r for r in results if not r.loaded]
        
        if failed:
            messages = [f"{r.plugin}: {', '.join(r.errors)}" for r in failed]
            pytest.fail(f"Failed plugins:\n" + "\n".join(messages))
    
    def test_no_duplicate_commands(self, checker):
        """No two plugins should register the same command."""
        from cli.registry import discover_commands, COMMANDS
        
        # Capture state before
        before = set(COMMANDS.keys())
        
        discover_commands()
        
        after = set(COMMANDS.keys())
        new_commands = after - before
        
        # Check for duplicates
        duplicates = []
        for cmd in new_commands:
            if cmd in before:
                duplicates.append(cmd)
        
        assert len(duplicates) == 0, f"Duplicate commands: {duplicates}"
    
    def test_all_plugin_commands_callable(self, checker):
        """Every registered plugin command must be callable."""
        from cli.registry import discover_commands, COMMANDS
        
        discover_commands()
        
        non_callable = []
        for name, fn in COMMANDS.items():
            if not callable(fn):
                non_callable.append(name)
        
        assert len(non_callable) == 0, f"Non-callable commands: {non_callable}"


class TestPluginMetadata:
    """Validate plugin metadata."""
    
    def test_plugin_has_version(self):
        """Every plugin should have a version."""
        from cli.registry import discover_commands
        from cli.plugin_manager import list_installed
        
        plugins = list_installed()
        
        for plugin in plugins:
            assert "version" in plugin, f"Plugin {plugin.get('name')} missing version"
            assert isinstance(plugin["version"], str)
            assert len(plugin["version"]) > 0
```

---

## Pytest Integration

### Fixtures (`conftest.py` additions)

```python
# tests/cli/ethan/conftest.py

import pytest
from pathlib import Path
from unittest.mock import patch
from tests.cli.ethan.snapshot import SnapshotEngine
from tests.cli.ethan.comparator import Comparator


@pytest.fixture
def golden_dir():
    """Provide path to golden snapshots."""
    return Path(__file__).parent / "golden"


@pytest.fixture
def snapshot_engine(golden_dir):
    """Provide configured snapshot engine."""
    return SnapshotEngine(snapshot_dir=str(golden_dir))


@pytest.fixture
def comparator():
    """Provide configured comparator."""
    return Comparator(tolerance_lines=2, ignore_patterns=[
        r"Session ID:", r"Timestamp:", r"\d{4}-\d{2}-\d{2}",
    ])


@pytest.fixture
def mock_api_offline():
    """Simulate offline API."""
    with patch("cli.core.client.alive", return_value=False):
        yield


@pytest.fixture
def mock_api_online():
    """Simulate online API."""
    with patch("cli.core.client.alive", return_value=True):
        yield


@pytest.fixture
def mock_logs_empty():
    """Simulate empty logs."""
    with patch("cli.core.logging.query_last", return_value=[]):
        yield


@pytest.fixture
def mock_memory_empty():
    """Simulate empty memory."""
    with patch("cli.core.memory.recent", return_value=[]):
        with patch("cli.core.memory.frequent", return_value=[]):
            yield


@pytest.fixture
def mock_no_user_plugins():
    """Simulate no user plugins."""
    with patch("cli.plugin_manager.list_installed", return_value=[]):
        yield


@pytest.fixture
def mock_config_defaults():
    """Simulate default config."""
    with patch("cli.core.config.get", return_value=None):
        with patch("cli.core.config.show", return_value=""):
            yield
```

---

## Snapshot Update Workflow

```bash
# 1. Run tests with snapshot update flag
pytest tests/cli/ethan/regression/test_snapshot_regression.py --update-snapshots

# 2. Review changes in golden/ directory
git diff tests/cli/ethan/golden/

# 3. If changes are expected, commit new snapshots
git add tests/cli/ethan/golden/
git commit -m "chore: update golden snapshots for CLI changes"

# 4. If changes are unexpected, fix code
# Do NOT update snapshots
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/cli-regression.yml
name: CLI Regression Tests

on: [push, pull_request]

jobs:
  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-xdist
      
      - name: Run snapshot regression
        run: |
          pytest tests/cli/ethan/regression/ -v \
            --junitxml=regression-results.xml \
            --tb=short
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: regression-results
          path: regression-results.xml
      
      - name: Check for snapshot drift
        run: |
          if [[ -n $(git diff --name-only tests/cli/ethan/golden/) ]]; then
            echo "⚠️ Golden files changed — review required"
            git diff --stat tests/cli/ethan/golden/
            # Fail workflow but allow manual override
            exit 1
          fi
      
      - name: Plugin compatibility check
        run: |
          pytest tests/cli/ethan/regression/test_plugin_compat.py -v
```

---

## Utilities

**File**: `tests/cli/ethan/helpers.py`

```python
"""Test helpers for CLI testing."""
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr


def capture_output(argv):
    """Capture CLI output for given argv.
    
    Args:
        argv: Command arguments (e.g., ["status"])
    
    Returns:
        Tuple of (exit_code, output_string)
    """
    from cli.registry import COMMANDS
    
    stdout_buf = StringIO()
    stderr_buf = StringIO()
    
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            cmd = argv[0] if argv else ""
            fn = COMMANDS.get(cmd)
            if not fn:
                exit_code = 1
            else:
                exit_code = fn(argv[1:])
    except Exception as e:
        exit_code = 1
        stderr_buf.write(f"Error: {e}\n")
    
    output = stdout_buf.getvalue() + stderr_buf.getvalue()
    return exit_code, output


def normalize_output(output: str) -> str:
    """Normalize CLI output for comparison."""
    import re
    
    # Strip ANSI
    output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
    # Normalize line endings
    output = output.replace('\r\n', '\n').replace('\r', '\n')
    # Replace dynamic values
    output = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',
                   '<SESSION_ID>', output)
    output = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', output)
    # Strip trailing whitespace
    lines = [line.rstrip() for line in output.split("\n")]
    return "\n".join(lines).strip()
```

---

## Implementation Roadmap

| Phase | Component | Effort | Value |
|---|---|---|---|
| 1 | Snapshot Engine + Basic Tests | Low | High |
| 2 | Comparator + Tolerance | Low | High |
| 3 | API Contract Validator | Medium | Medium |
| 4 | Plugin Compatibility Checker | Low | High |
| 5 | GitHub Actions Integration | Low | High |
| 6 | Golden file population | Medium | High |

**Estimated total effort**: 1 day for minimal viable regression suite.

---

## Benefits

| Benefit | Impact |
|---|---|
| Prevent regressions | Catches breaking changes before merge |
| Fast feedback | Tests run in <30s |
| Low maintenance | Snapshots auto-update with `--update-snapshots` |
| Clear diffs | Human-readable output mismatches |
| Plugin safety | Ensures plugin API stability |
| API guarantee | Validates backend contracts |

---

## Future Enhancements

- Visual diff viewer for snapshot changes (HTML report)
- Machine learning to detect "acceptable" drift vs "breaking" changes
- Snapshot pruning (remove unused snapshots)
- Integration with PR comments (auto-review snapshot changes)
- Performance benchmarks (track command execution time)
- Cross-platform snapshots (Windows vs Linux paths)