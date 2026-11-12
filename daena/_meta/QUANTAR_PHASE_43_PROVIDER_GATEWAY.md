# QUANTAR — Socle HROT provider gateway (Phase 43)

Date : 2026-11-04
Statut : implémenté et testé avec fournisseurs simulés — PARTIALLY_VALIDATED

## 1. Composants

- `core/security/hrot_provider_gateway.py`
  - `SecretProvider`
  - `ProviderGatewayAuthorization`
  - `ProviderGatewayRequest`
  - `ProviderGatewayResponse`
  - `ProviderGateway`
- `tests/core/test_hrot_provider_gateway.py` : 14 tests réussis.

## 2. Fonctionnalités

- Autorisation HROT avec principal, application, provider, model, capability, resource, action.
- Approbation par un approver distinct du principal.
- Expiration et révocation explicites.
- Quotas et rate limiting.
- Taille maximum des charges.
- Provider allowlist.
- Adapter boundary avec appel provider sans exposition de destination arbitraire.
- Masquage du secret dans la réponse.

## 3. Sécurité

- aucune clé transmise au conteneur dans ce code ;
- aucune destination fournisseur arbitraire ;
- les entrées sont validées ;
- les exceptions sont normalisées ;
- le secret reste côté ETHAN dans `SecretProvider`.

## 4. Compatibilité TradingAgents

Non démontrée. Un adaptateur future pourra utiliser la gateway comme point d’accès sans modifier arbitrairement les interfaces upstream.

## 5. Limites

- fournisseurs simulés uniquement ;
- aucun accès réseau ;
- gateway in-process, pas encore service indépendant ;
- pas de stockage durable des autorisations ;
- pas d’intégration Quantar runtime ;
- pas de validation réelle.

Le statut reste `PARTIALLY_VALIDATED`.
