---
name: <skill-name>
type: skill
version: "1.0.0"
status: draft | review | approved
description: |
  <Brief description of the skill for YAML consumers.>
---

# <Skill Name> Skill

## Purpose

<Detailed description of what this skill does.>

## When to Use
- <Use case 1>
- <Use case 2>

## When NOT to Use
- <Anti-pattern 1>
- <Anti-pattern 2>

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ... | ... | ... | ... |

## Output

| Field | Type | Description |
|-------|------|-------------|
| ... | ... | ... |

## Invariants

- <Invariant 1>
- <Invariant 2>

## Error Cases

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| ... | ... | ... |

## Test Scenarios

See: `tests/bdd/features/skills/<feature>.feature`

## Examples (Few-Shot)

### Example 1
```
Input: ...
Output: ...
```

## Related

- **Definition**: `backend/skills/<name>/definition.py`
- **Implementation**: `backend/skills/<name>/impl.py`
- **BDD Feature**: `tests/bdd/features/skills/<name>.feature`
