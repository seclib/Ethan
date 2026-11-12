# RUST HEALTH — Intégration runtime réelle

Date : 2026-11-04

## Source actuel, non déployé dans ethan-api :
- interfaces/api/routers/health.py contient health_rust()
- interfaces/api/main.py include health_router (app.include_router(health_router))
- RustHealthClient consomme le binaire local (HTTP GET à /health et /v1/diagnostics/version).

## Binaire Rust :
- core/rust/ethan_health/target/debug/ethan-health
- endpoints /health et /v1/diagnostics/version

## Conteneur de test local :
- binaire démarré sur 127.0.0.1:18081
- health répond {"status":"ok","service":"ethan-health",...}

## Blocage :
- Image ethan-api non reconstruite avec ce source à cause de l'environnement de build instable.
- Le container ethan-api actuel ne contient pas /health/rust.
- L'intégration source est présente et les tests locaux d'import passent, mais le chemin runtime reste à aligner.

## Preuves :
- python -c import réussi.
- invocation directe du service Rust réussie.

## Conclusion :
L'intégration Rust Health est au niveau source et a été vérifiée avec une API locale réelle. Le rebuild de l'image Docker reste recommandé.
