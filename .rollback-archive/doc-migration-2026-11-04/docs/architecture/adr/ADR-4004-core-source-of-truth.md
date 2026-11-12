# ADR-4004 — Le Core, source de vérité de l'état des composants

> Correspond à la demande « ADR-004 — Core comme source de vérité ».

**Statut** : Implémenté
**Date** : 2026-09-23
**Implémentation** : [`core/capability_manager/manager.py`](/core/capability_manager/manager.py)
(`detect`, `_load_state`/`_save_state` sur CoreRecordStore),
[`interfaces/api/routers/component_lifecycle.py`](/interfaces/api/routers/component_lifecycle.py),
[`interfaces/webui/src/lib/api/components.ts`](/interfaces/webui/src/lib/api/components.ts)

---

## Contexte

La Première Loi d'ETHAN impose que toute capacité métier vive dans Core ou
Runtime, les interfaces n'étant que des moyens d'afficher et de contrôler.
L'état d'un composant (« est-ce installé ? actif ? fonctionnel ? ») est une
donnée métier : elle doit survivre aux interfaces et être partagée par
toutes (WebUI, CLI, Desktop).

## Problème

Empêcher que le WebUI (ou toute interface) détermine lui-même l'état d'un
composant — par un test de port, un appel direct, ou un état gardé en
mémoire du navigateur — ce qui produirait des vérités divergentes.

## Décision

Flux unidirectionnel, sans source d'état en aval :

```text
Core (capability_manager)
  ↓  detect() / status() — persistance CoreRecordStore (domaine capability_manager)
Capability state (JSONB, typé, audité)
  ↓  GET /v1/components[?refresh=true]  (RBAC READ)
WebUI (rendu passif : badges, matrice d'actions)
```

1. **Seul le Core évalue** : support, dépendances, présence installée,
   santé fonctionnelle (`HealthChecker`). Le frontend n'exécute jamais de
   sonde.
2. **`refresh=true`** déclenche `detect()` : réconciliation de l'état
   persisté avec la réalité de l'hôte avant affichage. La section
   Capabilities l'utilise systématiquement (`listComponents(true)`).
3. **États explicites uniquement** : la réponse contient `state` (12 valeurs
   normalisées) + `last_error` — jamais un booléen déduit.
4. **Purge d'erreur à la réconciliation** : si `detect()` ramène un
   composant vers un état propre (`SUPPORTED`/`NOT_INSTALLED`),
   `last_error` est remis à `None` — l'UI n'affiche jamais une erreur
   périmée. (Correctif appliqué et testé.)
5. **Le WebUI transmet des intentions** (install/stop/configure/uninstall),
   invalide son cache (`react-query`) et ré-affiche l'état renvoyé par le
   Core. Aucun état métier n'est stocké côté navigateur.

## Alternatives considérées

| Alternative | Raison du rejet |
|---|---|
| Le frontend teste les endpoints lui-même (fetch direct Qdrant) | CORS, secrets exposés, vérité divergente, logique métier dans l'interface (violation AGENTS.md) |
| État gardé côté WebUI (store local) | Perdu au reload, désynchronisé entre onglets/interfaces, non auditable |
| Cache API sans réconciliation | Risque d'afficher un état obsolète après une manipulation hors ETHAN |

## Conséquences positives

- Toutes les interfaces voient la même vérité au même instant (le CLI
  `ethan components` et la WebUI consomment le même endpoint).
- Les états survivent aux redémarrages (persistance Core).
- Réconciliation continue : la réalité de l'hôte reprend toujours le dessus.

## Conséquences négatives

- Chaque lecture « fraîche » coûte une passe de détection (process check,
  TCP, HTTP) — maîtrisé par le polling 15 s + rafraîchissement manuel.
- Le Core doit être joignable pour toute consultation d'état (dépendance
  assumée : c'est ETHAN).

## Sécurité

- L'état est servi derrière l'authentification JWT + permission `READ` ;
  les mutations exigent des permissions plus fortes (voir
  [ESR-006](/docs/engineering/esr/ESR-006-security-model.md)).
- `last_error` est tronqué (200–300 caractères) : pas de fuite de pile
  interne vers l'UI.

## Compatibilité avec l'architecture existante

- Même principe que [ADR-3002](/docs/architecture/adr/ADR-3002-providers-source-of-truth.md)
  (ProviderManager = seule source de vérité des providers) — appliqué aux
  composants optionnels.
- Conforme au pattern déjà utilisé par tous les routers (injection du
  manager Core, passerelle mince).