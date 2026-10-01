# ESR-005 — WebUI Capability Manager

**Statut** : Implémenté
**Date** : 2026-09-23
**Décisions parentes** : [ADR-4004](/docs/architecture/adr/ADR-4004-core-source-of-truth.md),
[ADR-4003](/docs/architecture/adr/ADR-4003-data-lifecycle.md)
**Code** : [`interfaces/webui/src/lib/api/components.ts`](/interfaces/webui/src/lib/api/components.ts),
[`capabilities-section.tsx`](/interfaces/webui/src/components/features/settings/components/capabilities-section.tsx),
[`capability-dialogs.tsx`](/interfaces/webui/src/components/features/settings/components/capability-dialogs.tsx)
**Tests** : `interfaces/webui/tests/unit/capabilities-section.test.tsx` (19)

---

## 1. Catalogue

Navigation : **Settings ▸ Capabilities** (`#capabilities`, icône Puzzle).
Le catalogue provient intégralement de `GET /v1/components?refresh=true`
(détection incluse — états réels dès le premier rendu), groupé par
catégories (`provider → AI Providers`, `vector_database → Vector
Databases`, etc. — seules les catégories peuplées s'affichent).

## 2. États

`ComponentState` (miroir TypeScript des 12 états Core) rendu en badges
libellés : `Available`, `Not installed`, `Installing…`, `Installed`,
`Starting…`, `Running`, `Stopped`, `Unhealthy`, `Configuration required`,
`Ready`, `Uninstalling…`, `Error`. **Aucun « ✓ installé »** non fondé :
le libellé est une pure traduction de l'état Core ; le polling (15 s) et
le bouton « Rafraîchir l'état » (→ `detect`) maintiennent la vérité.

## 3. Matrice d'actions (par état)

| État | Boutons |
|---|---|
| `SUPPORTED` / `NOT_INSTALLED` | [Installer] |
| `INSTALLED` / `STOPPED` | [Démarrer] [Configurer] [Désinstaller] |
| `RUNNING` / `READY` | [Arrêter] [Configurer] [Désinstaller] (+ Activer/Désactiver si READY) |
| `CONFIGURATION_REQUIRED` | [Configurer] |
| `ERROR` | [Voir les détails] [Réessayer] + `last_error` affiché |
| `INSTALLING`/`STARTING`/`UNINSTALLING` | spinner « opération en cours… » (aucune action) |
| **backend `builtin`** | **[Configurer] seul** — jamais Install/Start/Stop/Uninstall |

## 4. Installation

`InstallDialog` : fetch `GET /plan` → affiche **description, version,
dépendances, étapes prévues, données créées** (du plan Core, résolu avec
les défauts du schema) → `[Annuler] [Installer]`. Après confirmation :
`POST /install` (202, `operation_id`) → `OperationProgress` (polling 1 s)
affiche la barre de progression **du Core** + les étapes cochées +
[Annuler] (→ `cancel`). Aucune progression simulée côté frontend.

## 5. Désinstallation

`UninstallDialog` : titre explicite (« Désinstaller … »), radio
**Conserver les données** (défaut) / **Supprimer définitivement**, plan
d'uninstall affiché, et — uniquement si suppression — une **double
confirmation** (case explicite) avant `POST /uninstall` avec
`delete_data` + `confirm_delete_data`. Résultat suivi via
`OperationProgress`.

## 6. Configuration & test

`ConfigureDialog`, deux modes :

- **Guidé** (recommandé) : champs générés depuis `config_schema` du Core
  (types, bornes min/max, choices, défauts, descriptions).
- **JSON** (avancé) : textarea avec validation à la saisie (erreurs
  précises du parseur), bouton **Formater**, **exemple généré du schéma
  réel** (défauts du Core — jamais un JSON fictif), retour au guidé.

[Tester la connexion] → `POST /test` → rendu du résultat Core
(`ok`, `level`, détail par check). `POST /configure` persiste ; le
composant repasse par stop/start si la spec le prévoit.

## 7. Gestion des données

Les `data_resources` (volumes, répertoires) sont affichés sur la carte
(« Données : qdrant_storage ») — l'utilisateur sait où sont ses données
**avant** de désinstaller (flux §5).

## 8. Discipline d'interface

- Le WebUI ne détermine **jamais** un état ([ADR-4004](/docs/architecture/adr/ADR-4004-core-source-of-truth.md)) ;
  il transmet des intentions et ré-affiche l'état Core (invalidation
  react-query).
- Aucune logique docker/pip/npm côté frontend — l'installation est une
  requête, pas du shell.
- Duplication évitée : la page Vector Database historique conserve son
  rôle de *configuration active* du RAG ; le gestionnaire de capacités
  gère le *cycle de vie* — les tests couvrent l'absence de conflit.