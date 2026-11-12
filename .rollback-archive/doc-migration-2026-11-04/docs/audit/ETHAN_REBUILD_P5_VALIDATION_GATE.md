# ETHAN — Rapport de validation P5 (gate avant intégration)

- Date : 2026-10-29
- Environnement : sandbox unrestricted; Ollama non réinitialisé; aucune migration de données.

## Résultats synthétiques

| Vérification | Attendu | Commande/scénario | Observé | Statut | Preuve | Risque résiduel |
|---|---|---|---|---|---|---|
| Import Python | importlinter conservé | `.venv/bin/lint-imports` | 5 contrats kept, 0 broken | réussi | rapport commande | low |
| Tests Python P3 | 9 passants | `.venv/bin/pytest tests/test_rust_health_adapter.py tests/test_python_imports.py -q` | 9 passed | réussi | pytest output | low |
| Ruff ciblé | 0 erreur | `.venv/bin/ruff check interfaces/bridge/rust/health_adapter.py tests/test_rust_health_adapter.py` | All checks passed | réussi | commande | low |
| Cargo tests | 6 passants | `cargo test --offline` | 6 passed | réussi | cargo output | low |
| Build Rust release | succès | `cargo build --release --offline` | succès (warning corrigé) | réussi | cargo output | low |
| Service Rust live | réponse HTTP 200 | démarrage éphémère + curl `/health`, `/health/ready`, `/v1/diagnostics/version` | 200 JSON | réussi | logs + body | faible pour santé seulement |
| Adaptateur live | succès | `RustHealthClient.get_health()` et diag | les deux réussis | réussi | commande sortie | low |
| Précision latency | mesure reproductible | 50 requêtes loopback | p50 0.20ms, p95 0.26ms | réussi | documenté | non comparable production |
| Typecheck Next.js | propre | `npm run typecheck` | 0 erreur après correction structurelle de `plugins/page.tsx` | réussi | sortie commande | low |
| Typecheck candidat Open WebUI | sans erreur | `npm run check` dans `rebuild/webui-candidate` | 9381 errors / 265 warnings (Node 24) | échoué/bloqué | sortie commande | bloquant pour WIT TypeScript formel, mais build production réussit |
| Build frontend candidat | build statique réussi | `./node_modules/.bin/vite build` | `✓ built in 1m 21s`, `build/index.html` | réussi | build/index.html | moyen (network-dependent pyodide bypass) |
| Secret scan | aucun secret ajouté | grep patterns sur fichiers livrés | matches redaction patterns code/doc seulement | réussi | scan | low |
| Ollama/data preservation | aucune réinitialisation | pas de commande destructrice exécutée | aucun volume/model réinstallé | réussi | commandes executes | low |
| Import-linter | contrats conservés | `.venv/bin/lint-imports` | 5 kept, 0 broken | réussi | commande | low |

## Échecs bloquants

1. Open WebUI candidate : `npm run check` massif (probable mismatch Node/version de développement).
2. Open WebUI candidate : dépendances réseau pour pyodide/embeddings non disponibles hors ligne.
3. Les tests Python API ont été récupérés après réparation de `typing_extensions` 4.16.0.

## Vérifications impossible/non exécutées

- Navigation réelle dans le navigateur des parcours Auth/API : impossible ici dans un sens interactif; aucune capture fabriquée.
- `TestClient`/parcours complet API FastAPI : dépend de la base et du provider; non prouvé dans ce gate.
- Backup/restore PostgreSQL réel sur volumes : non exécuté (pas d'accès Docker, pas de données prod).
- WebUI -> Rust end-to-end dans navigateur : non exécuté.
- Security tests MCP/skills/agents : audit statique seulement; pas de test automatisé new.

## Risques résiduels

- La dette TS Next.js `plugins/page.tsx` est levée; les tests API repassent après réparation `typing_extensions`.
- Aucune capacité métier migrée (P4 reste proposition Prompts seulement).
- Le prototype Rust n'est qu'un endpoint santé/diagnostic.
- Le candidat WebUI n'est pas prêt pour intégration stricte.
- Port santé 18081 et binding loopback : à valider en déploiement.

## Recommandation

**Corriger avant d'intégrer.** Suspendre toute intégration UI large jusqu'à ce que :
- le Next.js `plugins/page.tsx` soit réparé et typechecké ;
- le candidat Open WebUI soit testé sur la version Node documentée avec réseau autorisé ;
- une capacité métier P4 soit réellement implémentée, testée et documentée.

Le socle P3 peut être conservé en parallèle comme prototype validé.
