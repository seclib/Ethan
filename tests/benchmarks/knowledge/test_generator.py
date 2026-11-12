import os

from tests.benchmarks.knowledge.generator import generate_documents, generate_collections


def test_same_seed_same_dataset():
    a = generate_documents(seed=7, count=12, target_chars=200)
    b = generate_documents(seed=7, count=12, target_chars=200)
    assert [d.id for d in a] == [d.id for d in b]
    assert [d.content for d in a] == [d.content for d in b]


def test_different_seeds_change_contents():
    a = generate_documents(seed=1, count=3, target_chars=150)
    b = generate_documents(seed=2, count=3, target_chars=150)
    assert [d.content for d in a] != [d.content for d in b]


def test_unique_ids_and_prefix():
    docs = generate_documents(seed=3, count=100, target_chars=120)
    ids = [d.id for d in docs]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("bench-doc-") for i in ids)


def test_count_and_size_rules():
    docs = generate_documents(seed=9, count=20, target_chars=180)
    assert len(docs) == 20
    for d in docs:
        assert 180 <= len(d.content) <= 200

def test_collections():
    ids = generate_collections(seed=3, count=5)
    assert len(ids) == len(set(ids))
    assert all(i.startswith("bench-collection-") for i in ids)
