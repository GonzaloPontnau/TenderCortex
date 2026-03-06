# Design: Document Viewer Panel

## Technical Approach

Feature 100% frontend. El PDF se retiene en browser memory via `URL.createObjectURL` al momento del upload. Cuando el usuario clickea un documento en el sidebar, `App.tsx` cambia a layout split-view: el area `<main>` se divide en dos paneles flex (visor + chat) separados por un drag handle resizable. Un custom hook `useResizePanel` encapsula la logica de drag. En mobile (<768px), la feature se deshabilita via media query + JS listener.

## Architecture Decisions

### Decision: Renderizar PDF con `<iframe>`

**Choice**: `<iframe src={blobUrl} />`
**Alternatives considered**: `<embed>`, `<object>`, react-pdf (pdf.js wrapper)
**Rationale**: `<iframe>` tiene soporte nativo en todos los browsers modernos para renderizar PDFs con scroll integrado. No agrega dependencias. react-pdf (pdf.js) daria mas control (zoom, anotaciones) pero esos features estan fuera de scope y agrega ~500KB al bundle. Si en el futuro se necesitan features avanzados, se puede reemplazar el iframe sin cambiar la arquitectura del layout.

### Decision: Retener File como Object URL (browser-side)

**Choice**: `URL.createObjectURL(file)` en el frontend al momento del upload
**Alternatives considered**: Almacenar el PDF en backend y servir via endpoint GET
**Rationale**: El backend elimina el PDF temporal despues de indexar (`tmp_path.unlink`). Agregar storage en backend requiere cambios en la API, manejo de limpieza, y no aporta valor dado que la app es efimera por diseño (Qdrant in-memory). El Object URL vive mientras dure la sesion del browser, que es exactamente el ciclo de vida del dato.

### Decision: Resize via custom hook con mouse events

**Choice**: Custom hook `useResizePanel` que maneja mousedown/mousemove/mouseup en window
**Alternatives considered**: CSS `resize` property, libreria externa (react-resizable-panels)
**Rationale**: CSS `resize` no permite un drag handle entre dos paneles flex. Una libreria externa agrega dependencia para algo que son ~40 lineas de logica. El hook custom es autocontenido, testeable, y sigue el patron del proyecto (hooks en `src/hooks/`).

### Decision: Split ratio almacenado como porcentaje

**Choice**: Estado `viewerWidthPercent: number` (0-100) que define el % del espacio disponible que ocupa el visor
**Alternatives considered**: Pixeles absolutos
**Rationale**: El porcentaje se adapta automaticamente al resize del window sin recalculos. Los anchos minimos se validan en pixeles dentro del hook comparando contra el ancho real del container.

### Decision: Mobile detection con JS + Tailwind

**Choice**: Hook `useMediaQuery("(min-width: 768px)")` para logica + clases Tailwind `hidden md:flex` para UI
**Alternatives considered**: Solo CSS, solo JS
**Rationale**: Se necesita JS para el escenario "cerrar visor automaticamente al transicionar a mobile" (spec requirement). CSS solo no puede mutar estado React. Combinar ambos es el patron idomatic en React + Tailwind.

## Data Flow

```
Upload:

  User selects PDF
       |
       v
  Sidebar.onUpload(file)
       |
       v
  App.handleUpload(file)
       |
       +---> uploadDocumentStream(file)  --> backend (ingest)
       |
       +---> URL.createObjectURL(file)   --> blobUrl
       |
       v
  setDocuments([...prev, { name, chunks, uploadedAt, fileUrl: blobUrl }])


Open Viewer:

  User clicks doc in Sidebar
       |
       v
  Sidebar calls onDocumentSelect(doc)
       |
       v
  App.setActiveDocument(doc)     // doc with fileUrl
       |
       v
  Layout switches to split-view:
  ┌──────────┬─────────────────┬──┬──────────────────┐
  │ Sidebar  │  DocumentViewer  │||│   Chat Panel      │
  │ (w-72)   │  <iframe>        │||│   (messages +     │
  │          │  src={fileUrl}   │||│    input)          │
  │          │                  │||│                    │
  └──────────┴─────────────────┴──┴──────────────────┘
                               ^
                          ResizeHandle


Close Viewer:

  User clicks X in DocumentViewer
       |
       v
  App.setActiveDocument(null)
       |
       v
  Layout returns to normal:
  ┌──────────┬──────────────────────────────────────┐
  │ Sidebar  │  <main> (chat or PromptSuggestions)   │
  │ (w-72)   │                                       │
  └──────────┴──────────────────────────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/types.ts` | Modify | Agregar `fileUrl?: string` a interface `Document` |
| `frontend/src/App.tsx` | Modify | Estado `activeDocument`, layout condicional split-view, pasar `onDocumentSelect` al sidebar |
| `frontend/src/components/Sidebar.tsx` | Modify | Agregar prop `onDocumentSelect`, click handler en items de documento, indicador visual de clickeable (solo desktop) |
| `frontend/src/components/DocumentViewer.tsx` | Create | Componente visor: header con nombre de archivo + boton cerrar, iframe con el PDF |
| `frontend/src/components/ResizeHandle.tsx` | Create | Drag handle visual (linea vertical sutil con dots) |
| `frontend/src/hooks/useResizePanel.ts` | Create | Hook: mousedown/mousemove/mouseup, calcula porcentaje, valida min widths |
| `frontend/src/hooks/useMediaQuery.ts` | Create | Hook generico: `useMediaQuery(query) => boolean`, para detectar mobile |

## Interfaces / Contracts

```typescript
// types.ts - Document extension
interface Document {
  name: string;
  chunks: number;
  uploadedAt: Date;
  fileUrl?: string;  // blob URL from createObjectURL
}

// DocumentViewer.tsx
interface DocumentViewerProps {
  fileUrl: string;
  fileName: string;
  onClose: () => void;
}

// ResizeHandle.tsx
interface ResizeHandleProps {
  onMouseDown: (e: React.MouseEvent) => void;
}

// useResizePanel.ts
interface UseResizePanelOptions {
  containerRef: React.RefObject<HTMLDivElement>;
  minLeftPx?: number;   // default 300
  minRightPx?: number;  // default 350
  initialPercent?: number; // default 50
}

interface UseResizePanelReturn {
  leftPercent: number;
  handleMouseDown: (e: React.MouseEvent) => void;
  resetRatio: () => void;
}

// useMediaQuery.ts
function useMediaQuery(query: string): boolean;

// Sidebar.tsx - extended props
interface SidebarProps {
  // ...existing props...
  onDocumentSelect?: (doc: Document) => void;
  activeDocumentName?: string | null;
}
```

## Implementation Notes

### App.tsx Layout Logic

```
if (activeDocument && isDesktop):
  <main> becomes:
    <div ref={containerRef} className="flex-1 flex min-w-0">
      <div style={{ width: `${leftPercent}%` }}>  <!-- viewer -->
        <DocumentViewer ... />
      </div>
      <ResizeHandle onMouseDown={handleMouseDown} />
      <div style={{ width: `${100 - leftPercent}%` }}>  <!-- chat -->
        <!-- existing chat area (messages + input), NO PromptSuggestions -->
      </div>
    </div>

else:
  <main> stays as-is (current layout)
```

### useResizePanel Hook Core Logic

```
mousedown on handle:
  - capture startX, startPercent
  - add mousemove + mouseup listeners to window

mousemove:
  - deltaX = currentX - startX
  - containerWidth = containerRef.current.clientWidth
  - deltaPct = (deltaX / containerWidth) * 100
  - newPercent = clamp(startPercent + deltaPct, minLeftPct, 100 - minRightPct)
  - setLeftPercent(newPercent)

  where minLeftPct = (minLeftPx / containerWidth) * 100
  and   minRightPct = (minRightPx / containerWidth) * 100

mouseup:
  - remove listeners
```

### Object URL Lifecycle

- **Create**: En `App.handleUpload`, despues de upload exitoso: `URL.createObjectURL(file)`
- **Revoke**: No se revoca activamente ya que los docs viven toda la sesion. El browser los libera al cerrar la tab. Si en el futuro se agrega "eliminar documento", el revoke iria ahi.

### Mobile Auto-Close

```typescript
// En App.tsx
const isDesktop = useMediaQuery("(min-width: 768px)");

useEffect(() => {
  if (!isDesktop && activeDocument) {
    setActiveDocument(null);
  }
}, [isDesktop]);
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `useResizePanel` - clamp logic, min widths | Jest: mock containerRef, simulate mouse events |
| Unit | `useMediaQuery` - matches/no-matches | Jest: mock `window.matchMedia` |
| Unit | Object URL creation en handleUpload | Jest: mock `URL.createObjectURL` |
| Visual | Split-view layout, resize, mobile hide | Manual: npm run dev, test con browser devtools responsive mode |

## Migration / Rollout

No migration required. Feature es puramente aditiva en frontend. No hay cambios en backend, API, ni datos persistidos. Rollback = revertir el commit.

## Open Questions

Ninguna. Todas las decisiones estan resueltas con el input del usuario.
