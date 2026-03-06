# Design: Compliance Checklist Automatico

## Technical Approach

Agregar una capa de extraccion de requisitos sobre la infraestructura RAG existente. El servicio recupera chunks del vector store, los envia al LLM con un prompt especializado en deteccion de requisitos, y genera un checklist estructurado que se almacena en memoria. El frontend agrega una tab en el Sidebar para visualizar y gestionar el checklist.

No se modifica el grafo LangGraph ni se agregan dependencias. Se reutiliza `RAGService`, `get_llm()`, y los enums de `compliance_audit_validator`.

## Architecture Decisions

### Decision: Servicio independiente vs. nodo del grafo LangGraph

**Choice**: Servicio independiente (`ChecklistService`) con endpoints propios
**Alternatives considered**: Agregar un nodo `extract_requirements` al StateGraph
**Rationale**: El checklist es una funcionalidad ortogonal al flujo de Q&A. No depende de una pregunta del usuario sino de los documentos completos. Agregarlo al grafo complejizaria el state machine sin beneficio. Un servicio independiente es mas simple, testeable, y no afecta el pipeline existente.

### Decision: Extraccion batch vs. chunk-por-chunk

**Choice**: Batch -- enviar multiples chunks al LLM en una sola llamada
**Alternatives considered**: Procesar cada chunk individualmente
**Rationale**: Menos llamadas al LLM = menos latencia y tokens. El contexto largo del modelo (131K) permite enviar varios chunks por batch. La deduplicacion post-extraccion maneja requisitos que aparecen en multiples chunks.

### Decision: Almacenamiento en memoria vs. persistente

**Choice**: In-memory dict en el singleton `ChecklistService`
**Alternatives considered**: SQLite, Supabase
**Rationale**: Consistente con la filosofia "Privacy by Design" del proyecto (Qdrant in-memory, sin DB). Los datos se pierden al reiniciar, igual que los vectores. Futuro: se podria agregar persistencia opcional.

### Decision: Reutilizar enums de compliance_audit_validator vs. crear nuevos

**Choice**: Crear enums propios en `schemas/checklist.py` inspirados en los existentes
**Alternatives considered**: Importar directamente de `skills/compliance_audit_validator/definition.py`
**Rationale**: Las skills del producto estan desacopladas del backend core. Importar desde skills crearia una dependencia cross-layer. Los enums del checklist tienen valores ligeramente distintos (ej: `not_applicable` no existe en compliance_audit_validator). Mejor crear enums propios con valores alineados.

## Data Flow

```
  User clicks "Generar Checklist"
         |
         v
  POST /api/checklist/generate
         |
         v
  ChecklistService.generate()
         |
         +-- RAGService.get_indexed_documents() --> lista de docs
         +-- RAGService._client.scroll() --> recupera todos los chunks
         |
         v
  Agrupa chunks en batches (max ~4000 chars por batch)
         |
         v
  Para cada batch:
    +-- LLM.ainvoke(EXTRACTION_PROMPT + batch_text)
    +-- Parse JSON array de requisitos
    +-- Crear ChecklistItems con UUID
         |
         v
  Deduplica requisitos similares
         |
         v
  Almacena en _checklist (in-memory)
         |
         v
  Retorna ChecklistResponse con items + summary
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/schemas/checklist.py` | Create | Modelos Pydantic: ChecklistItemStatus, ChecklistCategory, ChecklistSeverity, ChecklistItem, ChecklistSummary, ChecklistResponse, ChecklistItemUpdate |
| `backend/app/services/checklist_service.py` | Create | ChecklistService con generate(), get_checklist(), update_item() y prompt de extraccion |
| `backend/app/services/__init__.py` | Modify | Exportar ChecklistService y get_checklist_service |
| `backend/app/api/routes/checklist.py` | Create | Endpoints: POST /generate, GET /, PATCH /items/{id} |
| `backend/app/api/routes/__init__.py` | Modify | Registrar checklist_router |
| `backend/app/api/__init__.py` | Modify | Incluir checklist_router |
| `backend/app/schemas/__init__.py` | Modify | Exportar tipos de checklist |
| `frontend/src/types.ts` | Modify | Agregar ChecklistItem, ChecklistSummary, ChecklistResponse |
| `frontend/src/hooks/useRFP.ts` | Modify | Agregar generateChecklist(), updateChecklistItem(), getChecklist() |
| `frontend/src/components/ChecklistPanel.tsx` | Create | Panel con lista de requisitos, filtros, toggle de estado |
| `frontend/src/components/Sidebar.tsx` | Modify | Agregar tab Documentos/Checklist |
| `frontend/src/App.tsx` | Modify | Pasar props de checklist al Sidebar |

## Interfaces / Contracts

### ChecklistService API

```python
class ChecklistService:
    async def generate(self) -> ChecklistResponse:
        """Extrae requisitos de documentos indexados y genera checklist."""
        ...

    def get_checklist(self) -> ChecklistResponse | None:
        """Retorna el checklist actual o None si no fue generado."""
        ...

    def update_item(self, item_id: str, status: ChecklistItemStatus) -> ChecklistItem:
        """Actualiza el estado de un item."""
        ...
```

### Pydantic Models

```python
class ChecklistItemStatus(str, Enum):
    PENDING = "pending"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"

class ChecklistCategory(str, Enum):
    LEGAL = "legal"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    ADMINISTRATIVE = "administrative"
    TIMELINE = "timeline"
    OTHER = "other"

class ChecklistSeverity(str, Enum):
    MANDATORY = "mandatory"
    DESIRABLE = "desirable"

class ChecklistItem(BaseModel):
    id: str
    requirement_text: str
    category: ChecklistCategory
    severity: ChecklistSeverity
    status: ChecklistItemStatus = ChecklistItemStatus.PENDING
    source_page: int | None = None
    source_document: str | None = None

class ChecklistSummary(BaseModel):
    total: int
    by_category: dict[str, int]
    by_severity: dict[str, int]
    by_status: dict[str, int]

class ChecklistResponse(BaseModel):
    items: list[ChecklistItem]
    summary: ChecklistSummary
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | ChecklistService: parse LLM response, deduplication, summary calculation | Mock LLM, assert item structure |
| Unit | Schemas: validation, enum values, serialization | Direct model instantiation |
| Integration | Endpoint flow: generate, get, update | TestClient with mocked services |
| Manual | Full flow: upload PDF, generate checklist, toggle items | Browser verification |
