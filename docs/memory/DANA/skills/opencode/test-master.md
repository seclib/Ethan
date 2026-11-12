# Test Master (test-master)

**Source :** `/home/fatsio/.config/opencode/skills/test-master/SKILL.md`  \n**Domaine :** Tests — Complet  \n**Type :** Skill technique  \n**Niveau :** Spécialisé (Niveau B)  \n

## Description

Generates test files, creates mocking strategies, analyzes code coverage, designs test architectures, produces test plans and defect reports across functional, performance, and security testing. Implements k6/Artillery load testing, OWASP security testing, flaky test debugging, shift-left testing, and quality gates.

## Main capabilities

- **Test file generation**: Creates comprehensive test files for codebases
- **Mocking strategies**: Designs mock objects and test doubles
- **Code coverage analysis**: Analyzes test coverage with thresholds and reports
- **Test architecture design**: Designs test structures and organization
- **Defect report production**: Produces defect reports across testing disciplines
- **Load testing**: Implements k6/Artillery performance and load tests

## What it can do

- Generate pytest/testunit test files with proper structure
- Design mock objects using MockK, Mockito, or similar frameworks
- Analyze code coverage percentages and identify untested paths
- Design test architectures aligned with project patterns
- Produce defect reports with severity classification
- Create k6 scripts for load and stress testing
- Implement OWASP security testing patterns

## When it is useful

- Establishing test suites for new projects
- Migrating to TDD methodology
- Adding performance and load testing to CI/CD
- Improving test coverage below acceptable thresholds
- Designing test architectures for microservice systems
- Debugging flaky tests and improving test reliability

## Practical examples

### pytest test generation

```python
import pytest

class TestCalculator:
    @pytest.fixture
    def calculator(self):
        return Calculator()

    def test_add(self, calculator):
        assert calculator.add(2, 3) == 5

    def test_subtract(self, calculator):
        assert calculator.subtract(5, 3) == 2
```

### k6 load test script

```javascript
import { check, sleep } from "k6";
import http from "k6/http";

export let options = {
    stages: [
        { duration: "2m", target: 100 }, // ramp up to 100 users
        { duration: "5m", target: 100 }, // stay at 100 users
        { duration: "2m", target: 0 },   // ramp down to 0
    ],
};

export default function () {
    const res = http.get("https://api.example.com/endpoint");
    check(res, { "status is 200": (r) => r.status === 200 });
    sleep(1);
}
```

### Coverage report configuration

```json
{
  "coverege": {
    "thresholds": {
      "global": {
        "branches": 80,
        "functions": 90,
        "lines": 85,
        "statements": 85
      }
    }
  }
}
```

## Original source path

`/home/fatsio/.config/opencode/skills/test-master/SKILL.md`

## Classification

- **Domaines :** tests, qualité, couverture, load testing
- **Statut :** Spécialisé (Niveau B)
- **Références :** `python-testing`, `change-impact`, `security-scan`
- **Validé :** Oui (rapport d'analyse stratégique Niveau B)
- **Auteur :** OpenCode Analysis
