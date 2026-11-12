# ETHAN — Modèles d'enregistrement

Date : 2026-11-03
Statut : PROPOSED

Ce document est un compagnon de `MEMORY_DATA_MODEL.md`. Il fournit des gabarits compacts pour les objets fréquemment créés.

## Gabarit minimal : EngineeringEvent

```yaml
---
id: "EVT-2026-001"
type: event
status: RECORDED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "script/manual/operation"
provenance_level: observed
event_type: migration
commit_refs:
  - "9e57d1c0"
related_components:
  - "CMP-YYYY"
parents: []
evidence_refs:
  - "EVD-YYYY"
confidence: medium
notes: "description courte"
---
```

## Gabarit minimal : Decision

```yaml
---
id: "DEC-2026-001"
type: decision
status: PROPOSED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "docs/memory/DECISIONS.md"
provenance_level: observed
title: "titre"
scope: architecture
impact: high
approved_by: ""
approved_at: ""
related_components: []
candidate_refs: []
evidence_refs: []
supersedes: []
superseded_by: []
confidence: high
notes: ""
---
```

## Gabarit minimal : Component

```yaml
---
id: "CMP-2026-001"
type: component
status: IMPLEMENTED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "AGENTS.md"
provenance_level: observed
category: core
implemented_files: []
tests: []
dependencies: []
related_components: []
evidence_refs: []
confidence: high
notes: ""
---
```

## Gabarit minimal : Verification

```yaml
---
id: "VER-2026-001"
type: verification
status: PENDING
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "manual"
provenance_level: observed
component_refs: []
test_refs: []
method: "command or procedure"
result: "observed result"
scope: "local"
dataset: "dataset description"
executed_at: "2026-11-03T10:00:00+04:00"
evidence_refs: []
confidence: medium
notes: ""
---
```

## Gabarits pour Incident et Repair

```yaml
---
id: "INC-2026-001"
type: incident
status: OPEN
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "audit"
provenance_level: observed
incident_type: link_failure
impact: medium
detected_at: "2026-11-03"
recovery_repairs: []
affected_components: []
evidence_refs: []
confidence: medium
notes: ""
---
```

```yaml
---
id: "REP-2026-001"
type: repair
status: PROPOSED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "audit"
provenance_level: derived
incident_refs:
  - "INC-YYYY-NNN"
affected_components: []
implemented_files: []
tests: []
verification_status: UNKNOWN
evidence_refs: []
confidence: medium
notes: ""
---
```

## Gabarit pour Knowledge

```yaml
---
id: "KNW-2026-001"
type: knowledge
status: PROVISIONAL
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "research or docs"
provenance_level: derived
knowledge_domain: research
source_refs: []
related_components: []
confidence: medium
notes: "résumé"
---
```

## Gabarit pour Skill

```yaml
---
id: "SKL-2026-001"
type: skill
status: PROVISIONAL
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "skill catalog"
skill_name: ""
version: "0.0.0"
objective: ""
prerequisites: []
tools: []
permissions: []
limits: []
tests: []
approval_status: proposed
evidence_refs: []
confidence: medium
notes: ""
---
```

## Gabarit pour Evidence

```yaml
---
id: "EVD-2026-001"
type: evidence
status: COLLECTED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: "command output"
provenance_level: observed
evidence_type: command_output
location: "file path or command"
sha256: ""
value_summary: ""
trusted: true
---
```

## Règles d'utilisation

- Chaque gabarit doit être complété avec une source réelle.
- Le statut doit rester cohérent avec sa catégorie.
- Aucun identifiant ne doit être réutilisé.
- Les références manquantes doivent être signalées.
- Une copie complète inutile doit être évitée au profit de références.

