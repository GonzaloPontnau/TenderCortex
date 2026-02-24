---
module: backend/app/agents/nodes/risk_sentinel_node.py
type: graph-node
version: "1.0.0"
status: approved
---

# SPEC: Risk Sentinel Node

## Purpose

Compliance audit gate that evaluates every specialist answer for quality, accuracy, and risk. Determines whether the answer passes to the user or needs refinement. Acts as the final quality gate before `END`.

## Position in Graph

| Aspect | Value |
|--------|-------|
| **Predecessors** | `specialist`, `quant` |
| **Successors** | `END` (if pass), `refine` (if fail and revisions < max) |
| **Conditional Routing** | `should_continue_after_audit()` checks `audit_result` and `revision_count` |

## Input State Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answer` | `str` | Yes | Specialist/quant answer to audit |
| `question` | `str` | Yes | Original user question |
| `context` | `list[Document]` | Yes | Full context |
| `filtered_context` | `list[Document]` | Yes | Filtered context |
| `revision_count` | `int` | Yes | Current refinement iteration |

## Output State Mutations

| Field | Type | Description |
|-------|------|-------------|
| `risk_level` | `str` | `low`, `medium`, `high`, `critical` |
| `compliance_status` | `str` | `approved`, `pending`, `rejected` |
| `risk_issues` | `list[str]` | List of detected issues |
| `gate_passed` | `bool` | Whether the audit gate passed |
| `audit_result` | `str` | `"pass"` or `"fail"` |

## Behavior Specification

### Happy Path (Approved)

1. Call `risk_audit(answer, docs, question)`
2. Receive `(risk_level, compliance_status, issues, gate_passed)`
3. If `compliance_status != "rejected"`: set `audit_result="pass"`, route to `END`

### Rejection Path

1. If `compliance_status == "rejected"`: set `audit_result="fail"`
2. Check `revision_count < settings.max_audit_revisions`
3. If within limit: route to `refine` node
4. If at limit: route to `END` (accept imperfect answer)

### Error Cases

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| Audit exception | Log error | Default to safe: `risk_level="medium"`, `compliance_status="approved"`, `gate_passed=True` |

## Invariants

- `audit_result` is always either `"pass"` or `"fail"`
- `risk_level` is always one of: `low`, `medium`, `high`, `critical`
- `compliance_status` is always one of: `approved`, `pending`, `rejected`
- Maximum `settings.max_audit_revisions` refinement rounds (safety cap)
- On error, defaults to **permissive** (pass) to avoid blocking the pipeline

## Performance Constraints

| Metric | Target |
|--------|--------|
| Max refinement rounds | `settings.max_audit_revisions` (default 2) |

## Related

- **BDD Feature**: `tests/bdd/features/pipeline/risk_sentinel.feature`
- **Implementation**: `backend/app/agents/nodes/risk_sentinel_node.py`
- **Audit logic**: `backend/app/agents/risk_sentinel.py`
