---
module: backend/app/agents/nodes/<node_name>.py
type: graph-node
version: "1.0.0"
status: draft | review | approved
---

# SPEC: <Node Name>

## Purpose

<One-paragraph description of what this node does in the pipeline.>

## Position in Graph

| Aspect | Value |
|--------|-------|
| **Predecessors** | <node(s) that feed into this node> |
| **Successors** | <node(s) this feeds into> |
| **Conditional Routing** | <conditions that determine next node, if any> |

## Input State Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `str` | Yes | User's question |
| ... | ... | ... | ... |

## Output State Mutations

| Field | Type | Description |
|-------|------|-------------|
| ... | ... | ... |

## Behavior Specification

### Happy Path

1. <Step 1>
2. <Step 2>
3. ...

### Error Cases

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| <condition> | <what happens> | <how it recovers> |

## Invariants

- <Invariant 1: something that must always be true>
- <Invariant 2>

## Performance Constraints

| Metric | Target |
|--------|--------|
| Latency | <e.g., <2s> |
| Max documents | <e.g., k=10> |

## Related

- **BDD Feature**: `tests/bdd/features/pipeline/<feature>.feature`
- **Implementation**: `backend/app/agents/nodes/<node>.py`
