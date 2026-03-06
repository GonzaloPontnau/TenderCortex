# Spec: ChecklistService

## Purpose

Servicio que extrae requisitos de documentos de licitacion indexados y genera un checklist estructurado usando RAG + LLM.

## Behavior

### generate_checklist()

**Input**: Ninguno (usa documentos ya indexados en el RAGService)

**Output**: `ChecklistResponse` con lista de `ChecklistItem`

**Happy Path**:
1. Recupera todos los chunks del vector store via RAGService
2. Agrupa chunks por pagina/fuente
3. Envia batches de chunks al LLM con prompt de extraccion
4. LLM retorna JSON array de requisitos con: texto, categoria, severidad, pagina
5. Deduplica requisitos similares
6. Retorna ChecklistResponse con items clasificados y estadisticas

**Error Cases**:

| Condition | Behavior | Recovery |
|-----------|----------|----------|
| No hay documentos indexados | Retorna ChecklistResponse vacio con mensaje | N/A |
| LLM falla al parsear | Log error, skip batch, continuar con resto | Partial result |
| Chunks insuficientes | Retorna lo que haya disponible | Mensaje indicando cobertura parcial |

### update_item_status()

**Input**: `item_id: str`, `new_status: ChecklistItemStatus`

**Output**: `ChecklistItem` actualizado

**Happy Path**:
1. Busca item por ID en el checklist en memoria
2. Actualiza status
3. Retorna item actualizado

**Error Cases**:

| Condition | Behavior | Recovery |
|-----------|----------|----------|
| Item no encontrado | Raise HTTPException 404 | N/A |
| Checklist no generado | Raise HTTPException 409 | Generar primero |

## Invariants

- Cada ChecklistItem tiene un ID unico (UUID)
- La categoria es un enum cerrado: legal, technical, financial, administrative, timeline, other
- La severidad es un enum cerrado: mandatory, desirable
- El status es un enum cerrado: pending, compliant, non_compliant, not_applicable
- El servicio es singleton (consistente con RAGService)
- Los datos son efimeros (se pierden al reiniciar, consistente con el proyecto)
