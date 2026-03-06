# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TenderCortex is a multi-agent AI system for automating public tender (licitación) analysis. It uses LangGraph to orchestrate specialist sub-agents that process uploaded RFP documents via RAG.

## Commands

### Backend (Python — run from `backend/`)

```bash
pip install -r requirements.txt                # Install deps
uvicorn app.main:app --reload --port 8000      # Dev server

pytest -v                                       # All tests
pytest tests/unit -v                            # Unit tests only
pytest tests/bdd -v -m bdd                      # BDD specs
pytest -m integration -v                        # Integration tests
pytest --cov=app --cov-report=term-missing      # Coverage

python scripts/check_specs.py                   # Verify SPEC <-> code consistency
python scripts/export_openapi.py                # Export OpenAPI spec
python scripts/validate_openapi.py              # Validate OpenAPI spec
```

### Frontend (TypeScript — run from `frontend/`)

```bash
npm install          # Install deps
npm run dev          # Vite dev server (proxies /api to localhost:8000)
npm run build        # Production build (TypeScript + Vite)
npm run lint         # ESLint
npm run generate-types  # Generate API types from OpenAPI
```

### Pre-commit validation

```bash
cd backend && pytest -v
cd backend && python scripts/check_specs.py
cd frontend && npm run build
```

## Architecture

### Multi-Agent Pipeline (LangGraph StateGraph)

The core pipeline lives in `backend/app/agents/rfp_graph.py`:

```
[Retrieve] → [Grade & Route] → [Router] → [Specialist Agent] → [Risk Sentinel] → [END]
                                   |              ↑                    |
                                   |              └── [Refine] ←──────┘ (max 2 retries)
                                   └→ [Quant Analysis] (if quantitative domain)
```

**Specialist domains:** legal, financial, technical, timeline, requirements, quantitative, general

Each query is: retrieved from Qdrant → graded for relevance → routed to a domain specialist → audited by Risk Sentinel → optionally refined if audit fails.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+), async, Pydantic V2 |
| LLM Orchestration | LangGraph + LangChain |
| LLM Inference | Groq API |
| Embeddings | HuggingFace Inference API (cloud) |
| Vector DB | Qdrant (in-memory, ephemeral by design) |
| Frontend | React 19 + TypeScript + Vite + TailwindCSS |
| Observability | Phoenix (optional, OTLP tracing) |
| Deploy | Vercel (frontend) + Render (backend) |

### Key Entry Points

- `backend/app/main.py` — FastAPI app
- `backend/app/agents/rfp_graph.py` — LangGraph state machine
- `backend/app/core/config.py` — Pydantic BaseSettings (chunk size, retrieval k, temperatures, etc.)
- `frontend/src/App.tsx` — React root
- `frontend/src/hooks/useRFP.ts` — Main app state hook

### API Routes (`backend/app/api/routes/`)

- `POST /api/chat` — Query answering via agent pipeline
- `POST /api/documents` — PDF ingestion; `GET` list; `DELETE` remove
- `GET /api/checklist` — Extract compliance requirements; `PUT` update status
- `GET /health` — Health check with dependency verification

### Backend Skills (`backend/skills/`)

8 domain-specific skills following the pattern: `SKILL.md + definition.py (Pydantic) + impl.py`. These are product skills used by the LLM agents, not development tools.

## Conventions

- **Logging:** Use `AgentLogger` from `app.core.logging` — never `print()`
- **Python:** Async for I/O, type hints everywhere, Pydantic V2 with `Field(description=...)`
- **TypeScript:** Functional components, explicit interfaces, no `any`, TailwindCSS for styling
- **Testing:** pytest with `asyncio_mode = auto`. Markers: `slow`, `integration`, `bdd`, `spec`
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- **Docstrings:** Written in Spanish (bilingual project)
- **Spec-Driven Development:** New features should have a SPEC before implementation. Templates in `openspec/templates/`. Workflow: Write Spec → Generate Tests → Implement → Validate with `check_specs.py`
- **New sub-agents:** Extend `BaseAgent` from `app.agents.base_agent`, register domain in agent factory
- **Error handling:** Use typed exceptions inheriting from `TenderCortexError`; never silently ignore errors
- **API responses:** Always include `agent_metadata` for pipeline traceability

## Environment Variables

**Backend:** `GROQ_API_KEY`, `GROQ_MODEL`, `HUGGINGFACE_API_KEY`, `APP_ENV`, `LOG_LEVEL`, `ENABLE_PHOENIX_TRACING`

**Frontend:** `VITE_API_URL` (production only; dev uses Vite proxy)

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to master: OpenAPI validation, unit tests, BDD specs, integration tests, coverage, spec consistency, frontend build.

Pre-commit hooks (`.pre-commit-config.yaml`): trailing whitespace, YAML/JSON validation, Ruff (Python lint/format), OpenAPI validation, spec consistency.
