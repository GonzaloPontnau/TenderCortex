---
module: backend/app/agents/nodes/specialist.py
type: graph-node
version: "1.0.0"
status: approved
---

# SPEC: Specialist Node

## Purpose

Generates the primary answer using a domain-specific specialist agent. Dispatches to the correct agent via `AgentFactory.create(domain)` and passes filtered documents as context.

## Position in Graph

| Aspect | Value |
|--------|-------|
| **Predecessors** | `grade_and_route` |
| **Successors** | `risk_sentinel` |
| **Conditional Routing** | None — always routes to risk_sentinel |

## Input State Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `str` | Yes | User's question |
| `domain` | `str` | Yes | Classified domain |
| `context` | `list[Document]` | Yes | Full retrieved context |
| `filtered_context` | `list[Document]` | Yes | Relevance-filtered context |

## Output State Mutations

| Field | Type | Description |
|-------|------|-------------|
| `answer` | `str` | Generated specialist response |

## Behavior Specification

### Happy Path

1. Read domain from state (default: `"general"`)
2. If domain is `"quantitative"`, override to `"general"` (quant handled separately)
3. Get `DependencyContainer` and create agent via `agent_factory.create(domain)`
4. Call `agent.generate(question=question, context=docs)`
5. Return answer string

### Domain-to-Agent Mapping

| Domain | Agent |
|--------|-------|
| `financial` | FinancialAgent |
| `legal` | LegalAgent |
| `technical` | TechnicalAgent |
| `timeline` | TimelineAgent |
| `requirements` | RequirementsAgent |
| `general` | GeneralAgent |
| `quantitative` | → `general` fallback |

### Error Cases

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| `AgentProcessingError` | Log error | Return error message (truncated to 300 chars) |
| Unexpected exception | Log error | Return error message with type (truncated to 200 chars) |

## Invariants

- `answer` is always set (never left empty) — even on error
- Quantitative domain never reaches this node's agent (redirected to general)
- Agent uses `get_docs(state)` which prefers `filtered_context` over `context`

## Related

- **BDD Feature**: `tests/bdd/features/agents/specialist_*.feature`
- **Implementation**: `backend/app/agents/nodes/specialist.py`
- **Factory**: `backend/app/agents/agent_factory.py`
