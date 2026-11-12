# RAG Architect (rag-architect)

**Source :** `/home/fatsio/.config/opencode/skills/rag-architect/SKILL.md`  \n**Domaine :** IA — RAG  \n**Type :** Skill technique  \n**Niveau :** Spécialisé (Niveau B)  \n

## Description

Designs production-grade RAG systems: chunking documents, generating embeddings, configuring vector stores (pgvector, Pinecone, Weaviate, Qdrant), building hybrid search pipelines, applying reranking, and evaluating retrieval quality.

## Main capabilities

- **Document chunking**: Implements semantic and recursive character chunking for document preprocessing
- **Embedding generation**: Configures embedding models (OpenAI, Cohere, HuggingFace) for vector representation
- **Vector store configuration**: Sets up pgvector, Pinecone, Weaviate, or Qdrant for vector storage
- **Hybrid search pipelines**: Combines vector search with keyword search (BM25) for improved retrieval
- **Reranking**: Applies cross-encoder or other reranking models to improve relevance
- **Retrieval quality evaluation**: Measures precision, recall, and nDCG for retrieval systems

## What it can do

- Design document ingestion pipelines from various formats (PDF, HTML, Markdown)
- Configure embedding models and vector databases
- Build hybrid search combining vector and keyword approaches
- Implement reranking with cross-encoders for relevance improvement
- Evaluate retrieval quality with precision@k, recall@k, nDCG metrics
- Set up RAG pipelines with proper context window management

## When it is useful

- Building AI applications requiring document retrieval
- Implementing question-answering systems over private document collections
- Creating knowledge bases for LLM augmentation
- Setting up semantic search capabilities
- Designing RAG systems for enterprise search or internal documentation

## Practical examples

### Document chunking with semantic boundaries

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""],
)

chunks = splitter.split_text(document_text)
```

### Vector store configuration (pgvector)

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for documents with vectors
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding VECTOR(768),
    metadata JSONB
);

-- Insert document with embedding
INSERT INTO documents (content, embedding, metadata)
VALUES ('Document content...', '[0.1, 0.2, ...]', {'source': 'report.pdf'});
```

### Hybrid search with BM25 and vector

```python
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

# Vector search
embeddings = model.encode(documents)
vector_similarity = cosine_similarity(query_embedding, embeddings)

# Keyword search
tokenized_docs = [doc.split() for doc in documents]
bm25 = BM25Okapi(tokenized_docs)
keyword_scores = bm25.get_scores(query_tokens)

# Combine scores
combined = alpha * vector_similarity + (1 - alpha) * keyword_scores
```

## Original source path

`/home/fatsio/.config/opencode/skills/rag-architect/SKILL.md`

## Classification

- **Domaines :** IA, RAG, embeddings, vector store, recherche
- **Statut :** Spécialisé (Niveau B)
- **Références :** `monitoring-expert`, `cost-aware-llm-pipeline`, `api-design`
- **Validé :** Oui (rapport d'analyse stratégique Niveau B)
- **Auteur :** OpenCode Analysis
