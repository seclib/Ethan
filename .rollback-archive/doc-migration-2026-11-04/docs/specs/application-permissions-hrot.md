# Spécification — Permissions et Human Root of Trust (MEM-014 Phase 3)

## États

- `requested` : permission demandée.
- `pending` : en attente d'approbation HROT.
- `granted` : accordée par HROT.
- `denied` : refusée.
- `revoked` : révoquée.

## Décisions

- `allow` : permission explicite, valide, non expirée, non révoquée et manifeste inchangé.
- `deny` : toutes les autres situations, y compris l'ambiguïté et les erreurs.

## HROT

Aucune permission n'est accordée sans preuve d'autorité humaine (`HumanAuthority`).
Aucune clé privée ou secret n'est requis ou stocké dans cette phase.

## Intégrité du manifeste

Chaque permission accordée peut porter un condensat de manifeste. Un changement de manifeste invalide la permission.

## Expiration et révocation

Les autorisations peuvent expirer et être révoquées explicitement.
