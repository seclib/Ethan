# QUANTAR — Secure Provider Gateway Bridge (Mission 16)

Date : 2026-11-04
Statut : `BLOCKED` (économie de l'isolation actuelle)

## Options étudiées

A. IPC sécurisé local (`fifo`/`socket` partagé)
   - Complexe, fragile sous Docker, risque de fuite.

B. Gateway HTTP local authentifié
   - Réutilise l'API ETHAN sans nouveau daemon, mais exige une exposition réseau et un contrôle strict.
   - Surface d'attaque accrue si le worker peut joindre l'API.

C. Adaptateur minimal via Provider Gateway in-process
   - Réutilise l'existant, aucune exposition réseau, mais ne peut pas être invoqué par un worker isolé sans transport.

Option C retenue conceptuellement pour la logique ; le transport réel entre worker et gateway nécessite une autorisation humaine séparée.

## État réel

- Provider Gateway : tests `14 passed`.
- Quantar worker : conteneur isolé, pas de socket, pas de credentials, pas de réseau gateway.
- Une tâche synthétique démarre le worker mais échoue proprement sur `OPENAI_API_KEY`.
- Le flux ETHAN Provider Manager → HROT → Gateway → Worker **n'est pas encore implémentable** sans modifier l'isolation ou les contrats.

## Résultat final

- `QuantarTaskService.status()` : `available=true` si image Docker présente.
- `QuantarTaskService` task run : `FAILED` sur credential absent.
- Integration complète : `BLOCKED`.
- Aucun secret injecté, aucun contournement HROT.

## Recommandation

Définir une stratégie d'inférence pour le worker, via une interface authentifiée et hors isolation, avec autorisation explicite. Ne pas masquer le blocage.
