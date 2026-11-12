# QUANTAR — Intégration HROT durable (Phase 50)

Date : 2026-11-04
Statut : implémentée avec tests contrôlés — PARTIALLY_VALIDATED

## 1. Architecture HROT trouvée

- `core/hrot/durable.py` fournit `DurableHrotStore` avec API async create/get/resolve/consume.
- `core/human_root` fournit le principe d'autorité humaine.
- `core/security/hrot_provider_gateway.py` fournit le Provider Gateway HROT in-process.

## 2. Interfaces réutilisées

- `DurableHrotStore.create`
- `DurableHrotStore.resolve`
- `DurableHrotStore.consume`
- `QuantarProviderBridge.prepare_authorization`
- `ProviderGateway.execute`

## 3. Modifications

- `core/applications/quantar_provider_bridge.py` : support `HrotDurableAuthorizationAuthority`.
- `core/security/hrot_provider_gateway.py` : nouvelle classe d'adaptation au store durable.
- `QuantarTask.execution_id` initialisé lors de la création.
- test durable simulé ajouté.

## 4. Tests

- Phase 49 bridge : 2 tests passés (un simulé? -> remplacé)
- Nouveau test durable : approuvé et refusé.
- Résultat : 2 tests passés, secret redacté.

## 5. Preuves de persistance

- L'autorisation est créée durablement dans un `DurableHrotStore` temporaire.
- L'approbation est résolue par un approver distinct.
- Le refus est effectué si l'approval n'a pas été approuvé.
- consommation consécutive possible.

## 6. Limites

- pas de canal runtime authentifié ;
- pas d'accès réel depuis le runner ;
- pas de persistance des contextes d'autorisation ;
- pas de tests multi-processus ;
- pas de réseau réel ni provider réel.

## 7. Décisions restantes

- transport local ;
- identité durable du conteneur ;
- lifecycle complet des autorisations.

Statut global : `PARTIALLY_VALIDATED`.
