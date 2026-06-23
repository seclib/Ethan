"""Tests — Cognitive Memory Architecture (ADR-2001)

Vérifie que la mémoire est un sous-système cognitif, pas une couche de persistance.
"""

import ast
from pathlib import Path

import pytest

# Répertoire du core (remonter de 3 niveaux: tests/core/ -> tests/ -> racine -> core/)
CORE_DIR = Path(__file__).parent.parent.parent / "core"

# Patterns interdits dans core/memory/ (hors abstractions)
FORBIDDEN_IN_MEMORY_IMPL = {
    "sqlite3",
    "redis",
    "qdrant",
    "pymongo",
    "psycopg2",
    "asyncpg",
    "mysql",
}


class TestCognitiveMemoryArchitecture:
    """Vérifie que la mémoire est architecturée comme un sous-système cognitif."""

    def test_memory_backend_is_abstract(self):
        """Vérifie que MemoryBackend est une abstraction cognitive."""
        memory_init = CORE_DIR / "memory" / "__init__.py"
        
        assert memory_init.exists(), "core/memory/__init__.py should exist"
        
        content = memory_init.read_text()
        tree = ast.parse(content)
        
        # Vérifier que MemoryBackend est une ABC
        found_abc = False
        found_memory_backend = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == "MemoryBackend":
                    found_memory_backend = True
                    # Vérifier qu'elle hérite de ABC
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == "ABC":
                            found_abc = True
        
        assert found_memory_backend, "MemoryBackend class should exist in core/memory/"
        assert found_abc, "MemoryBackend should inherit from ABC (abstract base class)"

    def test_no_database_imports_in_core_memory(self):
        """Vérifie qu'aucun import de base de données n'est dans core/memory/."""
        memory_dir = CORE_DIR / "memory"
        
        if not memory_dir.exists():
            return
        
        violations = []
        
        for py_file in memory_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Vérifier les imports directs
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        if module_name in FORBIDDEN_IN_MEMORY_IMPL:
                            rel_path = py_file.relative_to(CORE_DIR.parent)
                            violations.append(
                                f"{rel_path}:{node.lineno}: import '{alias.name}'"
                            )
                
                # Vérifier les from imports
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split(".")[0]
                        if module_name in FORBIDDEN_IN_MEMORY_IMPL:
                            rel_path = py_file.relative_to(CORE_DIR.parent)
                            violations.append(
                                f"{rel_path}:{node.lineno}: from '{node.module}' import ..."
                            )
        
        if violations:
            error_msg = "Forbidden database imports found in core/memory/:\n" + "\n".join(violations)
            pytest.fail(error_msg)

    def test_memory_entry_is_cognitive(self):
        """Vérifie que MemoryEntry représente une entrée cognitive, pas une ligne DB."""
        memory_init = CORE_DIR / "memory" / "__init__.py"
        content = memory_init.read_text()
        
        # Vérifier la présence de MemoryEntry
        assert "class MemoryEntry" in content, "MemoryEntry should be defined"
        
        # Vérifier les champs cognitifs (pas de champs SQL)
        required_fields = ["key", "value", "namespace", "metadata", "embedding", "timestamp", "ttl"]
        for field in required_fields:
            assert field in content, f"MemoryEntry should have '{field}' field"
        
        # Vérifier qu'il n'y a pas de champs SQL évidents
        sql_fields = ["id INTEGER PRIMARY KEY", "AUTOINCREMENT", "FOREIGN KEY", "CREATE TABLE"]
        for sql_field in sql_fields:
            assert sql_field not in content, "MemoryEntry should not contain SQL schema definitions"

    def test_memory_system_is_cognitive_not_persistence(self):
        """Vérifie que MemorySystem est un système cognitif, pas un ORM."""
        memory_init = CORE_DIR / "memory" / "__init__.py"
        content = memory_init.read_text()
        
        # Vérifier la présence de MemorySystem
        assert "class MemorySystem" in content, "MemorySystem should be defined"
        
        # Vérifier les méthodes cognitives
        cognitive_methods = ["store", "retrieve", "search", "delete", "list_namespaces", "clear"]
        for method in cognitive_methods:
            assert f"def {method}" in content or f"async def {method}" in content, \
                f"MemorySystem should have '{method}' method"
        
        # Vérifier qu'il n'y a pas de code SQL
        sql_patterns = ["SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE TABLE", "JOIN "]
        for pattern in sql_patterns:
            assert pattern not in content, "MemorySystem should not contain SQL queries"

    def test_no_filesystem_operations_in_core_memory(self):
        """Vérifie qu'il n'y a pas d'opérations fichiers directes dans core/memory/."""
        memory_dir = CORE_DIR / "memory"
        
        if not memory_dir.exists():
            return
        
        violations = []
        
        for py_file in memory_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Vérifier les appels à open(), Path(), etc.
                if isinstance(node, ast.Call):
                    func = node.func
                    
                    # open(...)
                    if isinstance(func, ast.Name) and func.id == "open":
                        rel_path = py_file.relative_to(CORE_DIR.parent)
                        violations.append(f"{rel_path}:{node.lineno}: direct open() call")
                    
                    # Path(...) ou pathlib.Path(...)
                    elif isinstance(func, ast.Attribute):
                        if func.attr in ["read_text", "write_text", "unlink", "mkdir", "glob"]:
                            rel_path = py_file.relative_to(CORE_DIR.parent)
                            violations.append(f"{rel_path}:{node.lineno}: filesystem operation")
        
        if violations:
            error_msg = "Forbidden filesystem operations in core/memory/:\n" + "\n".join(violations)
            pytest.fail(error_msg)

    def test_memory_backends_are_in_plugins(self):
        """Vérifie que les implémentations de backends sont dans plugins/, pas core/."""
        # Redis backend ne doit pas être dans core/
        core_redis = CORE_DIR / "memory" / "redis_backend.py"
        assert not core_redis.exists(), "Redis backend should not be in core/memory/"
        
        # SQLite backend ne doit pas être dans core/
        core_sqlite = CORE_DIR / "memory" / "sqlite_backend.py"
        assert not core_sqlite.exists(), "SQLite backend should not be in core/memory/"
        
        # Les backends doivent être dans plugins/
        plugins_memory = Path(__file__).parent.parent.parent / "plugins" / "memory"
        assert plugins_memory.exists(), "plugins/memory/ should exist"
        
        plugins_redis = plugins_memory / "redis_backend.py"
        plugins_sqlite = plugins_memory / "sqlite_backend.py"
        
        assert plugins_redis.exists(), "Redis backend should be in plugins/memory/"
        assert plugins_sqlite.exists(), "SQLite backend should be in plugins/memory/"