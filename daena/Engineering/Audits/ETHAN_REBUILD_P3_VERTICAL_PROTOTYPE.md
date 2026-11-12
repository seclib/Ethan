# ETHAN — Rapport P3 prototype vertical Core hybride

## Composants livrés

- Service Rust santé/diagnostic : `core/rust/ethan_health/`
  - `Cargo.toml`
  - `src/main.rs`
  - binaire release : `core/rust/ethan_health/target/release/ethan-health`
- Adaptateur Python isolé : `interfaces/bridge/rust/health_adapter.py`
- Tests : `tests/test_rust_health_adapter.py`

## Contrats exposés

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /v1/diagnostics/version`
- `GET /v1/diagnostics/timeout` (réponse déterministe, délai simulé 50ms)

Format JSON d'erreur : `{code, message, details, request_id, retryable}`.
Version de contrat : `ethan.p3.health.v1`.

## Configuration

Variables :
- `ETHAN_HEALTH_BIND` (défaut 127.0.0.1)
- `ETHAN_HEALTH_PORT` (défaut 18081)
- `ETHAN_HEALTH_LOG_LEVEL` (défaut info)
- `ETHAN_HEALTH_SERVICE_NAME` (défaut ethan-health)

Flags CLI equivalents `--bind`, `--port`, `--log-level`, `--service-name`.

Démarrage reproductible :
```sh
cargo build --release --offline
ETHAN_HEALTH_BIND=127.0.0.1 ETHAN_HEALTH_PORT=18081 target/release/ethan-health
```

## Tests exécutés

- Rust : `cargo test --offline` → **6 tests passants**
  - validation port nul
  - validation bind vide
  - route `/health`
  - route `/health/ready`
  - route `/v1/diagnostics/version`
  - route inconnue (404 contrat)
- Python : `.venv/bin/pytest tests/test_rust_health_adapter.py tests/test_python_imports.py -q` → **9 tests passants**
- Build release : `cargo build --release --offline` → succès.
- Tentative d'exécution : le binaire s'initialise et échoue ensuite au `bind` à cause du sandbox (`Operation not permitted`), donc pas de preuve réseau HTTP locale dans cet environnement.

## Limites / mesures

- Pas de mesure comparable de performance réclamée.
- Le service Rust actuel est un prototype de santé/diagnostic non destructif, pas un remplacement d'event store.
- Pas de migration de données.
- Pas de socket Docker exposé.
- Pas de privilèges implicites pour agents/plugins.
- Intégration WebUI(candidate) non exécutée en raison du sandbox réseau; le contrat documenté est testé par l'adaptateur Python.

## Décisions en attente

- Valider le port de production du service Rust (ne pas réutiliser 8080/kernel sans décision).
- Définir adapter officiel WebUI -> service.
- Valider licence Open WebUI avant intégration UI.

## Preuve live obtenue après ouverture du sandbox réseau

- Service démarré sur `127.0.0.1:18083` (processus éphémère, arrêté en fin de commande).
- `RustHealthClient.get_health()` a renvoyé `status=ok`, `ready=true`.
- `RustHealthClient.get_diagnostics_version()` a renvoyé `contract=ethan.p3.health.v1`, `mode=isolated-prototype`.
- Logs capturés : connexion entrante peer 127.0.0.1, accept et réponse.

## Mesure de référence (50 requêtes `/health`, une machine isolée)

- min = 0.18 ms
- p50 = 0.20 ms
- p95 = 0.26 ms
- max = 2.01 ms
- payload = 124 bytes
- conditions : Rust release, loopback, un seul client, sans TLS, sans charge concurrente.

## Authentification / permissions pour cette tranche

Le service P3 n'expose que des endpoints de santé et de diagnostic non destructifs.
Aucun secret, action destructive ou privilège système n'est exposé.
L'adaptateur Python ne transporte et ne normalise que HTTP/JSON.
