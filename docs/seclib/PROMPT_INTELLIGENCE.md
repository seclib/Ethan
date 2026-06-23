# ETHAN Prompt Intelligence Layer

## Philosophy

ETHAN should read user intent like a colleague:
- "fix docker" → run diagnostic + suggest fix
- "logs" → tail system logs
- "status" → show state

No rigid grammar. Context-aware. Proactive.

---

## 1. Intent Detection

### 1.1 Input Classification

```
User input
    │
    ▼
Classify into one of:
  [COMMAND]        — exact match to known command (run, status, logs, etc.)
  [INTENT]         — action-oriented phrase (fix docker, deploy app)
  [CHAT]           — conversational (hello, explain X)
  [SMART_CMD]      — short command shorthand (logs → ethan logs)
```

### 1.2 SHOT Parameter Detection

Extract key-value parameters from natural language:

| Input | Detected |
|-------|----------|
| `fix docker` | intent=fix, target=docker |
| `check api health` | intent=check, target=api, aspect=health |
| `deploy to staging` | intent=deploy, env=staging |
| `run pytest in /app` | intent=run, cmd=pytest, cwd=/app |

Pattern matching:
- `run <cmd>` → execute command
- `fix <target>` → diagnostic + repair
- `check <target>` → health check
- `deploy <target> to <env>` → deploy
- `logs [for <service>]` → tail logs

---

## 2. Smart Command Execution

### 2.1 Auto-Execution

When an intent maps 1:1 to a capability:

```
User: "fix docker"
    │
    ▼
Detect: intent=fix, target=docker
    │
    ▼
Query capability registry for "docker.repair" or "docker.diagnostic"
    │
    ▼
Execute via executor
    │
    ▼
Show result
```

### 2.2 Fuzzy Matching

| User says | Maps to |
|-----------|---------|
| `logs` | `ethan logs` |
| `log api` | `ethan logs --service api` |
| `status` | `ethan status` |
| `state` | `ethan status` |
| `help` | `ethan --help` |
| `plugins` | `ethan plugin list` |

---

## 3. Proactive Suggestions

### 3.1 Next Action Recommendations

After completing a task, suggest related actions:

```
✓ Deployed to staging

  What next?
  → check staging health
  → run tests
  → deploy to production
```

### 3.2 Contextual Hints

```
User: "fix docker"
Suggestion: I can diagnose docker — run diagnostic?
  → Yes, run docker.diagnostic
  → No, just show status
```

### 3.3 Auto-Completion

Based on history and context:
```
User types: "run tes"
Suggestion: Did you mean?
  → run pytest
  → run tests
```

---

## 4. Prompt Intelligence API

```python
class PromptIntelligence:
    @staticmethod
    def classify(input: str) -> PromptIntent:
        """Return intent type + extracted params."""

    @staticmethod
    def suggest(input: str, history: list[str]) -> list[str]:
        """Return suggested actions."""

    @staticmethod
    def next_actions(last_intent: PromptIntent) -> list[str]:
        """Recommend follow-up actions."""

    @staticmethod
    def execute(intent: PromptIntent) -> str:
        """Execute intent if unambiguous."""
```

---

## 5. Interaction Flows

### 5.1 Direct Execution

```
User: "fix docker"
    │
    ▼
Confidence: high (exact match to known pattern)
    │
    ▼
Execute: ethan run docker.diagnostic
    │
    ▼
Show result: ✓ Docker is healthy
```

### 5.2 Confirmation Prompt

```
User: "deploy staging"
    │
    ▼
Confidence: medium (ambiguous)
    │
    ▼
Confirm: Deploy what to staging?
  → Deploy current project
  → Deploy service <name>
  → Cancel
```

### 5.3 Clarification

```
User: "fix"
    │
    ▼
Confidence: low (missing target)
    │
    ▼
Prompt: Fix what?
  → docker
  → api
  → database
```

---

## 6. Capability Mapping

Known intent → capability mapping:

| Intent | Capability | Fallback |
|--------|------------|----------|
| `fix <target>` | `<target>.diagnostic` → `<target>.repair` | Show status |
| `check <target>` | `<target>.health` | Show info |
| `deploy <target>` | `<target>.deploy` | confirm |
| `run <cmd>` | `shell.run` | direct exec |
| `logs [for X]` | `logs.tail` | show hint |
| `status` | `system.state` | direct query |
| `help` | (built-in) | show help |

---

## 7. Confidence Levels

| Level | Behavior |
|-------|----------|
| **High** (≥0.9) | Execute directly, show result |
| **Medium** (0.6–0.9) | Show suggestion, wait for confirm |
| **Low** (<0.6) | Ask for clarification |

---

## 8. Example Session

```
◆  ethan  ◇  idle  ▸ fix docker

  ◆  ethan  ◇  thinking  ▸
  ■  Detected intent: fix docker
  ■  Querying docker.diagnostic capability...
  ✓  Docker is healthy (0.8s)

  What next?
  → check docker stats
  → deploy app
  → run tests

◆  ethan  ◇  idle  ▸ _