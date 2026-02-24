---
module: backend/app/agents/nodes/quant_node.py
type: graph-node
version: "1.0.0"
status: approved
---

# SPEC: Quant Node

## Purpose

Executes quantitative analysis when the domain is classified as `"quantitative"`. Generates charts (base64-encoded), textual insights, and data quality assessments. Skips processing for all other domains.

## Position in Graph

| Aspect | Value |
|--------|-------|
| **Predecessors** | `grade_and_route` (when domain=quantitative) |
| **Successors** | `risk_sentinel` |
| **Conditional Routing** | Skips (returns empty dict) if domain != "quantitative" |

## Input State Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `str` | Yes | User's question |
| `domain` | `str` | Yes | Must be `"quantitative"` to activate |
| `context` | `list[Document]` | Yes | Full context |
| `filtered_context` | `list[Document]` | Yes | Filtered context |

## Output State Mutations

| Field | Type | Description |
|-------|------|-------------|
| `quant_chart` | `str \| None` | Base64-encoded chart image |
| `quant_chart_type` | `str` | Chart type: `bar`, `line`, `pie`, `table`, `none` |
| `quant_insights` | `str` | Textual analysis of data |
| `quant_data_quality` | `str` | Data quality: `clean`, `sanitized`, `incomplete` |
| `answer` | `str` | Set to `quant_insights` for downstream processing |

## Behavior Specification

### Happy Path

1. Check if `domain == "quantitative"` — skip otherwise (return `{}`)
2. Call `quant_analyze(question, docs)` with filtered/full context
3. Receive tuple: `(chart_b64, chart_type, insights, data_quality)`
4. Set `answer` to insights text
5. Route to `risk_sentinel`

### Error Cases

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| Analysis exception | Log error | Return null chart, "none" type, error message as insights, "incomplete" quality |

## Invariants

- Returns empty dict `{}` when domain is not `"quantitative"`
- `quant_data_quality` is always one of: `clean`, `sanitized`, `incomplete`
- `answer` is always set when quant analysis runs (even on error)

## Related

- **BDD Feature**: `tests/bdd/features/pipeline/rfp_pipeline.feature` (quantitative scenario)
- **Implementation**: `backend/app/agents/nodes/quant_node.py`
- **Analysis**: `backend/app/agents/quant.py`
