# MEM_014_PHASE_23_NATS_RUNTIME_ALIGNMENT

Date : 2026-11-03
Statut : aligné et vérifié

## Cause racine

La divergence venait de l'utilisation du hostname Compose `nats` hors du réseau Docker et de l'absence d'alignement explicite entre l'instance attendue et le client backend lancé directement.

Le serveur NATS local écoute sur 127.0.0.1:4222 et accepte le token configuré dans `.env`.

## Stratégie validée

- Instance officielle locale : 127.0.0.1:4222.
- Les déploiements Compose continuent d'utiliser `nats://nats:4222` avec le même token.
- Le backend lancé directement doit utiliser `NATS_URL=nats://localhost:4222` et le même `NATS_TOKEN`.

## Preuves

- Connexion NATS réussie.
- Publication réussie sur `ethan.health.phase23`.
- Aucun secret affiché dans ce rapport.

## Tests

- Connexion réelle et publication validées.
- Référence MEM-014 : 128 tests passent.

## Risques résiduels

- Le backend et le WebUI sur 3001 restent à valider avec une session réelle.
- Les opérations destructives HROT restent bloquées.
