from tests.benchmarks.knowledge.scenarios import (
    benchmark_collection_operations,
    benchmark_document_persistence,
    benchmark_rag_ingestion,
    benchmark_rag_retrieval,
    benchmark_reconstruction,
)

def test_collection_operations():
    r, s = benchmark_collection_operations(n=2, warmup=0, iterations=2)
    assert r.iterations == 2
    assert s["collections"] == 2

def test_document_operations():
    r, s = benchmark_document_persistence(n=2, warmup=0, iterations=2)
    assert s["documents"] == 2

def test_rag_ingestion():
    r, s = benchmark_rag_ingestion(n=2, warmup=0, iterations=2)
    assert s["documents"] == 2

def test_rag_retrieval():
    r, s = benchmark_rag_retrieval(n=2, warmup=0, iterations=2)
    assert s["documents"] == 2 and s["hits"] >= 1

def test_reconstruction():
    r, s = benchmark_reconstruction(n=2, warmup=0, iterations=2)
    assert s["documents"] == 2
