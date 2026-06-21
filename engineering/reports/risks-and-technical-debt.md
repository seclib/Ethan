# Risks & Technical Debt — Ethan

> RFC-002 — Analyse des risques et de la dette technique
> Date : 2026-06-21

---

## 1. Technical Debt Inventory

### 1.1 Dualité de Code (Dette Critique)

**Problème :** Le dépôt contient deux systèmes parallèles :
- `src/ethan/` — Code historique (300+ fichiers, 35+ commandes CLI)
- `core/` — Nouvelles abstractions (agents, llm, events, auth, memory)

**Impact :**
- Duplication de logique (EventBus x2, Agent system x2)
- Confusion des développeurs (où ajouter du code ?)
- Maintenance doublée

**Effort estimé de résolution :** 2-3 semaines

### 1.2 Registres Multiples (Dette Significative)

**Problème :** 15 registres dans `src/ethan/core/registry.py` :
- AgentRegistry, EngineRegistry, ChannelRegistry, ToolRegistry
- MemoryRegistry, ModelRegistry, SkillRegistry, SpeechRegistry
- TTSRegistry, BenchmarkRegistry, CompressionRegistry
- ConnectorRegistry, MinerRegistry, RouterPolicyRegistry

**Et aussi dans `core/` :**
- `core/llm/` → ProviderRegistry
- `core/agents/` → AgentRegistry

**Impact :**
- Pas d'interface unifiée pour les registries
- Duplication de code (chaque registry a la même structure)
- Risque d'incohérence entre les registries

**Effort estimé de résolution :** 1 semaine

### 1.3 Agents Littéralement Vides (Dette Significative)

**Problème :** `core/agents/` contient une classe de base et des squelettes, mais :
- Aucun agent n'est intégré au runtime
- Les agents existants dans `src/ethan/agents/` ne sont pas migrés
- Pas de bridge entre les deux systèmes

**Impact :**
- Investissement inutilisable
- Les agents historiques continuent de fonctionner seuls

**Effort estimé de résolution :** 1-2 semaines

### 1.4 SDK Vide (Dette Significative)

**Problème :** `sdk/python/` et `sdk/typescript/` existent mais :
- Le SDK Python est squeletique (client de base)
- Le SDK TypeScript est vide
- Pas de documentation SDK
- Pas de tests SDK

**Impact :**
- Impossible pour des développeurs tiers d'intégrer Jarvis OS
- L'API publique n'a pas de client officiel

**Effort estimé de résolution :** 2-3 semaines

### 1.5 Workers Vides (Dette Moyenne)

**Problème :** `workers/` est un dossier vide.

**Impact :**
- Pas de traitement asynchrone hors du processus principal
- Les tâches longues bloquent le serveur API
- Pas de scaling horizontal possible

**Effort estimé de résolution :** 1 semaine

### 1.6 API Gateway Vide (Dette Faible)

**Problème :** `apps/gateway/` est un dossier vide.

**Impact :**
- Pas de point d'entrée unique pour les APIs externes
- La sécurité est gérée au niveau du backend uniquement

**Effort estimé de résolution :** 2-3 jours

### 1.7 Pas de Rate Limiting (Dette Moyenne)

**Problème :** Aucun rate limiting n'est implémenté.

**Impact :**
- Vulnérabilité aux attaques par déni de service
- Pas de protection contre les abus API
- Pas de quotas par utilisateur

**Effort estimé de résolution :** 2-3 jours

### 1.8 Pas d'Audit Logging (Dette Moyenne)

**Problème :** Les actions sensibles ne sont pas journalisées.

**Impact :**
- Impossible de tracer une compromission
- Non-conformité (SOC2, ISO27001)
- Pas de forensic possible

**Effort estimé de résolution :** 3-4 jours

---

## 2. Security Risks

### 2.1 Pas de Sandbox (Risque Critique)

**Description :** Les plugins (browser, terminal) n'ont pas de sandbox d'exécution.

**Risque :** Exécution de code non sécurisé.

**Impact potentiel :**
- Exécution de commandes arbitraires
- Fuite de données
- Compromission du système hôte

**Recommandation :** Implémenter un sandbox Docker ou WASM. Priorité P0.

### 2.2 API Keys en Mémoire (Risque Significatif)

**Description :** Les clés API (OpenAI, Anthropic, Google) sont chargées en mémoire depuis `.env`.

**Risque :** Exposition des secrets via dump mémoire ou crash logs.

**Recommandation :** Utiliser un vault, rotation régulière des clés. Priorité P1.

### 2.3 Pas de Scanning Sécurité (Risque Significatif)

**Description :** Aucun scan de sécurité n'est effectué sur les images Docker ou les dépendances.

**Risque :** Vulnérabilités non détectées.

**Recommandation :** Intégrer Trivy/Docker Scout dans le CI. Priorité P1.

---

## 3. Operational Risks

### 3.1 Pas de Kubernetes (Risque Élevé)

**Description :** Aucun support Kubernetes. `deploy/kubernetes/` est vide.

**Risque :** Impossible de scaler horizontalement, pas de rolling updates, pas d'auto-scaling.

**Recommandation :** Créer manifests K8s. Priorité P0.

### 3.2 Pas de Multi-Arch (Risque Significatif)

**Description :** Images Docker uniquement pour amd64.

**Risque :** Impossible de déployer sur ARM (Raspberry Pi, Apple Silicon, NAS).

**Recommandation :** Build multi-arch avec docker buildx. Priorité P1.

### 3.3 Pas de Backup Stratégie (Risque Significatif)

**Description :** Aucune stratégie de backup pour les 14 volumes persistants.

**Risque :** Perte de données définitive en cas de panne.

**Recommandation :** Scripts de backup + tests de restauration. Priorité P1.

---

## 4. Quality Debt

### 4.1 Couverture de Tests Inconnue (Dette Critique)

**Description :** 619 fichiers de test mais couverture non mesurée.

**Risque :** Code non testé en production.

**Recommandation :** Ajouter pytest-cov au CI, seuil à 80%. Priorité P0.

### 4.2 Type Checking Relâché (Dette Significative)

**Description :** Type checking Python non strict.

**Risque :** Bugs de type en production.

**Recommandation :** Activer pyright strict. Priorité P1.

### 4.3 Documentation Partielle (Dette Moyenne)

**Description :** Certains modules sont non documentés.

**Risque :** Difficulté d'onboarding et de maintenance.

**Recommandation :** ADR + docstrings obligatoires. Priorité P2.

### 4.4 Pas de Benchmarks Automatisés (Dette Moyenne)

**Description :** Les benchmarks existent (`src/ethan/bench/`) mais ne sont pas automatisés dans le CI.

**Risque :** Régression de performance non détectée.

**Recommandation :** Intégrer les benchmarks dans le CI. Priorité P2.

---

## 5. Debt Quantification

### 5.1 Effort Total Estimé

| Catégorie | Effort | Priorité |
|-----------|--------|----------|
| Dualité de code | 2-3 sem | P0 |
| Sandbox sécurité | 1-2 sem | P0 |
| Kubernetes | 1-2 sem | P0 |
| Couverture tests | 1 sem | P0 |
| Registres unifiés | 1 sem | P1 |
| Agents runtime | 1-2 sem | P1 |
| SDK public | 2-3 sem | P1 |
| Multi-arch | 3-4 jours | P1 |
| Audit logging | 3-4 jours | P1 |
| API Gateway | 2-3 jours | P2 |
| Rate limiting | 2-3 jours | P2 |
| Documentation | 1 sem | P2 |
| Benchmarks CI | 2-3 jours | P2 |
| **Total** | **~12-18 sem** | |

### 5.2 Debt Distribution

```
P0 (Critical)  ■■■■■■■■■■ 40%
P1 (High)      ■■■■■■■    30%
P2 (Medium)    ■■■■        20%
P3 (Low)       ■■          10%
```

---

## 6. Remediation Roadmap

### Phase 1 — Stabilisation (Semaine 1-2)
- [ ] P0: Sandbox pour plugins
- [ ] P0: Couverture de tests (CI + seuil)
- [ ] P0: Stratégie de migration src/ → core/

### Phase 2 — Scalabilité (Semaine 3-4)
- [ ] P0: Manifests Kubernetes
- [ ] P1: Multi-arch Docker
- [ ] P1: Workers asynchrones

### Phase 3 — Qualité (Semaine 5-6)
- [ ] P1: Registres unifiés
- [ ] P1: Agents runtime integration
- [ ] P1: Type checking strict

### Phase 4 — Extensibilité (Semaine 7-8)
- [ ] P1: SDK public
- [ ] P2: API Gateway
- [ ] P2: Rate limiting

### Phase 5 — Maturité (Semaine 9-10)
- [ ] P1: Audit logging
- [ ] P2: Documentation
- [ ] P2: Benchmarks CI

---

## 7. Métriques Clés

| Métrique | Valeur | Cible |
|----------|--------|-------|
| Fichiers Python | ~400 | ≤ 300 |
| Crates Rust | 16 | ≤ 10 |
| Extras Python | 32 | ≤ 20 |
| Services Docker | 10 | ≤ 12 |
| Registres | 17 | ≤ 5 |
| Tests coverage | ? | ≥ 80% |
| Multi-arch | amd64 | amd64 + arm64 |
| K8s support | ❌ | ✅ |
| SDK public | ❌ | ✅ |
| Audit logging | ❌ | ✅ |
| Rate limiting | ❌ | ✅ |
| Sandbox | ❌ | ✅ |
| Security scanning | ❌ | ✅ |