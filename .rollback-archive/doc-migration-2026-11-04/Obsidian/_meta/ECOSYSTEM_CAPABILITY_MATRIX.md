# ECOSYSTEM_CAPABILITY_MATRIX.md

Date : 2026-11-03

| Capacité | Statut | Preuve | Note |
|---|---|---|---|
| Engineering Memory Service | IMPLEMENTED_VERIFIED | tests directs + gitleaks | service core testé |
| Adaptateurs Knowledge/Skills | IMPLEMENTED_TESTED | tests unitaires | collecte non invasif |
| Adaptateurs agents | IMPLEMENTED_PARTIAL | tests unitaires | dépend de l'injection de l'intégration |
| Permissions/RBAC service | IMPLEMENTED_PARTIAL | tests FastAPI dependency | pas de validation bout-en-bout auth applicative |
| WebUI Engineering Memory | IMPLEMENTED_TESTED | unit le UI + build | smoke visuel limité |
| Contract application indépendante | DESIGNED_NOT_IMPLEMENTED | documents Phase 1.1 | pas d'API générique |
| Intelligence partagée | DESIGNED_NOT_IMPLEMENTED | document | appication et ETHAN doivent architecturer |
| Odin | IMPLEMENTED_PARTIAL | code existant et service | integration réelle à vérifier |
| Frame | IMPLEMENTED_PARTIAL | code exists | integration réelle à vérifier |
| TradingAgents | PLANNED_ONLY | audit only | moteur intact |
| Atreus | FUTURE_PLANNED | docs only | non implémenté |
| Mémoire Obsidian | DESIGNED_NOT_IMPLEMENTED | docs and manifests | service documentaire, pas source de cache |
| Skills catalogue | DESIGNED_NOT_IMPLEMENTED | adapter | pas de catalogue automatique |
