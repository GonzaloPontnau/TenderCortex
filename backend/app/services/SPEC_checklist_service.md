---
module: backend/app/services/checklist_service.py
type: service
version: "1.0.0"
status: approved
---

# SPEC: ChecklistService

## Purpose

Generate and manage a structured compliance checklist extracted from indexed tender documents.

## Public Interface

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `generate` | `async def generate() -> ChecklistResponse` | `ChecklistResponse` | Extract checklist items from indexed chunks using LLM batches |
| `get_checklist` | `def get_checklist() -> ChecklistResponse | None` | `ChecklistResponse \| None` | Return in-memory checklist if generated |
| `update_item` | `def update_item(item_id, status) -> ChecklistItem` | `ChecklistItem` | Update status of one checklist item by id |
| `clear` | `def clear() -> None` | `None` | Clear in-memory checklist and counters |
| `get_checklist_service` | `def get_checklist_service() -> ChecklistService` | Singleton | Module-level singleton accessor |

## Dependencies

### Internal
| Module | Purpose |
|--------|---------|
| `app.services.vector_store` | Source chunks for extraction |
| `app.services.llm_factory` | LLM client for batch extraction |
| `app.schemas.checklist` | Checklist models and enums |

## Behavior

### generate

Happy path:
1. Reads indexed records from vector store.
2. Builds prompt batches with source/page metadata.
3. Invokes LLM for requirement extraction per batch.
4. Parses structured items, normalizes enums, and deduplicates by semantic key.
5. Returns checklist with item stats and keeps it in memory for follow-up updates.

Error and recovery:
- No indexed records: returns an empty checklist response.
- Batch parse failure: logs and skips invalid items while continuing.
- LLM invocation failure in one batch: process continues with remaining batches.

### update_item

Happy path:
1. Validates a checklist exists.
2. Locates item by `item_id`.
3. Updates its `status` and returns the updated item.

Error and recovery:
- Checklist not generated yet: raises conflict-level application error.
- Item not found: raises not-found application error.

## Invariants

- Every `ChecklistItem.id` is unique.
- `category`, `severity`, and `status` remain constrained to declared enums.
- Service state is in-memory and ephemeral by design.
- Service is used via singleton accessor to keep state consistent across requests.
