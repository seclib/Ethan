# ETHAN_APPLICATION_INTEGRATION_COMPARISON

Date : 2026-11-03
Statut : audit comparatif en lecture seule

## Maturité réelle

| Critère | Odin | Frames | Quantar |
|---|---|---|---|
| Contrôleur dédié | Oui (`ethan-odin-controller-1`) | Non (service Compose dans ETHAN) | Non (statut/configuration uniquement) |
| Service backend | `core/plugins/odin.py` | `core/plugins/frame.py` | `core/applications/quantar_service.py` |
| Runtime indépendant | Oui | Oui | Oui, non activé |
| Docker Compose | Oui | Oui | Oui, image dédiée existante |
| Démarrage par ETHAN | Oui | Oui | Non démontré |
| Arrêt par ETHAN | Oui | Oui | Non |
| Authentification | Session + RBAC + controller token | Session + RBAC | Session + RBAC |
| HROT | Fail-closed | Fail-closed | Fail-closed |
| Surveillance santé | Oui | Oui | Limitée |
| WebUI | Page Odin | Page Frame | Page `/quantar` statique actuellement |
| Souveraineté Docker | Contrôleur isolé | ComposeService in-process | Compose en-dehors du runtime démontré |

## Décision

Adapter le modèle le plus simple à chaque application.

- Odin est mature avec contrôleur isolé.
- Frames prouve qu'un service Compose géré depuis le processus ETHAN est suffisant pour un runtime HTTP.
- Quantar n'a pas de port HTTP réel et ne possède donc pas encore une santé applicative exploitable.

Il est justifié pour Quantar de créer un contrôleur dédié selon le modèle d'Odin, plutôt que de forcer un service Compose sans endpoint de santé.

## Limites

- Aucune application n'a été démarrée réellement dans cette étude.
- Aucune extension de privilège HROT.
