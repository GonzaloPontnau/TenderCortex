---
module: backend/app/services/embeddings.py
type: service
version: "1.0.0"
status: approved
---

# SPEC: Embeddings Service

## Purpose

Factory singleton for HuggingFace Inference API-based embeddings. Uses cloud API instead of local model loading to minimize RAM consumption on free-tier hosting.

## Public Interface

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_embeddings` | `def get_embeddings() -> HuggingFaceEndpointEmbeddings` | Embeddings | Cached embeddings instance |

## Constants

| Name | Value | Description |
|------|-------|-------------|
| `MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `EMBEDDING_DIMENSION` | `384` | Vector dimension |

## Dependencies

### External
| Dependency | Purpose |
|------------|---------|
| `langchain_huggingface.HuggingFaceEndpointEmbeddings` | Embedding client |
| HuggingFace Inference API | Remote embedding computation |

### Internal
| Module | Purpose |
|--------|---------|
| `app.core.config.settings` | HuggingFace API key |

## Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `huggingface_api_key` | `str` | required | HuggingFace API token |

## Error Handling

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| Missing API key | `pydantic` validation error at startup | Set `HUGGINGFACE_API_KEY` env var |
| API rate limit | Propagated to caller | Retry at caller level |

## Invariants

- `get_embeddings()` is cached via `lru_cache` — always returns same instance
- `EMBEDDING_DIMENSION` (384) must match the Qdrant collection's vector size
- Model is loaded remotely (no local GPU/RAM required)
