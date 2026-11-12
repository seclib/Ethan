# ETHAN_UNIFIED_CONTROLLER_STUDY

Date : 2026-11-03
Statut : étude préparatoire, aucune migration effectuée

## Constat

Odin possède un contrôleur Docker isolé à allowlist stricte pour un seul projet Compose.

Quantar n'a pas de contrôleur dédié. Frames dépend de ComposeService générique mais doit être piloté depuis ETHAN selon les mêmes règles.

## Architecture actuelle

- `ethan-odin-controller-1` : contrôleur narrow pour Odin uniquement.
- API ETHAN : passerelle autorisée utilisant le contrôleur.
- Applications Tools : accès indirect au contrôleur, jamais au socket Docker.

## Proposition

Plutôt que migrer immédiatement vers `ethan-controller`, conserver un contrôleur dédié par application et une abstraction commune dans le backend :

- `ApplicationLifecycleService` (contrôleur logique backend) ;
- `ComposeControllerClient` (adaptateur par application) ;
- allowlist stricte par application ;
- policy d'identité et de projet.

Un contrôleur HTTP unifié multi-projets augmenterait la surface d'attaque et devrait supporter des justifications d'autorisation complexes.

## Sécurité

- Aucune application ne reçoit le Docker socket.
- HROT reste l'autorité.
- ACL minimales.
- Secrets jamais exposés.

## Recommandation

Maintenir les contrôleurs dédiés et normaliser leur contrat. Créer un service backend unifié au-dessus d'eux avant une éventuelle fusion physique.

## Limites

- Aucun code migré.
- Aucun test de migration exécuté.
