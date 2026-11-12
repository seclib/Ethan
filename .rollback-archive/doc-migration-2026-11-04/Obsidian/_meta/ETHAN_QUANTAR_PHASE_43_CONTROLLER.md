# ETHAN_QUANTAR_PHASE_43_CONTROLLER

Date : 2026-11-03
Statut : non implémenté, contrôleur dédié volontairement non créé

## Décision

Quantar ne reçoit pas de contrôleur Docker dédié à la manière d'Odin.

Justification :
- un contrôleur dédié avec socket Docker augmenterait la surface d'attaque ;
- Quantar est une application indépendante en lecture seule par défaut ;
- son orchestration peut être préparée côté backend via la classe `QuantarService` et le registre d'applications ;
- les opérations Docker réelles peuvent être proposées via un service d'exécution contrôlé uniquement si la stratégie d'isolation est validée.

## État réel

- `core/applications/quantar_service.py` existe.
- `/v1/quantar/*` sont enregistrés.
- Image Docker construite.
- Aucun conteneur n'a été démarré par ETHAN.

## Limites

- aucune opération de démarrage réelle ;
- HROT reste fail-closed ;
- aucune démonstration navigateur réelle ;
- aucune preuve de socket isolé expérimentale.
