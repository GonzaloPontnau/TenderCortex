# Proposal: implement-phoenix-observability

**Date**: 2026-03-05
**Status**: approved
**Author**: user (via SDD orchestrator)

## Problem Statement

TenderCortex uses LangGraph to orchestrate multi-agent pipelines, but there is no way to locally inspect trace data (latencies, token counts, agent routing decisions) during development. Developers must rely on log output alone, which is insufficient for debugging complex multi-step agent flows.

## Proposed Solution

Integrate Arize Phoenix as a **local-only, opt-in** observability layer for LangGraph traces. Phoenix provides a visual trace UI at `http://127.0.0.1:6006` that displays OpenTelemetry spans emitted by the LangChain instrumentor.

## Key Constraints

1. **Privacy by Design**: Tracing MUST NOT run in production. The feature is strictly local and toggleable via environment variable.
2. **Render Free Tier**: Phoenix dependencies MUST NOT increase production RAM usage. The tracing setup MUST be guarded so no Phoenix code is imported or executed when disabled.
3. **Project Conventions**: Must follow AGENTS.md rules -- Pydantic V2 config, async FastAPI, AgentLogger (no print), type hints everywhere.

## Scope

- Add 4 new Python packages to backend dependencies (dev/optional group).
- Add 2 new config fields to `Settings` class.
- Create one new module: `backend/app/core/phoenix_tracing.py`.
- Modify `backend/app/main.py` lifespan to conditionally call tracing setup.
- No frontend changes. No production behavior changes.

## Success Criteria

- Running `ENABLE_PHOENIX_TRACING=true uvicorn app.main:app` starts tracing to a local Phoenix instance.
- Running without the flag (or with `false`) has zero overhead -- no Phoenix imports, no OTel setup.
- All existing tests continue to pass with tracing disabled.
