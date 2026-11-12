# RAG Retrieval Strategies

ETHAN exposes a small set of **retrieval strategies** for its RAG engine. A strategy is *not* a second RAG system: it is a configuration of the single retrieval engine in `core/rag/retrieval.py`. Only strategies mapped to real code paths are exposed — the catalog is authoritative and lives in `core/rag/strategies.py`.

## Available Strategies

| ID | Label | What it does | Needs real embeddings |
|----|-------|--------------|-----------------------|
| `auto` | Automatic (recommended) | Semantic search when real embeddings are available, keyword search otherwise. ETHAN's default. | No |
| `keyword` | Simple — keywords | Lexical scoring: chunks containing the query words. Fast, works without any embedding model. | No |
| `semantic` | Semantic | Vector search over chunk embeddings (cosine similarity). Best for reformulated queries and synonyms. | Yes |
| `hybrid` | Hybrid (keywords + semantic) | Runs both lexical and vector search, fuses rankings with Reciprocal Rank Fusion (RRF). The most robust in practice. | Degrades to keyword-only |

> **Reranking is not exposed.** ETHAN has no cross-encoder and no `rank`/`rerank` capability on its LLM providers yet. The catalog only ever lists strategies backed by real code, so a future reranking implementation will appear automatically once added to the Core.

## Graceful Degradation

When no real embedding client is configured (no provider, or mock/zero vectors):

- `semantic` falls back to keyword retrieval (logged as a warning);
- `hybrid` runs the keyword component only;
- `auto` keeps choosing the best available path — no user action required.

Selecting a strategy that requires embeddings while none are available never fails; it degrades and the WebUI surfaces an amber notice.

## Recommendation

The Core computes a **recommendation** from the engine's real capabilities (never from UI heuristics):

- real embeddings available → **`hybrid`**;
- no real embeddings → **`auto`**.

It is exposed via `GET /v1/rag/strategies` (`recommendation.strategy_id`, `recommendation.reason`, `recommendation.has_real_embeddings`) and rendered as an "ETHAN recommendation" hint in the WebUI (collection creation dialog and Settings → RAG).

## Configuring

### Global default (Settings → RAG)

```http
PUT /v1/rag/config
{"strategy": "hybrid"}
```

Unknown strategies are rejected with HTTP 422 (strict validation). The value is persisted in the `rag-config` record and survives restarts.

### Per collection

Each knowledge collection may override the global strategy:

```http
POST /v1/knowledge/collections
{"name": "Docs", "retrieval_strategy": "semantic"}

PUT  /v1/knowledge/collections/{id}
{"retrieval_strategy": null}   # back to the global default
```

Effective resolution: **collection strategy → global strategy → `auto`**.

## Retrieval Endpoints

- `POST /v1/knowledge/collections/{id}/retrieve` — uses the collection's effective strategy.
- `POST /v1/knowledge/collections/retrieve-multi` — one engine pass over the union of several collections (global strategy).
- `GET  /v1/rag/strategies` — strategy catalog + Core recommendation.

## Which Strategy Should I Pick?

| Situation | Suggestion |
|-----------|------------|
| Just getting started, no embedding provider | `auto` (default) |
| Documents with exact terminology (logs, configs, code) | `keyword` |
| Users reformulate questions, synonyms matter | `semantic` |
| Mixed corpora, best overall recall | `hybrid` |

See `docs/adr/ADR-1010-rag-strategies.md` for the design decision and extension contract.
