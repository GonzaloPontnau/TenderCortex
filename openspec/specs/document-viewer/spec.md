# Document Viewer Specification

## Purpose

Define el comportamiento del visor de documentos PDF integrado en la aplicacion. Permite al usuario visualizar un PDF cargado en un panel lateral mientras mantiene acceso al chat, todo sin salir de la pagina.

## Requirements

### Requirement: PDF Retention in Browser Memory

El sistema MUST almacenar una referencia al archivo PDF subido (via `URL.createObjectURL`) en el estado del frontend durante la sesion activa. La URL MUST asociarse al `Document` correspondiente en el estado de la aplicacion.

El sistema MUST revocar el Object URL (`URL.revokeObjectURL`) cuando el documento ya no sea necesario (limpieza de sesion o navegacion fuera).

#### Scenario: PDF retenido tras upload exitoso

- GIVEN el usuario arrastra o selecciona un archivo PDF para subir
- WHEN la ingesta se completa exitosamente
- THEN el estado del `Document` incluye un campo `fileUrl` con un blob URL valido
- AND el PDF puede renderizarse usando ese URL

#### Scenario: Multiples documentos retienen sus URLs independientes

- GIVEN el usuario ya subio un documento "A.pdf"
- WHEN sube un segundo documento "B.pdf"
- THEN ambos documentos tienen `fileUrl` distintos y validos
- AND hacer click en cualquiera de los dos abre el PDF correspondiente

### Requirement: Document Viewer Panel Activation

El sistema MUST abrir un panel visor de PDF cuando el usuario hace click en un documento de la lista del sidebar. El panel visor MUST reemplazar el area principal (chat/sugerencias) y reubicar el chat en un panel a la derecha.

El visor MUST NOT activarse si el documento no tiene un `fileUrl` valido.

#### Scenario: Abrir visor al hacer click en documento

- GIVEN hay al menos un documento cargado con `fileUrl` valido
- WHEN el usuario hace click en el item del documento en el sidebar
- THEN el layout cambia a modo split-view: [sidebar | visor PDF | chat]
- AND el visor muestra el contenido del PDF seleccionado
- AND el chat permanece funcional en el panel derecho

#### Scenario: Cambiar de documento en el visor

- GIVEN el visor esta abierto mostrando "A.pdf"
- WHEN el usuario hace click en otro documento "B.pdf" en el sidebar
- THEN el visor actualiza su contenido para mostrar "B.pdf"
- AND el chat no se ve afectado (mensajes se mantienen)

#### Scenario: Click en documento sin fileUrl

- GIVEN existe un documento en la lista cuyo `fileUrl` es `null` o `undefined`
- WHEN el usuario hace click en ese documento
- THEN el visor MUST NOT abrirse
- AND el layout permanece sin cambios

### Requirement: Split-View Layout

Cuando el visor esta activo, el layout MUST organizarse en tres columnas: sidebar (ancho fijo) | visor PDF (flexible) | chat (flexible). El ancho minimo del visor SHOULD ser 300px. El ancho minimo del chat SHOULD ser 350px.

El area principal (sugerencias de prompts) MUST ocultarse cuando el visor esta activo, siendo reemplazada por la vista split (visor + chat).

#### Scenario: Layout split-view con proporciones por defecto

- GIVEN el visor no esta activo y el layout es el normal
- WHEN el usuario abre un documento en el visor
- THEN el sidebar mantiene su ancho fijo (w-72)
- AND el espacio restante se divide aproximadamente 50/50 entre visor y chat
- AND ambos paneles respetan sus anchos minimos

#### Scenario: PromptSuggestions se oculta en split-view

- GIVEN no hay mensajes de chat (estado vacio)
- AND el layout normalmente mostraria las PromptSuggestions
- WHEN el usuario abre un documento en el visor
- THEN las PromptSuggestions no se muestran
- AND el area de chat muestra el input de chat vacio listo para usar

### Requirement: Resizable Panels

El sistema MUST proporcionar un drag handle entre el panel del visor y el panel del chat que permita al usuario redimensionar ambos paneles. El resize MUST respetar los anchos minimos de cada panel.

El drag handle SHOULD tener un indicador visual sutil (linea o dots) y SHOULD cambiar el cursor a `col-resize` al hacer hover.

#### Scenario: Redimensionar paneles via drag

- GIVEN el visor esta abierto en split-view
- WHEN el usuario hace mousedown en el drag handle y arrastra hacia la derecha
- THEN el panel del visor se agranda y el panel del chat se achica
- AND ningun panel baja de su ancho minimo

#### Scenario: Respetar anchos minimos al redimensionar

- GIVEN el visor esta abierto en split-view
- WHEN el usuario arrastra el handle intentando reducir el chat por debajo de 350px
- THEN el chat se detiene en 350px y no se reduce mas

#### Scenario: Drag handle con feedback visual

- GIVEN el visor esta abierto en split-view
- WHEN el usuario hace hover sobre el drag handle
- THEN el cursor cambia a `col-resize`
- AND el handle muestra un indicador visual (highlight sutil)

### Requirement: Close Viewer

El sistema MUST proveer un boton de cierre visible en el panel del visor que restaure el layout original (sidebar + chat completo).

#### Scenario: Cerrar visor y restaurar layout

- GIVEN el visor esta abierto mostrando un PDF
- WHEN el usuario hace click en el boton de cierre (X)
- THEN el visor se cierra
- AND el layout vuelve al estado normal: [sidebar | chat completo]
- AND los mensajes del chat se preservan

#### Scenario: Estado limpio al cerrar

- GIVEN el visor esta abierto y el usuario redimensiono los paneles
- WHEN cierra el visor y luego abre otro documento
- THEN los paneles vuelven a las proporciones por defecto (50/50)

### Requirement: PDF Scroll Navigation

El visor MUST renderizar el PDF completo con scroll libre vertical. El usuario SHOULD poder hacer scroll suave a traves de todas las paginas del documento.

#### Scenario: Scroll a traves de un PDF multi-pagina

- GIVEN el visor muestra un PDF de 20 paginas
- WHEN el usuario hace scroll hacia abajo
- THEN el contenido del PDF se desplaza suavemente mostrando las paginas siguientes
- AND todas las paginas son accesibles via scroll

### Requirement: Mobile Behavior

El visor de documentos MUST NOT estar disponible en pantallas con ancho menor a 768px. En mobile, los items de la lista de documentos MUST NOT tener comportamiento de click para abrir el visor.

#### Scenario: Visor no disponible en mobile

- GIVEN el usuario esta en un dispositivo con pantalla menor a 768px
- WHEN visualiza la lista de documentos en el sidebar
- THEN los items de documentos no tienen indicador de click para abrir visor
- AND hacer click en un documento no produce ningun cambio de layout

#### Scenario: Transicion de desktop a mobile con visor abierto

- GIVEN el visor esta abierto en un viewport de 1200px
- WHEN el usuario reduce el viewport por debajo de 768px (o rota el dispositivo)
- THEN el visor se cierra automaticamente
- AND el layout vuelve al estado normal
