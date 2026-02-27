# Tasks: Compliance Checklist Automatico

## Phase 1: Backend — Schemas

- [x] 1.1 Create `backend/app/schemas/checklist.py` with enums: `ChecklistItemStatus` (pending, compliant, non_compliant, not_applicable), `ChecklistCategory` (legal, technical, financial, administrative, timeline, other), `ChecklistSeverity` (mandatory, desirable)
- [x] 1.2 In `checklist.py`, create `ChecklistItem` model with fields: `id` (str), `requirement_text` (str), `category` (ChecklistCategory), `severity` (ChecklistSeverity), `status` (ChecklistItemStatus, default pending), `source_page` (int | None), `source_document` (str | None)
- [x] 1.3 In `checklist.py`, create `ChecklistSummary` model with fields: `total` (int), `by_category` (dict[str, int]), `by_severity` (dict[str, int]), `by_status` (dict[str, int])
- [x] 1.4 In `checklist.py`, create `ChecklistResponse` model with fields: `items` (list[ChecklistItem]), `summary` (ChecklistSummary); add `from_items()` classmethod
- [x] 1.5 In `checklist.py`, create `ChecklistItemUpdate` model with field: `status` (ChecklistItemStatus)
- [x] 1.6 Update `backend/app/schemas/__init__.py` to export checklist types

## Phase 2: Backend — Service

- [x] 2.1 Create `backend/app/services/checklist_service.py` with `ChecklistService` class; constructor initializes `_items: dict[str, ChecklistItem] | None = None`; add `get_checklist_service()` singleton factory with `@lru_cache`
- [x] 2.2 In `ChecklistService`, implement `EXTRACTION_PROMPT` constant: system prompt that instructs the LLM to extract requirements from tender document text and return a JSON array with fields: requirement_text, category, severity, source_page
- [x] 2.3 In `ChecklistService`, implement `async generate() -> ChecklistResponse`: retrieve all chunks from RAGService via scroll, group into batches, call LLM per batch, parse JSON responses, create ChecklistItems with UUID ids, deduplicate, store in `_items`, return ChecklistResponse
- [x] 2.4 In `ChecklistService`, implement `get_checklist() -> ChecklistResponse | None`: return current checklist with computed summary, or None if not generated
- [x] 2.5 In `ChecklistService`, implement `update_item(item_id: str, status: ChecklistItemStatus) -> ChecklistItem`: find item by id, update status, return updated item; raise KeyError if not found
- [x] 2.6 In `ChecklistService`, implement `clear()`: reset `_items` to None (called when documents are cleared)
- [x] 2.7 Update `backend/app/services/__init__.py` to export `ChecklistService` and `get_checklist_service`

## Phase 3: Backend — API Routes

- [x] 3.1 Create `backend/app/api/routes/checklist.py` with `APIRouter`; implement `POST /checklist/generate` endpoint that calls `ChecklistService.generate()` and returns `ChecklistResponse`
- [x] 3.2 In `checklist.py`, implement `GET /checklist` endpoint that calls `get_checklist()` and returns 404 if not generated
- [x] 3.3 In `checklist.py`, implement `PATCH /checklist/items/{item_id}` endpoint that accepts `ChecklistItemUpdate` body and calls `update_item()`; return 404 if item not found, 409 if checklist not generated
- [x] 3.4 Update `backend/app/api/routes/__init__.py` to import and export `checklist_router`
- [x] 3.5 Update `backend/app/api/__init__.py` to include `checklist_router`

## Phase 4: Frontend — Types and Hook

- [x] 4.1 In `frontend/src/types.ts`, add types: `ChecklistItemStatus`, `ChecklistCategory`, `ChecklistSeverity`, `ChecklistItem`, `ChecklistSummary`, `ChecklistResponse`
- [x] 4.2 In `frontend/src/hooks/useRFP.ts`, add `generateChecklist()` method that calls `POST /api/checklist/generate` and returns `ChecklistResponse`
- [x] 4.3 In `useRFP.ts`, add `updateChecklistItem(itemId: string, status: ChecklistItemStatus)` method that calls `PATCH /api/checklist/items/{itemId}`

## Phase 5: Frontend — UI Components

- [x] 5.1 Create `frontend/src/components/ChecklistPanel.tsx` with props: `checklist: ChecklistResponse | null`, `onGenerate: () => void`, `onUpdateItem: (itemId: string, status: ChecklistItemStatus) => void`, `loading: boolean`, `hasDocuments: boolean`
- [x] 5.2 In `ChecklistPanel`, implement empty state: "Generar Checklist" button (disabled if no documents); loading state with spinner
- [x] 5.3 In `ChecklistPanel`, implement checklist view: summary header with progress bar, filter chips by category, list of items grouped by category
- [x] 5.4 In `ChecklistPanel`, implement item row: requirement text, severity badge (mandatory=orange, desirable=blue), status toggle button that cycles through states with distinct colors
- [x] 5.5 In `Sidebar.tsx`, add tab toggle between "Documentos" and "Checklist" views; Checklist tab only visible when documents.length > 0
- [x] 5.6 In `App.tsx`, add checklist state management (useState for ChecklistResponse), wire generateChecklist and updateChecklistItem handlers, pass props to Sidebar

## Phase 6: Integration

- [x] 6.1 Wire checklist clearing when documents are cleared (DELETE /api/index also clears checklist)
- [x] 6.2 Run `npm run build` in frontend to verify no TypeScript errors
- [x] 6.3 Verify lint: run eslint on modified frontend files (zero new lint errors; pre-existing ChatInput.tsx error not introduced by this change)
