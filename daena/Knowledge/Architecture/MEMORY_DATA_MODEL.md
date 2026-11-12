# ETHAN — Modèle de données de la mémoire technique

Date : 2026-11-03
Statut : PROPOSED
Confidentialité : architecture documentaire, sans secret

## 1. Formats

- Markdown pour la documentation humaine.
- YAML frontmatter pour les métadonnées exploitables par agent.
- Les relations au déRendering use JSON pointers.
- IDs stables et référents.
- Aucune dépendance à une interface graphique.

## 2. Schéma global

Tous les objets suivants partagent un enveloppe YAML commune :

```yaml
id: "CMP-2026-014"
type: component
status: IMPLEMENTED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: docs/memory/DECISIONS.md
provenance_level: observed
parents:
  - "EVT-2026-001"
related_components:
  - "CMP-YYYY-NNN"
evidence_refs:
  - "EVD-YYYY-NNN"
related_tests:
  - "TST-2026-001"
supersedes: []
superseded_by: []
confidence: medium
notes: ""
```

### Champs communs

<|constrain|> Champ | Type | Description |
|---|---|---|
| `id` | string | identifiant stable |
| `type` | enum | type d'entité |
| `status` | enum | statut propre à la catégorie |
| `created_at` | date ISO-8601 | date d'insertion dans la mémoire |
| `updated_at` | date ISO-8601 | dernière modification connue |
| `source_of_fact` | string | source opposable |
| `provenance_level` | observed / derived / inferred | origine logique |
| `parents` | list[string] | objets parents |
| `related_components` | list[string] | composants concernés |
| `evidence_refs` | list[string] | preuves |
| `supersedes` | list[string] | valeurs antérieures remplacées |
| `superseded_by` | list[string] | éléments successeurs |
| `confidence` | low / medium / high | niveau de confiance |
| `notes` | string | contexte utile |

## 3. Entités proposées

### 3.1 Component

Synthèse d'un élément architectural ou applicatif.

```yaml
---
id: "CMP-2026-001"
type: component
status: IMPLEMENTED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: AGENTS.md
provenance_level: observed
category: core
implemented_files:
  - "core/agents/manager.py"
tests:
  - "TST-2026-001"
dependencies:
  - "DEP-2026-001"
related_components: []
evidence_refs:
  - "EVD-2026-001"
confidence: high
notes: "Élément d'intelligence principale du Core."
---
```

Champs propres :

- `category` : `core`, `runtime`, `service`, `interface`, `agent`
- `implemented_files`
- `tests`
- `dependencies`

### 3.2 Decision

Décision architecturale ou technique.

```yaml
---
id: "DEC-2026-001"
type: decision
status: APPROVED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: docs/memory/DECISIONS.md
provenance_level: observed
title: "Conservation de la WebUI Next.js existante comme base"
related_components:
  - "CMP-YYYY"
candidate_refs:
  - ""
evidence_refs:
  - "EVD-YYYY"
scope: architecture
impact: high
approved_by: "operator"
approved_at: "2026-08-17"
supersedes: []
superseded_by: []
---
```

Champs propres :

- `title`
- `scope`
- `impact` : `low`, `medium`, `high`, `critical`
- `approved_by`
- `approved_at`
- `candidate_refs`

### 3.3 EngineeringEvent

Événement marquant du cycle de vie technique.

```yaml
---
id: "EVT-2026-001"
type: event
status: RECORDED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: git log
provenance_level: observed
event_type: migration
commit_refs:
  - "9e57d1c0"
related_components:
  - "CMP-YYYY"
severity: medium
duration_minutes: 0
notes: "Promotion / conservation lors d'une opération documentaire."
---
```

Champs propres :

- `event_type` : `commit`, `migration`, `audit`, `release`, `test_run`
- `commit_refs`
- `severity`
- `duration_minutes`

### 3.4 Incident

```yaml
---
id: "INC-2026-001"
type: incident
status: RESOLVED
created_at: "2026-11-03"
updated_at: "2026-08-19"
source_of_fact: Obsidian/Odsidian
provenance_level: observed
incident_type: merge_conflict
impact: high
detected_at: "2026-08-19"
recovery_repairs:
  - "REP-YYYY"
affected_components:
  - "CMP-YYYY"
evidence_refs:
  - "EVD-YYYY"
---
```

Champs propres :

- `incident_type`
- `impact`
- `detected_at`
- `recovery_repairs`
- `affected_components`

### 3.5 Repair

```yaml
---
id: "REP-2026-001"
type: repair
status: IMPLEMENTED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: Obsidian/Operational-Memory/TASKS.md
provenance_level: derived
incident_refs:
  - "INC-YYYY"
affected_components:
  - "CMP-YYYY"
implemented_files:
  - "interfaces/webui/..."
tests:
  - "TST-YYYY"
evidence_refs:
  - "EVD-YYYY"
verification_status: UNKNOWN
---
```

Champs propres :

- `incident_refs`
- `affected_components`
- `implemented_files`
- `tests`
- `verification_status`

### 3.6 Verification

```yaml
---
id: "VER-2026-001"
type: verification
status: PENDING
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: script/manual
provenance_level: observed
component_refs:
  - "CMP-YYYY"
test_refs:
  - "TST-YYYY"
method: "gitleaks --source Obsidian"
result: "no leaks found"
scope: memory
dataset: "local target"
executed_at: "2026-11-03T10:43:00+04:00"
evidence_refs:
  - "EVD-YYYY"
---
```

Champs propres :

- `component_refs`
- `test_refs`
- `method`
- `result`
- `scope`
- `dataset`
- `executed_at`

### 3.7 Dependency

```yaml
---
id: "DEP-2026-001"
type: dependency
status: CLEAN
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: pyproject.toml
provenance_level: observed
dependency_name: "PyYAML"
version_range: ">=6.0"
package_manager: "uv"
risk_level: low
vulnerabilities: []
used_by:
  - "CMP-YYYY"
evidence_refs:
  - "EVD-YYYY"
---
```

Champs propres :

- `dependency_name`
- `version_range`
- `package_manager`
- `risk_level`
- `vulnerabilities`
- `used_by`

### 3.8 TestResult

```yaml
---
id: "TST-2026-001"
type: test_result
status: PASSED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: Obsidian/Audit
provenance_level: observed
component_refs:
  - "CMP-YYYY"
command: "gitleaks detect --source Obsidian --no-git"
result: "no leaks found"
dataset: "136 target files"
observed_failures: []
evidence_refs:
  - "EVD-YYYY"
---
```

### 3.9 TechnicalDebt

```yaml
---
id: "DEBT-2026-001"
type: technical_debt
status: IDENTIFIED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: Obsidian/_meta/POST_MIGRATION_AUDIT.md
provenance_level: derived
component_refs:
  - "CMP-YYYY"
severity: medium
cause: "documentation layering"
mitigation: "manifest with checksums and clean rename decision"
related_tests: []
evidence_refs:
  - "EVD-YYYY"
---
```

Champs propres :

- `severity`
- `cause`
- `mitigation`
- `related_tests`

### 3.10 Evidence

```yaml
---
id: "EVD-2026-001"
type: evidence
status: COLLECTED
created_at: "2026-11-03"
updated_at: "2026-11-03"
source_of_fact: file path or command
provenance_level: observed
evidence_type: command_output
location: "Obsidian/Knowledge/INDEX_..."
sha256: "hex..."
value_summary: "captured result"
trusted: true
---
```

### 3.11 AgentReport

```yaml
---
id: "RPT-2026-001"
type: agent_report
status: PROVISIONAL
created_at: "2026-11-03"
updated_at: "2026-11-03"
agent: "codex"
source_of_fact: Obsidian audit session
provenance_level: derived
scope: "memory architecture"
related_components: []
related_events: []
evidence_refs:
  - "EVD-YYYY"
summary: "short"
findings:
  - "some finding"
recommendations:
  - "some recommendation"
---
```

## 4. Statuts recommandés

Les statuts s'appliquent selon la catégorie.

### Décisions

- `PROPOSED`
- `UNDER_REVIEW`
- `APPROVED`
- `REJECTED`
- `DEPRECATED`
- `SUPERSEDED`

### Propositions

- `PROPOSED`
- `UNDER_REVIEW`
- `IMPLEMENTED`
- `REJECTED`
- `DEPRECATED`

### Composants

- `PLANNED`
- `IMPLEMENTED`
- `VERIFIED`
- `DEPRECATED`
- `UNKNOWN`

### Incidents

- `OPEN`
- `INVESTIGATING`
- `MITIGATED`
- `RESOLVED`
- `VERIFIED`
- `FALSE_POSITIVE`

### Réparations

- `PROPOSED`
- `APPROVED`
- `IMPLEMENTED`
- `VERIFIED`
- `FAILED`
- `ABANDONED`

### Vérifications

- `PENDING`
- `PASSED`
- `FAILED`
- `INCONCLUSIVE`
- `OBSOLETE`

### Tests

- `RECORDED`
- `VERIFIED`
- `STALE`
- `INVALIDATED`

### Dépendances

- `CLEAN`
- `VULNERABLE`
- `REMEDIATED`
- `ACCEPTED_RISK`
- `UNKNOWN`

### Dette

- `IDENTIFIED`
- `ACCEPTED`
- `FIXED`
- `VERIFIED`
- `WAIVED`

### Évidence

- `COLLECTED`
- `TRUSTED`
- `DISPUTED`
- `RETRACTED`

### Rapport agent

- `PROVISIONAL`
- `REVIEWED`
- `VALIDATED`
- `REJECTED`
- `ABANDONED`

## 5. Règles de relation

Relations minimales :

- `parent` : relationship de dépendance structurelle
- `relates_to` : relation faible
- `depends_on`
- `verified_by`
- `conflicts_with`
- `supersedes`
- `superseded_by`
- `inferred_from`

Les relations must être candidates to review. They do not replace the source.

## 6. Format recommandé

Chaque fichier Markdown de la mémoire devrait préciser dans l'en-tête :

- `id`
- `type`
- `status`
- `created_at`
- `updated_at`
- `source_of_fact`
- `provenance_level`
- `parents`
- `related_components`
- `evidence_refs`
- `confidence`
- `notes`

Les champs inutiles ommited. Les anciennes entrées peuvent être migrées graduellement.

## 7. Évolution future

La migration du modèle est progressive. Aucune ancienne archive ne doit être rewrite juste pour correspondre au nouveau schéma. Les nouveaux items sont les premiers à suivre ce modèle, puis les anciennes entrées peuvent recevoir des index secondaires.

Les ADR officiels du projet, s'il est jugé utile, peuvent être créés sous `docs/adr/` avec une référence au modèle de cette mémoire.

## Validation

Cette architecture a été posée comme proposition. Elle n'a pas été appliquée en masse et n'a pas modifié le code ETHAN.

Document complémentaire :
`Obsidian/Operational-Memory/MEMORY_GOVERNANCE.md` et
`Obsidian/Knowledge/Architecture/MEMORY_DATA_MODEL.md`
sont liés à ce fichier.
