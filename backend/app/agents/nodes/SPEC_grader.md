---
module: backend/app/agents/nodes/grader.py
type: graph-node
version: "1.0.0"
status: approved
---

# SPEC: Grade and Route Node

## Purpose

Evaluates retrieved documents for relevance (batch LLM grading) and classifies the user's question into a domain — both operations run in parallel to reduce latency. Outputs filtered documents and domain classification.

## Position in Graph

| Aspect | Value |
|--------|-------|
| **Predecessors** | `retrieve` |
| **Successors** | `specialist` (most domains), `quant` (if domain=quantitative) |
| **Conditional Routing** | `route_after_router()` checks if `domain == "quantitative"` |

## Input State Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `str` | Yes | User's question |
| `context` | `list[Document]` | Yes | Documents from retrieve node |

## Output State Mutations

| Field | Type | Description |
|-------|------|-------------|
| `filtered_context` | `list[Document]` | Documents marked as relevant by the grader |
| `domain` | `str` | Classified domain (one of 7 domains) |

## Behavior Specification

### Happy Path

1. Run grading and routing in parallel via `asyncio.gather`
2. **Grading**: Send all documents + question to LLM in a single batch call
3. Parse LLM response for `<index>: relevant/not_relevant` lines
4. Filter documents where grade is "relevant"
5. **Routing**: Call `route_question()` to classify domain
6. Merge results and return

### Safety Net

1. If `len(relevant_docs) < safety_net_min_docs` AND question is data-heavy → use top `safety_net_fallback_docs`
2. If no relevant docs at all → use top `safety_net_fallback_docs` as fallback
3. Data-heavy detection: keyword-based heuristic (`fecha`, `presupuesto`, `monto`, etc.)

### Error Cases

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| Grading LLM error | Log error | Fallback to first `safety_net_fallback_docs` docs |
| Router LLM error | Log error | Default to `domain="general"` |
| Unparseable grade line | Skip that line | Continue with other lines |

## Invariants

- `filtered_context` is never empty (safety net ensures fallback)
- `domain` is always one of: `financial`, `legal`, `technical`, `timeline`, `requirements`, `quantitative`, `general`
- Documents are truncated to `settings.grader_doc_truncation` chars for grading

## Performance Constraints

| Metric | Target |
|--------|--------|
| LLM calls | 2 in parallel (grader + router) |
| Doc truncation | `settings.grader_doc_truncation` (1500 chars) |

## Related

- **BDD Feature**: `tests/bdd/features/pipeline/grading_node.feature`, `tests/bdd/features/pipeline/routing.feature`
- **Implementation**: `backend/app/agents/nodes/grader.py`
- **Router**: `backend/app/agents/router.py`
