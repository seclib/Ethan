"""Plugin validator — sécurité et intégrité des plugins."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

FORBIDDEN_IMPORTS = {
    "os", "sys", "subprocess", "shutil", "socket",
    "ctypes", "pickle", "marshal", "shelve",
    "multiprocessing", "threading", "signal",
}

FORBIDDEN_BUILTINS = {
    "exec", "eval", "compile", "__import__", "open",
}


class ValidationResult:
    """Résultat de validation."""
    def __init__(self, valid: bool = True, error: str = ""):
        self.valid = valid
        self.error = error


class PluginValidator:
    """Valide un plugin avant chargement."""

    def validate_manifest(self, manifest: dict) -> ValidationResult:
        """Valide le manifest."""
        required = ["name", "version", "api_version"]
        for field in required:
            if field not in manifest:
                return ValidationResult(False, f"Missing required field: {field}")
        return ValidationResult(True)

    def validate_imports(self, plugin_path: Path) -> ValidationResult:
        """Vérifie les imports interdits."""
        for py_file in plugin_path.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in FORBIDDEN_IMPORTS:
                                return ValidationResult(
                                    False,
                                    f"Forbidden import '{alias.name}' in {py_file.name}"
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.split(".")[0] in FORBIDDEN_IMPORTS:
                            return ValidationResult(
                                False,
                                f"Forbidden import from '{node.module}' in {py_file.name}"
                            )
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
                            return ValidationResult(
                                False,
                                f"Forbidden builtin '{node.func.id}' in {py_file.name}"
                            )
            except SyntaxError:
                return ValidationResult(False, f"Syntax error in {py_file.name}")
        return ValidationResult(True)

    def validate(self, path: Path, manifest: dict) -> ValidationResult:
        """Validation complète d'un plugin."""
        result = self.validate_manifest(manifest)
        if not result.valid:
            return result
        return self.validate_imports(path)