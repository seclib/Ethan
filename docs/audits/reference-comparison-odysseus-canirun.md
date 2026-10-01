# Reference Comparison — Odysseus & CanIRun.ai

> Audit comparatif des dépôts de référence (`examples/odysseus`, `examples/canirun.ai`)
> vs l'architecture ETHAN. Phase d'audit — **aucune implémentation dans ce document**.
>
> Règle directrice : ne jamais déclarer une architecture meilleure parce qu'elle vient
> d'une référence ; décider sur architecture, maintenabilité, sécurité, cohérence
> ETHAN, performances, tests, UX et absence de duplication.

## 1. Inventory

### 1.1 `examples/odysseus`

| Aspect | Détail |
|---|---|
| Licence | **AGPL-3.0** (⚠️ voir §Licensing) |
| Stack | Python/FastAPI (`app.py`, `routes/`, `services/`, `core/`) + UI, SQLite, Docker Compose NVIDIA/AMD |
| Services | `hwfit` (hardware fit), `memory`, `search`, `stt`, `tts`, `research`, `faces`, `shell`, `youtube`, `docs` |
| Routes | 40+ (cookbook, compare, email ×3, hwfit, model, embedding, vault, calendar, webhook…) |
| Intégrations | claude, codex, MCP servers |
| Docs sécurité | `SECURITY.md` (guidance déploiement), `THREAT_MODEL.md` |
| Tests | Nombreux tests cookbook (serve CPU-only, package detection, dépendances…) |
| Origine Cookbook | « built on [llmfit](https://github.com/AlexsJones/llmfit) » (licence à vérifier séparément) |

### 1.2 `examples/canirun.ai`

| Aspect | Détail |
|---|---|
| Licence | **MIT** (README + package.json) |
| Stack | Astro + pnpm monorepo ; 100 % **client-side** (rien ne quitte le navigateur) |
| Packages | `compatibility` (device slugs), `models` (catalogue), `runai` (recommand/process-manager, avec tests) |
| Données | `src/data/` : `models.ts` (55+ modèles), `gguf-sizes.json`, `hf-stats.json`, `aa-benchmarks.json`, `ollama-readmes.json` |
| Cœur | Détection hardware navigateur (WebGL/WebGPU/`deviceMemory`/micro-benchmark CPU) → VRAM requise par **7 quantizations** (Q2_K→F16) → **grade S–F** → tokens/s estimés par bande passante → best-picks par use case |

## 2. Audit Odysseus

### 2.1 Cookbook (modèle catalogue + fit + download + serve)

- Scan hardware réel : `nvidia-smi`, ROCm, `sysctl` Apple Silicon, support **rigs distants via SSH** (⚠️ `strict_host_key_checking=False` — voir §Security).
- Grouping GPU en **pools homogènes** (vLLM tensor-parallel n'est valide que sur GPUs identiques) ; plus gros pool = cible de serving par défaut.
- Cache des probes **24 h** (bouton Rescan manuel).
- `fit.py` : tables de **bande passante mémoire** par GPU (RTX/Radeon/Apple/H100…), fallback par backend (`cuda:220`, `metal:150`… GB/s), **poids par use case** (`general`, `coding`, `reasoning`, `chat`, `embedding`, `tts`, `stt`), estimation mémoire par quantization (`QUANT_BYTES_PER_PARAM`, pénalités qualité/vitesse).
- Download → serve (llama.cpp / vLLM) pilotés depuis l'UI, avec détection de packages et complétion de dépendances (tests dédiés).

### 2.2 Compare

- Sessions de comparaison A/B avec **mode blind** : mapping aléatoire left/right,
  identités des modèles **retirées des réponses API** en mode blind (le serveur
  conserve le mapping en DB), votes (`RecordVoteRequest.is_blind`).
- Révélation post-vote uniquement. UX « fun, no bias ».

### 2.3 Email

- Split mécanique propre : `email_routes.py` (handlers) / `email_helpers.py`
  (IMAP/SMTP, parsing, settings, modèles Pydantic) / `email_pollers.py`
  (boucles background : auto-summarize, scheduled mail).
- Fonctionnalités : triage IA (urgence, auto-tag, auto-spam), auto-summary,
  drafts de réponse générés, pièces jointes (extraction texte), multi-comptes
  avec routage par compte, détection des dossiers Sent/Drafts.
- Persistance SQLite ; appels LLM via `llm_call_async`.

### 2.4 Settings

- `prefs_routes.py` + `settings` persistés ; organisation par domaines
  (providers, models, email, calendar…) — proche de l'organisation ETHAN
  récemment auditée (Settings → AI / System / Integrations…). Rien de
  structurellement supérieur à l'état cible ETHAN.

## 3. Audit CanIRun.ai

- **Schéma de données exemplaire** (`packages/models/src/index.ts`) :
  `AIModel` = id, provider, family, `paramsBillions`, architecture
  (`dense|moe` + experts actifs), `contextLength`, `useCase[]`, `quants[]`
  (`{bits, vramGB, diskGB, quality}`), `minRamGB/recommendedRamGB`,
  `hfDownloads/Likes`, `ollamaId`, `ggufRepo`, `tools`, `thinking`,
  `license`, **`lineage`** (ne recommander que le plus récent d'une lignée —
  `getLineageCurrent`).
- Scoring : run status + tokens/s estimés (bande passante) + headroom mémoire
  + taille → **grade S–F** ; gating par use case ; best-picks quality-ranked.
- Détection hardware **navigateur** (aucune donnée envoyée) — complément
  possible du profil serveur ETHAN.
- `runai` : recommandation + process manager (lancer/arrêter un moteur local)
  **avec tests** (recommend, process-manager, telemetry, update).
- Zéro backend AI : tout le catalogue est statique et versionné (données
  reproductibles, reviewables en PR).