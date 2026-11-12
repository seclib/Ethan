from tests.benchmarks.knowledge.scenarios import benchmark_collection_operations, benchmark_document_persistence, benchmark_rag_retrieval

def test_collection_measured():
    r, stats = benchmark_collection_operations(n=2, warmup=0, iterations=2)
    assert r.iterations == 2
    assert len(r.warm_samples_seconds) == 2
    assert r.warmup_count == 0
    assert stats["collections"] == 2

def test_document_measured():
    r, stats = benchmark_document_persistence(n=2, warmup=0, iterations=2)
    assert len(r.warm_samples_seconds) == 2
    assert stats["documents"] == 2

def test_retrieval_measured():
    r, stats = benchmark_rag_retrieval(n=2, warmup=0, iterations=2)
    assert len(r.warm_samples_seconds) == 2
    assert stats["documents"] == 2
    assert stats["hits"] >= 1
