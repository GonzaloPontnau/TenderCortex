# Tasks: Document Viewer Panel

## Phase 1: Foundation (types y hooks base)

- [x] 1.1 Agregar campo `fileUrl?: string` a la interface `Document` en `frontend/src/types.ts`
- [x] 1.2 Crear `frontend/src/hooks/useMediaQuery.ts` — hook generico que recibe un media query string y retorna boolean via `window.matchMedia` + listener de cambio
- [x] 1.3 Crear `frontend/src/hooks/useResizePanel.ts` — hook que recibe `containerRef`, `minLeftPx` (default 300), `minRightPx` (default 350), `initialPercent` (default 50); expone `leftPercent`, `handleMouseDown`, `resetRatio`; logica de mousedown/mousemove/mouseup en window con clamp por anchos minimos

## Phase 2: Componentes nuevos

- [x] 2.1 Crear `frontend/src/components/ResizeHandle.tsx` — componente visual: `<div>` con ancho ~6px, cursor `col-resize`, indicador sutil (linea vertical + dots centrales), highlight en hover; recibe `onMouseDown` como prop
- [x] 2.2 Crear `frontend/src/components/DocumentViewer.tsx` — recibe `fileUrl`, `fileName`, `onClose`; renderiza header (nombre del archivo truncado + boton X de cierre) + `<iframe src={fileUrl}>` que ocupa el resto del espacio; estilos consistentes con design system (slate, border-slate-800, rounded)

## Phase 3: Integracion (wiring en Sidebar y App)

- [x] 3.1 Modificar `frontend/src/components/Sidebar.tsx` — agregar props `onDocumentSelect` y `activeDocumentName`; en cada `<li>` de documento: onClick que llame `onDocumentSelect(doc)` si `doc.fileUrl` existe; indicador visual del documento activo (borde orange o bg highlight); ocultar interactividad en mobile via clase `md:` de Tailwind
- [x] 3.2 Modificar `frontend/src/App.tsx` — agregar estado `activeDocument: Document | null`; usar `useMediaQuery("(min-width: 768px)")` para `isDesktop`; usar `useResizePanel` con ref al container split-view; en `handleUpload`: crear `URL.createObjectURL(file)` y guardarlo en el documento; effect para auto-cerrar visor si `!isDesktop`; resetear ratio al cerrar visor
- [x] 3.3 Modificar `frontend/src/App.tsx` layout — condicional: si `activeDocument && isDesktop`, renderizar split-view `[DocumentViewer | ResizeHandle | ChatPanel]` con widths por porcentaje; si no, mantener layout actual; en split-view el chat siempre muestra mensajes + input (nunca PromptSuggestions)

## Phase 4: Validacion visual

- [x] 4.1 Verificar con `npm run build` que no hay errores de TypeScript ni warnings
- [ ] 4.2 Test manual: subir PDF, click en documento, verificar que el visor abre con el PDF visible y el chat funciona al lado
- [ ] 4.3 Test manual: drag del resize handle, verificar que respeta anchos minimos (300px visor, 350px chat)
- [ ] 4.4 Test manual: cerrar visor con boton X, verificar que layout vuelve a normal y mensajes se preservan
- [ ] 4.5 Test manual: abrir devtools responsive mode < 768px, verificar que visor se cierra automaticamente y docs no son clickeables
- [ ] 4.6 Test manual: subir 2 PDFs, cambiar entre ellos en el visor, verificar que el iframe muestra el PDF correcto
