# ADR-4003 — Cycle de vie des données : uninstall ≠ delete data

> Correspond à la demande « ADR-003 — Lifecycle des données ».

**Statut** : Implémenté
**Date** : 2026-09-23
**Implémentation** : [`core/capability_manager/manager.py`](/core/capability_manager/manager.py)
(`uninstall`, `_do_uninstall`, `_check_dependent_enabled`), backends
(`keep_data`, `data_to_delete`), garde API (`confirm_delete_data`)
ESR liés : [ESR-002](/docs/engineering/esr/ESR-002-installation-engine.md),
[ESR-003](/docs/engineering/esr/ESR-003-docker-provisioning.md) (volumes),
[ESR-005](/docs/engineering/esr/ESR-005-webui-capability-manager.md) (dialog)

---

## Contexte

Les données d'un composant optionnel (volumes Docker, répertoires locaux)
représentent souvent la valeur réelle de l'installation : embeddings,
index vectoriels, historiques. Dans beaucoup d'outils, « désinstaller »
détruit implicitement les données — l'utilisateur le découvre trop tard.

## Problème

Comment permettre la désinstallation d'un composant sans jamais détruire
silencieusement ses données persistantes, tout en offrant une suppression
propre quand l'utilisateur la demande ?

## Décision

1. **Deux décisions distinctes** dans l'API :

```text
POST /v1/components/{id}/uninstall   { "delete_data": false }  → le service part, les données restent
POST /v1/components/{id}/uninstall   { "delete_data": true }   → il faut EN PLUS "confirm_delete_data": true
```

2. **Double confirmation obligatoire** pour la suppression de données : si
   `delete_data=true` sans `confirm_delete_data=true`, l'API répond
   **422** (« suppression de donnees non confirmee »). Vérifié en live.
3. **Défaut = conservation** : la spec `qdrant` déclare
   `keep_data: True` dans ses `uninstall_actions` ; le manager l'inverse
   uniquement sur demande explicite (`a["keep_data"] = not delete_data`).
4. **Dépendants protégés** : `_check_dependent_enabled` refuse la
   désinstallation si un autre composant actif dépend de la capability
   (erreur, pas de cascade silencieuse).
5. **Déclaratif** : `data_resources` de chaque spec décrit ce qui existe
   (volume `qdrant_storage`, répertoire ChromaDB, mémoire process) —
   le plan d'uninstall affiché à l'utilisateur en découle, avec une étape
   explicite « Conserver les donnees persistantes » ou
   « SUPPRESSION DES DONNEES PERSISTANTES » (destructive=True).
6. Après désinstallation (avec ou sans données) : état → `SUPPORTED`,
   config vidée, `enabled=False` — le composant redevient
   « supporté mais absent » ([ADR-4002](/docs/architecture/adr/ADR-4002-install-on-demand.md)).

## Alternatives considérées

| Alternative | Raison du rejet |
|---|---|
| Désinstallation = suppression totale (comportement `apt purge` par défaut) | Perte de données implicite, irreversibilité |
| Suppression de données via un endpoint séparé sans garde | Une mutation destructive doit être liée à l'intention de désinstallation et doublement confirmée |
| Corbeille / restauration des volumes | Complexité d'infrastructure non justifiée ; la double confirmation suffit au risque |

## Conséquences positives

- Zéro destruction silencieuse : toute suppression de données traverse deux
  confirmations et un plan affiché à l'avance.
- La réinstallation après désinstallation simple retrouve ses données
  (volume conservé).
- Les composants dépendants sont protégés d'une casse en cascade.

## Conséquences négatives

- « Keep data » peut laisser des volumes orphelins occupant de l'espace ;
  l'utilisateur doit savoir où sont ses données (les `data_resources` le
  documentent dans l'UI).
- Deux paramètres (`delete_data`, `confirm_delete_data`) à transmettre —
  toléré, c'est le prix de la barrière.

## Sécurité

- Opération destructive → permission `ADMIN` + double confirmation +
  audit (`_audit("uninstall", …, {"delete_data": …})`) + événement bus.
- La modification de `uninstall_actions` (`keep_data`) est **temporaire et
  restaurée dans un `finally`** — la spec développeur n'est jamais
  mutée durablement.

## Compatibilité avec l'architecture existante

- Le `UninstallDialog` WebUI implémente exactement le flux (radio
  Keep/Delete + double confirmation) — voir
  [ESR-005](/docs/engineering/esr/ESR-005-webui-capability-manager.md).
- S'inscrit dans la logique du commit existant `feat(plugins): … two-level
  uninstall` : ETHAN unifie la sémantique de désinstallation à deux
  niveaux sur plugins **et** composants.