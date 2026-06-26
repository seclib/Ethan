"""ETHAN Plugin Isolation System — enforcement and boundary rules.

Isolation boundaries:
  1. NO direct imports of kernel modules
  2. NO direct calls to other plugins
  3. NO in-process shared state between plugins
  4. NO access to kernel internals
  5. Communication ONLY via NATS events and capability registry

Enforcement:
  - Static analysis at plugin load time
  - Runtime boundary checks
  - Capability-based access control
"""

import ast
import sys
from pathlib import Path

# Kernel modules that plugins MUST NOT import
FORBIDDEN_IMPORTS = {
    "kernel",
    "kernel.kernel",
    "kernel.planner",
    "kernel.executor",
    "kernel.registry",
    "kernel.bus",
    "kernel.state",
    "kernel.ingest",
    "kernel.intent",
    "kernel.resolver",
    "kernel.response",
    "core.plugins",
    "core.discovery",
    "core.isolation",
    "sdk",
}

# Functions that plugins MUST NOT call
FORBIDDEN_FUNCTIONS = {
    "os.system",
    "os.popen",
    "subprocess.Popen",
    "subprocess.run",
    "subprocess.call",
    "eval",
    "exec",
    "__import__",
    "importlib",
}

# Allowlist of permitted module prefixes
ALLOWED_IMPORTS = {
    "ethan",
    "requests",
    "json",
    "datetime",
    "os.path",
    "pathlib",
    "typing",
    "logging",
    "re",
    "math",
    "collections",
    "itertools",
    "functools",
    "hashlib",
}

# ---- Static Analysis ----


class IsolationViolation(Exception):
    """Raised when a plugin violates isolation rules."""
    pass


class PluginAnalyzer(ast.NodeVisitor):
    """AST-based static analyzer for plugin code."""

    def __init__(self):
        self.violations: list[str] = []
        self._imported_names: set[str] = set()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.name
            self._imported_names.add(name)
            # Check forbidden imports
            if name in FORBIDDEN_IMPORTS or any(name.startswith(f + ".") for f in FORBIDDEN_IMPORTS):
                self.violations.append(f"forbidden import: {name}")

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module is None:
            return
        module = node.module
        self._imported_names.add(module)
        # Check forbidden imports
        if module in FORBIDDEN_IMPORTS or any(module.startswith(f + ".") for f in FORBIDDEN_IMPORTS):
            self.violations.append(f"forbidden import: {module}")
        # Check specific forbidden functions
        for alias in node.names:
            name = f"{module}.{alias.name}"
            if name in FORBIDDEN_FUNCTIONS:
                self.violations.append(f"forbidden function: {name}")

    def visit_Call(self, node: ast.Call):
        # Detect calls to forbidden built-in functions
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in ("eval", "exec", "__import__"):
                self.violations.append(f"forbidden built-in call: {name}")
        self.generic_visit(node)


def analyze_plugin_code(filepath: Path) -> list[str]:
    """Run static analysis on a plugin file. Returns list of violations."""
    try:
        with open(filepath) as f:
            source = f.read()
        tree = ast.parse(source)
        analyzer = PluginAnalyzer()
        analyzer.visit(tree)
        return analyzer.violations
    except SyntaxError:
        return ["syntax error in plugin code"]
    except Exception as e:
        return [f"analysis error: {e}"]


# ---- Runtime Boundaries ----


class PluginSandbox:
    """Runtime sandbox for plugin execution.

    Provides restricted access to system resources.
    All communication goes through this sandbox.
    """

    def __init__(self, plugin_name: str, capabilities: list[dict]):
        self._name = plugin_name
        self._capabilities = {c["name"]: c for c in capabilities}

    def emit_event(self, subject: str, payload: dict) -> None:
        """Emit an event via NATS (allowed)."""
        # Validation: plugin can only emit events on its own subjects
        prefix = self._name.replace("-", ".").lower()
        if not subject.startswith(f"ethan.capability.{prefix}") and not subject.startswith(f"ethan.plugin.{self._name}"):
            raise IsolationViolation(f"plugin '{self._name}' cannot emit on subject '{subject}'")
        # In production, this would publish to NATS
        pass

    def query_capability(self, name: str) -> dict | None:
        """Query the capability registry (read-only, allowed)."""
        return self._capabilities.get(name)

    def read_state(self, key: str) -> bytes | None:
        """Read state from allowed namespaces only."""
        prefix = f"{self._name}:"
        if not key.startswith(prefix):
            raise IsolationViolation(f"plugin '{self._name}' cannot read state key '{key}'")
        return None

    def write_state(self, key: str, value: bytes) -> None:
        """Write state to allowed namespaces only."""
        prefix = f"{self._name}:"
        if not key.startswith(prefix):
            raise IsolationViolation(f"plugin '{self._name}' cannot write state key '{key}'")
        pass


# ---- Enforcement ----


def enforce_isolation(plugin_name: str, plugin_dir: Path) -> list[str]:
    """Run all isolation checks on a plugin. Returns violations list."""
    entry = plugin_dir / "plugin.py"
    if not entry.exists():
        return ["entry point missing"]

    violations = []

    # 1. Static analysis
    code_violations = analyze_plugin_code(entry)
    violations.extend(code_violations)

    # 2. Check NO access to other plugin directories
    other_plugins = plugin_dir.parent.iterdir()
    for other in other_plugins:
        if other.is_dir() and other.name != plugin_name:
            if (plugin_dir / other.name).exists() or (plugin_dir / f"{other.name}.py").exists():
                violations.append(f"possible cross-plugin access to '{other.name}' detected")

    return violations


def validate_sandbox(plugin_name: str, capabilities: list[dict]) -> PluginSandbox:
    """Create a sandboxed environment for a plugin."""
    return PluginSandbox(plugin_name, capabilities)