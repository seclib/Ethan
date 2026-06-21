# Technical Risks — Ethan

> RFC-001 — Analyse des risques techniques
> Date : 2026-06-21

---

## 1. Risques Architecturaux

### R1 — Dualité de code (src/ethan/ vs core/)

**Description :** Le dépôt contient deux systèmes de code parallèles :
- `src/ethan/` — Code historique et legacy (300+ fichiers)
- `core/` — Nouvelles abstractions modernes (agents, llm, events, etc.)

**Risque :** Duplication de logique, incohérences, confusion des développeurs.

**Sévérité :** ÉLEVÉE

**Probabilité :** 90%

**Impact :** 
- Temps de développement augmenté
- Risque de bugs de régression
- Difficulté d'onboarding

**Recommandation :** 
- Définir une stratégie de migration claire
- Créer un mapping src/ethan/ → core/
- Éviter toute nouvelle fonctionnalité dans src/ethan/

---

### R2 — Dépendances optionnelles nombreuses

**Description :** 32 extras optionnels dans pyproject.toml, dont 15 channels de communication.

**Risque :** 
- Résolution de dépendances lente
- Conflits entre versions
- Surface d'attaque étendue

**Sévérité :** MOYENNE

**Probabilité :** 70%

**Impact :**
- CI builds lents (résolution uv.lock)
- Bugs de compatibilité entre extras
- Sécurité (chaque dépendance est un risque)

**Recommandation :**
- Réviser la nécessité de chaque extra
- Regrouper les dépendances peu utilisées
- Audit de sécurité régulier

---

### R3 — Workspace Rust étendu

**Description :** 16 crates Rust dans le workspace.

**Risque :** Temps de compilation excessif, complexité de la gestion des versions.

**Sévérité :** MOYENNE

**Probabilité :** 60%

**Impact :**
- Build CI > 30 minutes
- Dépendances croisées complexes
- Maintenance lourde

**Recommandation :**
- Caching CI (sccache)
- Réduction du nombre de crates si possible
- CI parallélisé

---

## 2. Risques de Sécurité

### S1 — Pas de sandbox

**Description :** Les plugins (browser, terminal) n'ont pas de sandbox d'exécution.

**Risque :** Exécution de code non sécurisé.

**Sévérité :** CRITIQUE

**Probabilité :** 40%

**Impact :**
- Exécution de commandes arbitraires
- Fuite de données
- Compromission du système hôte

**Recommandation :**
- Implémenter un sandbox (Docker ou WASM)
- Restreindre les permissions des plugins
- Audit de sécurité avant activation

---

### S2 — API Keys en mémoire

**Description :** Les clés API (OpenAI, Anthropic, Google) sont chargées en mémoire.

**Risque :** Exposition des secrets via dump mémoire ou crash logs.

**Sévérité :** MOYENNE

**Probabilité :** 50%

**Impact :**
- Vol de credentials API
- Facturation non autorisée

**Recommandation :**
- Utiliser un vault (Hashicorp Vault, env variables)
- Rotation régulière des clés
- Ne pas logger les credentials

---

### S3 — Pas d'audit logging

**Description :** Les actions sensibles (exécution de commandes, accès fichiers) ne sont pas journalisées.

**Risque :** Impossible de tracer une compromission.

**Sévérité :** MOYENNE

**Probabilité :** 30%

**Impact :**
- Pas de forensics possible
- Non-conformité (SOC2, ISO27001)

**Recommandation :**
- Ajouter un audit logger centralisé
- Logger toutes les actions sensibles
- Stocker les logs dans un système immutable

---

## 3. Risques Opérationnels

### O1 — Pas de Kubernetes

**Description :** Aucun support Kubernetes (manifests vides).

**Risque :** Impossible de scaler horizontalement.

**Sévérité :** ÉLEVÉE

**Probabilité :** 80%

**Impact :**
- Pas de déploiement cloud scalable
- Pas de rolling updates
- Pas d'auto-scaling

**Recommandation :**
- Créer manifests K8s (Deployment, Service, Ingress, ConfigMap)
- Helm chart pour déploiement
- HPA pour scaling automatique

---

### O2 — Pas de multi-arch

**Description :** Images Docker uniquement pour amd64.

**Risque :** Impossible de déployer sur ARM (Raspberry Pi, Apple Silicon, NAS).

**Sévérité :** MOYENNE

**Probabilité :** 70%

**Impact :**
- Plateformes exclues
- Pas de déploiement edge

**Recommandation :**
- Build multi-arch avec docker buildx
- CI pour amd64 + arm64

---

### O3 — Pas de healthcheck backend natif

**Description :** Le healthcheck backend dépend de curl dans l'image.

**Risque :** curl n'est pas toujours disponible.

**Sévérité :** FAIBLE

**Probabilité :** 30%

**Impact :**
- Faux négatifs healthcheck
- Restarts inutiles

**Recommandation :**
- Endpoint /health natif dans FastAPI
- Utiliser wget ou python healthcheck

---

## 4. Risques de Qualité

### Q1 — Couverture de tests inconnue

**Description :** 50 dossiers de tests mais couverture non mesurée.

**Risque :** Code non testé en production.

**Sévérité :** ÉLEVÉE

**Probabilité :** 60%

**Impact :**
- Bugs non détectés
- Régressions fréquentes

**Recommandation :**
- Ajouter pytest-cov au CI
- Définir un seuil de couverture minimal (80%)
- Tests d'intégration obligatoires

---

### Q2 — Pas de type checking strict

**Description :** Type checking Python relâché.

**Risque :** Bugs de type en production.

**Sévérité :** MOYENNE

**Probabilité :** 50%

**Impact :**
- Runtime TypeError
- API inconsistencies

**Recommandation :**
- Activer pyright/pylance strict
- Typing obligatoire pour les nouvelles fonctions

---

### Q3 — Documentation éparse

**Description :** La documentation est complète structurellement mais certains modules sont non documentés.

**Risque :** Difficulté d'onboarding et de maintenance.

**Sévérité :** MOYENNE

**Probabilité :** 60%

**Impact :**
- Temps d'onboarding long
- Décisions architecturales non documentées

**Recommandation :**
- ADR pour chaque décision majeure
- Docstrings obligatoires sur toutes les classes publiques

---

## 5. Résumé des Risques

| ID | Risque | Sévérité | Priorité | Recommandation |
|----|--------|----------|----------|----------------|
| R1 | Dualité de code | ÉLEVÉE | P0 | Stratégie de migration |
| R2 | Dépendances nombreuses | MOYENNE | P2 | Révision des extras |
| R3 | Rust workspace large | MOYENNE | P2 | CI caching |
| S1 | Pas de sandbox | CRITIQUE | **P0** | Implémenter sandbox |
| S2 | API Keys en mémoire | MOYENNE | P1 | Vault + rotation |
| S3 | Pas d'audit log | MOYENNE | P1 | Audit logger |
| O1 | Pas de Kubernetes | ÉLEVÉE | **P0** | Manifests K8s |
| O2 | Pas de multi-arch | MOYENNE | P1 | Build multi-arch |
| O3 | Healthcheck basique | FAIBLE | P3 | Endpoint natif |
| Q1 | Couverture tests | ÉLEVÉE | P0 | CI coverage |
| Q2 | Type checking | MOYENNE | P1 | pyright strict |
| Q3 | Documentation | MOYENNE | P2 | ADR + docstrings |

---

## 6. Matrice de Risques

```
CRITIQUE │        S1                      │
         │                                │
 ÉLEVÉE  │ R1  Q1         O1             │
         │                                │
 MOYENNE │ S2  S3  R2  R3  O2  Q2  Q3    │
         │                                │
  FAIBLE │                   O3           │
         └───────────────────────────────────
              FAIBLE   MOYENNE   ÉLEVÉE
                     Probabilité
```

**Actions immédiates (P0) :**
1. **S1** — Sandbox pour plugins (sécurité critique)
2. **O1** — Manifests Kubernetes (scalabilité)
3. **Q1** — Couverture de tests (qualité)
4. **R1** — Stratégie de migration (architecture)

---

## 7. Métriques Clés

| Métrique | Valeur | Cible |
|----------|--------|-------|
| Fichiers Python | ~400 | - |
| Crates Rust | 16 | ≤ 10 |
| Extras Python | 32 | ≤ 20 |
| Services Docker | 10 | ≤ 12 |
| Channels | 15+ | ≤ 8 |
| Tests coverage | ? | ≥ 80% |
| Multi-arch | amd64 only | amd64 + arm64 |
| K8s support | ❌ | ✅ |