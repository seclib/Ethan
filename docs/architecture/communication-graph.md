# Graphe de Communication ETHAN — Analyse SRE

**Auteur** : Distributed Systems Architect  
**Date** : 2026-07-20  

---

## 1. Graphe logique complet

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            LÉGENDE                                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ───► Liaison active et fonctionnelle (testée ou observable)                     │
│  - - ► Liaison théorique (non testée, peut être morte)                          │
│  ~~~► Liaison documentée mais absente du code                                   │
│  [X] Liaison cassée / jamais implémentée                                        │
│  [SPOF] Single Point of Failure                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘


                              ┌──────────────────────────────┐
                              │       docker compose          │
                              │    (orchestrateur hôte)       │
                              ├──────────────────────────────┤
                              │  systemd : ethan-core.service │
                              └─────────┬────────────────────┘
                                        │
                  ┌─────────────────────┼────────────────────────┐
                  │                     │                         │
                  ▼                     ▼                         ▼
        ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
        │    INTERFACES    │  │    CORE KERNEL    │  │      PERSISTENCE     │
        │                 │  │                  │  │                      │
        │ CLI ───► NATS   │  │ kernel.py ──► NATS│  │ redis ──► stockage   │
        │ WebUI ──► HTTP  │  │ bootstrap.py     │  │ postgres ──► stockage│
        │ API ────► NATS  │  │ scheduler.py     │  │                  │
        │        ──► HTTP │  │ modules_launcher  │  │                  │
        └─────────────────┘  └──────────────────┘  └──────────────────────┘


                              ┌──────────────────────────────┐
                              │            NATS               │
                              │        (Event Bus)            │
                              │  ethan.module.*               │
                              │  ethan.kernel.*               │
                              │  ethan.interface.*            │
                              │  ethan.goals.*                │
                              │  ethan.plan.*                 │
                              └──────────┬───────────────────┘
                                         │
          ┌──────────────────────────────┼──────────────────────────┐
          │                ┌─────────────┴──────────────┐          │
          ▼                ▼                            ▼          ▼
┌─────────────────┐ ┌──────────────────────┐ ┌──────────────────┐ ┌──────────────┐
│   MODULES       │ │   API Gateway        │ │   Prometheus     │ │   Ollama     │
│                 │ │                      │ │                  │ │   (profile)  │
│ executive ──►   │ │ main.py              │ │ /metrics ──►     │ │              │
│ planner   ──►   │ │ /v1/health           │ │  NATS telemetry  │ │ API HTTP     │
│ memory    ──►   │ │ /health/detailed     │ │                  │ │              │
│ reflective──►   │ │ /api/v1/events       │ │                  │ │              │
│ learning  ──►   │ │                      │ │                  │ │              │
│ autonomy  ──►   │ │ routiers :           │ │                  │ │              │
│ metacogn. ──►   │ │ message, state,      │ │                  │ │              │
└─────────────────┘ │ internal             │ └──────────────────┘ └──────────────┘
                    └──────────────────────┘
```

---

## 2. Tableau des connexions

### 2.1 Connexions actives (fonctionnelles)

| # | Initiateur | Écouteur | Protocole | Sujet / Endpoint | Testée ? | Documentée ? |
|---|-----------|----------|-----------|-----------------|----------|-------------|
| 1 | CLI (`ethan`) | NATS | NATS TCP | `ethan.interface.command` | ❌ | ❌ |
| 2 | API Gateway | NATS | NATS TCP | `ethan.interface.*` | ✅ | ❌ |
| 3 | Kernel | NATS | NATS TCP | `kernel.>`, `goal.>`, `module.>`, `intent.>` | ✅ | ✅ |
| 4 | Modules (x7) | NATS | NATS TCP | `ethan.module.*` | ✅ | ✅ |
| 5 | Kernel | Redis | Redis TCP (RESP) | `kernel:state:*` | ✅ | ❌ |
| 6 | API | Redis | Redis TCP (RESP) | Session cache | ❌ | ❌ |
| 7 | Kernel | PostgreSQL | PostgreSQL TCP | `events`, `goals`, `snapshots` | ✅ | ❌ |
| 8 | API | PostgreSQL | PostgreSQL TCP | State queries | ❌ | ❌ |
| 9 | Prometheus | API (scrape) | HTTP | `GET /metrics` | ❌ | ❌ |
| 10 | WebUI (ui) | API | HTTP | `GET /api/*` | ✅ | ✅ |
| 11 | API | NATS | NATS TCP | Healthcheck NATS | ✅ (health) | ❌ |
| 12 | Kernel | NATS | NATS TCP | Healthcheck NATS | ✅ (health) | ❌ |

### 2.2 Connexions théoriques (non testées, peut-être mortes)

| # | Initiateur | Écouteur | Protocole | Statut |
|---|-----------|----------|-----------|--------|
| 13 | CLI Python (`interfaces/cli/main.py`) | NATS | NATS TCP | ❌ Jamais démarré par `ethan up` |
| 14 | Desktop (Tauri) | API | HTTP | ❌ Jamais démarré |
| 15 | Channels (Telegram) | NATS | NATS TCP | ❌ Non implémenté |
| 16 | MCP Server | API | HTTP/SSE | ❌ Non implémenté |
| 17 | Ollama | API | HTTP | ⚠️ Profile `llm` uniquement |
| 18 | Qdrant | API | gRPC/HTTP | ⚠️ docker-compose.dev.yml uniquement |

### 2.3 Connexions documentées mais absentes du code

| # | Initiateur | Écouteur | Protocole | Problème |
|---|-----------|----------|-----------|----------|
| 19 | Kernel Go (`core/kernel-go/main.go`) | NATS | NATS TCP | **Jamais construit ni déployé** — code legacy inutilisé |
| 20 | Runtime Go (`runtime/`) | NATS | NATS TCP | **Dossier mort** — README le confirme |
| 21 | Rust crates | — | FFI/Python | **Aucun pont Python/Rust** dans le code |

### 2.4 Connexions cassées

| # | Initiateur | Écouteur | Problème |
|---|-----------|----------|----------|
| 22 | API (avant) | HTTP `/health` | **Endpoint `/v1/health` n'existait pas** → ✅ Corrigé |
| 23 | Modules (avant) | NATS | **Healthcheck ne faisait qu'importer nats** → ✅ Corrigé |
| 24 | Kernel bootstrap | NATS | **Aucun retry** → ✅ Corrigé (10 tentatives avec backoff) |

---

## 3. Points de rupture

### 3.1 SPOF (Single Points of Failure)

| Composant | Raison | Impact |
|-----------|--------|--------|
| **NATS** | Tout le trafic event-driven passe par NATS | Coupure totale du système |
| **PostgreSQL** | Source de vérité pour les états persistants | Perte des goals, événements, snapshots |
| **Docker Daemon** | Tous les services tournent dans des conteneurs | Arrêt total |
| **Docker Hub** | Pull des images de base au premier démarrage | Build impossible sans cache |

### 3.2 Boucles

| # | Boucle | Risque |
|---|--------|--------|
| 25 | `api` → `depends_on: postgres:healthy` → `redis:healthy` → `nats:healthy` | Dépendance en cascade OK |
| 26 | `ui` → `depends_on: api:healthy` | L'API dépend de postgres+redis+nats → chaîne cohérente |
| 27 | `kernel` → `depends_on: postgres:healthy` → `redis:healthy` → `nats:healthy` | ✅ Pas de boucle |

### 3.3 Appels redondants

| # | Redondance | Explication |
|---|-----------|-------------|
| 28 | Kernel connecte NATS **et** Redis **et** PostgreSQL | Nécessaire (tiers différents) |
| 29 | API connecte NATS **et** Redis **et** PostgreSQL | Nécessaire (rôles différents) |
| 30 | Modules connectent NATS **et** Redis **et** PostgreSQL | Nécessaire (modules cognitive) |

---

## 4. Dépendances non fonctionnelles

### 4.1 Composants jamais contactés

| Composant | Dans le code ? | Contacté par ? | Raison |
|-----------|---------------|----------------|--------|
| Qdrant | docker-compose.dev.yml | Aucun service | Optionnel (vector store) |
| Ollama | docker-compose.yml (profile llm) | API (`/v1/chat`) | Optionnel (LLM local) |
| Grafana | infrastructure/grafana/ | Prometheus | Pas dans docker-compose.yml |
| Jaeger | Pas implémenté | — | Futur (tracing distribué) |
| Channels (Telegram) | interfaces/channels/ | NATS | Non connecté |
| Desktop | interfaces/desktop/ | API HTTP | Non lancé |

### 4.2 Dépendances inutilisées dans le code

| Dépendance | Fichier | Raison |
|-----------|---------|--------|
| `core/autonomy/healing.py` | importé dans bootstrap.py | Jamais instancié |
| `core/autonomy/idle.py` | importé dans bootstrap.py | Jamais instancié |
| `core/autonomy/scheduler.py` (PriorityScheduler) | importé dans bootstrap.py | Jamais instancié |
| `core/autonomy/weakness.py` (WeaknessDetector) | importé dans bootstrap.py | Jamais instancié |
| `core/autonomy/curiosity.py` (CuriosityEngine) | importé dans bootstrap.py | Jamais instancié |
| `core/autonomy/environment.py` (EnvironmentAnalyzer) | importé dans bootstrap.py | Jamais instancié |
| `core/learning/detector.py` (PatternDetector) | instancié mais jamais utilisé | Paramètre threshold inchangé |
| `core/learning/generator.py` (RuleGenerator) | instancié mais jamais utilisé | Non connecté |
| `core/learning/modeler.py` (SelfModelUpdater) | instancié mais jamais utilisé | Non connecté |

---

## 5. Résumé des statuts par connexion

```
Connexions totales recensées :  30
Connexions actives :             12  (40%)
Connexions théoriques :          6   (20%)
Connexions documentées absentes : 3   (10%)
Connexions cassées (corrigées) : 3   (10%)
Connexions jamais contactées :   6   (20%)
```

---

## 6. Risques identifiés

| Risque | Type | Impact | Probabilité |
|--------|------|--------|-------------|
| NATS down → tout le système paralysé | SPOF | Critique | Faible |
| PostgreSQL down → perte des états persistants | SPOF | Élevé | Faible |
| Docker Hub inaccessible au démarrage | Lock-in | Bloquant | Moyenne |
| Qdrant/Ollama jamais contactés | Ressources gaspillées | Faible | Élevée |
| Code mort dans bootstrap.py (6 classes inutilisées) | Dette technique | Faible | Certaine |
| CLI Python jamais démarré automatiquement | Fonctionnalité cachée | Faible | Certaine |
| Desktop/Channels jamais connectés | Fonctionnalité manquante | Moyenne | Certaine |

---

## 7. Recommandations

1. **Éliminer le code mort** : Supprimer les 6 classes importées mais jamais instanciées dans `core/bootstrap.py`
2. **Ajouter un watchdog NATS** : Script qui vérifie la connectivité NATS toutes les 30s
3. **Rendre Ollama optionnel explicite** : Utiliser `profiles` ou `.env` au lieu d'être dans le docker-compose principal
4. **Connecter Qdrant** à l'API memory (ou supprimer du dev.yml)
5. **Démarrer le CLI Python automatiquement** via `ethan up` ou un service systemd dédié