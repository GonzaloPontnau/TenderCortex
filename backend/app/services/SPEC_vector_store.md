---
module: backend/app/services/vector_store.py
type: service
version: "1.0.0"
status: approved
---

# SPEC: RAGService (Vector Store)

## Purpose

Retrieval-Augmented Generation service using Qdrant in-memory as the vector store. Handles document ingestion (PDF → chunks → embeddings → vectors), similarity search, index management, and health checks. Ephemeral by design — data is lost on container restart.

## Public Interface

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `warmup` | `async def warmup() -> None` | `None` | Pre-warm embeddings API and initialize store |
| `ingest_document` | `async def ingest_document(file_path, original_filename) -> int` | `int` | Process PDF and return chunk count |
| `similarity_search` | `async def similarity_search(query, k=10) -> list[Document]` | `list[Document]` | Find k most similar documents |
| `health_check` | `async def health_check() -> bool` | `bool` | Verify store is operational |
| `clear_index` | `async def clear_index() -> bool` | `bool` | Delete all vectors |
| `get_stats` | `async def get_stats() -> dict` | `dict` | Collection statistics |
| `get_indexed_documents` | `async def get_indexed_documents() -> list[dict]` | `list[dict]` | List indexed documents with chunk counts |
| `get_rag_service` | `def get_rag_service() -> RAGService` | Singleton | Module-level singleton |

## Dependencies

### External
| Dependency | Purpose |
|------------|---------|
| `qdrant_client.QdrantClient` | In-memory vector database |
| `langchain_qdrant.QdrantVectorStore` | LangChain integration |
| `langchain_community.document_loaders.PyPDFLoader` | PDF parsing |
| `langchain_text_splitters.RecursiveCharacterTextSplitter` | Document chunking |

### Internal
| Module | Purpose |
|--------|---------|
| `app.services.embeddings` | Embedding model and dimension |
| `app.core.config.settings` | Chunk size, overlap, batch sizes |

## Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `chunk_size` | `int` | 1000 | Characters per chunk |
| `chunk_overlap` | `int` | 200 | Overlap between chunks |
| `ingestion_batch_size` | `int` | 50 | Chunks per ingestion batch |
| `embedding_batch_size` | `int` | 32 | Texts per parallel API call |
| `retrieval_k` | `int` | 10 | Default similarity search k |

## Error Handling

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| Qdrant initialization failure | Log + raise | Caller handles |
| PDF parsing error | Log + raise | Caller returns 500 |
| Empty PDF (no chunks) | Log warning, return 0 | Non-fatal |
| Embedding API error | Propagated | Retry at API level |
| Health check failure | Returns `False` | Non-fatal |

## Invariants

- Collection name is always `COLLECTION_NAME` ("rfp_demo_collection")
- Vector dimension is always `EMBEDDING_DIMENSION` (384)
- Distance metric is always COSINE
- `_ensure_initialized` decorator guarantees store is ready before any operation
- `clear_index` recreates the collection (not just deletes points)
- Embedding batches are processed concurrently via `asyncio.gather`
- All Qdrant operations use `asyncio.to_thread` (non-blocking)
