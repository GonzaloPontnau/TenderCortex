---
module: backend/app/services/<service_name>.py
type: service
version: "1.0.0"
status: draft | review | approved
---

# SPEC: <Service Name>

## Purpose

<One-paragraph description of this service's responsibility.>

## Public Interface

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| ... | `async def method(arg: type) -> type` | ... | ... |

## Dependencies

### External
| Dependency | Purpose |
|------------|---------|
| ... | ... |

### Internal
| Module | Purpose |
|--------|---------|
| ... | ... |

## Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| ... | ... | ... | ... |

## Error Handling

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| ... | ... | ... |

## Invariants

- <Invariant 1>
- <Invariant 2>

## Related

- **Implementation**: `backend/app/services/<service>.py`
