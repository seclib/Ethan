# Conventions d'identité applicative (MEM-014 Phase 1)

- `app_id` identifie l'application ; `instance_id` identifie une instance déployée.
- Les deux valeurs suivent `IDENTIFIER_PATTERN` : lettres, chiffres, `.`, `_`, `:`, `-`.
- La version applicative et la version du contrat suivent le motif sémantique `x.y.z`.
- L'identité applicative est indépendante de l'authentification et de l'autorisation.
- Une capacité déclarée n'est pas une capacité autorisée.
- Un manifeste ne s'attribue jamais une permission.
