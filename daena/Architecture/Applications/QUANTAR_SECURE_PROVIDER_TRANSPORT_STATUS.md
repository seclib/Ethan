# Quantar Secure Provider Transport — ANO-03 Status

Statut : BLOCKED

## 1. Architecture découverte
- Quantar Service : `core/applications/quantar_service.py`
- Worker runtime : `examples/quantar/quantar_task_runner.py`
- Gateway HROT : `core/security/hrot_provider_gateway.py`
- Bridge existant : `core/applications/quantar_provider_bridge.py`
- ProviderManager canonique : `core/llm/provider_manager.py`

## 2. Cause persistante de ANO-03
- La gateway Provider existe dans le processus ETHAN, mais n'expose aucun transport démontré vers un worker Quantar isolé.
- Un worker actuel ne peut ni présenter une identité HROT, ni requêter le Provider Gateway, car aucune frontière de process/transport n'est implémentée.
- Les secrets fournisseurs restent dans ETHAN kernel, volontairement hors du worker. Cette restriction n'a pas été contournée.
- `QuantarProviderBridge` prépare et consomme une autorisation HROT et peut exécuter `ProviderGateway`, mais il ne constitue pas encore un transport sûr entre processus.

## 3. Preuves actuelles
- `tests/core/test_quantar_provider_bridge.py` valide les chemins d'autorisation durable (succès/refus), sans transport runtime.
- `tests/core/test_hrot_provider_gateway.py` pour les 14 tests passants.
- `QuantarService.status()` expose `docker_image_available` et `inprocess_available`, mais n'inclut pas de capacité provider gateway validated.
- `quantar_task_runner.py` d'exécution réelle directe de TradingAgents no call au Gateway.

## 4. Pourquoi aucune implémentation n'est revendiquée ici
Le blocage architecturale n'est pas un simple bug de Python. L'introduction d'un socket HTTP sans accès secure, d'un tunnel ou d'un endpoint sans authentication HROT pouvait contourner les exigences non négociables. Le bon chemin nécessite :
- une identité de worker authentifiée ;
- une autorisation HROT durable ;
- un canal local restreint et attaque-hard ;
- des opérations scoped ;
- l'intégration Gateway ↔ ProviderManager ;
- des tests end-to-end sans fuite de secret.

## 5. Prochaines étapes actionnables
1. Concevoir un endpoint Auth-HROT seulement pour `provider:infer`.
2. Transporter des opérations via un canal local contrôlé plutôt qu'un network ouvert.
3. Faire un adapter TradingAgents ↔ Gateway-INréel.
4. Test avec fake local Ollama et secret fictive, en vérifiant l'absence de toute fuite.

Statut final : BLOCKED.
