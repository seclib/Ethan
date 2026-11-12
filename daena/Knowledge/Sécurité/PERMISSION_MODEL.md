# ETHAN — Modèle de permissions pour l'Engineering Memory

Date : 2026-11-03
Statut : PROPOSED
Source de vérité humaine : Human Root of Trust

## Matrice

| Rôle | READ | PROPOSE | RECORD | MODIFY | ARCHIVE | VALIDATE | HUMAN_APPROVE | ADMINISTER |
|---|---|---|---|---|---|---|---|---|
| READER | oui | non | non | non | non | non | non | non |
| PROPOSER | oui | oui | non | non | non | non | non | non |
| RECORDER | oui | oui | oui | non | non | non | non | non |
| VALIDATOR | oui | oui | oui | non | non | oui | non | non |
| HUMAN_AUTHORITY | oui | oui | oui | oui | oui | oui | oui | non |
| ADMIN | oui | oui | oui | oui | oui | oui | oui | oui |

## Règles

1. Aucun agent ne possède `HUMAN_APPROVE`.
2. `VALIDATOR` ne possède ni `MODIFY`, ni `ARCHIVE`, ni `HUMAN_APPROVE`.
3. `RECORDER` ne peut pas promouvoir le statut d'une information.
4. Les vues reclassent uniquement si un humain intervient.
5. Les repères et violations sont en permanence observables.
6. Les archives ne peuvent pas être réécrites pour masquer une erreur.
7. Les secrets sont redactés avant publication.

## Opérations privilégiées

- `approve_decision`
- `archive_secret_record`
- `publish_memory`
- `purge_record`

## Gouvernance HROT

- L'humain approuve.
- L'agent propose et enregistre.
- Le serveur valide et conserve.
- Les preuves restent accessibles.
