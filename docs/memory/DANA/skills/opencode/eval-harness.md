# Eval Harness (eval-harness)

**Source :** `/home/fatsio/.config/opencode/skills/eval-harness/SKILL.md`  \n**Domaine :** Tests — EDD  \n**Type :** Framework de développement  \n**Niveau :** Expérimental (Niveau C)  \n

## Description

Eval-driven development (EDD) framework for AI coding sessions — defines pass/fail criteria before implementation, measures agent reliability with pass@k, and builds regression suites for prompt/agent changes.

## Main capabilities

- **Pass/fail criteria definition**: Defines acceptance criteria before implementation starts
- **pass@k measurement**: Measures agent reliability and success rates across k attempts
- **Regression suite building**: Constructs regression suites for prompt or agent changes
- **Session grading**: Grades AI coding sessions against defined criteria
- **Prompt/agent change tracking**: Tracks changes and their impact on test outcomes
- **Human-grade evaluation**: Supports model-based, rule, or human graders

## What it can do

- Define evaluation criteria for AI coding tasks
- Run agents against test suites and measure pass rates
- Build regression suites when prompts or agents change
- Generate session evaluation reports with pass@k statistics
- Compare different agent configurations or prompt versions
- Support multiple grading approaches (model-based, rule-based, human)

## When it is useful

- Establishing eval-driven development for AI coding sessions
- Measuring and comparing agent reliability across versions
- Building regression suites for prompt or agent changes
- Grading AI coding session quality before delivery
- Comparing different model configurations or prompt strategies
- Supporting model-based, rule, or human evaluation approaches

## Practical examples

### Evaluation criteria definition

```yaml
# evaluation.yaml
task: "Implement a function that calculates Fibonacci numbers"
pass_criteria:
  - "Function correctly computes fibonacci(n) for n >= 0"
  - "Handles edge cases: fibonacci(0) = 0, fibonacci(1) = 1"
  - "Returns appropriate error for negative inputs"
  - "pass@k: 3 out of 3 attempts must pass"
grading:
  - type: "model-based"
    model: "gpt-4o-mini"
    rubric: "Correctness and edge case handling"
```

### pass@k measurement

```python
# Measure agent reliability across k attempts
def measure_pass_at_k(agent, task, k=3):
    results = []
    for i in range(k):
        result = agent.run(task)
        results.append(result.success)
    pass_at_k = sum(results) / k
    return pass_at_k, results
```

### Regression suite tracking

```markdown
# Regression Suite

| Prompt Version | Task | Result | Notes |
|---|---|---|---|
| v1.0 | Implement X | ✅ Pass | Original implementation |
| v1.1 | Add Y constraint | ❌ Fail | Regression: Y not handled |
| v1.2 | Fix Y handling | ✅ Pass | Regression fixed |
```

## Original source path

`/home/fatsio/.config/opencode/skills/eval-harness/SKILL.md`

## Classification

- **Domaines :** tests, EDD, évaluation, agent reliability
- **Statut :** Expérimental (Niveau C)
- **Références :** `test-master`, `change-impact`, `continuous-learning-v2`
- **Validé :** Oui (rapport d'analyse stratégique Niveau C — framework en développement)
- **Auteur :** OpenCode Analysis
