---
module: backend/app/agents/nodes/retrieve.py
type: graph-node
version: "1.0.0"
status: approved
---

# SPEC: Retrieve Node

## Purpose

Fetches relevant documents from the Qdrant vector store using similarity search. This is the first processing node in the pipeline — it provides the RAG context that all downstream nodes depend on.

## Position in Graph

| Aspect | Value |
|--------|-------|
| **Predecessors** | `START` |
| **Successors** | `grade_and_route` (if docs found), `END` (if no docs) |
| **Conditional Routing** | `route_after_retrieve()` checks `no_documents` flag |

## Input State Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `str` | Yes | User's question to search for |
| `trace_id` | `str` | Yes | Request tracing identifier |

## Output State Mutations

| Field | Type | Description |
|-------|------|-------------|
| `context` | `list[Document]` | Retrieved documents (k=`settings.retrieval_k`) |
| `revision_count` | `int` | Initialized to `0` |
| `filtered_context` | `list[Document]` | Empty list (set if no docs) |
| `domain` | `str` | Set to `"none"` if no documents |
| `answer` | `str` | Set to `NO_DOCUMENTS_MESSAGE` if no documents |
| `audit_result` | `str` | Set to `"pass"` if no documents |
| `no_documents` | `bool` | `True` if vector store is empty |

## Behavior Specification

### Happy Path

1. Log pipeline start with question and trace_id
2. Call `rag.similarity_search(question, k=settings.retrieval_k)`
3. If documents returned: set `context` to documents, `revision_count` to 0
4. Route to `grade_and_route` node

### No Documents Path

1. If similarity_search returns empty list
2. Set `no_documents=True`, `domain="none"`, `answer=NO_DOCUMENTS_MESSAGE`
3. Set `audit_result="pass"` (skip pipeline)
4. Route directly to `END`

### Error Cases

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| Vector store exception | Log error | Return empty context, `revision_count=0` |
| RAG service unavailable | Log error | Return empty context |

## Invariants

- `revision_count` is always initialized to `0` by this node
- If `no_documents` is `True`, `answer` contains `NO_DOCUMENTS_MESSAGE`
- If `no_documents` is `True`, `domain` is `"none"` and `audit_result` is `"pass"`
- `context` is always a `list` (never `None`)

## Performance Constraints

| Metric | Target |
|--------|--------|
| Retrieval k | `settings.retrieval_k` (default 10) |
| Latency | <1s (in-memory Qdrant) |

## Related

- **BDD Feature**: `tests/bdd/features/pipeline/retrieve_node.feature`
- **Implementation**: `backend/app/agents/nodes/retrieve.py`
- **State**: `backend/app/agents/state.py`
