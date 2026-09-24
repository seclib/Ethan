"""Plugin validator — sécurité et intégrité des plugins (Core-owned).

Capacité unique de validation des plugins pour tout ETHAN :

  - manifest : schéma Core (``id``/``name``/``version``) ou schéma
    legacy (``name``/``version``/``api_version``) conservé pour la
    compatibilité des plugins historiques ;
  - code : aucun import de module dangereux ni builtin dangereux
    (analyse AST), appliqué avant tout chargement.

Les interfaces (CLI) et le loader legacy sont des *clients* de cette
capacité — ``plugins/validator.py`` est un shim de compatibilité qui
re-exporte ce module.  Source de vérité unique : ``core/``.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

FORBIDDEN_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "ctypes",
    "pickle",
    "marshal",
    "shelve",
    "multiprocessing",
    "threading",
    "signal",
}

FORBIDDEN_BUILTINS = {
    "exec",
    "eval",
    "compile",
    "__import__",
    "open",
}

# id Core : minuscules/alphanum/tiret, commence par alphanum (uuid inclus).
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class ValidationResult:
    """Résultat de validation."""

    def __init__(self, valid: bool = True, error: str = ""):
        self.valid = valid
        self.error = error

    def __repr__(self) -> str:
        return f"ValidationResult(valid={self.valid!r}, error={self.error!r})"


class PluginValidator:
    """Valide un manifest et le code d'un plugin avant chargement."""

    def validate_manifest(self, manifest: dict[str, Any]) -> ValidationResult:
        """Valide un manifest — schéma legacy ou schéma Core.

        ``name`` et ``version`` sont requis dans les deux schémas.
        La présence de ``api_version`` marque le manifest legacy
        (comportement historique du loader) ; sinon le schéma Core
        s'applique et exige un ``id`` au format identifiant.
        """
        for field in ("name", "version"):
            value = manifest.get(field)
            if not isinstance(value, str) or not value.strip():
                return ValidationResult(False, f"Missing required field: {field}")

        if "api_version" in manifest:
            # Schéma legacy : api_version marqueur présent → validé.
            return ValidationResult(True)

        plugin_id = manifest.get("id")
        if isinstance(plugin_id, str) and plugin_id:
            if not _ID_RE.match(plugin_id):
                return ValidationResult(False, f"Invalid plugin id: {plugin_id!r}")
            return ValidationResult(True)

        return ValidationResult(False, "Missing required field: id")

    def validate_imports(self, plugin_path: Path) -> ValidationResult:
        """Vérifie qu'aucun import/builtin interdit n'apparaît dans le code."""
        for py_file in plugin_path.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in FORBIDDEN_IMPORTS:
                                return ValidationResult(
                                    False,
                                    f"Forbidden import '{alias.name}' in {py_file.name}",
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.split(".")[0] in FORBIDDEN_IMPORTS:
                            return ValidationResult(
                                False,
                                f"Forbidden import from '{node.module}' in {py_file.name}",
                            )
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
                            return ValidationResult(
                                False,
                                f"Forbidden builtin '{node.func.id}' in {py_file.name}",
                            )
            except SyntaxError:
                return ValidationResult(False, f"Syntax error in {py_file.name}")
        return ValidationResult(True)

    def validate(self, path: Path, manifest: dict[str, Any]) -> ValidationResult:
        """Validation complète d'un plugin (manifest puis code)."""
        result = self.validate_manifest(manifest)
        if not result.valid:
            return result
        return self.validate_imports(path)


__all__ = [
    "FORBIDDEN_BUILTINS",
    "FORBIDDEN_IMPORTS",
    "PluginValidator",
    "ValidationResult",
]
