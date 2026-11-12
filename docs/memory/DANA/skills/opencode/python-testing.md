# Python Testing (python-testing)

**Source :** `/home/fatsio/.config/opencode/skills/python-testing/SKILL.md`  \n**Domaine :** Tests — Python  \n**Type :** Skill technique  \n**Niveau :** Indispensable (Niveau A)  \n

## Description

Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization, and coverage requirements. TDD cycle (red-green-refactor), coverage targets (80%+ critical paths 100%), fixture patterns, mock strategies, parametrized tests.

## Main capabilities

- **TDD cycle**: Implements red-green-refactor test-driven development cycle
- **pytest fixtures**: Creates reusable fixture patterns for test isolation
- **Mocking strategies**: Implements mock objects and test doubles with unittest.mock or pytest-mock
- **Parametrized tests**: Runs same test with multiple inputs using pytest.mark.parametrize
- **Coverage targets**: Aims for 80%+ critical paths coverage, 100% for critical paths
- **Test organization**: Structures test files and modules following project conventions

## What it can do

- Generate pytest test files with proper fixture patterns
- Create parametrized tests for multiple input scenarios
- Implement mock objects for dependency isolation
- Set up coverage reporting and threshold enforcement
- Design test organization patterns (unit, integration, E2E)
- Run TDD cycle (red-green-refactor) for feature development

## When it is useful

- Establishing TDD methodology in Python projects
- Adding test suites to existing Python codebases
- Setting up coverage targets and reporting in CI/CD
- Implementing fixture patterns for test isolation
- Creating parametrized tests for broad input coverage
- Enforcing 80%+ critical paths coverage thresholds

## Practical examples

### pytest fixture example

```python
import pytest

@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="session")
def database():
    """Create session-scoped database fixture."""
    setup_database()
    yield
    teardown_database()
```

### Parametrized test

```python
import pytest

@pytest.mark.parametrize("a, b, expected", [
    (2, 3, 5),
    (5, 7, 12),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_addition(a, b, expected):
    assert a + b == expected
```

### Coverage configuration

```toml
# pyproject.toml
[tool.pytest]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["test_*"]
python_functions = ["test_*"]

[tool.pytest.options]
addopts = "--cov=myproject --cov-report=term-missing --cov-report=html"

[pytest.cov]
run = true
source = ["myproject"]
```

## Original source path

`/home/fatsio/.config/opencode/skills/python-testing/SKILL.md`

## Classification

- **Domaines :** tests, Python, TDD, pytest, couverture
- **Statut :** Indispensable (Niveau A)
- **Références :** `test-master`, `python-pro`, `change-impact`
- **Validé :** Oui (rapport d'analyse stratégique Niveau A)
- **Auteur :** OpenCode Analysis
