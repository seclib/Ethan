# ADR-MEM-014 Phase 10 — HROT Cryptography

- Algorithme : Ed25519.
- Bibliothèque : cryptography.
- Preuve : structure versionnée canonicalisée en JSON compact, signée Ed25519.
- Clé privée : conservée uniquement dans le signer, jamais persistée par MEM-014.
- Vérificateur : indépendant, ne dépend que de clés publiques de confiance.
- Anti-rejeu : identifiant de preuve enregistré dans l'ensemble consommé du vérificateur.
- Révocation : clé ou preuve marquée révoquée.
- Fail-closed en cas d'erreur, d'absence de vérificateur ou de preuve invalide.
