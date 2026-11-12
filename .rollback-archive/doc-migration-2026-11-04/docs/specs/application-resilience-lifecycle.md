# Spécification — Résilience et cycle de vie (MEM-014 Phase 6)

## Résilience

- Retries bornés avec backoff et jitter.
- Circuit breaker `CLOSED`, `OPEN`, `HALF_OPEN`.
- Classification des erreurs.
- Idempotence et protection de concurrence.
- Aucun retry aveugle sur opération non idempotente.

## Cycle de vie

États supportés :

- `registered`, `validated`, `ready`, `starting`, `running`, `degraded`, `stopping`, `stopped`, `failed`, `unknown`.

Transitions non autorisées refusées. Un état inconnu reste explicite.

## Isolation

Les pannes sont isolées par application et par instance. Aucune permission n'est déclenchée automatiquement.

## Limites

- Pas d'application réelle lancée.
- Persistance durable non incluse pour les registres in-memory.
