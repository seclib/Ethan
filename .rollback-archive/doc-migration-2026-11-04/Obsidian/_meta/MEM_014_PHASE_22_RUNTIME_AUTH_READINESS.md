# MEM_014_PHASE_22_RUNTIME_AUTH_READINESS

Date : 2026-11-03
Statut : diagnostic et correctif technique limité

## État initial

- Le backend démarre plus loin avec la correction du shadowing `CoreRecordStore`.
- `NATS_URL` attend `nats://nats:4222` selon `.env`, mais le nom `nats` n'est pas résoluble hors du réseau Compose.
- Le processus local indépendant ne fait pas partie du flux d'intégration ETHAN déclaré et son secret effectif n'est pas accessible.

## Correctif appliqué

- `interfaces/api/main.py` : import local renommé pour éviter qu'une importation tardive n'emasque `CoreRecordStore` sur toute la fonction.

## Audit authentification

- Routes publiques définies dans `interfaces/api/auth.py`.
- Routes protégées via middleware JWT ou API key.
- Identité fondée sur `sub` JWT.
- Pas de mot de passe par défaut introduit.

## Résultats exacts

- Tentative de backend sur 8000 : la première tentative a échoué sur l'import local de CoreRecordStore (corrigé).
- Une tentative ultérieure a atteint `Application startup complete`, mais le bind a échoué car un autre processus occupy le port 8000.
- Aucune authentification réussie n'a été démontrée avec le WebUI.

## Limites

- Environnement NATS/Docker non aligné.
- Authentification réelle non validée.
- Aucune capture navigateur réelle.
- HROT reste fail-closed.

## Action humaine requise

Démarrer l'environnement Compose complet avec le token partagé et le réseau `nats`, ou fournir le backend déjà démarré par le service système.
