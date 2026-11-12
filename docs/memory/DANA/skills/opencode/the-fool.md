# The Fool (the-fool)

**Source :** `/home/fatsio/.config/opencode/skills/the-fool/SKILL.md`  \n**Domaine :** Révision critique — Raisonnement adversarial  \n**Type :** Analyse stratégique  \n**Niveau :** Expérimental (Niveau C)  \n

## Description

Defies ideas, plans, decisions, or proposals using structured critical reasoning. Plays devil's advocate, runs pre-mortems, red teams, or audits evidence and assumptions. Finds blind spots and unstated assumptions.

## Main capabilities

- **Critical reasoning**: Structured analysis of ideas, plans, and decisions to identify weaknesses
- **Pre-mortem analysis**: Simulates project failure to identify potential risks and blind spots
- **Red teaming**: Challenges assumptions and proposed solutions from multiple perspectives
- **Assumption auditing**: Identifies unstated or hidden assumptions in proposals
- **Blind spot detection**: Finds gaps in reasoning that others may miss
- **Evidence assessment**: Evaluates evidence quality and identifies contradictions

## What it can do

- Play devil's advocate in planning sessions and decision reviews
- Conduct pre-mortem analyses on project plans
- Challenge architectural decisions and proposed solutions
- Identify hidden assumptions in requirements and designs
- Audit evidence and identify contradictory information
- Generate structured critical reports with findings and recommendations

## When it is useful

- Architectural design reviews and decision making
- Project planning and risk assessment
- Evaluating proposed solutions or architectures
- Identifying blind spots in team reasoning
- Pre-mortem analysis before project initiation
- Red teaming for security and strategy reviews

## Practical examples

### Pre-mortem analysis template

```markdown # Pre-Mortem Analysis

**Project**: [Project Name]
**Date**: [Date]
**Team**: [Team Members]

Imagine it's 6 months from now and the project has failed. Write down the reasons why:

1. ...
2. ...
3. ...

**Root Cause Analysis**:
- [Identify root causes]
- [Connect to assumptions]
- [Connect to missing evidence]

**Mitigation Strategies**:
- [Actions to prevent these causes]
- [Contingency plans]
```

### Devil's advocate framework

```markdown
## Question: Should we use MongoDB for user profiles?

### Arguments For:
1. Flexible schema for evolving requirements
2. Horizontal scaling built-in
3. JSON document model matches application data

### Arguments Against (Devil's Advocate):
1. ACID transactions limited compared to relational
2. Query complexity for relational-style operations
3. Potential data modeling anti-patterns

### Evidence Required:
- [Benchmark data on scaling characteristics]
- [Team expertise with document databases]
- [Specific use case requirements analysis]
```

## Original source path

`/home/fatsio/.config/opencode/skills/the-fool/SKILL.md`

## Classification

- **Domaines :** raisonnement critique, adversarial, analyse, blind spots
- **Statut :** Expérimental (Niveau C)
- **Références :** `change-impact`, `the-fool`, `agent-introspection-debugging`
- **Validé :** Oui (rapport d'analyse stratégique Niveau C — nécessite validation)
- **Auteur :** OpenCode Analysis
