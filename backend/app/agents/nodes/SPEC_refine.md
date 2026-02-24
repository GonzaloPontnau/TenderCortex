---
module: backend/app/agents/nodes/refine.py
type: graph-node
version: "1.0.0"
status: approved
---

# SPEC: Refine Node

## Purpose

Improves answers that failed the risk sentinel audit. Uses the original context, question, and failed answer to generate a refined response with domain-specific prompting. Increments the revision counter for the safety cap.

## Position in Graph

| Aspect | Value |
|--------|-------|
| **Predecessors** | `risk_sentinel` (on audit failure) |
| **Successors** | `risk_sentinel` (re-audit the refined answer) |
| **Conditional Routing** | None — always returns to risk_sentinel |

## Input State Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `str` | Yes | Original user question |
| `answer` | `str` | Yes | Previous answer that failed audit |
| `domain` | `str` | Yes | Domain classification |
| `context` | `list[Document]` | Yes | Full context |
| `filtered_context` | `list[Document]` | Yes | Filtered context |
| `revision_count` | `int` | Yes | Current revision number |

## Output State Mutations

| Field | Type | Description |
|-------|------|-------------|
| `answer` | `str` | Refined answer text |
| `revision_count` | `int` | Incremented by 1 |

## Behavior Specification

### Happy Path

1. Increment `revision_count` by 1
2. Get filtered/full context documents via `get_docs(state)`
3. Format context as concatenated text
4. Build refinement prompt with: domain, context, question, previous answer
5. Call LLM with `settings.refine_temperature`
6. Return refined answer and updated revision_count
7. Route back to `risk_sentinel` for re-audit

### Error Cases

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| LLM invocation error | Log error | Increment revision_count only (keep original answer) |

## Invariants

- `revision_count` is always incremented by exactly 1
- Uses `settings.refine_temperature` (default 0.1) for slight creativity
- Prompt includes the previous answer for improvement context
- Even on error, `revision_count` is incremented (prevents infinite loops)

## Performance Constraints

| Metric | Target |
|--------|--------|
| Temperature | `settings.refine_temperature` (0.1) |
| Max iterations | Bounded by `settings.max_audit_revisions` (checked by risk_sentinel) |

## Related

- **BDD Feature**: `tests/bdd/features/pipeline/refinement.feature`
- **Implementation**: `backend/app/agents/nodes/refine.py`
- **Prompt**: `REFINE_PROMPT` in `backend/app/agents/prompts/graph_prompts.py`
