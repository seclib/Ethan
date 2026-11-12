# Conventions de nommage

## Format des fichiers

`YYYY-MM-DD_agent_projet_sujet.md`

- `YYYY-MM-DD` : date de création (ISO 8601)
- `agent` : cline, codex, copilot, chatgpt, manual
- `projet` : nom du projet (ethan, odin, etc.)
- `sujet` : description courte en kebab-case

## Métadonnées standardisées (frontmatter YAML)

```yaml
---
id: "unique-id"
agent: "cline"
agent_version: "4.1.26"
date: "2026-10-28"
project: "ethan"
component: "docker"
type: "conversation"  # conversation, report, plan, decision, procedure, test, incident
status: "completed"   # completed, interrupted, error, compacted
verified: true        # true si vérifié par un test ou une exécution
source: "raw/cline/tasks/12345/"
---
```

## Types de documents

| Type | Description |
|------|-------------|
| conversation | Conversation complète avec un agent IA |
| report | Rapport technique ou d'audit |
| plan | Plan de travail ou d'implémentation |
| decision | Décision d'architecture |
| procedure | Procédure d'installation/configuration |
| test | Résultats de tests |
| incident | Erreur rencontrée et correction |
| synthesis | Synthèse technique (référence des archives) |

## Statuts de vérification

| Statut | Description |
|--------|-------------|
| completed | Session terminée normalement |
| interrupted | Session interrompue (pas de réponse finale) |
| error | Session avec erreur |
| compacted | Session compressée (Copilot) |
| skipped | Session vide ou non pertinente |
| verified | Résultat vérifié par test/exécution |
| unverified | Non vérifié |
