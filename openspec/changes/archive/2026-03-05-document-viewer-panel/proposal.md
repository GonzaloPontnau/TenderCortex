# Proposal: Document Viewer Panel

## Intent

Permitir al usuario visualizar el PDF cargado directamente en la aplicacion, sin salir de la pagina. Al hacer click en un documento del sidebar, se abre un panel visor que muestra el PDF con scroll libre, mientras el chat se mantiene accesible en un panel a la derecha.

## Scope

### In Scope

- Almacenamiento del File object en browser memory (Object URL) durante la sesion
- Panel visor de PDF que reemplaza el area principal cuando se activa
- Chat reubicado en panel derecho junto al visor
- Resize drag handle entre visor y chat
- Boton de cierre para volver al layout normal
- Scroll libre dentro del PDF
- Feature deshabilitada en pantallas mobile

### Out of Scope

- Almacenamiento del PDF en backend
- Navegacion por paginas (paginador, go-to-page)
- Zoom controls
- Anotaciones o highlights sobre el PDF
- Busqueda de texto dentro del PDF

## Affected Areas

| Area | Impacto |
|------|---------|
| `frontend/src/types.ts` | Extender `Document` con `fileUrl` |
| `frontend/src/App.tsx` | Layout condicional (normal vs split-view) |
| `frontend/src/components/Sidebar.tsx` | Click handler en items de documento |
| `frontend/src/components/DocumentViewer.tsx` | Nuevo componente visor PDF |
| `frontend/src/components/ResizeHandle.tsx` | Nuevo componente resize handle |

## Approach

- Usar `URL.createObjectURL(file)` al subir para retener el PDF en memoria del browser
- Renderizar el PDF via `<iframe>` o `<embed>` con el object URL
- Layout con CSS flexbox: sidebar fijo | visor (flex, resizable) | chat (flex, resizable)
- Resize via drag handle con mouse/touch events
- Media query o JS check para deshabilitar en mobile
- Consistente con el design system existente (slate, orange, TailwindCSS)

## Rollback Plan

Revertir los cambios es trivial: eliminar los componentes nuevos y restaurar el layout original en `App.tsx`. No hay cambios en backend ni en persistencia.
