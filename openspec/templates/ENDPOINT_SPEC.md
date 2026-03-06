---
module: backend/app/api/routes/<route_file>.py
type: api-endpoint
version: "1.0.0"
status: draft | review | approved
---

# SPEC: <Endpoint Name>

## Purpose

<One-paragraph description of this endpoint.>

## HTTP Contract

| Aspect | Value |
|--------|-------|
| **Method** | `POST` / `GET` / `DELETE` |
| **Path** | `/api/<path>` |
| **Auth** | None / Bearer token |
| **Content-Type** | `application/json` / `multipart/form-data` |

## Request

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| ... | ... | ... | ... |

## Response (200)

| Field | Type | Description |
|-------|------|-------------|
| ... | ... | ... |

## Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Invalid input | `{"detail": "..."}` |
| 422 | Validation error | `{"detail": [...]}` |
| 500 | Server error | `{"detail": "Internal server error"}` |

## Behavior Specification

### Happy Path
1. <Step 1>
2. <Step 2>

### Error Cases
| Condition | Response |
|-----------|----------|
| ... | ... |

## Related

- **BDD Feature**: `tests/bdd/features/api/<feature>.feature`
- **OpenAPI**: See `backend/openapi.json`
- **Pydantic schemas**: `backend/app/schemas/`
