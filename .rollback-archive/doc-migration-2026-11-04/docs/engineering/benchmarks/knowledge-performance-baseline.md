# Knowledge Performance Baseline

## Baseline JSON
- `tests/benchmarks/knowledge/baseline-small.json`
- scope: in-memory Knowledge collection benchmark
- dataset documents: 10 (reported in benchmark metadata, not API)
- result shown in JSON baseline

## Environment
- local sandbox
- Python `time.perf_counter`
- in-memory CoreRecordStore
- native Memory vector store
- no PostgreSQL, no Docker
- no model download, no Qdrant, no ChromaDB

## Measured evidence
Results are available in `baseline-small.json`.
Median, p95, min, max all derived from measured operations only.

## Limitations
- no backend PostgreSQL timing
- no frontend timing
- no huge dataset (1000 docs)
- synthetic data only
- ZIP / huge RAG ingestion timings not measured here

## Next steps
1. Run `100` and `1000` document benchmarks.
2. Produce DB-backed baseline after Phase 2.1.5 environment is available.
3. Keep raw samples and report measurements separated strictly
