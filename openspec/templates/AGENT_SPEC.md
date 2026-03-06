---
module: backend/app/agents/specialists/<agent_name>.py
type: specialist-agent
version: "1.0.0"
status: draft | review | approved
domain: <domain_name>
---

# SPEC: <Agent Name> Specialist

## Purpose

<One-paragraph description of this specialist agent's role.>

## Domain

| Aspect | Value |
|--------|-------|
| **Domain key** | `<domain>` |
| **Keywords** | <words that route to this agent> |
| **Fallback** | <what happens if this agent fails> |

## Prompt Design

| Section | Description |
|---------|-------------|
| **System prompt** | <summary of the system prompt> |
| **Context formatting** | <how documents are formatted for this agent> |
| **Output constraints** | <max chars, required sections, etc.> |

## Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | User's question |
| `context` | `list[Document]` | Filtered documents |

## Output

| Field | Type | Description |
|-------|------|-------------|
| `answer` | `str` | Generated response |

## Behavior Specification

### Happy Path
1. Receives question and context documents
2. Formats context using domain-specific formatter
3. Invokes LLM with system prompt + formatted context
4. Returns answer string

### Error Cases
| Error | Behavior |
|-------|----------|
| LLM timeout | Returns error message string |
| Empty context | Indicates information not available |

## Invariants

- Answer must reference only provided context documents
- Answer must not exceed `settings.answer_max_chars`

## Related

- **BDD Feature**: `tests/bdd/features/agents/specialist_<domain>.feature`
- **Base class**: `backend/app/agents/base/base_agent.py`
