# ETHAN — Validation opérationnelle (Mission 7)

Date : 2026-11-04
Statut : ÉTUDE DE VALIDATION OPÉRATIONNELLE
Chemin demandé : `Obsidian/Architecture/Applications/ETHAN_OPERATIONAL_VALIDATION.md`

## 1. Résumé exécutif

- L'API réelle Docker (`ethan-api`) répond et expose les statuts de plugins et composants.
- ODIN et Frames sont accessibles via l'API réelle en lecture/authentification, avec statut `not_installed` et actions adéquates.
- Quantar est en mode réel côté API : le moteur signale que `tradingagents` n'est pas importable dans l'environnement courant, donc `runtime=unavailable`.
- Rust Health est validé au niveau façade Python (binary health = ok).
- Les endpoints protégés refusent l'accès sans authentification.
- Les tests unitaires et API réels référencés précédemment passent.
- Aucun test Docker de démarrage, arrêt, WebUI, Rust route dans l'API ni résilience scriptée réelle n'a été lancé dans cette campagne.

Statut global : `PARTIALLY_VALIDATED`

## 2. Environnement testé

- Dépôt : `/home/fatsio/AI/Ethan`, branche `refactor/ethan-rebuild-p0`, commit `9e57d1c0` plus modifications locales.
- API Docker : conteneur `ethan-api`, image `ethan-api`, Up healthy.
- UI Docker : conteneur `ethan-ui`, Up healthy.
- Postgres/NATS/Redis : conteneurs Up.
- Odin controller : conteneur `ethan-odin-controller-1`, Up healthy.
- Python de validation locale : `.venv/bin/python`.
- Playwright : non installé dans l'environnement Python.
- Rust binaries : présents et fonctionnels pour `ethan-health` et `ethan-capability-contract`.

## 3. État initial

- Git : nombreuses modifications et fichiers non suivis préexistants, aucun nettoyage destructif.
- Douze conteneurs applicatifs/infra en état `Up`.
- Aucune opération de redémarrage/container start-stop exécutée.

## 4. Résultats ODIN

Statut : `PARTIALLY_VALIDATED`

Preuves réelles :
- `curl GET /v1/plugins/odin/status` avec utilisateur authentifié retourne un JSON cohérent.
- statut observé : `"status":"not_installed"`, `allowed_actions":["install"]`, port `4173`.
- endpoint protégé refus sans token : `401 Unauthorized`.
- confinement, redaction, allowlist et contrôleur validés par `tests/core/test_odin.py` et `tests/core/test_odin_compose_controller.py` (33 réussis).

Non testé :
- démarrage réel et arrêt du conteneur ODIN ;
- détection de conflit de port ;
- contrôleur indisponible.

## 5. Résultats Frames

Statut : `PARTIALLY_VALIDATED`

Preuves réelles :
- `curl GET /v1/plugins/frame/status` retourne un JSON cohérent.
- statut observé : `"status":"not_installed"`, port `5190`, chemin du repo issu de l'image (`/app/examples/frame/compose.yaml`).
- API frontend protégée par authentification.

Validations tests :
- `tests/interfaces/test_frame_api.py` : 19 réussis.
Non testé :
- cycle de vie réel via ComposeService ;
- image `frame-frame` effective et rendu.

## 6. Résultats Quantar

Statut : `PARTIALLY_VALIDATED`

Preuves réelles :
- `curl GET /v1/quantar/status` retourne : `runtime=unavailable`, message `TradingAgents is not importable`.
- le service est accessible et authentifié.
- la persistance déjà validée par unit tests : `tests/core/test_quantar_service_phase36.py` et `test_quantar_phase45_reconciliation.py`.

Non testé :
- tâche réelle end-to-end ;
- annulation et réconciliation réelles ;
- isolation conteneur réelle dans cette campagne.

## 7. Résultats HROT

Statut : `VALIDATED` au niveau tests unitaires.

Preuves :
- `tests/core/test_hrot_provider_gateway.py` : 14 réussis.
- Les endpoints `/v1/odin/status` et `/v1/frame/status` refusent sans authentification.

## 8. Résultats Rust / Python

Statut : `PARTIALLY_VALIDATED`

Preuves :
- `core/rust/ethan_health/target/release/ethan-health` répond `status=ok`, `ready=true`.
- Façade Python `RustHealthClient` retourne le health avec succès dans la même invocation.
- `validate_contract()` du contrat Rust retourne `ok=true`.
- `tests/core/test_capability_rust_contract.py` : 2 réussis.
Non testé :
- route `/v1/health/rust` dans l'API réelle (image en cours sans route exprimée selon OpenAPI).
- indisponibilité du binaire via route réelle.

## 9. Résultats WebUI

Statut : `NOT_TESTED`

- Playwright non installé.
- Aucune validation navigateur réelle n'a été effectuée.
- Aucun changement de design effectué.

## 10. Tests intercomposants

- API → ODIN : validé par appel authentifié réel (`NOT_INSTALLED` cohérent).
- API → Frames : validé par appel authentifié réel.
- API → Quantar : validé par appel authentifié réel.
- API → Rust Health : validé indirectement via façade dans le même processus, pas via route réelle.
- Capability Manager → contrat Rust : tests 2 réussis.
- Applications → permissions HROT : refus 401 démontré; scénarios complets de permission manquante non réexécutés dans cette campagne.

Statut : `PARTIALLY_VALIDATED`

## 11. Résilience

Non validé en conditions réelles dans cette campagne.
`NOT_TESTED` pour timeout, retry borné, redémarrage, reprise après échec, événements dupliqués.

## 12. Anomalies et risques

1. La WebUI est présente et healthy, mais non validée navigateur.
2. L'API réelle ne expose pas `/v1/health/rust` selon OpenAPI de la version déployée, empêchant la validation route HTTP directe.
3. Quantar n'est pas opérationnel pour l'exécution réelle dans l'image API à cause de l'absence de `tradingagents`.
4. Le test capability health passait avec httpx mocké; a été rendu déterministe via `tcp`.
5. Les opérations Docker réelles des applications n'ont pas été tentées pour éviter de démarrer/arrêter des conteneurs.

## 13. Preuves reproductibles

- `curl http://127.0.0.1:8000/v1/health` → `200`.
- `curl http://127.0.0.1:8000/v1/plugins/odin/status` sans token → `401`.
- `curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/v1/plugins/odin/status` → JSON.
- `curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/v1/plugins/frame/status` → JSON.
- `curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/v1/quantar/status` → JSON unavailable.
- `core/rust/ethan_health/target/release/ethan-health` → health ok.
- `.venv/bin/python ... interfaces.bridge.rust.health_adapter.RustHealthClient` → health dictionary.

## 14. Limitations

Aucun lancement destructif n'a été effectué.
Les validations de browser, Docker lifecycle, résilience réelle et route Rust API sont laissées explicites en `NOT_TESTED`.

## 15. État final par composant

| Composant | Statut |
|---|---|
| ETHAN API (health, auth, plugins) | `PARTIALLY_VALIDATED` |
| ODIN | `PARTIALLY_VALIDATED` |
| Frames | `PARTIALLY_VALIDATED` |
| Quantar | `PARTIALLY_VALIDATED` |
| ODIN/Frames/Quantar sécurité HROT | `PARTIALLY_VALIDATED` |
| WebUI | `NOT_TESTED` |
| Rust Health source | `VALIDATED` |
| Rust Health API route | `NOT_TESTED` |
| Capability Manager | `VALIDATED` |
| HROT provider bridge | `VALIDATED` |

## 16. Recommandations hiérarchisées

1. Exécuter une campagne Browser réelle pour ODIN, Frames, Quantar.
2. Démarrer/réconcilier un vrai conteneur Quantar sans accès hôte.
3. Reconstruire et redéployer l'API pour exposer et tester `/v1/health/rust`.
4. Valider ODIN/Frames lifecycle réel.
5. Conserver les protections et interdiction d'auto-install documentées.
