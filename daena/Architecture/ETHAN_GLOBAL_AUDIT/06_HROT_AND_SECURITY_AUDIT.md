# 06 — HROT and Security

## Observé

- Auth backend utilise `require_permission(...)`, ex: `Permission.PLUGINS`, `Permission.EXECUTE`.
- HROT durable store PostgreSQL/JSONL existe.
- `ProviderGateway` est in-process; pas de transport worker.
- `SecretProvider` conserve secrets en mémoire et les masque.
- Permissions Docker : Quantar conteneur read-only, cap drop all, network none.

## HROT actuel

- Contrôles par permission sont réels.
- `gateway_guard(ActionType.PLUGIN_INSTALL)` observable.
- Provider Gateway approvals HROT ne sont pas branchés dans Quantar runtime.
- Différence entre disponibilité et autorisation existe et doit rester.

## Risques

- Ne pas masquer une indisponibilité derrière un bool `available`.
- Ne pas exposer les secrets.
- Tout conteneur worker qui demande LLM doit soit utiliser endpoint sans secret, soit passer par un gateway authentifié futur.```mermaid
flowchart LR
  WebUI --> Auth[require_permission]
  Auth --> API[router]
  API --> HROT[Durable HROT]
  API --> Secret[SecretProvider]
  Secret --> Gateway[ProviderGateway]
  Gateway --> Provider[LLM Provider]
```
