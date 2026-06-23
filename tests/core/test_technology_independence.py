"""Tests — Technology Independence (ADR-1005)

Vérifie que le core n'importe pas de dépendances technologiques directes.
"""

import ast
import os
from pathlib import Path

import pytest

# Modules interdits dans le core
FORBIDDEN_IMPORTS = {
    "openai",
    "anthropic",
    "docker",
    "sqlite3",
    "psycopg2",
    "asyncpg",
    "qdrant",
    "redis",
    "ollama",
    "requests",
    "httpx",
    "pydantic",
    "fastapi",
    "uvicorn",
    "playwright",
    "selenium",
    "boto3",
    "google.cloud",
    "azure",
    "cohere",
    "huggingface",
    "transformers",
    "torch",
    "tensorflow",
}

# Répertoires du core autorisés
CORE_DIRS = {"core", "tests/core"}


class TestCoreTechnologyIndependence:
    """Vérifie que le core ne dépend pas de technologies externes."""

    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def core_files(self, project_root):
        """Trouve tous les fichiers Python dans core/ et tests/core/."""
        files = []
        for core_dir in CORE_DIRS:
            dir_path = project_root / core_dir
            if dir_path.exists():
                files.extend(dir_path.rglob("*.py"))
        return files

    def test_no_forbidden_imports(self, core_files, project_root):
        """Vérifie qu'aucun import interdit n'est présent dans le core."""
        violations = []
        
        for file_path in core_files:
            # Ignorer les fichiers __pycache__
            if "__pycache__" in str(file_path):
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    # Vérifier les imports directs
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name.split(".")[0]
                            if module_name in FORBIDDEN_IMPORTS:
                                rel_path = file_path.relative_to(project_root)
                                violations.append(
                                    f"{rel_path}:{node.lineno}: import '{alias.name}'"
                                )
                    
                    # Vérifier les from imports
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_name = node.module.split(".")[0]
                            if module_name in FORBIDDEN_IMPORTS:
                                rel_path = file_path.relative_to(project_root)
                                violations.append(
                                    f"{rel_path}:{node.lineno}: from '{node.module}' import ..."
                                )
            except (SyntaxError, UnicodeDecodeError) as e:
                # Ignorer les fichiers avec des erreurs de syntaxe
                pass
        
        if violations:
            error_msg = "Forbidden technology imports found in core:\n" + "\n".join(violations)
            pytest.fail(error_msg)

    def test_core_uses_abstractions(self, project_root):
        """Vérifie que le core utilise les abstractions définies."""
        core_init = project_root / "core" / "__init__.py"
        
        if core_init.exists():
            content = core_init.read_text()
            # Vérifier que le core documente son indépendance
            assert "abstraction" in content.lower() or "interchangeable" in content.lower(), \
                "Core should document technology independence"

    def test_providers_are_abstract(self, project_root):
        """Vérifie que les providers sont bien abstraits."""
        providers_file = project_root / "core" / "providers" / "__init__.py"
        
        if providers_file.exists():
            content = providers_file.read_text()
            assert "ABC" in content or "abstractmethod" in content, \
                "Providers should use abstract base classes"
            assert "ReasoningProvider" in content, \
                "Core should define ReasoningProvider abstraction"

    def test_memory_is_abstract(self, project_root):
        """Vérifie que le système de mémoire est bien abstrait."""
        memory_file = project_root / "core" / "memory" / "__init__.py"
        
        if memory_file.exists():
            content = memory_file.read_text()
            assert "ABC" in content or "abstractmethod" in content, \
                "Memory should use abstract base classes"
            assert "MemoryBackend" in content, \
                "Core should define MemoryBackend abstraction"