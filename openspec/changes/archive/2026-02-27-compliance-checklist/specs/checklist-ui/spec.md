# Spec: Checklist UI

## Purpose

Panel de checklist integrado en el Sidebar que muestra los requisitos extraidos de los documentos de licitacion, permite filtrar por categoria y marcar el estado de cumplimiento.

## Behavior

### Vista inicial (sin checklist)
- Muestra boton "Generar Checklist" (deshabilitado si no hay documentos)
- Al hacer click, llama al endpoint y muestra loading

### Vista con checklist generado
- Header con resumen: X/Y requisitos cumplidos
- Barra de progreso visual por estado
- Filtros por categoria (chips/tags)
- Lista de items agrupados por categoria
- Cada item muestra: texto, severidad badge, estado toggle
- Click en un item alterna su estado: pending -> compliant -> non_compliant -> not_applicable -> pending

### Interaccion con Sidebar
- Tab toggle: "Documentos" | "Checklist"
- El tab de Checklist solo aparece cuando hay documentos cargados

## Visual Design
- Consistente con el design system existente (slate/orange palette)
- Badge de severidad: mandatory = orange/red, desirable = blue
- Estado: pending = slate, compliant = green, non_compliant = red, not_applicable = gray
- Animaciones sutiles en toggle de estado
