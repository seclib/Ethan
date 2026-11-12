# Python Professional (python-pro)

**Source :** `/home/fatsio/.config/opencode/skills/python-pro/SKILL.md`  \n**Domaine :** Ingénierie — Python  \n**Type :** Skill technique  \n**Niveau :** Indispensable (Niveau A)  \n

## Description

Python 3.11+ application expert with type safety, async programming, and robust error handling. Generates type-annotated Python code, configures mypy in strict mode, writes pytest test suites with fixtures and mocking, and validates code with black and ruff. Enforces strict typing schemas as required by ECC guardrails (no `any` bypass).

## Main capabilities

- **Type-annotated code generation**: Creates Python 3.11+ code with full type hints using PEP 484/526/604 conventions
- **Strict mypy configuration**: Sets up mypy in strict mode with appropriate configuration for the project
- **Pytest test suite creation**: Generates comprehensive test suites with fixtures, parametrization, and mocking strategies
- **Code formatting and linting**: Integrates with black (formatter) and ruff (linter) for code quality enforcement
- **Async programming patterns**: Implements async/await patterns with proper type safety
- **Error handling patterns**: Generates robust error handling with typed errors over string messages

## What it can do

- Generate type-annotated Python functions and classes with full type safety
- Configure mypy strict mode and appropriate per-project settings
- Create pytest test files with fixtures, mock objects, and parametrized tests
- Set up black and ruff configuration for code quality enforcement
- Implement async/await patterns with proper type annotations
- Generate structured error handling with custom exception types

## When it is useful

- Starting a new Python project requiring type safety from the beginning
- Adding type annotations to an existing Python codebase
- Setting up CI/CD pipelines with code quality checks (mypy, black, ruff)
- Creating pytest test suites with proper fixture patterns
- Enforcing ECC guardrails against `any` bypass in type annotations

## Practical examples

### Type-annotated function

```python
def calculate_total(items: list[dict[str, float | int]]) -> float:
    """Calculate the total of a list of item dictionaries."""
    return sum(item["price"] * item["quantity"] for item in items)
```

### Pytest fixture example

```python
import pytest

@pytest.fixture
def client():
    """Create a test client fixture."""
    with TestClient(app) as c:
        yield c
```

### mypy configuration

```ini
[mypy]
strict = True
disallow_untyped_defs = True
disallow_return_any = True
```

## Original source path

`/home/fatsio/.config/opencode/skills/python-pro/SKILL.md`

## Classification

- **Domaines :** ingénierie, Python, type-safety, async, tests
- **Statut :** Indispensable (Niveau A)
- **Références :** `error-handling`, `python-testing`, `api-design`
- **Validé :** Oui (rapport d'analyse stratégique Niveau A)
- **Auteur :** OpenCode Analysis
