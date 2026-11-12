# ADR-1013 — Cycle de vie des tâches Knowledge

- Statut : Proposed
- Contexte : Core pipeline in-process, pas de worker dédié visible.
- Décision : État métier Core (`CoreRecordStore`) ; workers/support async orchestrés par services Core.
- Alternatives : microservice de tâches — reporté.
- Risques : résilience et concurrency limitées ; pas de retry documenté.
- Tests : tests intégration async futurs.
