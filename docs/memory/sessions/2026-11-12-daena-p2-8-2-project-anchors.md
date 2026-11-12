# Session — 2026-11-12 — DAĒNĀ P2.8.2 : Project Anchors

Mission : introduire un mécanisme cohérent d'ancrage des connaissances et des
données ETHAN à un projet, sans duplication de contenu.

Prérequis : P2.8.0 et P2.8.1 clôturées. Contraintes : aucun reset, aucun
clean, aucun commit automatique, stash intact, corpus et PostgreSQL préservés.

---

## 1. État Git initial et final

| | Initial | Final |
|---|---|---|
| Branche | `refactor/ethan-rebuild-p0` | identique |
| HEAD | `57e254b0` | `57e254b0` (aucun commit) |
| Modifiés (M) | 76 | **78** (+2 : `interfaces/api/main.py`, `interfaces/api/routers/projects.py`) |
| Renommés (R) | 47 | 47 |
| Supprimés (D) | 12 | 12 |
| Non suivis (??) | 200 | 211 (+4 : module, tests, 2 docs ; +7 artefacts runtime) |
| **Total** | **335** | **348** |
| Stash | `stash@{0}: On main: audit-pre-refactoring-state` | **intact** |

Le corpus `daena/` est resté **strictement intact** (868 fichiers lisibles,
116 répertoires, empreintes SHA256 identiques au baseline P2.8.0).

---

## 2. Cartographie des modèles concernés

État vérifié **avant** modification — aucun `project_id` dans les cinq modèles :

| Modèle | Fichier | `project_id` | Nature |
|---|---|---|---|
| `MemoryRecord` | `core/engineering_memory/models.py:52` | ❌ | partageable |
| `KnowledgeNode` | `core/knowledge/types.py:62` | ❌ | partageable |
| `ResourceRecord` | `core/resources/registry.py` | ❌ | partageable |
| `Mission` | `core/missions/types.py` | ❌ | **exclusif** |
| `ArchivedSession` | `core/knowledge/agent_traces/types.py:68` | ❌ | **exclusif** |

Précédents relevés : `core/state/chats.py:40` (ancrage direct sur un chat),
`core/dedup/types.py:68` (`project_ids` multi-projet),
`core/projects/__init__.py:459` (`knowledge_ids` — contexte **déclaré** par le
projet, concept distinct de l'ancrage), `core/projects/__init__.py:423`
(pseudo-projet `general`).

---

## 3. Architecture retenue

**Relation dédiée** (`core_domain_records[project-anchors]`) plutôt qu'un champ
identique sur les cinq modèles. Motifs : multi-projet natif, provenance portée
par la relation, **aucune migration de schéma ni de données**, chemin de
requête et règle d'isolation uniques, chemin de lecture et d'écriture
homogène avec le reste du Core.

- `ProjectAnchor` : `anchor_id` (UUIDv5 déterministe), `target_type`,
  `target_id`, `project_id`, `created_at`, `actor`, `metadata`, `detached_at`.
- Portée **dérivée** : `GLOBAL` (0 ancre), `PROJECT` (1), `MULTI_PROJECT` (>1).
- Exclusivité : `Mission` et `ArchivedSession` (0..1 ancre) ; les autres
  catégories partageables.
- Isolation : `filter_by_project()` retourne le global et le sien, jamais
  l'exclusif d'un autre projet.
- Détachement : marque l'ancre `detached_at`, **ne supprime pas** la donnée et
  conserve l'historique.

---

## 4. Fichiers créés et modifiés

### Créés

| Fichier | Rôle |
|---|---|
| `core/projects/anchors.py` | `ProjectAnchor`, `AnchorScope`, `AnchorTargetType`, `ProjectAnchorService` |
| `tests/core/test_project_anchors.py` | 26 tests ciblés |
| `docs/architecture/dana-p2-8-2-project-anchors.md` | architecture des ancrages |
| `docs/memory/sessions/2026-11-12-daena-p2-8-2-project-anchors.md` | ce rapport |

### Modifiés

| Fichier | Modification |
|---|---|
| `interfaces/api/routers/projects.py` | 4 routes d'ancrage, délégation pure au Core |
| `interfaces/api/main.py` | câblage du service sur le `domain_store` partagé |
| `docs/memory/DECISIONS.md` | ADR **D-008** |
| `docs/memory/PROJECT_STATE.md` | historique de phase |
| `docs/architecture/dana-p2-8-1-persistence-unification.md` | renvoi croisé |

---

## 5. Tests exécutés — résultats exacts

```bash
cd AI/Ethan
.venv/bin/python -m pytest tests/core/test_project_anchors.py -q
# 26 passed

.venv/bin/python -m pytest tests/core/test_project_anchors.py \
  tests/core/test_resource_persistence_unification.py \
  tests/core/test_dana_p2_7_document_discovery.py \
  tests/core/test_engineering_memory_destination_mapping.py \
  tests/core/test_engineering_memory{,_vault,_adapters,_security}.py \
  tests/core/test_agent_manager_engineering_memory.py -q
# 151 passed

.venv/bin/python -m pytest tests/core/ -q --no-header -p no:cacheprovider \
  --ignore=<11 fichiers en erreur de collection pré-existante>
# 27 failed, 910 passed, 1 skipped, 8 errors
```

**910 passés** (884 + 26), 27 échecs + 8 erreurs **strictement identiques** à la
référence pré-existante.

---

## 6. Preuves de persistance et d'isolation

- Persistance : `test_attach_persists_to_the_store`,
  `test_anchor_survives_a_simulated_restart` (service reconstruit sur le même
  store → ancre relue, auteur conservé).
- Isolation : `test_filter_by_project_keeps_global_and_own` (global + sien
  retenus, celui d'autrui exclu), `test_global_targets_exclude_anchored_data`.
- Exclusivité : `test_exclusive_target_refuses_second_project`.
- Historique : `test_detach_preserves_history` (ancre détachée, auteur et date
  conservés), `test_reattach_reactivates_the_same_anchor` (même `anchor_id`).
- Domaine dédié : `test_anchor_domain_is_dedicated` (les domaines `knowledge`
  et `projects` inchangés).

---

## 7. Compatibilité historique

Aucun projet inventé, aucun rattachement déduit : les 100 `KnowledgeNode`, les
118 `MemoryRecord` et les 536 `ResourceRecord` existants restent de portée
`GLOBAL` et exploitables (`test_historical_data_without_anchor_stays_global`).
Un rattachement ultérieur explicite reste possible à tout moment.

**Aucune migration n'est nécessaire ni préparée** : la relation est additive et
le schéma des cinq modèles est inchangé.

---

## 8. Anomalies restantes

A1 à A6, R2 et R3 des rapports précédents restent **ouvertes et suivies** —
aucune traitée silencieusement. Limites propres à P2.8.2 :

| Limite | Impact |
|---|---|
| `ResourceRegistry` non branché sur le store partagé | les ancres de type `resource` n'ont pas encore de cible réelle en production (P2.8.6) |
| `missions` = 0 ligne en PG | ancres de type `mission` non exerçables en runtime |
| sessions archivées hors store (vault) | l'inventaire des cibles `session` n'est pas résolvable par le service (P2.8.7) |
| `global_targets()` ne couvre que `knowledge` et `resources` | liste vide pour les autres types — assumé |
| aucun ConsumerCore n'applique encore le filtre projet | l'API existe comme service Core, pas encore branchée sur les managers |
| routes API non validées en conditions authentifiées | l'API `/v1/projects/*` est protégée par authentification ; validation structurelle seulement |

---

## 9. Niveau réel de validation

| Niveau | État |
|---|---|
| **IMPLEMENTED** | ✅ modèle, service Core, règles de portée, validation de projet, exclusivité, isolation, routes API, câblage |
| **TESTED** | ✅ 26/26 ciblés · 151/151 (P2.8.2 + P2.8.1 + P2.7 + P2.8.0 + EM) · suite core 910 (+26, Δ0 régression) |
| **RUNTIME_VALIDATED** | ❌ — le service n'est pas encore sollicité par un ConsumerCore ; l'API est protégée par authentification (pas de credential d'exécution) |
| **E2E_VALIDATED** | ❌ |
| **NOT_VERIFIED** | exploitation réelle des ancres par les managers (phase ultérieure) |

---

## 10. Décision sur la porte de sortie

**P2.8.2 est PARTIELLEMENT validable.** Le modèle est défini, documenté,
implémenté et testé ; les relations sont persistantes ; les données
historiques restent compatibles ; les recherches respectent la portée projet
au niveau du service.

Ce qui manque pour une validation complète :

1. **Exploitation par les ConsumerCore** — le filtrage projet existe comme
   API Core (`filter_by_project`) mais n'est pas encore appliqué aux managers
   (KnowledgeManager, RAG). Le champ `project_id` de `chats` est le candidat
   naturel. Relève des phases suivantes (P2.8.4, P2.8.5).
2. **Validation RUNTIME de l'API** — les routes sont structurellement
   validées ; une exécution authentifiée n'a pas pu être réalisée dans cette
   session (aucun credential disponible, et la mission n'en fournit pas).

**Aucune migration n'est à préparer ni à autoriser** : la relation est additive.

**P2.8.3 non commencée.** J'attends la décision de l'opérateur.

---

# Consolidation P2.8.2 — Mission 02 « Stabilisation fonctionnelle » (2026-11-12)

> Ajout **chronologique**. Les constats des sections 1 à 10 décrivent l'état
> d'origine de la phase ; ils ne sont pas effacés. Cette section consigne la
> consolidation : défauts constatés, corrections, tests et limites
> restantes.

Mission : corriger, renforcer et valider complètement l'implémentation des
Project Anchors avant toute progression de la feuille de route.

Contraintes : périmètre limité aux Project Anchors ; aucune refonte ; aucun
reset, clean, commit, stash ; aucune migration ; tests sur stores isolés et
données synthétiques ; ne pas lancer P2.8.3.

## 11. État Git initial et final

| | Initial (début de mission) | Final |
|---|---|---|
| Branche | `refactor/ethan-rebuild-p0` | **`master` (branche sans commit)** |
| HEAD | `9ae9744f` | **aucun commit** |
| Entrées `git status` | 349 | 51 (toutes `A` : index neuf) |
| Stash | `stash@{0}: On main: audit-pre-refactoring-state` | **absent** |
| Fichiers de travail | intacts | **intacts** |

### 11.1 Réinitialisation du dépôt par un processus externe — constat critique

À **13:57**, pendant la mission, le répertoire `.git` a été **supprimé puis
recréé** par un processus externe :

- `.git/config` est nouveau (seul `remote origin` =
  `https://github.com/seclib/Ethan.git`) ;
- la branche courante est `master`, **sans aucun commit** ;
- `refs/heads/` est vide ; le reflog est vide ;
- les commits `57e254b0`, `95a4765b`, `9ae9744f` **ne sont plus dans la base
  d'objets** (`git cat-file -t` : « Not a valid object name ») ;
- le stash `audit-pre-refactoring-state` a disparu avec l'ancien `.git` ;
- `git ls-remote origin` ne renvoie **aucune référence** : l'historique n'est
  pas récupérable depuis le remote ;
- 4172 fichiers sont désormais indexés comme **nouveaux** (`A`).

**Cette opération n'a pas été effectuée par la présente session** : aucun
`commit`, `reset`, `clean`, `stash` ni `checkout` n'a été exécuté, et
l'historique de commandes de la session ne contient que des lectures, des
tests et des écritures de fichiers.

**Aucune réparation n'a été tentée** : recréer des refs ou committer
reviendrait à performing une opération Git que la mission interdit, et
l'indexation nouvelle peut masquer l'état réel du dépôt. La décision de
restauration appartient à l'opérateur.

**Perte effective** : l'historique Git local et le stash. **Aucune perte de
travail** : tous les fichiers de travail sont intacts et vérifiés — les
sources modifiées (1 214 + 429 + 977 + 348 lignes) et la documentation sont
présentes et les tests passent.

**Fait objectif, non causé par cette session** : 119 suppressions de
fichiers `daena/` (`Archives/Conversations/`, `Knowledge/genealogie/`,
`Knowledge/Syntheses/by-agent/`, `_meta/source-snapshots/`) étaient
**staged** dans l'index par un processus externe avant la réinitialisation.
Les fichiers sont **présents sur le disque** (l'index les marque supprimés,
l'arbre de travail les conserve) et l'intégrité du corpus est vérifiée :
**0 fichier supprimé du disque**, 1 modifié (journal d'audit append-only),
31 ajoutés (enregistrements de traçabilité P2.8.3 et événements de
démarrage de l'API). Aucune restauration n'a été tentée : ce serait une
opération destructive hors périmètre.

## 12. Défauts identifiés, causes et corrections

Douze défauts (§12 du document d'architecture pour le détail) :
**A1** réactivation ignorant l'exclusivité · **A2** absence d'atomicité
(contrôle puis écriture) · **B1** existence des cibles jamais vérifiée ·
**C1** panne du store transformée en « projet introuvable » · **C2**
inventaire inaccessible rendu par une liste vide · **D1** `detach()` sans
validation · **E1** métadonnées d'origine effacées à la réactivation ·
**E2** absence d'historique des cycles · **F1** filtrage quadratique ·
**F2** filtrage accepté pour un projet inexistant ou inactif · **G1** panne
non traduite dans les routes · **G2** `detach()` sans gestion d'erreur.

Cause racine commune : le `CoreRecordStore` **ne fournissait aucune
garantie** — ni concurrence (`save()` = upsert simple), ni distinction
entre « absent » et « inconnu » (`get()`/`list()` avalent les pannes).

Correction : trois méthodes strictes (`get_strict`, `list_strict`,
`save_strict`) et une section critique `atomic(guard)` — transaction
PostgreSQL + `pg_advisory_xact_lock`, repli `asyncio.Lock` sans
PostgreSQL. **Aucune base nouvelle, aucun daemon, aucune migration, aucun
changement de schéma.**

## 13. Résultats des tests

```
$ .venv/bin/python -m pytest tests/core/test_project_anchors.py -q
48 passed                       (26 d'origine + 22 de consolidation)

$ .venv/bin/python -m pytest interfaces/api/tests/test_project_anchors_api.py -q
17 passed

$ .venv/bin/python -m pytest tests/core/ -q   # 12 fichiers de collection ignorés (pré-existants)
27 failed, 960 passed, 1 skipped, 8 errors in 66.30s

$ .venv/bin/python -m pytest interfaces/api/tests/ -q
373 passed, 1 skipped, 1 warning in 6.73s
```

Référence avant consolidation : `tests/core/` = **938 passés** (910
baseline P2.8.2 + 28 P2.8.3) / 27 failed / 8 errors ; après : **960
passés** (+22) / **27 failed / 8 errors identiques**. Les 27 échecs et
8 erreurs sont pré-existants (`test_rust_bridge` ×23,
`test_technology_independence`, `test_intent_routing` ×8) et **inchangés** :
la comparaison a été faite sur la même exécution, avec le même jeu
d'ignores.

**Preuve que les tests détectent réellement les défauts** : la section
critique (A2) puis le contrôle de réactivation (A1) ont été neutralisés
successivement ; les tests correspondants ont alors **échoué**
(`assert 2 == 1` pour la concurrence, `1 failed` pour la réactivation) et
 repassent avec les correctifs. Aucune assertion n'a été relâchée.

## 14. Preuves de persistance et d'isolation

- **Persistance** : 48 tests sur store isolé relus après reconstruction du
  service ; le domaine `project-anchors` est seul modifié (les domaines
  `knowledge`, `resources`, `missions`, `projects` sont vérifiés
  inchangés).
- **Isolation** : `GLOBAL`, `PROJECT`, `MULTI_PROJECT`, cible exclusive
  d'un autre projet, cible détachée redevenue globale, projet inexistant
  ou inactif, `include_global=False`, isolation entre deux projets — tous
  couverts par des tests dédiés.

## 15. Contrôles HROT

| Contrôle | Résultat |
|---|---|
| Lecture sans jeton | **401** |
| Écriture avec le rôle `viewer` (sans `MEMORY`) | **403** |
| Écriture avec le rôle `user` (avec `MEMORY`) | **201 / 200** |
| Règle métier (type inconnu, projet inconnu, cible absente, projet inactif, conflit d'exclusivité) | **422** |
| Ancre absente au détachement | **404** |
| Panne du store | **503** (distincte du 422) |

Aucun système d'authentification parallèle n'a été créé : les routes
utilisent le middleware et le RBAC existants.

## 16. Validation runtime

- **Instance isolée** (store mémoire, utilisateur synthétique, aucun accès
  PostgreSQL ni au corpus) : les cinq routes ont été exercées en HTTP réel
  (`POST`, `GET` liste, `GET` scope, `GET` global, `DELETE`) et chaque
  code de statut observé correspond au contrat. L'ancre créée porte son
  cycle d'historique et le verdict `target_existence: verified`.
- **Conteneur de production** (`ethan-api`, image reconstruite) : les cinq
  routes sont **exposées** (OpenAPI) et la **porte d'authentification
  répond 401** sur les cinq, sans jeton.
- **E2E authentifié sur la production** : **NOT_VERIFIED** — aucun
  identifiant opérateur autorisé n'est disponible dans cet environnement.
  Aucun jeton n'a été fabriqué avec le secret du serveur : ce serait
  contourner les protections. La validation E2E reste à faire par
  l'opérateur avec ses identifiants.

## 17. Anomalies hors périmètre (documentées, non traitées)

| # | Anomalie | Suite |
|---|---|---|
| **H0** | **Réinitialisation complète du dépôt par un processus externe** (§11.1) : `.git` supprimé et recréé, branche `master` sans commit, historique et stash perdus, 4172 fichiers indexés comme nouveaux. Fichiers de travail intacts. | **Critique — décision opérateur requise** ; aucune réparation tentée (interdit par la mission) |
| H1 | 119 suppressions `daena/` staged par un processus externe (fichiers présents sur le disque) | Signalée — restauration à décider par l'opérateur |
| H2 | Le rôle `api-key` n'a aucune permission RBAC : les routes d'ancrage sont réservées aux sessions humaines | Signalée — un mécanisme par portée existe (`require_memory_scope`, P2.8.3) mais n'a pas été appliqué ici |
| H3 | Le résolveur des documents d'ingénierie parcourt le vault (≈ 0,5 s par ancrage) | Acceptable pour une opération rare ; optimisation possible |
| H4 | `ResourceRegistry` non branché sur le store partagé : le domaine `resources` est vide en production | P2.8.6 |
| H5 | Sessions archivées non persistées : source `SESSION` non résolvable | P2.8.7 |
| H6 | `KnowledgeManager` et le pipeline RAG ne sont pas branchés sur les ancres | P2.8.3 → P2.8.8 |

## 18. Statut réel de P2.8.2 après consolidation

| Statut | Éléments |
|---|---|
| **IMPLEMENTED** | modèle à cycles, service, validation symétrique, résolution d'existence, section critique, inventaire honesté, routes et traduction d'erreurs |
| **TESTED** | 48 tests Core + 17 tests API ; non-régression 960 + 373 |
| **RUNTIME_VALIDATED** | cinq routes en HTTP réel sur instance isolée ; exposition et porte 401 sur le conteneur de production |
| **E2E_VALIDATED** | — (aucun identifiant opérateur autorisé ; non contourné) |
| **PARTIAL** | isolation : disponible et testée dans le service, **non appliquée** aux managers Core ; aucune ancre réelle en production |
| **BLOCKED** | aucun défaut du périmètre ; le seul blocage est l'absence d'identifiant opérateur pour l'E2E production |
| **NOT_VERIFIED** | E2E production authentifié ; exploitation réelle des ancres par `KnowledgeManager` / RAG |

**Porte de sortie** : les défauts relevant du périmètre de P2.8.2 sont
corrigés, testés et documentés. La validation E2E authentifiée en
production reste impossible sans identifiant opérateur autorisé — elle est
signalée explicitement, sans contournement. **P2.8.3 n'est pas
engagée.**
