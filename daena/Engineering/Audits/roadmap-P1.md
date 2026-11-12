# Roadmap P1 — Actions Importantes (Court terme)

**Objectif** : Décisions structurelles et nettoyage  
**Date de création** : 2026-07-19  
**Statut** : ✅ Complété  
**Propriétaire** : Équipe Core + Architecture

---

## P1-1 : Décider du sort de `runtime/` et `rust/`

**Fichiers concernés** :
- `runtime/` (racine)
- `rust/` (racine)

### Statut

- [x] **Identifié** (2026-07-19)
- [x] **Analysé** (usage, imports, dépendances)
- [x] **Décidé** : Option C — Documenter et isoler (legacy/README.md créé)
- [x] **Implémenté** : README.md créé pour documenter le statut legacy
- [x] **Documenté**

**Décision** : Les dossiers `runtime/` et `rust/` sont conservés en tant que code legacy avec documentation claire. Pas d'imports détectés dans le code principal.

---

## P1-2 : Éliminer les doublons

**Fichiers concernés** :
- `core/orchestration/` et `core/orchestrator/`

### Statut

- [x] **Identifié** (2026-07-19)
- [x] **Analysé** (contenu, imports, dépendances)
- [x] **Décidé** : Fusion effectuée — `core/orchestration/` fusionné dans `core/orchestrator/`
- [x] **Implémenté** : Fichiers fusionnés, imports mis à jour
- [x] **Documenté**

**Note** : `core/registry/module.py` et `core/registry/module_registry.py` - le premier est utilisé comme helpers, le second comme registry principal. Aucune action requise.

---

## P1-3 : Nettoyer les dossiers vides

**Fichiers concernés** :
- `core/agents/` - **Note** : Contient du code actif (autonomy.py, base.py, etc.), PAS un dossier vide
- `core/pkg/` - **Note** : Contient du code actif (events/, types/), PAS un dossier vide
- `core/cmd/`, `core/proto/`, `core/tests/`, `core/deployment/kubernetes/`, `core/deployment/postgres/` - **VIDES** et supprimés

### Statut

- [x] **Identifié** (2026-07-19)
- [x] **Vérifié** : 
  - `core/agents/` et `core/pkg/` contiennent du code actif → conservés
  - Dossiers vides identifiés et supprimés
- [x] **Implémenté** :
  - `core/cmd/` supprimé (vide)
  - `core/proto/` supprimé (vide)
  - `core/tests/` supprimé (vide)
  - `core/deployment/kubernetes/` supprimé (vide)
  - `core/deployment/postgres/` supprimé (vide)

---

## P1-4 : Clarifier la documentation README.md

**Fichier concerné** : `README.md`

### Statut

- [x] **Identifié** (2026-07-19)
- [x] **Corrigé** : gRPC → HTTP REST (port 8000), health endpoint mis à jour
- [x] **Implémenté** :
  - Ligne 28 : `**HTTP REST** (port 8000)` — corrigé
  - Ligne 557 : Endpoint `/health` sur port 8000 — corrigé
- [x] **Validé**

---

## Résumé P1

| ID | Action | Priorité | Fichier | Statut |
|----|--------|----------|---------|--------|
| P1-1 | Documenter `runtime/` et `rust/` | **P1** | `runtime/`, `rust/` | ✅ Complété |
| P1-2 | Éliminer les doublons | **P1** | `core/orchestration/` | ✅ Complété |
| P1-3 | Nettoyer dossiers vides | **P1** | `core/cmd/`, `core/proto/`, etc. | ✅ Complété |
| P1-4 | Clarifier README.md | **P1** | `README.md` | ✅ Complété |

---

**Dernière mise à jour** : 2026-07-19