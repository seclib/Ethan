# ADR-4007 — Fork Open WebUI comme frontend : gate de licence et de marque

- **Statut** : Proposed / Blocking
- **Date** : 2026-10-29

## Contexte
- Open WebUI v0.9.1 est dans `examples/open-webui`.
- Licence = Open WebUI License historique, avec clause 4 restreignant altération/suppression du branding, sauf ≤50 utilisateurs finaux sur 30 jours, permission écrite, ou licence enterprise.
- ETHAN est Apache-2.0.

## Décision proposée
Aucune modification d'identité Open WebUI ne sera faite tant qu'une décision légale/produit n'est pas documentée.

## Alternatives
1. Conserver Next.js actuel (Apache-2.0) et importer patterns UX (pas de code Open WebUI).
2. Utiliser Open WebUI avec backend shim et conserver branding acceptable.
3. Obtenir enterprise license pour rebrand.
4. Implémenter UI inspirée (clean-room) sans copier code.

## Blocking conditions
- Document légal précisant usages, audience et budget.
- Validation du nombre d'utilisateurs final prévu.
- Choix des conditions de maintenance et coûts.
