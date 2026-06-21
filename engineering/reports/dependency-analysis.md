# Dependency Analysis — Ethan

> RFC-002 — Analyse détaillée des dépendances
> Date : 2026-06-21

---

## 1. Dependency Categories

### 1.1 Runtime Dependencies (Obligatoires)

| Package | Version | Usage | Risque |
|---------|---------|-------|--------|
| click | >=8 | CLI framework | Faible |
| httpx | >=0.27 | HTTP client | Faible |
| openai | >=1.30 | OpenAI API + embeddings | Faible |
| rich | >=13 | Terminal UI | Faible |
| tomlkit | >=0.12 | TOML parsing | Faible |
| websockets | >=15.0.1 | WebSocket | Faible |
| datasets | >=4.5.0 | Dataset management | Faible |
| ddgs | >=9.11.4 | DuckDuckGo search | Faible |
| nvidia-ml-py | >=12.560 | GPU metrics | Faible |
| posthog | >=3.0 | Telemetry | Faible |
| python-telegram-bot | >=22.6 | Telegram channel | Faible |

**Risque principal :** openai comme dépendance obligatoire crée une friction pour les utilisateurs qui veulent uniquement Ollama.

### 1.2 Optional Dependencies (Extras)

| Extra | Packages | Usage | Couverture |
|-------|----------|-------|------------|
| server | fastapi, uvicorn, pydantic, python-multipart | API server | 5 |
| inference-cloud | anthropic | Anthropic provider | 1 |
| inference-google | google-genai | Gemini provider | 1 |
| inference-litellm | litellm | Multi-provider LLM | 1 |
| inference-vllm | vllm | GPU inference | 1 |
| inference-mlx | mlx-lm | Apple Silicon | 1 |
| inference-gemma | pygemma | Gemma local | 1 |
| memory-faiss | faiss-cpu, sentence-transformers, numpy | Vector search | 3 |
| memory-colbert | colbert-ai, torch | Neural search | 2 |
| memory-bm25 | rank-bm25 | Keyword search | 1 |
| memory-pdf | pdfplumber | PDF parsing | 1 |
| speech | faster-whisper | Speech-to-text | 1 |
| browser | playwright | Browser automation | 1 |
| sandbox-wasm | wasmtime | WASM sandbox | 1 |
| sandbox-docker | docker | Docker sandbox | 1 |
| scheduler | croniter | Job scheduling | 1 |
| security-signing | cryptography | Code signing | 1 |
| channels (15+) | discord, slack, twitter, gmail, etc. | Communication | 15+ |
| docs | mkdocs, mkdocs-material, mkdocstrings | Documentation | 5 |
| mining-pearl-* | docker, httpx | Pearl mining | 2 |

**Total : 32 extras, ~50+ packages optionnels**

### 1.3 Dépendances de Développement

| Package | Version | Usage |
|---------|---------|-------|
| pytest | >=8 | Test framework |
| pytest-asyncio | >=0.24 | Async tests |
| pytest-cov | >=5 | Coverage |
| respx | >=0.22 | HTTP mocking |
| ruff | >=0.4 | Linting |
| pre-commit | >=3.0 | Git hooks |
| maturin | >=1.12.6 | Rust build |

---

## 2. Dependency Graph

### 2.1 Python Dependencies

```
ethan (package)
    │
    ├── click              → CLI
    ├── httpx              → HTTP for LLM APIs, search, channels
    ├── openai             → LLM, embeddings, TTS, vision
    ├── rich               → CLI output formatting
    ├── tomlkit            → Config parsing
    ├── websockets         → WebSocket server
    ├── datasets           → Dataset loading (evals)
    ├── ddgs               → DuckDuckGo search
    ├── nvidia-ml-py       → GPU metrics
    ├── posthog            → Telemetry
    └── python-telegram-bot → Telegram channel (obligatoire ?)
```

**Note :** `python-telegram-bot` est une dépendance obligatoire alors qu'elle pourrait être optionnelle.

### 2.2 Frontend Dependencies

```
ethan-chat (package)
    │
    ├── react 19           → UI framework
    ├── react-dom 19       → DOM rendering
    ├── react-router 7     → Routing (SPA)
    ├── zustand 5          → State management
    │
    ├── @base-ui/react     → UI primitives (shadcn)
    ├── tailwindcss 4      → CSS utility framework
    ├── lucide-react       → Icons
    │
    ├── react-markdown     → Markdown rendering
    ├── rehype-highlight   → Code highlighting
    ├── rehype-katex       → Math rendering
    ├── remark-gfm         → GitHub Flavored Markdown
    ├── remark-math        → Math in markdown
    ├── katex              → Math engine
    │
    ├── recharts           → Charts & graphs
    ├── motion             → Animations
    ├── sonner             → Toast notifications
    ├── class-variance-authority → UI variants
    ├── clsx               → Class merging
    ├── tailwind-merge     → Tailwind class merging
    ├── tw-animate-css     → Tailwind animations
    │
    ├── @tauri-apps/api 2  → Desktop (Tauri)
    ├── @tauri-apps/plugin-* → Tauri plugins (7)
    │
    ├── posthog-js         → Analytics
    └── shadcn             → CLI for components
```

### 2.3 Rust Dependencies

```
ethan (workspace, 16 crates)
    │
    ├── serde / serde_json     → Serialization (quasi-standard)
    ├── tokio                  → Async runtime (standard)
    ├── reqwest                → HTTP client
    ├── rusqlite               → SQLite (bundled)
    ├── rig-core 0.31          → LLM framework
    ├── pyo3 0.23              → Python bindings
    ├── ed25519-dalek          → Signatures
    ├── tracing                → Logging
    ├── chrono                 → Dates
    ├── uuid                   → IDs
    ├── sha2                   → Hashing
    ├── regex                  → Regex
    ├── sysinfo                → System info
    ├── parking_lot            → Sync primitives
    ├── async-trait            → Async traits
    ├── schemars               → JSON Schema
    └── meval                  → Math expressions
```

---

## 3. Dependency Conflicts & Risks

### 3.1 Version Conflicts Potentiels

| Dependency | Problème | Risque |
|------------|----------|--------|
| torch (colbert extra) | Version fixe, incompatible avec certaines configs | Moyen |
| openai (obligatoire) | Contrainte même si non utilisé | Faible |
| playwright (browser) | Nécessite navigateur installé | Moyen |
| vllm | CUDA obligatoire | Moyen |
| mlx-lm | Apple Silicon uniquement | Faible |

### 3.2 Dépendances Obsolètes

| Dépendance | Version | Risque |
|------------|---------|--------|
| Aucune identifiée | - | - |

### 3.3 Dépendances Sous License Restrictive

| Dépendance | License | Compatible Apache 2.0 |
|------------|---------|----------------------|
| Toutes | MIT, Apache 2.0, BSD | ✅ |

---

## 4. Dependency Optimization Opportunities

### 4.1 Réduction Dépendances Obligatoires

```python
# Actuel (obligatoire)
dependencies = [
    "openai>=1.30",
    "python-telegram-bot>=22.6",
    ...
]

# Suggestion (optionnel)
[project.optional-dependencies]
server = ["openai>=1.30"]
channel-telegram = ["python-telegram-bot>=22.6"]
```

### 4.2 Dépendances Dupliquées

| Package | Dans | Aussi dans |
|---------|------|-----------|
| httpx | Core | channel-twitter |
| openai | Core | media, inference-cloud |
| docker | mining-pearl | sandbox-docker |

### 4.3 Dépendances Peu Utilisées

| Extra | Usage probable | Suggestion |
|-------|---------------|------------|
| Compression | Non référencé dans les docs | Supprimer ou documenter |
| Connector | Non référencé dans les docs | Supprimer ou documenter |
| RouterPolicy | Non référencé dans les docs | Supprimer ou documenter |

---

## 5. Build Dependency Graph

```
Python build (hatchling + hatch-vcs)
    │
    ├── Python 3.10+
    ├── uv (package manager)
    └── git (for version from tags)
    
Frontend build (Vite 6)
    │
    ├── Node.js 20+
    ├── npm
    └── TypeScript 5.7
    
Rust build (Cargo)
    │
    ├── Rust 1.88+
    ├── Cargo
    ├── maturin (for Python bindings)
    └── PyO3 (for FFI)

Docker build
    │
    ├── Docker 24+
    ├── Docker Compose 2+
    └── BuildKit (default)
```

---

## 6. Summary

| Métrique | Valeur |
|----------|--------|
| Dépendances obligatoires Python | 11 |
| Extras optionnels | 32 |
| Packages optionnels totaux | ~50+ |
| Dépendances Frontend (production) | ~30 |
| Crates Rust | 16 |
| Images Docker | 11 |
| Licences différentes | 3 (MIT, Apache-2.0, BSD) |
| Risques identifiés | 5 |
| Opportunités d'optimisation | 3 |