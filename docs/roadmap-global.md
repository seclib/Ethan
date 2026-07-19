# Roadmap Globale — Suivi des Actions Architecture

**Date de création** : 2026-07-19  
**Statut** : En cours  
**Propriétaire** : Équipe Architecture + Core  
**Révision** : Hebdomadaire

---

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                   ETHAN Architecture Roadmap                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  P0 — Actions Critiques (Immédiat)                          │
│  ├─ ✅ P0-1 : Corriger healthchecks Docker                 │
│  ├─ ⏳ P0-2 : Mettre à jour README.md                      │
│  ├─ ✅ P0-3 : Ajouter logs dans ./ethan up                 │
│  ├─ ✅ P0-4 : Configurer PYTHONPATH                        │
│  └─ ✅ P0-5 : Améliorer ./ethan status                     │
│                                                             │
│  P1 — Actions Importantes (Court terme)                     │
│  ├─ ⏳ P1-1 : Décider sort de runtime/ et rust/            │
│  ├─ ⏳ P1-2 : Éliminer les doublons                        │
│  ├─ ⏳ P1-3 : Nettoyer dossiers vides                      │
│  └─ ⏳ P1-4 : Clarifier README.md                          │
│                                                             │
│  P2 — Améliorations (Moyen terme)                           │
│  ├─ ⏳ P2-1 : Installer package éditable                   │
│  ├─ ⏳ P2-2 : Ajouter tests d'intégration                  │
│  └─ ⏳ P2-3 : Ajouter métriques Prometheus                 │
│                                                             │
│  P3 — Optimisations (Long terme)                            │
│  ├─ ⏳ P3-1 : Clarifier Go vs Python                       │
│  ├─ ⏳ P3-2 : Décider sort de jarvis-OS/                   │
│  ├─ ⏳ P3-3 : Ajouter OpenTelemetry                        │
│  ├─ ⏳ P3-4 : Ajouter Grafana                              │
│  └─ ⏳ P3-5 : CI/CD complet                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Légende

| Icône | Statut | Description |
|-------|--------|-------------|
| ✅ | **Corrigé** | Action implémentée et déployée |
| ⏳ | **En cours** | En attente de décision ou d'implémentation |
| 🔄 | **En progression** | Implémentation en cours |
| ⚠️ | **Bloqué** | Bloqué par une décision externe |
| ❌ | **Annulé** | Action annulée |

---

## P0 — Actions Critiques (Immédiat)

**Objectif** : Corriger les problèmes bloquants  
**Deadline** : 2026-07-19  
**Statut global** : 🟡 Partiellement complété

### P0-1 : Corriger healthchecks Docker

- **Fichier** : `docker-compose.yml`
- **Priorité** : P0
- **Statut** : ✅ Corrigé
- **Responsable** : Équipe Core
- **Impact** : Élevé (bloquant)
- **Validation** : `docker compose ps --services --filter "health=healthy"`
- **Notes** : Corrigé lors de la session précédente

### P0-2 : Mettre à jour README.md

- **Fichier** : `README.md`
- **Priorité** : P0
- **Statut** : ⏳ En attente
- **Responsable** : Équipe Documentation
- **Impact** : Élevé (documentation)
- **Actions** :
  - [ ] Corriger section "API exposée" (gRPC → HTTP)
  - [ ] Corriger section "Boot Lifecycle" (/health)
  - [ ] Ajouter section "Architecture réelle"
- **Notes** : Requiert une relecture complète du README

### P0-3 : Ajouter logs explicites dans `./ethan up`

- **Fichier** : `scripts/cmd-up.sh`
- **Priorité** : P0
- **Statut** : ✅ Corrigé
- **Responsable** : Équipe Core
- **Impact** : Élevé (opérationnel)
- **Validation** : `./ethan up` affiche les logs
- **Notes** : Implémenté lors de la session précédente

### P0-4 : Configurer PYTHONPATH dans launcher

- **Fichier** : `ethan`
- **Priorité** : P0
- **Statut** : ✅ Corrigé
- **Responsable** : Équipe Core
- **Impact** : Élevé (bloquant)
- **Validation** : `./ethan python3 -c "import core.kernel"`
- **Notes** : Implémenté lors de la session précédente

### P0-5 : Améliorer `./ethan status`

- **Fichier** : `scripts/cmd-status.sh`
- **Priorité** : P0
- **Statut** : ✅ Corrigé
- **Responsable** : Équipe Core
- **Impact** : Élevé (opérationnel)
- **Validation** : `./ethan status` affiche les tests de connectivité
- **Notes** : Implémenté lors de la session précédente

### Progression P0

```
5/5 actions identifiées
4/5 actions implémentées
0/5 actions testées en production
0/5 actions validées par l'équipe

⏱ Temps estimé restant : 2-4h
```

---

## P1 — Actions Importantes (Court terme)

**Objectif** : Décisions structurelles et nettoyage  
**Deadline** : 2026-07-26  
**Statut global** : ⏳ En attente de décision

### P1-1 : Décider du sort de `runtime/` et `rust/`

- **Fichiers** : `runtime/`, `rust/`
- **Priorité** : P1
- **Statut** : ⏳ En attente
- **Responsable** : Architecture Team
- **Impact** : Moyen (dette technique)
- **Options** :
  - [ ] Option A : Supprimer
  - [ ] Option B : Intégrer
  - [ ] Option C : Documenter et isoler
- **Deadline décision** : 2026-07-26
- **Notes** : Requiert une analyse des imports

### P1-2 : Éliminer les doublons

- **Fichiers** : `core/orchestration/`, `core/orchestrator/`, `core/registry/module.py`, `core/registry/module_registry.py`
- **Priorité** : P1
- **Statut** : ⏳ En attente
- **Responsable** : Architecture Team
- **Impact** : Moyen (dette technique)
- **Options** :
  - [ ] Option A : Fusionner
  - [ ] Option B : Renommer et clarifier
  - [ ] Option C : Supprimer le doublon
- **Deadline décision** : 2026-07-26
- **Notes** : Requiert une analyse des imports

### P1-3 : Nettoyer les dossiers vides

- **Fichiers** : `core/agents/`, `core/pkg/`, `__pycache__/`
- **Priorité** : P1
- **Statut** : ⏳ En attente
- **Responsable** : Équipe Core
- **Impact** : Faible (propreté)
- **Actions** :
  - [ ] Supprimer `core/agents/`
  - [ ] Supprimer `core/pkg/`
  - [ ] Supprimer tous les `__pycache__/`
- **Deadline** : 2026-07-26
- **Notes** : Action rapide, peut être faite immédiatement

### P1-4 : Clarifier la documentation README.md

- **Fichier** : `README.md`
- **Priorité** : P1
- **Statut** : ⏳ En attente
- **Responsable** : Équipe Documentation
- **Impact** : Moyen (documentation)
- **Actions** :
  - [ ] P1-4.1 : Corriger section "API exposée"
  - [ ] P1-4.2 : Corriger section "Boot Lifecycle"
  - [ ] P1-4.3 : Ajouter section "Architecture réelle"
- **Deadline** : 2026-07-26
- **Notes** : Complémentaire à P0-2

### Progression P1

```
4/4 actions identifiées
0/4 actions décidées
0/4 actions implémentées

⏱ Temps estimé restant : 1-2 jours
```

---

## P2 — Améliorations (Moyen terme)

**Objectif** : Améliorer la qualité du code et ajouter les tests  
**Deadline** : 2026-08-02  
**Statut global** : ⏳ En attente

### P2-1 : Installer le package en mode éditable

- **Fichier** : `pyproject.toml`
- **Priorité** : P2
- **Statut** : ⏳ En attente
- **Responsable** : Équipe DevOps
- **Impact** : Moyen (maintenabilité)
- **Actions** :
  - [ ] Installer `pip install -e .`
  - [ ] Supprimer `sys.path.insert()` dans `interfaces/api/main.py`
  - [ ] Mettre à jour Dockerfiles
  - [ ] Vérifier tous les imports
- **Deadline** : 2026-08-02
- **Notes** : Débloque la suppression du `sys.path` hacking

### P2-2 : Ajouter des tests d'intégration

- **Fichier** : `tests/`
- **Priorité** : P2
- **Statut** : ⏳ En attente
- **Responsable** : Équipe Core
- **Impact** : Élevé (qualité)
- **Actions** :
  - [ ] Créer `tests/test_healthchecks.py`
  - [ ] Créer `tests/test_imports.py`
  - [ ] Créer `tests/test_dependencies.py`
  - [ ] Ajouter la CI/CD
- **Deadline** : 2026-08-02
- **Notes** : Nécessite P0 terminé

### P2-3 : Ajouter des métriques Prometheus

- **Fichier** : `core/telemetry/`, `infrastructure/prometheus/`
- **Priorité** : P2
- **Statut** : ⏳ En attente
- **Responsable** : Équipe DevOps
- **Impact** : Moyen (observabilité)
- **Actions** :
  - [ ] Ajouter endpoint `/metrics` dans `interfaces/api/main.py`
  - [ ] Créer `infrastructure/prometheus/prometheus.yml`
  - [ ] Ajouter Prometheus dans `docker-compose.yml`
- **Deadline** : 2026-08-02
- **Notes** : Requiert des ressources supplémentaires

### Progression P2

```
3/3 actions identifiées
0/3 actions implémentées

⏱ Temps estimé restant : 2-3 jours
```

---

## P3 — Optimisations (Long terme)

**Objectif** : Clarifier la stratégie technique et l'observabilité  
**Deadline** : 2026-08-16  
**Statut global** : ⏳ En attente

### P3-1 : Clarifier la stratégie Go vs Python pour Core

- **Fichiers** : `core/main.go`, `core/go.mod`, `core/kernel.py`, `core/bootstrap.py`
- **Priorité** : P3
- **Statut** : ⏳ En attente
- **Responsable** : Architecture Team + CTO
- **Impact** : Élevé (architectural)
- **Options** :
  - [ ] Option A : Tout migrer vers Python
  - [ ] Option B : Tout migrer vers Go
  - [ ] Option C : Cohabitation (recommandé)
- **Deadline décision** : 2026-08-02
- **Notes** : Décision stratégique majeure

### P3-2 : Décider du sort de `jarvis-OS/`

- **Fichier** : `jarvis-OS/`
- **Priorité** : P3
- **Statut** : ⏳ En attente
- **Responsable** : Architecture Team
- **Impact** : Moyen (dette technique)
- **Options** :
  - [ ] Option A : Ancien projet (legacy)
  - [ ] Option B : Projet lié (évolution)
  - [ ] Option C : Projet séparé (monorepo)
- **Deadline décision** : 2026-08-02
- **Notes** : Requiert une analyse approfondie

### P3-3 : Ajouter des traces OpenTelemetry

- **Fichier** : `core/telemetry/`, `interfaces/api/`
- **Priorité** : P3
- **Statut** : ⏳ En attente
- **Responsable** : Équipe DevOps
- **Impact** : Moyen (observabilité)
- **Actions** :
  - [ ] Ajouter OpenTelemetry dans `core/`
  - [ ] Ajouter FastAPIInstrumentor dans `interfaces/api/main.py`
  - [ ] Ajouter Jaeger dans `docker-compose.yml`
- **Deadline** : 2026-08-16
- **Notes** : Complémentaire à P2-3

### P3-4 : Améliorer l'observabilité avec Grafana

- **Fichier** : `infrastructure/grafana/`
- **Priorité** : P3
- **Statut** : ⏳ En attente
- **Responsable** : Équipe DevOps
- **Impact** : Moyen (observabilité)
- **Actions** :
  - [ ] Créer dashboard Grafana
  - [ ] Ajouter Grafana dans `docker-compose.yml`
  - [ ] Créer datasources Prometheus
- **Deadline** : 2026-08-16
- **Notes** : Complémentaire à P2-3 et P3-3

### P3-5 : CI/CD complet

- **Fichier** : `.github/workflows/`, `Makefile`
- **Priorité** : P3
- **Statut** : ⏹ En attente
- **Responsable** : Équipe DevOps
- **Impact** : Élevé (qualité)
- **Actions** :
  - [ ] Créer `.github/workflows/ci.yml`
  - [ ] Ajouter cibles Makefile
  - [ ] Intégrer tests et linting
- **Deadline** : 2026-08-16
- **Notes** : Requiert P2-2 terminé

### Progression P3

```
5/5 actions identifiées
0/5 actions décidées
0/5 actions implémentées

⏱ Temps estimé restant : 3-4 semaines
```

---

## Vue d'ensemble par priorité

```
P0 — Critiques (Immédiat)
├─ ✅ 4/5 actions complétées
├─ ⏳ 1/5 actions en cours
└─ 🎯 Impact : Bloquant

P1 — Importantes (Court terme)
├─ ⏳ 4/4 actions en attente de décision
└─ 🎯 Impact : Dette technique

P2 — Améliorations (Moyen terme)
├─ ⏳ 3/3 actions en attente
└─ 🎯 Impact : Qualité

P3 — Optimisations (Long terme)
├─ ⏳ 5/5 actions en attente
└─ 🎯 Impact : Architecture
```

---

## Actions immédiates

### Cette semaine (2026-07-19 → 2026-07-26)

1. **P0-2** : Mettre à jour README.md (Documentation)
2. **P1-3** : Nettoyer dossiers vides (Core)
3. **P1-1** : Analyser `runtime/` et `rust/` (Architecture)
4. **P1-2** : Analyser doublons (Architecture)

### Semaine prochaine (2026-07-26 → 2026-08-02)

1. **P2-1** : Installer package éditable (DevOps)
2. **P1-4** : Finaliser README.md (Documentation)
3. **P2-2** : Créer tests d'intégration (Core)
4. **P3-1** : Décider Go vs Python (Architecture)
5. **P3-2** : Décider sort de `jarvis-OS/` (Architecture)

---

## Métriques

### Temps estimé par priorité

| Priorité | Actions | Temps total | Temps par action |
|----------|---------|-------------|------------------|
| P0 | 5 | 2-4h | 30min-1h |
| P1 | 4 | 1-2 jours | 3-6h |
| P2 | 3 | 2-3 jours | 1-2 jours |
| P3 | 5 | 3-4 semaines | 3-5 jours |

### Temps réellement passé

| Priorité | Temps passé | Temps restant |
|----------|-------------|---------------|
| P0 | 4h | 1-2h (tests + README) |
| P1 | 0h | 1-2 jours |
| P2 | 0h | 2-3 jours |
| P3 | 0h | 3-4 semaines |

---

## Décisions en attente

### Architecture Team

1. **P1-1** : Sort de `runtime/` et `rust/` — Deadline 2026-07-26
2. **P1-2** : Doublons (`orchestration/` vs `orchestrator/`) — Deadline 2026-07-26
3. **P3-1** : Stratégie Go vs Python — Deadline 2026-08-02
4. **P3-2** : Sort de `jarvis-OS/` — Deadline 2026-08-02

### Équipe Core

1. **P0-2** : Mise à jour README.md — Deadline 2026-07-26
2. **P2-1** : Package éditable — Deadline 2026-08-02

### Équipe Documentation

1. **P0-2** : Correction README.md — Deadline 2026-07-26
2. **P1-4** : Clarification README.md — Deadline 2026-07-26

### Équipe DevOps

1. **P2-1** : Package éditable — Deadline 2026-08-02
2. **P2-3** : Prometheus — Deadline 2026-08-02
3. **P3-3** : OpenTelemetry — Deadline 2026-08-16
4. **P3-4** : Grafana — Deadline 2026-08-16
5. **P3-5** : CI/CD — Deadline 2026-08-16

---

##historique des modifications

| Date | Version | Auteur | Description |
|------|---------|--------|-------------|
| 2026-07-19 | 1.0 | Architecture Team | Création initiale |

---

## Liens utiles

- [Audit d'architecture complet](architecture-audit.md)
- [Roadmap P0](roadmap-P0.md)
- [Roadmap P1](roadmap-P1.md)
- [Roadmap P2](roadmap-P2.md)
- [Roadmap P3](roadmap-P3.md)
- [Service Orchestration](service-orchestration.md)
- [Audit `./ethan up`](audit-ethan-up.md)

---

**Dernière mise à jour** : 2026-07-19  
**Prochaine révision** : 2026-07-26