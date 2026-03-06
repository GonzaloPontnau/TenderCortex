# Spec: Phoenix Tracing (Observability)

**Change**: implement-phoenix-observability
**Domain**: phoenix-tracing (NEW)
**Type**: Infrastructure / Cross-cutting concern
**Date**: 2026-03-05

---

## 1. Overview

This specification defines the behavior of the local Phoenix observability integration for TenderCortex. The system MUST provide opt-in OpenTelemetry tracing of LangGraph/LangChain operations, exporting spans to a local Arize Phoenix instance.

---

## 2. Requirements

### REQ-PT-01: Configuration Fields

The `Settings` class (Pydantic V2 BaseSettings) MUST expose two new fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_phoenix_tracing` | `bool` | `False` | Toggle for Phoenix tracing |
| `phoenix_endpoint` | `str` | `"http://127.0.0.1:6006/v1/traces"` | OTLP HTTP endpoint for Phoenix |

- Both fields MUST be configurable via environment variables (`ENABLE_PHOENIX_TRACING`, `PHOENIX_ENDPOINT`).
- `enable_phoenix_tracing` MUST default to `False` so tracing is disabled unless explicitly opted in.
- `phoenix_endpoint` MUST have a sensible default pointing to the standard local Phoenix port.

### REQ-PT-02: Tracing Setup Function

The system MUST provide an isolated `setup_phoenix_tracing()` function in a dedicated module (`app/core/phoenix_tracing.py`).

- The function MUST configure an OpenTelemetry `TracerProvider` with an OTLP HTTP span exporter targeting `settings.phoenix_endpoint`.
- The function MUST call `LangChainInstrumentor().instrument()` to auto-instrument all LangChain/LangGraph operations.
- The function MUST log (via `AgentLogger`) that tracing has been activated and the target endpoint.
- The function MUST NOT use `print()`.
- The function SHOULD set a meaningful service name (e.g., `"tendercortex-backend"`) on the `Resource`.

### REQ-PT-03: Conditional Activation in Lifespan

The FastAPI `lifespan` function MUST conditionally invoke `setup_phoenix_tracing()`:

- Tracing MUST be initialized ONLY IF `settings.enable_phoenix_tracing` is `True`.
- When `settings.enable_phoenix_tracing` is `False`, NO Phoenix or OpenTelemetry imports MUST occur at module level. The import MUST be deferred (lazy) inside the conditional block or inside `setup_phoenix_tracing()`.
- Activation MUST happen during the lifespan startup phase, before the application begins serving requests.

### REQ-PT-04: Production Safety

- Phoenix tracing MUST NOT run in production. When `enable_phoenix_tracing` is `False` (the default), the system MUST have zero tracing overhead.
- The Phoenix-related packages (`arize-phoenix`, `openinference-instrumentation-langchain`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`) SHOULD be listed as optional/dev dependencies so they are not required for production deployments.
- If tracing is enabled but Phoenix packages are not installed, the system MUST catch the `ImportError`, log a warning, and continue without tracing (graceful degradation).

### REQ-PT-05: Dependencies

The following packages MUST be added to the backend dependency manifest:

- `arize-phoenix`
- `openinference-instrumentation-langchain`
- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp`

These MAY be placed in an optional dependency group (e.g., `[dev]` or `[tracing]`) to keep production image lean.

---

## 3. Scenarios

### SC-PT-01: Happy Path -- Tracing Enabled with Phoenix Running

```gherkin
Given the environment variable ENABLE_PHOENIX_TRACING is set to "true"
  And the environment variable PHOENIX_ENDPOINT is set to "http://127.0.0.1:6006/v1/traces"
  And a Phoenix server is running locally on port 6006
When the FastAPI application starts
Then setup_phoenix_tracing() SHALL be called during lifespan startup
  And an OpenTelemetry TracerProvider SHALL be configured with an OTLP HTTP exporter
  And the exporter endpoint SHALL be "http://127.0.0.1:6006/v1/traces"
  And LangChainInstrumentor().instrument() SHALL be called
  And a log message SHALL be emitted indicating tracing is active
  And subsequent LangChain/LangGraph operations SHALL produce trace spans visible in Phoenix UI
```

### SC-PT-02: Happy Path -- Tracing Enabled with Default Endpoint

```gherkin
Given the environment variable ENABLE_PHOENIX_TRACING is set to "true"
  And the environment variable PHOENIX_ENDPOINT is NOT set
When the FastAPI application starts
Then setup_phoenix_tracing() SHALL be called
  And the OTLP exporter SHALL target the default endpoint "http://127.0.0.1:6006/v1/traces"
```

### SC-PT-03: Tracing Disabled (Default)

```gherkin
Given the environment variable ENABLE_PHOENIX_TRACING is NOT set
When the FastAPI application starts
Then setup_phoenix_tracing() SHALL NOT be called
  And NO OpenTelemetry TracerProvider SHALL be configured
  And NO LangChain instrumentation SHALL be applied
  And NO Phoenix-related modules SHALL be imported
  And the application SHALL start and serve requests normally
```

### SC-PT-04: Tracing Explicitly Disabled

```gherkin
Given the environment variable ENABLE_PHOENIX_TRACING is set to "false"
When the FastAPI application starts
Then setup_phoenix_tracing() SHALL NOT be called
  And the application SHALL behave identically to SC-PT-03
```

### SC-PT-05: Tracing Enabled but Phoenix Packages Not Installed

```gherkin
Given the environment variable ENABLE_PHOENIX_TRACING is set to "true"
  And the Phoenix-related packages are NOT installed in the environment
When the FastAPI application starts
  And setup_phoenix_tracing() is called
Then an ImportError SHALL be caught
  And a WARNING-level log message SHALL be emitted indicating that tracing packages are missing
  And the application SHALL continue startup without tracing
  And the application SHALL serve requests normally
```

### SC-PT-06: Tracing Enabled but Phoenix Server Unreachable

```gherkin
Given the environment variable ENABLE_PHOENIX_TRACING is set to "true"
  And Phoenix packages are installed
  And NO Phoenix server is running on the configured endpoint
When the FastAPI application starts
Then setup_phoenix_tracing() SHALL complete without error
  And the TracerProvider and instrumentor SHALL be configured
  And the application SHALL start normally
  And spans MAY fail to export silently (OTel SDK handles export failures gracefully)
  And the application SHALL NOT crash or hang due to unreachable Phoenix
```

### SC-PT-07: Custom Phoenix Endpoint

```gherkin
Given the environment variable ENABLE_PHOENIX_TRACING is set to "true"
  And the environment variable PHOENIX_ENDPOINT is set to "http://10.0.0.5:9999/v1/traces"
When the FastAPI application starts
Then the OTLP exporter SHALL target "http://10.0.0.5:9999/v1/traces"
```

### SC-PT-08: Config Validation -- Pydantic V2 Compliance

```gherkin
Given the Settings class in config.py
When a developer inspects the enable_phoenix_tracing and phoenix_endpoint fields
Then both fields SHALL use Pydantic V2 Field with type annotations
  And enable_phoenix_tracing SHALL be typed as bool
  And phoenix_endpoint SHALL be typed as str
  And both fields SHALL be loadable from environment variables following existing SettingsConfigDict conventions
```

### SC-PT-09: No print() Statements

```gherkin
Given the module app/core/phoenix_tracing.py
When a developer inspects the source code
Then there SHALL be zero occurrences of print()
  And all output SHALL use AgentLogger from app.core.logging
```

### SC-PT-10: Existing Tests Unaffected

```gherkin
Given the full backend test suite
  And ENABLE_PHOENIX_TRACING is NOT set (defaults to False)
When pytest is executed
Then all existing tests SHALL pass without modification
  And no test SHALL require Phoenix packages to be installed
```

---

## 4. Invariants

| ID | Invariant |
|----|-----------|
| INV-PT-01 | When `enable_phoenix_tracing` is `False`, zero Phoenix/OTel modules are imported and zero tracing overhead exists. |
| INV-PT-02 | The `setup_phoenix_tracing()` function MUST be idempotent -- calling it multiple times MUST NOT create duplicate TracerProviders or instrumentors. |
| INV-PT-03 | The tracing module MUST NOT introduce any new mandatory dependencies for production deployment. |
| INV-PT-04 | No `print()` calls anywhere in the tracing module. |
| INV-PT-05 | All new config fields MUST follow Pydantic V2 conventions with type annotations. |

---

## 5. Error Cases

| Condition | Expected Behavior | Recovery |
|-----------|-------------------|----------|
| Phoenix packages not installed + tracing enabled | Catch `ImportError`, log warning | Application continues without tracing |
| Phoenix server unreachable + tracing enabled | OTel SDK handles export failure silently | Application runs; spans are dropped |
| Invalid `PHOENIX_ENDPOINT` URL format | Pydantic validation or OTel SDK error at setup time | Log error, skip tracing, continue startup |
| `setup_phoenix_tracing()` raises unexpected exception | Catch broadly in lifespan, log error | Application continues without tracing |

---

## 6. Out of Scope

- Running Phoenix as a sidecar in production.
- Automatic Phoenix server launch from the backend.
- Frontend observability.
- Distributed tracing across frontend-backend boundary.
- Trace data persistence or export to cloud observability platforms.
