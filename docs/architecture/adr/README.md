# ADR — Architecture Decision Records (WebUI Platform)

Ces ADR sont des **brouillons** préparés à partir de l'évaluation `docs/architecture/webui-platform-architecture-assessment.md` (2026-09-07). Ils n'ont **pas encore été approuvés** : ils décrivent les décisions proposées et les alternatives, pour discussion avant implémentation.

| ADR | Sujet | Statut |
|---|---|---|
| ADR-3001 | Store de records unifié (ConfigStore + WebUIStore → CoreRecordStore) | Proposition |
| ADR-3002 | Providers : ProviderManager = seule source de vérité (suppression fallback statique) | Proposition |
| ADR-3003 | Domaine `Projects` (conversation container + knowledge scope + execution context) | Proposition |
| ADR-3004 | Back-end de vecteurs unique | Proposition |
| ADR-3005 | Folders (arborescence) vs Domains (étiquettes transverses) — pas de fusion | Proposition |
| ADR-3006 | Contrats API versionnés (OpenAPI + tests de contrat) | Proposition |

Règles d'implémentation rappelées (AGENTS.md) :

- Toute logique métier vit dans `core/` ; les interfaces (WebUI, CLI) consomment uniquement via l'API.
- Aucune ressource dupliquée physiquement ; les relations sont référencées.
- Aucune stratégie/option exposée sans chemin de code réel dans le Core.
