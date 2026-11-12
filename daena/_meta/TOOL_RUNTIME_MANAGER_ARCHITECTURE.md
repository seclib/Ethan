# TOOL RUNTIME MANAGER — Architecture commune et contract outils ETHAN

Date : 2026-11-04
Statut : proposition architecturale — audit effectué, pas de migration exécutée

## 1. Audit préalable

### Mécanismes existants

- `core/plugins/compose_service.py` fournit une base commune Docker Compose pour les outils conteneurisés.
- `core/plugins/odin.py` utilise `ComposeService` avec santé par conteneur.
- `core/plugins/quantar.py` réutilise également `ComposeService` avec santé basée sur `docker compose ps`.
- `core/applications/quantar_service.py` ajoute un runtime one-shot conteneurisé pour l'exécution réelle de TradingAgents.
- `interfaces/api/routers/quantar.py` expose le cycle de vie et les données d'exécution.

### Conclusion

Il existe déjà une abstraction réutilisable. La recommandation est d'étendre `ComposeService` au lieu de créer un second orchestrateur.

## 2. Contrat commun des outils

Champs minimaux :

- `application_id`
- `display_name`
- `runtime_type`
- `runtime_mode`
- `compose_file`
- `compose_project`
- `lifecycle_policy`
- `startup_policy`
- `health_policy`
- `resource_limits`
- `required_capabilities`
- `security_profile`

Règles :

- les outils déclarent leur contrat, ils n'inventent pas leur commande Docker ;
- les actions sont passées par une API approuvée ;
- tout conteneur est soumis à un profil de sécurité fixe.

Types d'outils :

- conteneurisé ;
- in-process ;
- service persistant ;
- worker one-shot ;
- application interactive.

## 3. Tool Runtime Manager

Le gestionnaire doit :

- découvrir les outils déclarés ;
- valider le contrat ;
- démarrer et arrêter un outil ;
- lire l'état réel ;
- exécuter health checks ;
- collecter les logs ;
- gérer les erreurs ;
- appliquer HROT avant actions sensibles.

Il ne doit pas :
- exécuter de commande docker arbitraire ;
- monter de socket Docker pour un outil ;
- exécuter d'analyse financière ;
- contourner les profils de sécurité.

## 4. Réutilisation d'abstractions existantes

- `ComposeService` reste le mécanisme de base ;
- `QuantarService` garde son runtime one-shot ;
- l'interface frontend utilise l'API ETHAN ;
- pas de catalogue central d'applications.

## 5. Adaptation Quantar

- Utiliser `quantar-runtime:latest` via Compose ;
- conserver les restrictions actuelles ;
- garder le comportement one-shot ;
- ne pas démarrer automatiquement d'analyse.

## 6. WebUI commune

- afficher état réel : arrêté, démarrage, actif, erreur ;
- actions start/stop/restart via backend ;
- logs et configuration ;
- stratégie de démarrage ;
- respect du thème sombre professionnel.

## 7. Sécurité

- aucune commande Docker arbitraire depuis le WebUI ;
- aucune ouverture de socket pour un outil ;
- aucun privilège excessif ;
-:frame et Odin restent selon leurs modèles actuels jusqu’à Justification.

## 8. Migration progressive

1. contrat et validation ;
2. runtime manager générique ;
3. Quantar comme outil de référence ;
4. WebUI ;
5. autres outils selon architecture ;
6. validation.

## 9. Risques et points ouverts

- plusieurs mécanismes de lifecycle coexistent et peuvent diverger ;
- Quantar nécessite une validation runtime renforcée ;
- WebUI dépend de l'image déployée réelle ;
- l'approbation humaine doit rester dans le circuit.

## 10. Conclusion

L'architecture proposée réutilise l'abstraction existante et évite un second orchestrateur. Elle doit être implémentée progressivement, en commençant par Quantar et les composants partagés.
