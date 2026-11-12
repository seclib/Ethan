# MEM_014_HROT_OPERATIONAL_READINESS_REPORT

Date : 2026-11-03
Phase : MEM-014 Phase 11 — HROT Operational Readiness
Statut : opérationnel preparatoire, non activé en production

## Architecture retenue

- `SoftwareEncryptedKeyStorage` : stockage chiffré par passphrase, permissions restrictives, pas de restitution de la clé.
- `HrotTrustStore` : persistance SQLite des preuves consommées et clés révoquées.
- `OperationalHrotService` : facade create/present/approve/sign/verify.
- Anti-rejeu persistant et révocation survivant au redémarrage.

## Frontière de confiance réelle

- L'agent ne possède pas la clé.
- La signature exige un stockage déverrouillé.
- La vérification est indépendante.
- L'absence de stockage fait échouer l'opération.
- Mode fail-closed conservé.

## Limites

- Le stockage logiciel ne remplace pas un HSM/TPM/secret-service OS.
- Le composant de signature reste dans le même processus pour cette phase.
- Pas de flux WebUI réel ni de service Linux externe.
- Pas de cryptographie production sans validation humaine du stockage.

## Tests

- 7 tests phase 11 passent.
- Régression complète phase précédente à réexécuter.

## Prochaine étape

Valider le stockage sécurisé cible avec l'opérateur, puis définir le flux humain réel dans le WebUI.
