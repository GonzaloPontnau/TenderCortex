# Design: Implement Phoenix Observability

**Change**: implement-phoenix-observability
**Date**: 2026-03-05

---

## Technical Approach

Add a conditionally-loaded Phoenix tracing layer that instruments LangChain/LangGraph operations via OpenTelemetry. The entire tracing subsystem is isolated in a single new module (`app/core/phoenix_tracing.py`) and gated behind `settings.enable_phoenix_tracing`. When disabled (the default), zero Phoenix/OTel code is imported and zero RAM overhead exists. This maps directly to the proposal's "local-only, opt-in" strategy and satisfies all REQ-PT-* specifications.

---

## Architecture Decisions

### Decision: Single-Module Isolation

**Choice**: All Phoenix/OTel logic lives in one new file `backend/app/core/phoenix_tracing.py` with a single public function `setup_phoenix_tracing()`.
**Alternatives considered**: (A) Spread OTel setup across `config.py` and `main.py` inline; (B) Create a separate `observability/` package with multiple files.
**Rationale**: The scope is small (one TracerProvider, one exporter, one instrumentor). A single module keeps the blast radius minimal, is easy to remove later, and avoids polluting existing modules. Option A would violate single-responsibility; option B is over-engineering for ~40 lines of setup code.

### Decision: Lazy Import via Conditional Block in Lifespan

**Choice**: The `lifespan` function in `main.py` checks `settings.enable_phoenix_tracing` and only then imports and calls `setup_phoenix_tracing()`. Inside `phoenix_tracing.py`, all Phoenix/OTel imports are at function scope (inside `setup_phoenix_tracing()`), not at module top level.
**Alternatives considered**: (A) Top-level import with runtime guard; (B) Plugin/entry-point discovery.
**Rationale**: Lazy imports inside the function body guarantee that when tracing is disabled, `import app.core.phoenix_tracing` itself does not pull in heavy OTel/Phoenix packages. This is critical for the Render Free Tier RAM constraint. The existing codebase already uses conditional lazy imports (e.g., `uvicorn` import inside `if __name__`), so this follows project conventions.

### Decision: Dev Dependencies in Separate Requirements File

**Choice**: Create `backend/requirements-tracing.txt` listing the four Phoenix/OTel packages. Production `Dockerfile` continues to install only `requirements.txt`.
**Alternatives considered**: (A) Add to main `requirements.txt` with comments; (B) Use pip extras in `pyproject.toml`.
**Rationale**: The project uses `requirements.txt` (not `pyproject.toml`), so pip extras are not available. A separate file keeps production image lean and makes intent explicit. Developers run `pip install -r requirements-tracing.txt` to opt in. This also prevents accidental production installation via the existing `Dockerfile` which only copies `requirements.txt`.

### Decision: Use `get_logger` (Not `AgentLogger`) for Infrastructure Logging

**Choice**: Use `get_logger(__name__)` (stdlib-compatible logger) inside `phoenix_tracing.py`.
**Alternatives considered**: Use `AgentLogger` directly.
**Rationale**: `AgentLogger` is designed for LangGraph pipeline tracing (with flow symbols, node enter/exit). Phoenix tracing setup is infrastructure-level logging, not agent-level. The existing `main.py` uses `get_logger(__name__)` for infrastructure messages (lifespan start/stop). Following the same pattern maintains consistency. The spec says "AgentLogger (no print)" -- `get_logger` is the project's standard infrastructure logger, satisfying the no-print requirement while keeping agent-specific semantics separate.

### Decision: Broad Exception Catch in Lifespan Wrapper

**Choice**: Wrap the `setup_phoenix_tracing()` call in `main.py` with a `try/except Exception` that logs and continues.
**Alternatives considered**: (A) Let exceptions propagate; (B) Only catch `ImportError`.
**Rationale**: The spec (REQ-PT-04, Error Cases table) requires graceful degradation for ImportError, unreachable server, and "unexpected exception." A broad catch in the lifespan ensures the application never fails to start due to tracing issues. The `setup_phoenix_tracing()` function itself catches `ImportError` specifically and logs a targeted warning; the lifespan wrapper is a safety net for anything else.

---

## Data Flow

```
Application Startup (lifespan)
        │
        ▼
settings.enable_phoenix_tracing == True?
        │                          │
       YES                        NO
        │                          │
        ▼                          ▼
  lazy import                   (skip entirely,
  phoenix_tracing               zero imports,
        │                        zero overhead)
        ▼
  setup_phoenix_tracing()
        │
        ├── import OTel SDK + Phoenix instrumentor
        │
        ├── Create Resource(service.name="tendercortex-backend")
        │
        ├── Create OTLPSpanExporter(endpoint=settings.phoenix_endpoint)
        │
        ├── Create TracerProvider(resource, span_processor)
        │
        ├── set_tracer_provider(tracer_provider)
        │
        ├── LangChainInstrumentor().instrument()
        │
        └── logger.info("Phoenix tracing active -> {endpoint}")


Runtime (after startup)
        │
        ▼
  LangChain/LangGraph operations
        │
        ▼
  Auto-instrumented by LangChainInstrumentor
        │
        ▼
  OTel spans exported via OTLP HTTP
        │
        ▼
  Phoenix UI at http://127.0.0.1:6006
```

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/core/phoenix_tracing.py` | Create | New module with `setup_phoenix_tracing()` function. All OTel/Phoenix imports are lazy (inside function body). Uses `get_logger` for logging. Catches `ImportError` and logs warning on missing packages. |
| `backend/app/core/config.py` | Modify | Add two fields to `Settings`: `enable_phoenix_tracing: bool = False` and `phoenix_endpoint: str = "http://127.0.0.1:6006/v1/traces"`. Both use `Field()` with descriptions per Pydantic V2 conventions. |
| `backend/app/main.py` | Modify | Add conditional block in `lifespan()` startup: if `settings.enable_phoenix_tracing`, lazily import and call `setup_phoenix_tracing()`, wrapped in try/except for graceful degradation. |
| `backend/requirements-tracing.txt` | Create | New file listing: `arize-phoenix`, `openinference-instrumentation-langchain`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`. |

---

## Interfaces / Contracts

### New Config Fields (in `backend/app/core/config.py`)

```python
# Added to the Settings class, in a new "# Observability" section
enable_phoenix_tracing: bool = Field(
    default=False,
    description="Enable local Phoenix tracing for LangGraph/LangChain operations.",
)
phoenix_endpoint: str = Field(
    default="http://127.0.0.1:6006/v1/traces",
    description="OTLP HTTP endpoint for the Phoenix collector.",
)
```

### Public Function (in `backend/app/core/phoenix_tracing.py`)

```python
def setup_phoenix_tracing(endpoint: str) -> None:
    """Configura OpenTelemetry TracerProvider con exportador OTLP hacia Phoenix.

    Args:
        endpoint: URL del endpoint OTLP HTTP de Phoenix.

    Raises:
        ImportError: Si los paquetes de tracing no estan instalados
                     (capturado internamente, loguea warning).
    """
```

### Lifespan Integration (in `backend/app/main.py`)

```python
# Inside lifespan(), before yield, after the existing logger.info():
if settings.enable_phoenix_tracing:
    try:
        from app.core.phoenix_tracing import setup_phoenix_tracing
        setup_phoenix_tracing(settings.phoenix_endpoint)
    except Exception as exc:
        logger.warning(f"Phoenix tracing failed to initialize: {exc}")
```

---

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `setup_phoenix_tracing()` configures OTel correctly when packages available | Mock OTel SDK classes; verify `TracerProvider`, `OTLPSpanExporter`, and `LangChainInstrumentor().instrument()` are called with correct args. |
| Unit | `setup_phoenix_tracing()` catches ImportError gracefully | Patch imports to raise `ImportError`; verify warning is logged and no exception propagates. |
| Unit | Config fields have correct defaults | Instantiate `Settings` with minimal env vars; assert `enable_phoenix_tracing is False` and `phoenix_endpoint` matches default. |
| Unit | Lifespan does not import phoenix_tracing when disabled | Mock `settings.enable_phoenix_tracing = False`; verify `setup_phoenix_tracing` is never called. |
| Integration | Full tracing pipeline with local Phoenix | Manual (developer runs Phoenix locally + `ENABLE_PHOENIX_TRACING=true`). Not automated in CI. |

Note: All unit tests MUST work without Phoenix packages installed (use mocks). Tests MUST NOT require a running Phoenix server.

---

## Migration / Rollout

No migration required.

- The feature defaults to off (`enable_phoenix_tracing = False`).
- No database changes, no API contract changes, no frontend changes.
- Production `Dockerfile` does not install `requirements-tracing.txt`, so no production impact.
- Developers opt in by: (1) `pip install -r requirements-tracing.txt`, (2) setting `ENABLE_PHOENIX_TRACING=true` in their local `.env`.

---

## Open Questions

- [x] Should Phoenix packages go in main `requirements.txt` or a separate file? **Resolved**: Separate `requirements-tracing.txt` to keep production image lean and avoid RAM overhead on Render Free Tier.
- [ ] Should we add a `docker-compose.yml` for local dev that auto-starts Phoenix alongside the backend? (Out of scope for this change but worth considering as a follow-up.)
