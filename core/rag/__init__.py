"""ETHAN Core — RAG Module.

Retrieval Augmented Generation : ingestion, embeddings, retrieval, contexte LLM.
"""

from core.rag.context import RAGContext
from core.rag.embeddings import RAGEmbeddings
from core.rag.ingestion import DocumentChunk, IngestedDocument, RAGIngestion
from core.rag.pipeline import RAGPipeline
from core.rag.retrieval import RAGRetrieval, RetrievedChunk

__all__ = [
    "RAGEmbeddings",
    "RAGIngestion",
    "RAGRetrieval",
    "RetrievedChunk",
    "RAGContext",
    "RAGPipeline",
    "DocumentChunk",
    "IngestedDocument",
]
