# PHASE_19_1_NATS_BACKEND_RECOVERY

Date : 2026-11-03
Statut : diagnostic réalisé, correction non appliquée

## Cause racine identifiée

Le backend démarre initialement avec `NATS_URL=nats://localhost:4222` par défaut, mais `NATS_TOKEN` n'est pas propagé à son environnement local.

Dans le déploiement Docker, `NATS_URL=nats://nats:4222` et `NATS_TOKEN` est injecté depuis `.env`. La configuration NATS utilise `authorization { token: $NATS_TOKEN }`.

L'instance locale de `nats-server` fonctionne sur 127.0.0.1:4222, mais l'authentification partagée ne peut pas être vérifiée sans accès au processus racine qui détient la configuration active. Aucune modification n'a été appliquée pour éviter de contourner l'authentification.

## Preuves

- Tentative de démarrage backend : `NATS Authorization Violation`.
- Configuration NATS versionnée : `infrastructure/nats/nats-server.conf` utilise `authorization { token: $NATS_TOKEN }`.
- `.env` contient `NATS_URL=nats://nats:4222` et un token non vide.
- La résolution DNS du nom `nats` échoue hors du réseau Docker.
- `nats-server` écoute sur `127.0.0.1:8222` en monitoring et accepte des connexions.

## Correction nécessaire

Corriger l'environnement local en fournissant le même `NATS_TOKEN` à uvicorn que celui avec lequel `nats-server` a été démarré, ou utiliser le réseau Docker prévu. Sans accès à la valeur effective du processus `nats-server`, aucune correction sûre ne peut être appliquée.

## Validation

Aucune connexion backend réussie n'a été démontrée. La phase n'est pas déclarée réussie.

## Risques restants

- Informations d'authentification non accessibles depuis le processus courant.
- Modification de l'environnement potentiellement invasive si effectuée sans validation.
