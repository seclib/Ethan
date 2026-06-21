# Repository Audit — Ethan

> RFC-001 — Analyse complète du dépôt
> Date : 2026-06-21
> Auteur : Principal Software Architect

---

## 1. Organisation du dépôt

```
Ethan/                          # Racine du projet
│
├── src/ethan/                  # Code source Python principal (300+ fichiers)
├── core/                            # Nouvelles abstractions (agents, llm, events, auth, memory, metrics)
├── providers/                       # Fournisseurs LLM (Ollama, OpenAI, Anthropic)
├── plugins/                         # Plugins système (browser, terminal)
├── apps/                            # Points d'entrée applicatifs (api/, gateway/)
├── sdk/                             # SDKs (python/, typescript/)
├── workers/                         # Workers asynchrones (vide)
├── services/                        # Déclarations de services (vide)
│
├── frontend/                        # Application web React + Vite + Tauri
│   ├── src/                         # Code source TypeScript
│   └── src-tauri/                   # Application desktop Tauri (Rust)
│
├── deploy/                          # Déploiement
│   ├── docker/                      # Dockerfiles + docker-compose
│   ├── traefik/                     # Reverse proxy
│   ├── prometheus/                  # Monitoring
│   ├── grafana/                     # Dashboards
│   ├── kubernetes/                  # Manifests K8s (vide)
│   ├── launchd/                     # macOS service
│   ├── systemd/                     # Linux service
│   └── windows/                     # PowerShell scripts
│
├── rust/                            # Crates Rust
│   ├── Cargo.toml                   # Workspace Rust (16 crates)
│   └── crates/                      # Implémentations Rust
│
├── configs/                         # Configuration
│   └── ethan/                  # config.toml, prompts, examples
│
├── scripts/                         # Scripts shell/Python
│   ├── install/                     # Scripts d'installation
│   ├── mining/                      # Scripts de minage
│   └── pearl/                       # Scripts Pearl
│
├── tests/                           # Tests (50+ dossiers, 200+ fichiers)
├── docs/                            # Documentation (architecture, deployment, dev, getting-started)
├── examples/                        # Exemples d'utilisation (10+ dossiers)
├── assets/                          # Images, logos
│
├── docker-compose.yml               # Production stack (10 services)
├── docker-compose.dev.yml           # Development stack
├── .env.example                     # Variables d'environnement
├── Makefile                         # Commandes automatisées
├── pyproject.toml                   # Build Python (hatchling + hatch-vcs)
└── mkdocs.yml                       # Documentation build
```

**Observation** : Le dépôt a une structure quasi-monorepo. Le code principal est dans `src/ethan/` mais des abstractions supplémentaires existent dans `core/`. Il y a une redondance entre `src/ethan/` et `core/` qui devra être résolue.

**Risque** : Dualité entre `src/ethan/` (code historique) et `core/` (nouvelles abstractions). Risque de duplication de code.

---

## 2. Build System

### Python
- **Build backend** : Hatchling + hatch-vcs
- **Gestionnaire** : uv (uv.lock présent)
- **Python** : 3.10–3.13
- **Entry points** : `jarvis` CLI, `ethan-eval` CLI
- **Version** : Git tag-driven (semver)

### Frontend
- **Build** : Vite 6 + TypeScript 5.7
- **UI** : React 19 + TailwindCSS 4 + shadcn/ui
- **Tests** : Vitest 3.2

### Rust
- **Version** : Rust 1.88 minimum
- **Workspace** : 16 crates (core, engine, agents, tools, learning, telemetry, security, etc.)
- **FFI** : PyO3 pour liaison Python-Rust

**Observation** : Build système mature et bien configuré. Le workspace Rust est large avec 16 crates.

---

## 3. Gestion des dépendances

### Dépendances principales (pyproject.toml)
| Catégorie | Dépendances | Volonté |
|-----------|-------------|---------|
| Core | click, httpx, rich, openai | Faible |
| LLM | openai, anthropic, litellm, google-genai | Optionnel |
| Memory | faiss, colbert, bm25, chromadb, pdfplumber | Optionnel |
| Channels | telegram, discord, slack, twitter, gmail, etc. (15+) | Optionnel |
| Media | faster-whisper (speech), openai (vision) | Optionnel |
| Sandbox | wasmtime, docker | Optionnel |
| Inference | mlx-lm, vllm, pygemma | Optionnel |
| Observability | posthog | Optionnel |

### Dépendances Frontend
| Catégorie | Technologie |
|-----------|-------------|
| UI | React 19, shadcn/ui, tailwindcss 4 |
| Charts | Recharts |
| Markdown | react-markdown, remark-gfm, katex |
| Desktop | Tauri 2 (tauri-apps/api, plugin-shell, plugin-dialog, etc.) |
| State | Zustand |
| Analytics | posthog-js |

### Dépendances Rust
| Catégorie | Crate |
|-----------|-------|
| Core | serde, tokio, reqwest, thiserror, tracing |
| Database | rusqlite (bundled SQLite) |
| LLM | rig-core 0.31 |
| Security | ed25519-dalek, sha2 |
| Python FFI | pyo3 0.23 |

**Observation** : Dépendances nombreuses mais bien organisées en groupes optionnels. Le design est extensible par feature flags.

**Risque** : 15+ channels de communication différents. Complexité de maintenance.

---

## 4. Configuration

### Fichiers de configuration
| Fichier | Format | Usage |
|---------|--------|-------|
| `.env.example` | Shell variables | Variables d'environnement documentées |
| `configs/ethan/config.toml` | TOML | Configuration applicative |
| `configs/ethan/prompts/` | Fichiers | Prompts système |
| `frontend/components.json` | JSON | Configuration shadcn/ui |

**Variables d'environnement** (`.env.example`) :
- `OPENJARVIS_API_KEY` — Clé API (obligatoire)
- `OPENJARVIS_ENGINE_DEFAULT` — Moteur par défaut (ollama, openai, etc.)
- `OLLAMA_HOST` — Hôte Ollama
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` — Clés API cloud
- `OPENJARVIS_DATABASE_URL` — URL de base de données (SQLite/PostgreSQL)
- `POSTGRES_*` — Configuration PostgreSQL
- `REDIS_*` — Configuration Redis
- `PROMETHEUS_*`, `GRAFANA_*` — Configuration monitoring
- `TRAEFIK_*` — Configuration reverse proxy
- `POSTHOG_API_KEY` — Télémétrie

**Observation** : Configuration bien organisée avec valeurs par défaut. Aucun secret codé en dur.