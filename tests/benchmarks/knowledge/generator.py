"""Deterministic synthetic Knowledge dataset generator (no DB/service)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
import random


@dataclass(frozen=True)
class BenchmarkDocument:
    id: str
    title: str
    content: str
    metadata: dict


def generate_documents(
    *,
    seed: int = 1,
    count: int = 100,
    target_chars: int = 500,
    prefix: str = "bench",
) -> list[BenchmarkDocument]:
    if count <= 0:
        raise ValueError("count must be positive")
    if target_chars <= 0:
        raise ValueError("target_chars must be positive")
    rng = random.Random(seed)
    docs = []
    for i in range(count):
        seed_token = f"{prefix}-{seed:04d}-{i:05d}"
        chunk = rng.choice(["alpha", "beta", "gamma", "delta"])
        template = (
            f"Document {i}; seed={seed}; identifier={seed_token}; marker={chunk}. "
            "Repeated text for stable upload and chunking. " * 20
        )
        content = (template * ((target_chars // len(template)) + 1))[:target_chars]
        digest = hashlib.sha256(content.encode()).hexdigest()[:8]
        docs.append(
            BenchmarkDocument(
                id=f"{prefix}-doc-{seed:04d}-{i:05d}",
                title=f"{prefix} document {i}",
                content=content,
                metadata={
                    "benchmark": True,
                    "seed": seed,
                    "index": i,
                    "digest": digest,
                },
            )
        )
    return docs


def generate_collections(seed: int, count: int, prefix: str = "bench") -> list[str]:
    if count <= 0:
        raise ValueError("count must be positive")
    return [f"{prefix}-collection-{seed:04d}-{i:03d}" for i in range(count)]
