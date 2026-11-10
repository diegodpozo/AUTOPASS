# RESPONSABLES DEL BACKLOG

Relevamiento de **quien es el responsable de cada funcion/historia** del tablero
[backlogAUTOPASS](https://github.com/MarianoJAC/backlogAUTOPASS).

- **Fuente de datos (vigente):** Firebase `backlog/rows2`
  (`https://backlog-dd061-default-rtdb.firebaseio.com/backlog/rows2.json`).
  El `DATA` de `index.html` es solo semilla/fallback; se comparo contra Firebase y
  **difiere en 2 filas** (T20 y T35: el seed las asigna a Diego, Firebase a Mariano)
  y en 3 descripciones con acentos rotos en el seed (T75, T168, T214). Vale Firebase.
- **Fecha del relevamiento:** 01/11/2026.
- **Filas totales:** 320 (mas 13 secciones = 333 elementos).
- **Campos usados:** `responsable`, `estado`, `mvp`, `tipo` (`H` historia de usuario,
  `T` tarea tecnica, `F` funcionalidad/entregable).

## Resumen por responsable

| Responsable | Total | CERRADA | EN CURSO | PENDIENTE | % del tablero |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mariano | 132 | 118 | 3 | 11 | 41.2% |
| Diego | 97 | 75 | 1 | 21 | 30.3% |
| Veronica | 47 | 38 | 7 | 2 | 14.7% |
| Teresa | 44 | 40 | 3 | 1 | 13.8% |

## Reparto por seccion

| Seccion | Total | Reparto |
| --- | ---: | --- |
| HISTORIAS DE USUARIO | 93 | Diego: 41, Mariano: 29, Teresa: 18, Veronica: 5 |
| HISTORIAS DE USUARIO ADMINISTADOR | 61 | Mariano: 35, Veronica: 16, Diego: 5, Teresa: 5 |
| INFRAESTRUCTURA Y LOGICA DE AFORO | 6 | Mariano: 6 |
| DASHBOARD ADMINISTRATIVO | 8 | Mariano: 8 |
| APLICACI?N MOVIL-USUARIO | 12 | Veronica: 12 |
| HARDWARE IOT | 8 | Mariano: 6, Teresa: 2 |
| CALIDAD Y SEGURIDAD | 13 | Mariano: 11, Teresa: 2 |
| DOCUMENTACI?N | 3 | Teresa: 3 |
| ENTREVISTAS | 3 | Veronica: 2, Diego: 1 |
| FUNCIONALIDADES CORE DEL SISTEMA | 51 | Mariano: 18, Teresa: 13, Diego: 11, Veronica: 9 |
| FUNCIONALIDADES INCLUIDAS MVP2 | 29 | Diego: 14, Mariano: 13, Veronica: 2 |
| METRICAS (MVP 4) | 23 | Diego: 21, Veronica: 1, Teresa: 1 |
| MEJORAS ADICIONALES (SEP-OCT 2026) | 10 | Mariano: 6, Diego: 4 |

## Quien hizo cada funcion (detalle por seccion)

### HISTORIAS DE USUARIO

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H1 | Como usuario quiero ver mapa de los estacionamientos | H | MVP 1 | CERRADA | Diego |
| T1 | cargar mapa interactivo en la app | T | MVP 1 | CERRADA | Diego |
| T2 | consultar lista de estacionamientos disponibles en BD | T | MVP 1 | CERRADA | Diego |
| T3 | mostrar iconos en el mapa con su ubicacion | T | MVP 1 | CERRADA | Diego |
| T4 | actualizar estado(libre/ocupado)en tiempo real | T | MVP 1 | CERRADA | Diego |
| H2 | Como usuario quiero filtrar estacionamientos por localidad | H | MVP 3 | CERRADA | Diego |
| T5 | Seleccionar localidad desde menu desplegabe o buscador | T | MVP 3 | CERRADA | Diego |
| T6 | Consultar estacionamientos de esa localidad en BD | T | MVP 3 | CERRADA | Diego |
| T7 | Mostrar solo esos puntos en el mapa | T | MVP 3 | CERRADA | Diego |
| T8 | Permitir cambiar localidad y refrescar resultados | T | MVP 3 | CERRADA | Diego |
| H3 | Como usuario quiero buscar estacionamientos en el mapa | H | MVP 2 | CERRADA | Diego |
| T9 | ingresar texto de busqueda(ej. ITUZAINGO) | T | MVP 2 | CERRADA | Diego |
| T10 | Validar coincidencia con localidades disponibles | T | MVP 2 | CERRADA | Diego |
| T11 | Centrar mapa en la localidad buscada | T | MVP 2 | CERRADA | Diego |
| T12 | mostrar estacionamientos cercanos | T | MVP 2 | CERRADA | Diego |
| H4 | Como usuario quiero ver detalles de un estacionamiento en el mapa | H | MVP 1 | CERRADA | Teresa |
| T13 | seleccionar icono de estacionamiento en el mapa | T | MVP 1 | CERRADA | Teresa |
| T14 | mostar informacion: direccion. cantidad de espacios. tarifas | T | MVP 1 | CERRADA | Teresa |
| T16 | Mostrar boton para reservar diectamente desde el mapa | T | MVP 2 | CERRADA | Diego |
| H5 | Como usuario quiero reservar una espacio desde el mapa | H | MVP 2 | CERRADA | Diego |
| T17 | seleccionar estacionamiento en el mapa | T | MVP 2 | CERRADA | Diego |
| T18 | consultar disponibilidad de espacios | T | MVP 2 | CERRADA | Diego |
| T19 | elegir fecha/hora y vehiculo | T | MVP 2 | CERRADA | Diego |
| T20 | Redirigir a flujo de pago(mercado Pago/tarjeta) | T | MVP 4 | PENDIENTE | Mariano |
| T21 | Confirmar reserva y mostrar en pantalla | T | MVP 2 | CERRADA | Diego |
| H6 | Como usuario quiero listar mis vehiculos | H | MVP 1 | CERRADA | Mariano |
| T22 | consultar mi lista de vehiculos asociados en la BD | T | MVP 1 | CERRADA | Mariano |
| T23 | mostrar en pantalla | T | MVP 1 | CERRADA | Mariano |
| T24 | ordenar por patente o fecha de alta | T | MVP 1 | CERRADA | Mariano |
| T25 | permitir seleccionar vehiculo principal | T | MVP 1 | CERRADA | Mariano |
| H7 | Como usuario quiero dar de alta un vehiculo | H | MVP 1 | CERRADA | Teresa |
| T26 | completar formulario con patente y datos opcionales | T | MVP 1 | CERRADA | Teresa |
| T27 | Validar formato de patente | T | MVP 1 | CERRADA | Teresa |
| T28 | Guardar en BD vinculado al usuario | T | MVP 1 | CERRADA | Teresa |
| T29 | Confirmar alta en pantalla | T | MVP 1 | CERRADA | Teresa |
| H8 | Como usuario quiero reservar una espacio | H | MVP 1 | CERRADA | Veronica |
| T30 | seleccionar fecha y hora de reserva | T | MVP 1 | CERRADA | Veronica |
| T31 | Validar disponibilidad en BD | T | MVP 1 | CERRADA | Veronica |
| T32 | Asociar reserva al vehiculo elegido | T | MVP 1 | CERRADA | Veronica |
| T33 | Guardar reserva en BD | T | MVP 1 | CERRADA | Veronica |
| H9 | Como usuario quiero pagar mi reserva | H | MVP 1 | CERRADA | Mariano |
| T34 | Selecionar metodo de pago(mercado pago/tarjeta) | T | MVP 1 | CERRADA | Mariano |
| T35 | Redirigir a pasarela de pago segura | T | MVP 4 | PENDIENTE | Mariano |
| T36 | Validar transaccion exitosa | T | MVP 1 | CERRADA | Mariano |
| T37 | Guardar comprobante en BD | T | MVP 1 | CERRADA | Mariano |
| T38 | Mostrar confirmacion en pantalla | T | MVP 1 | CERRADA | Mariano |
| H10 | Como usuario quiero ingresar al estacionamiento con mi patente | H | MVP 1 | CERRADA | Mariano |
| T39 | Capturar patente con camara en ingreso | T | MVP 1 | CERRADA | Mariano |
| T40 | Validar contra reservas activas en BD | T | MVP 1 | CERRADA | Mariano |
| T41 | Enviar se?al a barrera para abrir | T | MVP 1 | CERRADA | Mariano |
| T42 | Registrar hora de ingreso | T | MVP 1 | CERRADA | Mariano |
| H11 | Como usuario quiero egresar del estacionamiento con mi patente | H | MVP 1 | CERRADA | Mariano |
| T43 | capturar patente con camara en salida | T | MVP 1 | CERRADA | Mariano |
| T44 | Validar contra reservas activas en BD | T | MVP 1 | CERRADA | Mariano |
| T45 | Enviar se?al a barrera para abrir | T | MVP 1 | CERRADA | Mariano |
| T46 | Registrar hora de salida y calcular tiempo de estancia | T | MVP 1 | CERRADA | Mariano |
| H12 | Como usuario quiero ver mis reservas historicas | H | MVP 1 | CERRADA | Diego |
| T47 | Consultar reservas pasadas en BD | T | MVP 1 | CERRADA | Diego |
| T48 | Mostrar lista en pantalla | T | MVP 1 | CERRADA | Diego |
| T49 | Permitir filtrar por fecha o vehiculo | T | MVP 1 | CERRADA | Diego |
| H13 | Como usuario quiero recibir notificaciones de mis reservas | H | MVP 1 | CERRADA | Diego |
| T50 | Enviar email con confirmacion y comprobante de pago | T | MVP 1 | CERRADA | Diego |
| T51 | Notificar recordatorio antes de la hora de ingreso | T | MVP 2 | CERRADA | Diego |
| T52 | Mostrar alertas en la app | T | MVP 4 | PENDIENTE | Diego |
| H22 | Como usuario quiero iniciar sesi?n | H | MVP 1 | CERRADA | Diego |
| T85 | Crear pantalla login | T | MVP 1 | CERRADA | Diego |
| T86 | Validar Credenciales | T | MVP 1 | CERRADA | Diego |
| T87 | Mostrar errores | T | MVP 1 | CERRADA | Diego |
| H23 | Como usuario quiero ver espacios disponibles | H | MVP 1 | CERRADA | Teresa |
| T88 | mostrar espacios | T | MVP 1 | CERRADA | Teresa |
| T89 | Actualizar en tiempo real | T | MVP 1 | CERRADA | Teresa |
| H24 | como usuario quiero reservar un espacio | H | MVP 1 | CERRADA | Teresa |
| T91 | seleccionar espacio | T | MVP 1 | CERRADA | Teresa |
| T92 | elegir fecha y hora | T | MVP 1 | CERRADA | Teresa |
| T93 | confirmar reserva | T | MVP 1 | CERRADA | Teresa |
| H25 | Como usuario quiero cancelar reserva | H | MVP 1 | CERRADA | Diego |
| T94 | buscar reserva | T | MVP 1 | CERRADA | Diego |
| T95 | cancelar reserva | T | MVP 1 | CERRADA | Diego |
| T96 | liberar espacio | T | MVP 1 | CERRADA | Diego |
| H26 | Como usuario quiero registar ingreso | H | MVP 1 | CERRADA | Teresa |
| T97 | Registrar hora | T | MVP 1 | CERRADA | Teresa |
| T98 | asignar espacio | T | MVP 1 | CERRADA | Teresa |
| H27 | como usuario quiero registar salida | H | MVP 1 | CERRADA | Diego |
| T99 | Registrar salida | T | MVP 1 | CERRADA | Diego |
| T100 | Liberar espacio | T | MVP 1 | CERRADA | Diego |
| T101 | Calcular tiempo | T | MVP 1 | CERRADA | Diego |
| H28 | Como usuario quiero ver costo | H | MVP 1 | CERRADA | Mariano |
| T102 | Calcular tarifa | T | MVP 1 | CERRADA | Mariano |
| T103 | mostrar monto | T | MVP 1 | CERRADA | Mariano |
| H29 | Como usuario quiero pagar | H | MVP 1 | CERRADA | Mariano |
| T104 | selecionar medio de pago | T | MVP 1 | CERRADA | Mariano |
| T105 | confirmar pago | T | MVP 1 | CERRADA | Mariano |
| T106 | generar comprobante | T | MVP 1 | CERRADA | Mariano |

### HISTORIAS DE USUARIO ADMINISTADOR

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H31 | Como administrador quiero ver espacios | H | MVP 1 | CERRADA | Veronica |
| T109 | visualizar estado | T | MVP 1 | CERRADA | Veronica |
| T110 | actualizar datos | T | MVP 1 | CERRADA | Veronica |
| H32 | Como administrador quiero registrar ingresos | H | MVP 1 | CERRADA | Veronica |
| T111 | cargar datos del vehiculo | T | MVP 1 | CERRADA | Veronica |
| T112 | asignar espacio | T | MVP 1 | CERRADA | Veronica |
| H33 | como administrador quiero asignar espacios | H | MVP 1 | CERRADA | Mariano |
| T113 | seleccionar espacio | T | MVP 1 | CERRADA | Mariano |
| T114 | confirmacion asigancion | T | MVP 1 | CERRADA | Mariano |
| H34 | como administrador quiero ver ocupacion | H | MVP 1 | CERRADA | Mariano |
| T115 | calcular ocupacion | T | MVP 1 | CERRADA | Mariano |
| T116 | mostrar datos | T | MVP 1 | CERRADA | Mariano |
| H36 | Como administrador quiero generar reportes | H | MVP 1 | CERRADA | Mariano |
| T119 | seleccionar periodo | T | MVP 1 | CERRADA | Mariano |
| T120 | generar reporte | T | MVP 1 | CERRADA | Mariano |
| H37 | Como administador quiero ver reservas | H | MVP 1 | CERRADA | Mariano |
| T121 | listar reservas filtrar | T | MVP 1 | CERRADA | Mariano |
| T122 | filtrar | T | MVP 1 | CERRADA | Mariano |
| H58 | Como administrador quiero bloquear espacios | H | MVP 4 | PENDIENTE | Mariano |
| T123 | seleccionar espacios | T | MVP 4 | PENDIENTE | Mariano |
| T124 | marcar como bloqueado | T | MVP 4 | PENDIENTE | Mariano |
| H14 | Como administrador quiero loguearme en el panel de gestion | H | MVP 1 | CERRADA | Veronica |
| T53 | Ingresar credenciales de administardor | T | MVP 1 | CERRADA | Veronica |
| T54 | validar contra BD con JWT | T | MVP 1 | CERRADA | Veronica |
| T55 | Generar token de sesion | T | MVP 1 | CERRADA | Veronica |
| T56 | Mostar acceso al dashboard | T | MVP 1 | CERRADA | Veronica |
| H15 | Como administrador quiero visualizar el estado de los espacios en tiempo real | H | MVP 1 | CERRADA | Veronica |
| T57 | consultar oupacion desde sensores via MQTT | T | MVP 1 | CERRADA | Veronica |
| T58 | Mostrar mapa de espacios ocupadas/libres en el dashboard | T | MVP 1 | CERRADA | Veronica |
| T59 | Actualizar automaticamente cada pocos segundos | T | MVP 1 | CERRADA | Veronica |
| T60 | Permitir filtrar por sector o nivel | T | MVP 1 | CERRADA | Veronica |
| H16 | Como administrador quiero gestionar las reservas de usuarios | H | MVP 1 | CERRADA | Diego |
| T61 | Consultar reservas activas en BD | T | MVP 1 | CERRADA | Diego |
| T62 | Mostrar lista con datos de usuario y vehiculo | T | MVP 1 | CERRADA | Diego |
| T63 | Permitir cancelar o modificar reservas | T | MVP 1 | CERRADA | Diego |
| T64 | Registrar cambios en BD y notificar al usuario | T | MVP 1 | CERRADA | Diego |
| H17 | Como administrador quiero ver el historial de ingresos y egresos | H | MVP 1 | CERRADA | Mariano |
| T65 | Consultar registros de camaras de patente en BD | T | MVP 1 | CERRADA | Mariano |
| T66 | Mostrar lista con hora de ingreso/egreso y duracion | T | MVP 1 | CERRADA | Mariano |
| T67 | Permitir exportar a CSV/Excel | T | MVP 1 | CERRADA | Mariano |
| T68 | Filtrar por fechas o vehiculos | T | MVP 1 | CERRADA | Mariano |
| H18 | Como administrador quiero generar reportes de uso del estacionamiento | H | MVP 1 | CERRADA | Mariano |
| T69 | Consultar metricas de ocupacion promedio | T | MVP 1 | CERRADA | Mariano |
| T70 | Calcular ingresos por reservas y pagos | T | MVP 1 | CERRADA | Mariano |
| T71 | Mostrar gr?ficos en el dashboard | T | MVP 1 | CERRADA | Mariano |
| T72 | Exportar reporte en PDF/Excel | T | MVP 1 | CERRADA | Mariano |
| H19 | Como administrador quiero configurar tarifas y m�todos de pago | H | MVP 1 | CERRADA | Mariano |
| T73 | Consultar tarifas actuales en BD | T | MVP 1 | CERRADA | Mariano |
| T74 | Modificar valores de tarifa por hora o d?a | T | MVP 1 | CERRADA | Mariano |
| T75 | Configurar integracion con Mercado Pago/tarjetas | T | MVP 4 | PENDIENTE | Mariano |
| T76 | Guardar cambios y aplicarlos en reservas futuras | T | MVP 1 | CERRADA | Mariano |
| H20 | Como administrador quiero gestionar los estacionamientos en el mapa | H | MVP 2 | CERRADA | Teresa |
| T77 | Dar de alta un nuevo estacionamiento con ubicacion y capacidad | T | MVP 2 | CERRADA | Teresa |
| T78 | Editar datos de estacionamientos existentes | T | MVP 2 | CERRADA | Teresa |
| T79 | Eliminar estacionamientos obsoletos | T | MVP 2 | CERRADA | Teresa |
| T80 | Validar cambios en BD y reflejarlos en el mapa interactivo | T | MVP 2 | CERRADA | Teresa |
| H21 | Como administrador quiero recibir alertas de incidentes | H | MVP 4 | PENDIENTE | Mariano |
| T81 | Detectar fallos en sensores o barreras | T | MVP 4 | PENDIENTE | Mariano |
| T82 | Mostrar notificacion en el dashboard | T | MVP 4 | PENDIENTE | Mariano |
| T83 | Registrar incidentes en BD | T | MVP 4 | PENDIENTE | Mariano |
| T84 | Permitir marcar como resuelto | T | MVP 4 | PENDIENTE | Mariano |

### INFRAESTRUCTURA Y LOGICA DE AFORO

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H38 | Como administrador. quiero configurar el sistema de aforo | H | MVP 1 | CERRADA | Mariano |
| T127 | Setup inicial de fastapi y db sqlite con tabla parking_aforo | T | MVP 1 | CERRADA | Mariano |
| T128 | Crear endpoint /access/validate-plate para recibir datos del m?dulo alpr | T | MVP 1 | CERRADA | Mariano |
| T129 | Implementar script de inventario y gesti?n de estados de espacios | T | MVP 1 | CERRADA | Mariano |
| T130 | Integrar alpr con python (opencv/easyocr) para captura de im?genes | T | MVP 1 | CERRADA | Mariano |
| T131 | Configurar broker mqtt para comunicaci?n con barreras | T | MVP 1 | CERRADA | Mariano |

### DASHBOARD ADMINISTRATIVO

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H39 | Como administrador. quiero ver el aforo en tiempo real | H | MVP 1 | CERRADA | Mariano |
| T132 | Visualizar contador de ocupacion en tiempo real | T | MVP 1 | CERRADA | Mariano |
| H40 | Como administrador. quiero consultar el log de actividad | H | MVP 1 | CERRADA | Mariano |
| T133 | Mostrar tabla con fotos de evidencia de accesos | T | MVP 1 | CERRADA | Mariano |
| H41 | Como administrador. quiero controlar barreras de forma manual | H | MVP 1 | CERRADA | Mariano |
| T134 | Implementar botones de apertura/cierre manual | T | MVP 1 | CERRADA | Mariano |
| H42 | Como administrador. quiero gestionar campa?as y promociones | H | MVP 1 | CERRADA | Mariano |
| T135 | Crud para cupones y promociones | T | MVP 1 | CERRADA | Mariano |

### APLICACI?N MOVIL-USUARIO

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H43 | Como usuario. quiero acceder a la app desde mi celular | H | MVP 4 | EN CURSO | Veronica |
| T136 | Setup de expo (react native) y navegaci?n inicial | T | MVP 4 | EN CURSO | Veronica |
| H44 | Como usuario. quiero ver el aforo en la home | H | MVP 4 | EN CURSO | Veronica |
| T137 | Sincronizar contador de aforo mediante api | T | MVP 4 | EN CURSO | Veronica |
| H45 | Como usuario. quiero canjear puntos de fidelizaci?n | H | MVP 3 | CERRADA | Veronica |
| T138 | Pantalla de canje de puntos por beneficios | T | MVP 3 | CERRADA | Veronica |
| H46 | Como usuario. quiero ingresar cupones de descuento | H | MVP 3 | CERRADA | Veronica |
| T139 | Modulo de ingreso y validaci?n de c?digos | T | MVP 3 | CERRADA | Veronica |
| H47 | Como usuario. quiero recibir notificaciones de mi reserva | H | MVP 2 | CERRADA | Veronica |
| T140 | Avisos de ingreso y recordatorios de salida | T | MVP 2 | CERRADA | Veronica |
| H48 | Como usuario. quiero un m?todo de contingencia si falla el alpr | H | MVP 3 | CERRADA | Veronica |
| T141 | Generador de qr din?mico como plan b | T | MVP 3 | CERRADA | Veronica |

### HARDWARE IOT

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H49 | Como operador. quiero que el hardware publique eventos | H | MVP 1 | CERRADA | Mariano |
| T142 | Firmware para publicaci?n mqtt de eventos y simulaci?n | T | MVP 1 | CERRADA | Mariano |
| H50 | Como operador. quiero que el hardware responda a comandos | H | MVP 1 | CERRADA | Mariano |
| T143 | Suscripci?n a comando open y control de barrera | T | MVP 1 | CERRADA | Mariano |
| H51 | Como operador. quiero mostrar mensajes en pantalla local | H | MVP 4 | EN CURSO | Teresa |
| T144 | Ui local con lcd i2c | T | MVP 4 | EN CURSO | Teresa |
| H52 | Como operador. quiero evitar accidentes en la barrera | H | MVP 4 | EN CURSO | Mariano |
| T145 | L?gica anti-colisi?n con sensor de seguridad | T | MVP 4 | EN CURSO | Mariano |

### CALIDAD Y SEGURIDAD

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H53 | Como administrador. quiero validar el flujo completo del sistema | H | MVP 1 | CERRADA | Mariano |
| T146 | Prueba de flujo completo: alpr -> pago -> salida | T | MVP 1 | CERRADA | Mariano |
| H54 | Como administrador. quiero probar el sistema bajo carga | H | MVP 3 | CERRADA | Teresa |
| T147 | Pruebas de estr?s con aforo concurrente | T | MVP 3 | CERRADA | Teresa |
| H55 | Como administrador. quiero garantizar la seguridad de acceso | H | MVP 1 | CERRADA | Mariano |
| T148 | Implementaci?n de jwt y cifrado en api | T | MVP 1 | CERRADA | Mariano |
| T236 | Endurecer la API: JWT con iat/jti/token_type, logout que revoca el token, guard de SECRET_KEY demo, CORS explicito, PII enmascarada en logs y rate-limit 30/min en mutadores admin | T | MVP 4 | CERRADA | Mariano |
| T237 | Autenticar el nodo ALPR en validate-plate/exit-plate/validate-qr con X-Node-Secret (red local sin secreto) | T | MVP 4 | CERRADA | Mariano |
| T238 | Remediar N+1 en listados de reservas: selectinload(Reservation.user) en repos y workers + limpieza de duplicado get_unpaid_overdue | T | MVP 4 | CERRADA | Mariano |
| T239 | REFACTORIZACION: refactorizacion general del codigo backend y frontend | T | MVP 4 | CERRADA | Mariano |
| T240 | MODULARIZACION: division del codigo en modulos reutilizables | T | MVP 4 | CERRADA | Mariano |
| T241 | CI Y COBERTURA DE TESTS: pipeline de GitHub Actions reactivado con gate de cobertura | T | MVP 4 | CERRADA | Mariano |
| T242 | Seguridad: proteger heartbeat y aislar pisos por sede | T | MVP 4 | CERRADA | Mariano |

### DOCUMENTACI?N

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H56 | Documentar para el MVP1 | H | MVP 1 | CERRADA | Teresa |
| T149 | presentacion en power | T | MVP 1 | CERRADA | Teresa |
| T150 | recopilacion de datos | T | MVP 1 | CERRADA | Teresa |

### ENTREVISTAS

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H57 | Entrevista con posibles clientes | H | MVP 1 | CERRADA | Veronica |
| T151 | san juan de dios | T | MVP 1 | CERRADA | Veronica |
| T152 | estacionamiento Moron | T | MVP 1 | CERRADA | Diego |

### FUNCIONALIDADES CORE DEL SISTEMA

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| F01 | ARQUITECTURA DE DATOS Y PERSISTENCIA | F | MVP 2 | CERRADA | Veronica |
| T168 | Diseñar el modelo relacional en SQLAlchemy | T | MVP 4 | PENDIENTE | Veronica |
| T169 | Implementar inyeccion de dependencias para sesiones BD | T | MVP 2 | CERRADA | Veronica |
| T170 | Desarrollo del sistema de migraciones y parches | T | MVP 2 | CERRADA | Veronica |
| F02 | MOTOR DE RECONOCIMIENTO (ALPR) | F | MVP 2 | CERRADA | Mariano |
| T171 | Integracion de EasyOCR con procesamiento asincronico | T | MVP 2 | CERRADA | Mariano |
| T172 | Algoritmo de consenso de patentes para validacion | T | MVP 2 | CERRADA | Mariano |
| T173 | Pre-procesamiento de imagenes con OpenCV | T | MVP 2 | CERRADA | Mariano |
| F03 | SERVICIOS FINANCIEROS (BILLING SERVICE) | F | MVP 2 | CERRADA | Teresa |
| T174 | Logica centralizada para calculo de deudas por estadia | T | MVP 2 | CERRADA | Teresa |
| T174b | Sistema de gamificacion: generacion automatica Puntos | T | MVP 2 | CERRADA | Teresa |
| T174c | Avisar al usuario los puntos ganados al pagar una reserva | T | MVP 2 | CERRADA | Teresa |
| T175 | Modelado de tarifas dinamicas gestionadas desde DB | T | MVP 2 | CERRADA | Teresa |
| F04 | COMUNICACION Y CONTROL DE HARDWARE | F | MVP 2 | CERRADA | Diego |
| T175b | Protocolo de comunicacion MQTT para telemetria | T | MVP 2 | CERRADA | Diego |
| T175c | Implementacion de comandos remotos (OPEN. CLOSE) via MQTT | T | MVP 2 | CERRADA | Diego |
| T175d | Sistema de logs de eventos de hardware para auditoria | T | MVP 2 | PENDIENTE | Diego |
| F05 | NUCLEO DE LA API Y SEGURIDAD | F | MVP 3 | CERRADA | Mariano |
| T176 | Ruteo modular con FastAPI para escalabilidad | T | MVP 3 | CERRADA | Mariano |
| T177 | Esquemas de validacion Pydantic para integridad | T | MVP 3 | CERRADA | Mariano |
| T177b | Sistema de autenticacion y autorizacion JWT | T | MVP 3 | CERRADA | Mariano |
| F06 | GESTION DE FLUJO DE VEHICULOS | F | MVP 3 | CERRADA | Teresa |
| T15 | consultar disponibilidad en tiempo real | T | MVP 3 | CERRADA | Teresa |
| T178 | Logica de vinculacion automatica Patente-Vehiculo-Usuario | T | MVP 3 | CERRADA | Teresa |
| T179 | Control de aforo en tiempo real con contadores globales | T | MVP 3 | CERRADA | Teresa |
| T179b | Validacion de estados para evitar errores de registro | T | MVP 3 | CERRADA | Teresa |
| F07 | INFRAESTRUCTURA Y DESPLIEGUE ONLINE | F | MVP 3 | CERRADA | Mariano |
| T196 | Migrar la base de datos de local/Turso a Postgres online (Neon) con script de migraci?n | T | MVP 3 | CERRADA | Mariano |
| T197 | Eliminar consultas N+1 y paralelizar la carga del dashboard | T | MVP 3 | CERRADA | Mariano |
| T198 | Arrancar el servidor sin --reload y abrir el navegador cuando responde | T | MVP 3 | CERRADA | Mariano |
| T199 | Automatizar instalaci?n y arranque: setup_backend.bat, run_server.ps1 y encoding UTF-8 | T | MVP 3 | CERRADA | Mariano |
| H72 | Como administrador quiero registrar reclamos y darles seguimiento con tickets | H | MVP 3 | CERRADA | Mariano |
| T200 | Implementar modelo, API y gesti?n de tickets de reclamo | T | MVP 3 | CERRADA | Mariano |
| T201 | Agregar soporte visual de tickets en el dashboard | T | MVP 3 | CERRADA | Mariano |
| H73 | Como administrador quiero estad?sticas y avisos del motor OCR en c?mara | H | MVP 3 | CERRADA | Diego |
| T202 | Medir tiempos de lectura de patentes y guardarlos en BD | T | MVP 3 | CERRADA | Diego |
| T203 | Mostrar panel de estad?sticas OCR en el dashboard | T | MVP 3 | CERRADA | Diego |
| T204 | Mostrar mensajes y avisos de eventos de c?mara v?a WebSocket | T | MVP 3 | CERRADA | Diego |
| T205 | Mejorar la lectura de patentes: modo de lectura, regex LATAM, QR y OCR (RapidOCR/PaddleOCR) | T | MVP 3 | CERRADA | Diego |
| T206 | Implementar recuperaci?n de sesi?n y restauraci?n del pipeline EasyOCR | T | MVP 3 | CERRADA | Diego |
| F08 | UI Y EXPERIENCIA | F | MVP 3 | CERRADA | Diego |
| T213 | Redise?o responsive del dashboard y landing | T | MVP 3 | CERRADA | Mariano |
| F09 | MANTENIMIENTO Y GENERAL | F | MVP 3 | CERRADA | Veronica |
| T215 | Fix de cancelaci?n de reservas y limpieza de setup | T | MVP 3 | CERRADA | Teresa |
| T216 | Deshabilitar CI pipeline temporalmente | T | MVP 3 | CERRADA | Veronica |
| T217 | Varios cambios y mejoras generales | T | MVP 3 | CERRADA | Teresa |
| T214 | Integracion de hardware Arduino con servomotores para barreras | T | MVP 4 | EN CURSO | Mariano |
| F10 | REALIZACION DE MAQUETA | F | MVP 3 | EN CURSO | Veronica |
| T218 | Construcci?n de la maqueta | T | MVP 3 | EN CURSO | Veronica |
| T219 | Decoraci?n de la maqueta | T | MVP 3 | EN CURSO | Teresa |
| T220 | Mecanizaci?n de la maqueta | T | MVP 3 | EN CURSO | Veronica |

### FUNCIONALIDADES INCLUIDAS MVP2

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H59 | Como administrador quiero gestionar multiples sucursales | H | MVP 2 | CERRADA | Mariano |
| T180 | implementar branch isolation con datos separados por sucursal | T | MVP 2 | CERRADA | Mariano |
| T181 | crear endpoint de validacion de QR en acceso | T | MVP 2 | CERRADA | Mariano |
| T182 | implementar cancelacion automatica de reservas impagas | T | MVP 2 | CERRADA | Mariano |
| T183 | soportar reservas multi-tipo: dia, semana, mes | T | MVP 2 | CERRADA | Mariano |
| H60 | Como desarrollador quiero modularizar el frontend | H | MVP 2 | CERRADA | Diego |
| T184 | refactorizar dashboard en modulos ES6 separados | T | MVP 2 | CERRADA | Diego |
| H61 | Como administrador quiero ver reportes financieros | H | MVP 2 | CERRADA | Mariano |
| T185 | implementar reportes financieros con filtros y exportacion CSV | T | MVP 2 | CERRADA | Mariano |
| H62 | Como administrador quiero configurar precios trimodales | H | MVP 2 | CERRADA | Mariano |
| T186 | implementar tarifas diferenciadas por tipo de vehiculo | T | MVP 2 | CERRADA | Mariano |
| H63 | Como administrador quiero ver ocupacion en tiempo real con WebSockets | H | MVP 2 | CERRADA | Mariano |
| T187 | implementar WebSockets para actualizacion en tiempo real | T | MVP 2 | CERRADA | Mariano |
| H64 | Como administrador quiero gestionar aforo inteligente | H | MVP 2 | CERRADA | Mariano |
| T188 | implementar plazas fijas para periodo largo y aforo de paso | T | MVP 2 | CERRADA | Mariano |
| H65 | Como administrador quiero recibir notificaciones in-app | H | MVP 2 | CERRADA | Diego |
| T189 | implementar servicio de notificaciones in-app | T | MVP 2 | CERRADA | Diego |
| H66 | Como usuario quiero un tour interactivo de onboarding | H | MVP 2 | CERRADA | Diego |
| T190 | implementar tour interactivo de onboarding | T | MVP 2 | CERRADA | Diego |
| H67 | Como administrador quiero usar un reloj virtual | H | MVP 2 | CERRADA | Diego |
| T191 | implementar sistema de reloj virtual | T | MVP 2 | CERRADA | Diego |
| H68 | Como administrador quiero soft-delete de usuarios | H | MVP 2 | CERRADA | Veronica |
| T192 | implementar soft-delete de usuarios con anonimizacion | T | MVP 2 | CERRADA | Veronica |
| H69 | Como usuario quiero ver numeros con separador de miles | H | MVP 2 | CERRADA | Diego |
| T193 | implementar separador de miles universal con formatNum() | T | MVP 2 | CERRADA | Diego |
| H70 | Como administrador quiero RBAC descentralizado | H | MVP 2 | CERRADA | Diego |
| T194 | implementar RBAC con aislamiento de datos por sucursal | T | MVP 2 | CERRADA | Diego |
| H71 | Optimizar avisos del sistema | H | MVP 2 | CERRADA | Diego |
| T195 | mejorar los avisos, dividiendolos en 3 posibles: exito / info / error | T | MVP 2 | CERRADA | Diego |

### METRICAS (MVP 4)

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| H74 | Como administrador quiero consultar un portal de metricas del sistema | H | MVP 4 | EN CURSO | Diego |
| H75 | Como administrador quiero ver la actividad de entradas y salidas por hora desde el primer dato | H | MVP 4 | PENDIENTE | Diego |
| H76 | Como administrador quiero consultar el rendimiento del motor OCR/ALPR en el tiempo | H | MVP 4 | PENDIENTE | Diego |
| H77 | Como administrador quiero ver la evolucion de la recaudacion y metodos de pago | H | MVP 4 | PENDIENTE | Diego |
| H78 | Como administrador quiero que el grafico siga en vivo el paso del tiempo | H | MVP 4 | PENDIENTE | Diego |
| H79 | Como administrador quiero recorrer el historico hasta el primer dato del sistema | H | MVP 4 | PENDIENTE | Diego |
| H80 | Como administrador de sucursal quiero ver las metricas acotadas a mi sucursal | H | MVP 4 | PENDIENTE | Diego |
| T221 | crear pagina /metricas con lista de metricas, KPIs y navegacion | T | MVP 4 | PENDIENTE | Diego |
| T222 | agregar boton de METRICAS en el sidebar del dashboard (global y sucursal) | T | MVP 4 | PENDIENTE | Diego |
| T223 | endpoint GET /v1/reports/metrics/access-activity con bucketizado horario | T | MVP 4 | PENDIENTE | Diego |
| T224 | grafico de actividad de accesos: entradas y salidas por hora | T | MVP 4 | PENDIENTE | Diego |
| T225 | endpoint GET /v1/reports/ocr-activity con serie completa de latencia OCR | T | MVP 4 | PENDIENTE | Diego |
| T226 | grafico de curva de latencia OCR con promedio, maximo y minimo | T | MVP 4 | PENDIENTE | Diego |
| T227 | metrica de recaudacion con evolucion de ingresos y metodos de pago | T | MVP 4 | PENDIENTE | Diego |
| T228 | componente reutilizable de controles de grafico movil: seguir en vivo, ventana, INICIO/FINAL y deslizador | T | MVP 4 | PENDIENTE | Diego |
| T229 | eje X de tiempo real (escala lineal) con ticks adaptativos por dia/hora | T | MVP 4 | PENDIENTE | Diego |
| T230 | filtro por sucursal respetando el rol del administrador | T | MVP 4 | PENDIENTE | Diego |
| T231 | autenticacion y autorizacion de la seccion METRICAS (admin y local_admin) | T | MVP 4 | PENDIENTE | Diego |
| T232 | pruebas automatizadas de los endpoints de metricas | T | MVP 4 | PENDIENTE | Diego |
| T233 | exportar reportes de metricas en CSV/Excel | T | MVP 4 | PENDIENTE | Diego |
| T234 | MANUAL DE USUARIO | T | MVP 4 | PENDIENTE | Veronica |
| T235 | MANUAL DE IMPLEMENTACION | T | MVP 4 | PENDIENTE | Teresa |
| T243 | mapa de calor de ocupacion: autos por hora en la pestana Metricas | T | MVP 4 | CERRADA | Diego |

### MEJORAS ADICIONALES (SEP-OCT 2026)

| ID | Funcion / historia | Tipo | MVP | Estado | Responsable |
| --- | --- | --- | --- | --- | --- |
| T244 | PWA instalable: manifest, service worker con precache y safe areas | T | MVP 4 | CERRADA | Mariano |
| T245 | Login con OAuth (Google) en el portal de cliente | T | MVP 4 | CERRADA | Mariano |
| T246 | Limites por usuario: maximo 5 vehiculos y 5 reservas, sin reservas en paralelo en otra sucursal | T | MVP 4 | CERRADA | Diego |
| T247 | Pago manual en CAJA y KPIs de recaudacion efectivo/digital | T | MVP 4 | CERRADA | Mariano |
| T248 | Vouchers: descuento aplicado al total, ubicacion de canje en promos y reimpresion | T | MVP 4 | CERRADA | Diego |
| T249 | Sistema integral de notificaciones tipificadas con globito en el dashboard | T | MVP 4 | CERRADA | Mariano |
| T250 | Subida de archivos/adjuntos en tickets de reclamo | T | MVP 4 | CERRADA | Diego |
| T251 | Ajuste financiero al editar reservas pagadas y devolucion en efectivo imputada al reporte | T | MVP 4 | CERRADA | Mariano |
| T252 | Grilla horaria 24h con selector INICIO/FIN y ocupacion de reservas pagadas en /parking/status | T | MVP 4 | CERRADA | Mariano |
| T253 | Tarifario por sucursal: fix del calculo de tarifas por sede | T | MVP 4 | CERRADA | Diego |

## Tareas abiertas por responsable

Solo las filas que **no** estan `CERRADA` (PENDIENTE o EN CURSO).

### Mariano (14 abiertas)

| ID | Funcion / historia | MVP | Estado |
| --- | --- | --- | --- |
| T20 | Redirigir a flujo de pago(mercado Pago/tarjeta) | MVP 4 | PENDIENTE |
| T35 | Redirigir a pasarela de pago segura | MVP 4 | PENDIENTE |
| H58 | Como administrador quiero bloquear espacios | MVP 4 | PENDIENTE |
| T123 | seleccionar espacios | MVP 4 | PENDIENTE |
| T124 | marcar como bloqueado | MVP 4 | PENDIENTE |
| T75 | Configurar integracion con Mercado Pago/tarjetas | MVP 4 | PENDIENTE |
| H21 | Como administrador quiero recibir alertas de incidentes | MVP 4 | PENDIENTE |
| T81 | Detectar fallos en sensores o barreras | MVP 4 | PENDIENTE |
| T82 | Mostrar notificacion en el dashboard | MVP 4 | PENDIENTE |
| T83 | Registrar incidentes en BD | MVP 4 | PENDIENTE |
| T84 | Permitir marcar como resuelto | MVP 4 | PENDIENTE |
| H52 | Como operador. quiero evitar accidentes en la barrera | MVP 4 | EN CURSO |
| T145 | L?gica anti-colisi?n con sensor de seguridad | MVP 4 | EN CURSO |
| T214 | Integracion de hardware Arduino con servomotores para barreras | MVP 4 | EN CURSO |

### Diego (22 abiertas)

| ID | Funcion / historia | MVP | Estado |
| --- | --- | --- | --- |
| T52 | Mostrar alertas en la app | MVP 4 | PENDIENTE |
| T175d | Sistema de logs de eventos de hardware para auditoria | MVP 2 | PENDIENTE |
| H74 | Como administrador quiero consultar un portal de metricas del sistema | MVP 4 | EN CURSO |
| H75 | Como administrador quiero ver la actividad de entradas y salidas por hora desde el primer dato | MVP 4 | PENDIENTE |
| H76 | Como administrador quiero consultar el rendimiento del motor OCR/ALPR en el tiempo | MVP 4 | PENDIENTE |
| H77 | Como administrador quiero ver la evolucion de la recaudacion y metodos de pago | MVP 4 | PENDIENTE |
| H78 | Como administrador quiero que el grafico siga en vivo el paso del tiempo | MVP 4 | PENDIENTE |
| H79 | Como administrador quiero recorrer el historico hasta el primer dato del sistema | MVP 4 | PENDIENTE |
| H80 | Como administrador de sucursal quiero ver las metricas acotadas a mi sucursal | MVP 4 | PENDIENTE |
| T221 | crear pagina /metricas con lista de metricas, KPIs y navegacion | MVP 4 | PENDIENTE |
| T222 | agregar boton de METRICAS en el sidebar del dashboard (global y sucursal) | MVP 4 | PENDIENTE |
| T223 | endpoint GET /v1/reports/metrics/access-activity con bucketizado horario | MVP 4 | PENDIENTE |
| T224 | grafico de actividad de accesos: entradas y salidas por hora | MVP 4 | PENDIENTE |
| T225 | endpoint GET /v1/reports/ocr-activity con serie completa de latencia OCR | MVP 4 | PENDIENTE |
| T226 | grafico de curva de latencia OCR con promedio, maximo y minimo | MVP 4 | PENDIENTE |
| T227 | metrica de recaudacion con evolucion de ingresos y metodos de pago | MVP 4 | PENDIENTE |
| T228 | componente reutilizable de controles de grafico movil: seguir en vivo, ventana, INICIO/FINAL y deslizador | MVP 4 | PENDIENTE |
| T229 | eje X de tiempo real (escala lineal) con ticks adaptativos por dia/hora | MVP 4 | PENDIENTE |
| T230 | filtro por sucursal respetando el rol del administrador | MVP 4 | PENDIENTE |
| T231 | autenticacion y autorizacion de la seccion METRICAS (admin y local_admin) | MVP 4 | PENDIENTE |
| T232 | pruebas automatizadas de los endpoints de metricas | MVP 4 | PENDIENTE |
| T233 | exportar reportes de metricas en CSV/Excel | MVP 4 | PENDIENTE |

### Veronica (9 abiertas)

| ID | Funcion / historia | MVP | Estado |
| --- | --- | --- | --- |
| H43 | Como usuario. quiero acceder a la app desde mi celular | MVP 4 | EN CURSO |
| T136 | Setup de expo (react native) y navegaci?n inicial | MVP 4 | EN CURSO |
| H44 | Como usuario. quiero ver el aforo en la home | MVP 4 | EN CURSO |
| T137 | Sincronizar contador de aforo mediante api | MVP 4 | EN CURSO |
| T168 | Diseñar el modelo relacional en SQLAlchemy | MVP 4 | PENDIENTE |
| F10 | REALIZACION DE MAQUETA | MVP 3 | EN CURSO |
| T218 | Construcci?n de la maqueta | MVP 3 | EN CURSO |
| T220 | Mecanizaci?n de la maqueta | MVP 3 | EN CURSO |
| T234 | MANUAL DE USUARIO | MVP 4 | PENDIENTE |

### Teresa (4 abiertas)

| ID | Funcion / historia | MVP | Estado |
| --- | --- | --- | --- |
| H51 | Como operador. quiero mostrar mensajes en pantalla local | MVP 4 | EN CURSO |
| T144 | Ui local con lcd i2c | MVP 4 | EN CURSO |
| T219 | Decoraci?n de la maqueta | MVP 3 | EN CURSO |
| T235 | MANUAL DE IMPLEMENTACION | MVP 4 | PENDIENTE |

## Lectura rapida

- **Mariano**: 132 filas (T: 98, H: 31, F: 3). MVP: MVP 1: 75, MVP 4: 27, MVP 2: 17, MVP 3: 13. Secciones donde aparece: 9.
- **Diego**: 97 filas (T: 70, H: 25, F: 2). MVP: MVP 2: 30, MVP 1: 29, MVP 4: 26, MVP 3: 12. Secciones donde aparece: 7.
- **Veronica**: 47 filas (T: 31, H: 13, F: 3). MVP: MVP 1: 23, MVP 3: 11, MVP 2: 7, MVP 4: 6. Secciones donde aparece: 7.
- **Teresa**: 44 filas (T: 33, H: 9, F: 2). MVP: MVP 1: 21, MVP 2: 10, MVP 3: 10, MVP 4: 3. Secciones donde aparece: 7.

## Nota metodologica

El `responsable` es el campo declarado en el tablero, no una atribucion de
autoría de commits: el backlog es la fuente de verdad de la planificacion y su
historial (`backlog/revisions`) guarda el estado del tablero, no la autoria del
codigo. Para ver quien escribio el codigo hay que mirar `git log` / `git blame`
del repositorio AUTOPASS.
