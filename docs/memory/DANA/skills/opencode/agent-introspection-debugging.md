# Agent Introspection Debugging (agent-introspection-debugging)

**Source :** `/home/fatsio/.config/opencode/skills/agent-introspection-debugging/SKILL.md`  \n**Domaine :** Débogage agent  \n**Type :** Workflow de débogage  \n**Niveau :** Expérimental (Niveau C)  \n

## Description

Workflow auto-debugging for repeated agent run failures. Captures failure state, diagnoses common agent-specific failure patterns, applies contained recovery actions, and produces structured human-readable debug report.

## Main capabilities

- **Failure state capture**: Captures and logs the state at the point of agent failure
- **Pattern diagnosis**: Identifies common agent-specific failure patterns (looping, Goodhart-gaming, wrong answer completion)
- **Contained recovery**: Applies recovery actions within bounded scope to avoid cascading failures
- **Structured debug report**: Produces human-readable report with failure analysis and recommendations
- **Recurring issue tracking**: Tracks recurring failure patterns across multiple agent runs
- **Root cause identification**: Isolates root causes of agent failures

## What it can do

- Capture failure state including last actions, observations, and error messages
- Diagnose common patterns: spinning (infinite loops), Goodhart-gaming (optimizing for wrong metric), running wrong answer to completion
- Apply contained recovery: reset state, retry with modified parameters, fall back to simpler approach
- Generate structured debug report with failure classification and recommended actions
- Track failure patterns over time to identify systemic issues
- Provide recommendations for preventing recurrence

## When it is useful

- Repeated agent run failures with same or similar symptoms
- Identifying why an agent is spinning or looping
- Diagnoding Goodhart-gaming behavior where agent optimizes for wrong metric
- Recovering from agent running a wrong answer to completion
- Systemic analysis of agent failure patterns across multiple runs
- Improving agent reliability through failure pattern analysis

## Practical examples

### Failure state capture

```json
{
  "timestamp": "2026-11-11T10:30:00Z",
  "agent_state": {
    "current_task": "Implement calculate function",
    "last_action": "Call search tool with query 'algorithm'",
    "error_message": "TypeError: search result is undefined",
    "call_stack": ["run()", "execute_tool()", "parse_result()"]
  },
  "failure_pattern": "tool_output_parsing_error",
  "recovery_attempted": true,
  "recovery_action": "Reset agent state and retry with simplified query"
}
```

### Pattern diagnosis and recovery

```
Failure observed: Agent spinning on same task for 20+ iterations
Diagnosed pattern: Infinite loop (spinning)
Recovery action: Reset task state, add iteration limit, retry with timeout
```

### Structured debug report

```markdown
# Agent Debug Report

**Date**: 2026-11-11
**Agent**: ETHAN OS Agent
**Task**: Implement calculator with edge cases

## Failure Analysis
- Pattern: Spinning (infinite loop)
- Iterations: 23 before intervention
- Last successful action: Addition operation

## Root Cause
- No iteration limit configured
- Agent continuously retries same operation without progress check

## Recommended Actions
1. Add iteration limit of 5 attempts
2. Implement progress tracking to detect stagnation
3. Add fallback to manual calculation if exceeded
```

## Original source path

`/home/fatsio/.config/opencode/skills/agent-introspection-debugging/SKILL.md`

## Classification

- **Domaines :** débogage, agent, patterns, recovery
- **Statut :** Expérimental (Niveau C)
- **Références :** `the-fool`, `change-impact`, `test-master`
- **Validé :** Oui (rapport d'analyse stratégique Niveau C — workflow en développement)
- **Auteur :** OpenCode Analysis
