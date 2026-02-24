---
module: backend/app/services/llm_factory.py
type: service
version: "1.0.0"
status: approved
---

# SPEC: LLM Factory

## Purpose

Factory singleton for creating `ChatGroq` LLM instances with configurable temperature. Provides a health check endpoint for the Groq API.

## Public Interface

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_llm` | `def get_llm(temperature: float = 0.0) -> ChatGroq` | `ChatGroq` | Cached LLM instance per temperature |
| `check_groq_health` | `async def check_groq_health() -> bool` | `bool` | Verify Groq API connectivity |

## Dependencies

### External
| Dependency | Purpose |
|------------|---------|
| `langchain_groq.ChatGroq` | LLM client |
| `httpx` | Health check HTTP calls |
| Groq API | LLM inference service |

### Internal
| Module | Purpose |
|--------|---------|
| `app.core.config.settings` | API key, model name |

## Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `groq_api_key` | `str` | required | Groq API authentication key |
| `groq_model` | `str` | `openai/gpt-oss-120b` | Model identifier |

## Error Handling

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| Missing API key | `pydantic` validation error at startup | Set `GROQ_API_KEY` env var |
| Health check timeout | Returns `False` | Non-fatal, used in `/health` |
| Health check network error | Returns `False` | Non-fatal |

## Invariants

- `get_llm()` is cached via `lru_cache` — same temperature returns same instance
- `request_timeout` is always 60 seconds
- `max_retries` is always 3
- Health check timeout is 5 seconds
