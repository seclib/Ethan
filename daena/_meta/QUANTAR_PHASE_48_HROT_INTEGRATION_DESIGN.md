# QUANTAR — Architecture HROT durable et intégration Provider Gateway (Phase 48)

Date : 2026-11-04
Statut : design préparatoire ; aucune exécution réelle démontrée — PARTIALLY_VALIDATED

## 1. Audit de l'existant

### 1.1 Gateway existant

`core/security/hrot_provider_gateway.py` contient :
- `ProviderGatewayAuthorization`
- `ProviderGatewayRequest`
- `ProviderGatewayResponse`
- `SecretProvider`
- `ProviderGateway.execute()`

Forces : contrat HROT, validation stricte, allowlist, rate-limit, redaction, tests unitaires.

Limites : autorisations in-memory, aucun moteur HROT durable, aucun canal runtime, aucune intégration avec Quantar.

### 1.2 Moteur HROT durable

`core/hrot/durable.py` fournit `DurableHrotStore` avec PostgreSQL/JSONL. Il supporte création, récupération, resolution, consommation, expiration et concurrence par transaction.

Il constitue le point de vérité le plus adapté pour l'autorisation durable.

### 1.3 Human Root

`core/human_root` fournit le principe d'approbation humaine et l'audit log.

C'est l'auteurité finale pour toute autorisation sensible.

## 2. Architecture retenue

### Moteur HROT unique

Réutiliser `HumanRoot` + `DurableHrotStore` comme source d'autorité. Le `ProviderGateway` actuel doit être réduit à un adaptateur/validateur, pas à un second moteur.

### Provider Gateway durable

Nouveau flux cible :

1. ETHAN crée une demande d'autorisation HROT pour l'expérience QUANTAR;
2. l'humain approuve ou refuse ;
3. une autorisation HROT durable est consommée pour une opération précise ;
4. le gateway reçoit une requête du runner via un canal authentifié ;
5. il vérifie l'autorisation durable, l'identité, le rôle et les limites ;
6. il exécute l'appel provider et renvoie le résultat au conteneur.

Aucun secret ne transite vers Quantar.

## 3. Canal conteneur → gateway

Deux options comparées :

### A. Passphrase locale signée temporaire

- Quantar reçoit une autorisation éphémère liée à `task_id` et `execution_id`.
- Le gateway vérifie l'autorisation durable, puis authentifie le runner.
- Faible pouvoir latent, révocation naturelle.
- Compatible avec `network: none` uniquement si un transport local existe.

### B. Port-forwarding / HTTP loopback via proxy

- Le conteneur atteint un endpoint ETHAN sur localhost uniquement;
- `network: none` rend cette solution impossible.
- Risque d'élargir le réseau sans preuve.

Recommandation : Option A avec un point unique applicatif et une autorisation temporaire, une fois le transport local validé.

## 4. Protocole proposé

Chaque requête comprend :

- `task_id`
- `execution_id`
- `authorization_id`
- `provider_id`
- `model_id`
- `capability`
- `resource`
- `action`
- `messages`
- `parameters`
- `correlation_id`

Toute requête est validée strictement, même en absence de réseau upstream.

Quantar ne reçoit jamais une clé API ni un secret.

## 5. Cycle de vie de l'autorisation

- `DECLARED` : demande créée ;
- `VERIFIED` : authentification réussie ;
- `AVAILABLE` : configuration présente avec provider ;
- `AUTHORIZED` : l'action spécifique est approuvée et non révoquée.

Une autorisation `AUTHORIZED` se consume à l'opération et ne peut pas être réutilisée après expiration.

## 6. Adaptation TradingAgents

- Utiliser un client d'inférence ETHAN au lieu d'appeler directement les fournisseurs LangChain.
- Conserver les interfaces HROT existantes au maximum.
- Ne pas modifier arbitrairement upstream.
- Définir un wrapper quantar-specific qui accepte la future gateway.

## 7. Persistance

- Chaque autorisation durable est stockée via le moteur HROT.
- Recharger uniquement les autorisations non expirées et non révoquées.
- Une autorisation interrompue reste non réutilisable.
- Les autorisations expirées ne sont jamais restaurées.

## 8. Tests simulés requis

- identité valide ;
- identité inconnue ;
- provider non autorisé ;
- autorisation expirée ;
- révocation ;
- requête malformée ;
- hors périmètre ;
- indisponibilité du moteur ;
- absence de secret dans logs/résultats ;
- réutilisation refusée.

## 9. Risques et blocages

- absence d'un service HROT runtime opérationnel pour Quantar ;
- absence de canal local authentifié validé ;
- absence d'adapter TradingAgents pour la gateway ;
- absence de tests end-to-end.

## 10. Décisions restantes

- choisir le transport local authentifié ;
- définir le format du token d'autorisation ;
- définir les limites par tâche ;
- décider si l'opération complète nécessite une approbation humaine supplémentaire.

Statut : `PARTIALLY_VALIDATED` — conception prête, non implémentée ni démontrée.
