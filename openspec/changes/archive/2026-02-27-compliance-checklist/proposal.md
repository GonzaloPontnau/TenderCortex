# Proposal: Compliance Checklist Automatico

## Intent

Los equipos de procurement dedican horas a leer pliegos de licitacion, identificar cada requisito, y crear un checklist manual para verificar cumplimiento. TenderCortex ya tiene toda la infraestructura de RAG e inteligencia de dominio necesaria. Este feature agrega un endpoint que extrae automaticamente todos los requisitos de los documentos ingresados y genera un checklist estructurado por categorias, con clasificacion de severidad (obligatorio/deseable) y estado de cumplimiento trackeable.

## Scope

### In Scope
- Servicio backend `ChecklistService` que usa RAG + LLM para extraer requisitos de documentos indexados
- Modelos Pydantic para `ChecklistItem` y `ChecklistResponse`
- Endpoint `POST /api/checklist/generate` que genera el checklist a partir de documentos indexados
- Endpoint `PATCH /api/checklist/items/{item_id}` para actualizar estado de items
- Endpoint `GET /api/checklist` para obtener el checklist actual
- Componente frontend `ChecklistPanel` integrado en el Sidebar
- Prompt especializado en extraccion de requisitos
- Clasificacion automatica por categoria (legal, tecnico, financiero, administrativo, plazos)
- Deteccion de severidad (mandatory/desirable) reutilizando keywords del compliance_audit_validator

### Out of Scope
- Persistencia entre sesiones (consistente con el diseno efimero del proyecto)
- Exportacion a Excel/PDF (feature futuro)
- Validacion de compliance automatica contra perfil de empresa (ya existe en compliance_audit_validator)
- Modificacion del grafo LangGraph principal

## Approach

1. Crear modelos Pydantic en `backend/app/schemas/checklist.py` para items y respuesta
2. Crear `backend/app/services/checklist_service.py` que usa RAGService para obtener chunks y LLM para extraer requisitos estructurados
3. Crear `backend/app/api/routes/checklist.py` con endpoints REST
4. Agregar tipos TypeScript y metodo en `useRFP.ts`
5. Crear componente `ChecklistPanel.tsx` en el Sidebar

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/schemas/checklist.py` | New | Modelos Pydantic para checklist |
| `backend/app/services/checklist_service.py` | New | Servicio de extraccion de requisitos |
| `backend/app/api/routes/checklist.py` | New | Endpoints REST |
| `backend/app/api/routes/__init__.py` | Modified | Registrar checklist_router |
| `backend/app/api/__init__.py` | Modified | Incluir checklist_router |
| `frontend/src/types.ts` | Modified | Agregar tipos de checklist |
| `frontend/src/hooks/useRFP.ts` | Modified | Agregar generateChecklist() |
| `frontend/src/components/ChecklistPanel.tsx` | New | UI del checklist |
| `frontend/src/App.tsx` | Modified | Integrar ChecklistPanel |
| `frontend/src/components/Sidebar.tsx` | Modified | Tab para alternar documentos/checklist |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| LLM no extrae todos los requisitos | Medium | Usar prompt con few-shot examples; recuperar suficientes chunks (k alto) |
| Requisitos duplicados | Medium | Deduplicacion por similaridad en el service |
| Latencia en generacion | Low | SSE streaming para feedback; cache del resultado |
| Documentos sin requisitos claros | Low | Manejo graceful con mensaje informativo |

## Success Criteria

- [ ] El endpoint genera un checklist con requisitos categorizados a partir de documentos indexados
- [ ] Cada item tiene categoria, severidad, texto del requisito, y pagina fuente
- [ ] El usuario puede marcar items como cumplido/no cumplido/pendiente desde el frontend
- [ ] El checklist se muestra en una tab del Sidebar
- [ ] El frontend muestra conteo de items por estado (cumplidos/pendientes/total)
