# Tasks: Implement Phoenix Observability

**Change**: implement-phoenix-observability
**Date**: 2026-03-05
**Depends on**: proposal.md, specs/phoenix-tracing/spec.md, design.md

---

## Phase 1: Infrastructure / Dependencies

- [x] 1.1 Create `backend/requirements-tracing.txt` with the four Phoenix/OTel packages: `arize-phoenix`, `openinference-instrumentation-langchain`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp` (one per line)
- [x] 1.2 Add two new fields to the `Settings` class in `backend/app/core/config.py`: `enable_phoenix_tracing: bool = Field(default=False, description="Enable local Phoenix tracing for LangGraph/LangChain operations.")` and `phoenix_endpoint: str = Field(default="http://127.0.0.1:6006/v1/traces", description="OTLP HTTP endpoint for the Phoenix collector.")` under a new `# Observability` comment section

## Phase 2: Core Implementation

- [x] 2.1 Create `backend/app/core/phoenix_tracing.py` with a `setup_phoenix_tracing(endpoint: str) -> None` function. All OTel/Phoenix imports MUST be lazy (inside the function body, not at module top level). Use `get_logger(__name__)` for logging (not `print()`, not `AgentLogger`)
- [x] 2.2 Inside `setup_phoenix_tracing()`: create an OTel `Resource` with `service.name="tendercortex-backend"`, instantiate `OTLPSpanExporter(endpoint=endpoint)`, create a `TracerProvider` with a `SimpleSpanProcessor` (or `BatchSpanProcessor`) wrapping the exporter, call `set_tracer_provider()`, and call `LangChainInstrumentor().instrument()`
- [x] 2.3 Inside `setup_phoenix_tracing()`: wrap all OTel/Phoenix imports in a `try/except ImportError` block that logs a WARNING via `get_logger` indicating tracing packages are missing, then returns early (graceful degradation per REQ-PT-04 and SC-PT-05)
- [x] 2.4 At the end of `setup_phoenix_tracing()`: log an INFO message indicating Phoenix tracing is active and the target endpoint

## Phase 3: Integration / Wiring

- [x] 3.1 Modify the `lifespan()` function in `backend/app/main.py`: add a conditional block in the startup phase that checks `settings.enable_phoenix_tracing`. When `True`, lazily import `setup_phoenix_tracing` from `app.core.phoenix_tracing` and call it with `settings.phoenix_endpoint`
- [x] 3.2 Wrap the entire tracing block in `main.py` lifespan with `try/except Exception as exc` that logs `logger.warning(f"Phoenix tracing failed to initialize: {exc}")` and continues startup (broad safety net per design decision)

## Phase 4: Testing

- [x] 4.1 Create `backend/tests/unit/test_phoenix_config.py`: test that `Settings` instantiated without `ENABLE_PHOENIX_TRACING` env var has `enable_phoenix_tracing == False` and `phoenix_endpoint == "http://127.0.0.1:6006/v1/traces"` (validates SC-PT-08 and REQ-PT-01)
- [x] 4.2 Create `backend/tests/unit/test_phoenix_tracing.py`: test that `setup_phoenix_tracing()` calls `TracerProvider`, `OTLPSpanExporter`, and `LangChainInstrumentor().instrument()` with correct arguments when packages are available (mock all OTel/Phoenix classes). Validates SC-PT-01
- [x] 4.3 In `test_phoenix_tracing.py`: test that `setup_phoenix_tracing()` catches `ImportError` when Phoenix packages are missing, logs a WARNING, and does not raise (patch imports to raise `ImportError`). Validates SC-PT-05
- [x] 4.4 In `test_phoenix_tracing.py`: test that `setup_phoenix_tracing()` uses the custom endpoint passed as argument (e.g., `"http://10.0.0.5:9999/v1/traces"`). Validates SC-PT-07
- [x] 4.5 Create `backend/tests/unit/test_lifespan_tracing.py`: test that the lifespan does NOT import or call `setup_phoenix_tracing` when `settings.enable_phoenix_tracing` is `False`. Validates SC-PT-03 and SC-PT-04
- [x] 4.6 In `test_lifespan_tracing.py`: test that the lifespan catches any exception from `setup_phoenix_tracing()` and logs a warning without crashing. Validates SC-PT-06 error resilience
- [x] 4.7 Run the full existing test suite (`pytest backend/`) with `ENABLE_PHOENIX_TRACING` unset to confirm zero regressions. Validates SC-PT-10

## Phase 5: Cleanup / Verification

- [x] 5.1 Verify that `backend/app/core/phoenix_tracing.py` contains zero `print()` calls (validates INV-PT-04 and SC-PT-09)
- [x] 5.2 Verify that the production `backend/Dockerfile` does NOT reference `requirements-tracing.txt` (validates REQ-PT-04 production safety)
- [x] 5.3 Verify idempotency: confirm that calling `setup_phoenix_tracing()` twice does not create duplicate TracerProviders or instrumentors (validates INV-PT-02). Add a guard or test as needed
