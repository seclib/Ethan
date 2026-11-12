# INDEX — Mémoire technique ETHAN

## 1. État opérationnel immédiat

- [PROJECT_STATE.md](Operational-Memory/PROJECT_STATE.md)
- [DECISIONS.md](Operational-Memory/DECISIONS.md)
- [TASKS.md](Operational-Memory/TASKS.md)
- [BLOCKERS.md](Operational-Memory/BLOCKERS.md)

## 1bis. Audit de documentation (Phase B — 2026-11-04)

- [Inventaire documentaire](Operational-Memory/DOCUMENTATION_INVENTORY.md)

- [Rapport d’audit et plan proposé](Operational-Memory/DOCUMENTATION_AUDIT_REPORT_2026-11-04.md)

Statut : PROPOSED — en attente d’approbation avant migration. Ce document n’altère aucune source.

## 2. Couverture technique et statut de synchronisation

Selon l'audit conservé dans `_meta/odsidian-metadata/COVERAGE-REPORT.md` et `AUDIT-ARCHIVES.md` :

| Période | État |
|---|---|
| 2026-04 | 1 session Copilot |
| 2026-05 | 1 session Copilot |
| 2026-06 | 25 sessions Cline |
| 2026-07 | 18 sessions Cline |
| 2026-08 | 40 sessions Cline |
| 2026-09 | aucune source disponible, lacune confirmée |
| 2026-10 | 2 sessions Codex |

Les archives volumineuses sont découpées en parties et indexées dans `_meta/odsidian-metadata/PARTS-INDEX.md`.

Totale source B : 104 fichiers, dont 94 sous `01-Archives/`. Source A externe : 90 fichiers. L'ensemble combiné traité dans cette migration correspond à 194 fichiers.

## 3. Archives

- [Conversations Cline](Archives/Conversations/cline/)
- [Conversations Codex](Archives/Conversations/codex/)
- [Conversations Copilot](Archives/Conversations/copilot/)
- [Archive unifiée Cline préservée de Source A](Archives/Conversations/from-ethan-knowledge/cline/2026-08-13/1786588790163.md)
- Fragments Cline correspondants : `Archives/Conversations/cline/2026-08-13/1786588790163-part-01.md` à `part-05.md`
- [Rapports et audits d'archives](Archives/Rapports-Agents/)

Source B fournit la hiérarchie principale. Source A n'a apporté qu'une archive unifiée et ses métadonnées divergentes.

## 4. Connaissances

- [Synthèses par agent](Knowledge/Syntheses/by-agent/)
- [Index importé de Source A](Knowledge/INDEX_ETHAN_KNOWLEDGE.md)
- [Architecture](Knowledge/Architecture/)
- [Composants](Knowledge/Composants/)
- [Sécurité](Knowledge/Sécurité/)
- [Procédures](Knowledge/Procedures/)
- [Incidents](Knowledge/Incidents/)
- [Tests et preuves](Knowledge/Tests-et-Preuves/)
- [Décisions](Knowledge/Decisions/)

Versions historiques préservées :

- `Knowledge/Syntheses/by-agent/cline-summary-ethan-knowledge-2026-10-28T11-29.md`
- `Knowledge/Syntheses/by-agent/codex-summary-ethan-knowledge-2026-10-28T11-29.md`
- `Knowledge/Syntheses/by-agent/copilot-summary-ethan-knowledge-2026-10-28T11-29.md`
- `Knowledge/INDEX_ETHAN_KNOWLEDGE.md`
- `_meta/INDEX_ODSIDIAN_SOURCE.md`

Les versions horodatées sont les plus anciennes. Les versions canoniques sont celles de Source B après synchronisation du 2026-10-28T12:12:30.

## 5. Métadonnées et migration

- [SOURCE_INVENTORY.md](_meta/SOURCE_INVENTORY.md)
- [MIGRATION_REPORT.md](_meta/MIGRATION_REPORT.md)
- [Conventions Source B](_meta/odsidian-metadata/conventions.md)
- [Rapport de couverture Source B](_meta/odsidian-metadata/COVERAGE-REPORT.md)
- [Index des parties Source B](_meta/odsidian-metadata/PARTS-INDEX.md)
- [Audit des archives Source B](_meta/AUDIT-ARCHIVES_ODSIDIAN.md) — absent si non copié; vérifier si présent

## 6. Sources et mémoire opérationnelle

- [Sources docs/memory](Operational-Memory/sources/docs-memory/)
- [Métadonnées importées de Source A](Operational-Memory/sources/ethan-knowledge-meta/)
- [Inventaire général des ressources ETHAN](/tmp/ETHAN_RESOURCES_INVENTORY.md)
- [Plan Phase 2 Public/Private](/tmp/ETHAN_PHASE2_SEPARATION_PLAN.md)
- [Plan de fusion Obsidian](/tmp/ETHAN_OBSIDIAN_MERGE_PLAN.md)

Les chemins `/tmp` sont des artefacts temporaires et ne doivent pas être considérés comme faisant partie du dépôt.

## 7. Éléments à traiter manuellement

- réconcilier les comptes contradictoires des index Source A et Source B ;
- confirmer l'équivalence ou la différence entre l'archive unifiée Cline et ses cinq parties ;
- choisir la stratégie de publication publique de la cible Obsidian ;
- valider l'accessibilité GitHub et les références distantes ;
- mettre à jour les références existantes à `Odsidian` lorsque l'orthographe définitive de la mémoire est confirmée.

## 8. Mémoire technique ETHAN (Phase 1)

- [Architecture de la mémoire technique](Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md)
- [Modèle de données de la mémoire technique](Knowledge/Architecture/MEMORY_DATA_MODEL.md)
- [Gouvernance de la mémoire technique](Operational-Memory/MEMORY_GOVERNANCE.md)

## 9. Registre et protocole agent

- [Registre central de routage](Metadata/REGISTRY.md)
- [Protocole AGENTS](AGENTS.md)
- [Gabarits d'enregistrement](Knowledge/Architecture/RECORD_TEMPLATES.md)

## 8b. Mémoire technique ETHAN (Phase CTO)

- [ADR-EM-001 — Architecture Engineering Memory](Knowledge/Architecture/ADR-EM-001-engineering-memory-architecture.md)
- [ESR-EM-001 — Exigences système](Knowledge/Architecture/ESR-EM-001-engineering-memory.md)
- [ASR-EM-001 — Exigences sécurité](Knowledge/Architecture/ASR-EM-001-engineering-memory-security.md)
- [Service Architecture (composants, flux, matrices, risques)](Knowledge/Architecture/EM-SERVICE-ARCHITECTURE.md)

## 10. Sécurité de la mémoire

- [ASR-EM-001 — Exigences sécurité](Knowledge/Architecture/ASR-EM-001-engineering-memory-security.md)
- [Modèle de permissions](Knowledge/Sécurité/PERMISSION_MODEL.md)
