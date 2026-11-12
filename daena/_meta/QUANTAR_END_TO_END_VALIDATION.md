# QUANTAR — Validation end-to-end contrôlée

Date : 2026-11-04
Statut : PARTIALLY_VALIDATED

## 1. Preuve réelle d'exécution one-shot

- Repertoire de test : `/tmp/qp-e2e-1793775000`
- Conteneur : `quantar-runtime:latest`
- Réseau : `none`
- Sortie : code `0`
- Résultat : decision `FAKE HOLD NVDA 2026-09-01`

Le fichier `result.json` a été écrit atomiquement et contient le statut `COMPLETED`.

## 2. Table des tests

| Test | Résultat | Preuve |
|---|---|---|
| Création et persistance de task.json | PASS (contrôlé) | fichier JSON écrit et monté dans /data/quantar |
| Refus d'une tâche sans autorisation HROT | PASS (unitaire) | gateway unit tests |
| Exécution autorisée | PASS (contrôlé) | conteneur retour 0, résultat écrit |
| Restrictions conteneur | PASS (contrôlé) | réseau none, utilisateur 1000, cap_drop, read-only |
| Récupération result.json | PASS (contrôlé) | fichier lu, decision présente |
| États finaux | PASS (contrôlé) | statut final COMPLETED |
| Persistance après redémarrage service | PASS (unité) | _load_persisted_tasks |
| Annulation et interruption | PARTIELLEMENT | tests contrôlés, pas de tâche réelle Docker |
| Doubles exécutions | NON TESTÉ runtime | protection in-process uniquement |
| Nettoyage contrôlé | PASS (contrôlé) | conteneur ephemere --rm |

## 3. Limites

- fake TradingAgents monté manuellement ;
- pas de fournisseur réel ni LLM ;
- aucune persistance multi-instance démontrée ;
- aucun test webui Playwright ;
- pas de preuve HROT channel ;
- pas de vrai test d'annulation pendant propagate.

## Conclusion

La validation unitaire et le test fake Docker réel démontrent le fonctionnement one-shot contrôlé. Le statut reste PARTIALLY_VALIDATED car toutes les preuves runtime critiques ne sont pas acquises.
