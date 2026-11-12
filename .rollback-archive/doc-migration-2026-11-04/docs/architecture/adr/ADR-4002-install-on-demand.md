# ADR-4002 — Installation à la demande (supported ≠ installed ≠ running ≠ ready)

> Correspond à la demande « ADR-002 — Installation à la demande ».

**Statut** : Implémenté
**Date** : 2026-09-23
**Implémentation** : [`core/capability_manager/types.py`](/core/capability_manager/types.py)
(machine à états), [`core/capability_manager/manager.py`](/core/capability_manager/manager.py)
(opérations explicites), catalogue [`builtin.py`](/core/capability_manager/builtin.py)
ESR liés : [ESR-001](/docs/engineering/esr/ESR-001-capability-model.md) (états),
[ESR-002](/docs/engineering/esr/ESR-002-installation-engine.md) (pipeline)

---

## Contexte

Les assistants IA ont historiquement masqué la frontière entre « ce que le
système *peut* faire » et « ce qu'il *fait* tourner ». Sur l'hôte d'ETHAN,
tirer une image Docker ou installer un paquet Python est une opération
lourde, consommatrice d'espace disque, et à impact sécurité. Une interface
qui affiche « ✓ Qdrant installé » alors que le conteneur n'existe pas
produce des diagnostics faux et une méfiance utilisateur durable.

## Problème

Comment garantir qu'aucun composant optionnel n'apparaît comme disponible
s'il n'est pas réellement présent, et qu'aucun composant n'est déployé sans
une action explicite de l'utilisateur ?

## Décision

1. **Aucune installation automatique** — ni au boot, ni au premier usage, ni
   par une tâche de fond. Le cycle de vie ne démarre que sur un appel API
   explicite (`POST /v1/components/{id}/install`).
2. **Quatre notions séparées**, chacune un état de la machine à états :

```text
SUPPORTED      le catalogue Core déclare le composant (spec enregistrée)
≠
NOT_INSTALLED  support vérifié, rien n'est présent sur l'hôte
≠
RUNNING        processus/conteneur démarré (santé basique)
≠
READY          santé fonctionnelle validée (palier "functional")
```

3. La machine à états **interdit les sauts** : `SUPPORTED → {NOT_INSTALLED,
   ERROR}` uniquement ; `NOT_INSTALLED → INSTALLING` uniquement. Passer de
   « supporté » à « prêt » sans installation réelle est impossible par
   construction.
4. `requires_confirmation=True` sur les specs à impact (Docker, pip) :
   le frontend doit présenter un plan avant exécution.
5. Docker lui-même **n'est jamais installé par ETHAN** : une spec Docker
   dépend de la dépendance système `docker`, et son absence produit l'état
   `SUPPORTED` avec un message explicite (observé en production :
   « Docker est requis mais absent. Installez Docker manuellement »).

## Alternatives considérées

| Alternative | Raison du rejet |
|---|---|
| Auto-install au premier usage (« lazy provisioning ») | Effet surprise, disque/réseau consommés sans consentement, échec opaques au démarrage |
| Booléen unique `installed: true/false` | Masque installing/starting/unhealthy ; un composant démarré mais malade apparaîtrait « installé » |
| Promesse de « zéro configuration » (tout préinstallé) | Gonfle l'image, casse le mode minimal, ralentit le boot (cf. plan de remise en état du boot) |

## Conséquences positives

- L'utilisateur voit toujours la vérité : 3 états réels distincts observés
  en live (`memory: READY`, `qdrant: SUPPORTED`, `chromadb: NOT_INSTALLED`).
- Zéro effet de bord réseau/disque au boot — le boot reste prévisible.
- Chaque installation est auditable (qui, quand, quelle config).

## Conséquences négatives

- Friction volontaire : l'installation demande une confirmation et une
  attente (progression réelle).
- Un composant supporté mais absent est un piège potentiel pour un
  développeur qui suppose sa présence ; les tests doivent le couvrir.

## Sécurité

- Les opérations de mutation exigent `ADMIN` (install/uninstall),
  `SETTINGS` (configure/start/stop/enable/disable) ou `EXECUTE`
  (detect/test) — voir
  [ESR-006](/docs/engineering/esr/ESR-006-security-model.md).
- Échec honnête : un échec d'installation positionne `ERROR` +
  `last_error`, jamais un état optimiste.

## Compatibilité avec l'architecture existante

- La détection (`detect()`) réconcilie l'état persisté avec la réalité de
  l'hôte à chaque lecture `?refresh=true` — un composant installé hors
  ETHAN (ou supprimé manuellement) est réDécouvert honnêtement.
- Complète [ADR-4001](/docs/architecture/adr/ADR-4001-capability-manager.md)
  (machine à états) et [ADR-4004](/docs/architecture/adr/ADR-4004-core-source-of-truth.md)
  (l'état affiché provient du Core, jamais du frontend).