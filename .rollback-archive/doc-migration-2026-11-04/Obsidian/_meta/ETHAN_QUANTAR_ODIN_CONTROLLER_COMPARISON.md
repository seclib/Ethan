# ETHAN_QUANTAR_ODIN_CONTROLLER_COMPARISON

Date : 2026-11-03
Statut : audit statique, aucune modification

## Odin

- Contrôleur dédié : `scripts/odin_compose_controller.py`.
- Processus isolé (`ethan-odin-controller-1`).
- Il possède le Docker socket uniquement pour ce conteneur.
- Il expose uniquement les opérations allowlistées via `/health` et `/run`.
- Il authentifie par token Bearer.
- Il redirige les commandes Docker Compose vers un projet fixe `odin`.
- L'API Odin ETHAN appelle ce contrôleur au lieu d'invoquer Docker directement.

## Quantar

- Aucun contrôleur dédié.
- Le service `QuantarService` n'a pas été implémenté comme contrôleur.
- Le routeur `/v1/quantar` gère uniquement le statut et la configuration.
- Le runtime Docker Quantar n'a jamais été démontré opérationnel.

## Comparaison

| Critère | Odin | Quantar |
|---|---|---|
| Contrôleur dédié | Oui | Non |
| Lifecycle | oui, via controller | non |
| Supervision | oui | non |
| Authentification | Bearer token controller | session ETHAN pour API |
| HROT | reste fail-closed | fail-closed déclaré |
| Gestion Docker | allowlist stricte | Docker Compose local possible, non intégré |
| Logs | anonymisés | non démontrés |
| WebUI | page existante | page existe mais runtime non démontré |

## Recommandation

Pour une application isolée réellement, soit :
1. étendre le modèle de composant Docker via un service ETHAN existant ;
2. créer un contrôleur dédié pour Quantar, avec la même frontière d'isolation qu'Odin.

Le deuxième choix est le plus sûr. Il évite de donner à ETHAN ou à Quantar un accès direct au socket Docker en dehors du contrôleur.

## Limites

- Aucun secret affiché.
- Aucune opération destructive exécutée.
