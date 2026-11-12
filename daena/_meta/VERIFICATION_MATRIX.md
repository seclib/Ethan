# VERIFICATION_MATRIX — ETHAN

Date : 2026-11-03
Statut : PROPOSAL

## Matrice initiale

| Contrôle | Statut | Preuve | Risque |
|---|---|---|---|
| Import FastAPI | VERIFIED | `interfaces.api.main` import OK | faible |
| Tests mémoire Python | VERIFIED | 17 tests core/interface réussis | faible |
| Validation SHA | VERIFIED | hashes fournis dans rapports | moyenne |
| Odsidian restauration | VERIFIED | 104 fichiers / SHA exacts | faible (source de vérité antérieure) |
| Gitleaks | VERIFIED | no leaks found | faible |
| Auto-executé sur sources historiques | PARTIALLY_IMPLEMENTED | checklists/rorrar annotation | moyenne |
| Typecheck WebUI | VERIFIED | commande npm réussie | faible |
| Build WebUI | VERIFIED | build output route `/engineering-memory` | faible |
| Typecheck global | VERIFIED for observed code | build Webui | faible |
| Integration Composition Root | PARTIALLY_IMPLEMENTED | app import and wired managers | moyenne |
| RBAC HTTP réel | TESTED (TestClient) | tests de permission 403/200 | moyenne |
| Idempotence | VERIFIED | tests passés | faible |
| Restauration intégrale | PARTIALLY_IMPLEMENTED | documentation / non live test | élevée |
| Chaînage / append-only | NOT_IMPLEMENTED | non présent | élevée |
| Publication public | NOT_IMPLEMENTED | aucune push env. | moyenne |
| Secrets scan | VERIFIED | gitleaks | faible |
| Documentation cohérence | PARTIALLY_IMPLEMENTED | lien check 0 pour docs propres | moyenne |
| Index source B | PARTIAL / FAILED | 90 liens cassés, cause connue | moyenne |

## Référence test par rubrique

- service core : 5 tests
- adaptateurs : 2 tests
- sécurité : 4 tests
- knowledge/skills : 2 tests
- agents : 2 tests
- routeurs HTTP auth : 4 tests
- UI : 1 test
- total direct : 20 tests, toutes réussies (sans avertissement majeur sauf plugin-deprecation)

## Conditions de passage

La matrice ne constitue ni une certification complète ni une garantie.
