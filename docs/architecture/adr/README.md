# ADR — Architecture Decision Records (WebUI Platform)

Ces ADR constituent le **niveau 2** de la hiérarchie documentaire : le niveau 1
est `docs/architecture/ARCHITECTURE-CIBLE.md` (référence opposable). Les ADR
`3xxx` (données/domaines) et `4xxx` (capacités/plateforme) portent chacun une
ligne **« État audité »** datée, qui confronte la décision au code réel.

| ADR | Sujet | Statut doc | Audit 2026-09-24 |
|---|---|---|---|
| ADR-3001 | Store de records unifié (ConfigStore + WebUIStore → CoreRecordStore) | Proposition | ❌ Non implémenté |
| ADR-3002 | Providers : ProviderManager = seule source de vérité (suppression fallback statique) | Proposition | ✅ Implémenté |
| ADR-3003 | Domaine `Projects` (conversation container + knowledge scope + execution context) | Proposition | ✅ Implémenté |
| ADR-3004 | Back-end de vecteurs unique | Proposition | ❌ Non tranché |
| ADR-3005 | Folders (arborescence) vs Domains (étiquettes transverses) — pas de fusion | Proposition | 🟡 Partiel |
| ADR-3006 | Contrats API versionnés (OpenAPI + tests de contrat) | Proposition | 🟡 Partiel |
| ADR-4001 | Capability Manager centralisé dans le Core (cycle de vie des composants optionnels) | Implémenté | ✅ Confirmé |
| ADR-4002 | Installation à la demande — supported ≠ installed ≠ running ≠ ready | Implémenté | ✅ Confirmé |
| ADR-4003 | Cycle de vie des données — uninstall ≠ delete data (double confirmation) | Implémenté | ✅ Confirmé |
| ADR-4004 | Le Core, source de vérité de l'état des composants | Implémenté | ✅ Confirmé |

Règles d'implémentation rappelées (AGENTS.md) :

- Toute logique métier vit dans `core/` ; les interfaces (WebUI, CLI) consomment uniquement via l'API.
- Aucune ressource dupliquée physiquement ; les relations sont référencées.
- Aucune stratégie/option exposée sans chemin de code réel dans le Core.
