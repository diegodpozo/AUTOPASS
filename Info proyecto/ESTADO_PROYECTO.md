# Estado del Proyecto: AUTOPASS (Actualizado 2026-08-27)

### 🚀 Hitos Recientes (Agosto 2026) - Seguridad (Rate Limiting, Sesiones Multi-Dispositivo & Soft Delete)
- [x] **Rate Limiting por IP (SlowAPI)**: Nueva dependencia `slowapi==0.1.9` con `core/limiter.py`. Límite global default `300/min` y límites específicos en los endpoints públicos de auth: `/login` 15/min, `/register` 10/min, `/forgot-password` 5/min, `/reset-password` 10/min. Activado con `app.state.limiter` y `RateLimitExceeded` handler en `main.py` (mitiga fuerza bruta de login y abuso de registro).
- [x] **Gestión de Sesiones Multi-Dispositivo (`UserSession`)**: Nueva tabla `user_sessions` (migración Alembic `b7e3a1d2c4f5`) que registra en cada login `device_id`, `user_agent` e `ip_address`. Al detectar acceso desde otro dispositivo real (mismo user-agent + IP se absorben como el mismo PC), se dispara una notificación in-app `NEW_DEVICE_LOGIN` ("Nuevo inicio de sesión").
- [x] **Soft Delete de Usuarios (`is_deleted`)**: El borrado de usuarios pasa a ser lógico — `delete_user` marca `is_deleted = True` en lugar de eliminar la fila. Todas las consultas de usuarios (auth, admin, services) filtran `is_deleted == False`, preservando integridad referencial de reservas, accesos y tickets.
- [x] **Token de Recuperación con Propósito**: `forgot-password`/`reset-password` usan un JWT con `purpose: "recovery"` y expiración de `RECOVERY_TOKEN_EXPIRE_MINUTES` (30 min); `reset-password` valida el propósito antes de actualizar la contraseña.
- [x] **Normalización de Email en Login**: El email se normaliza a minúsculas/trim antes de autenticar y al buscar usuarios.

### 🚀 Hitos Recientes (Agosto 2026) - Versión 9.10.0 (ALPR Paper Testing Engine, Dual RapidOCR/PaddleOCR & 7-Char Priority Matching)
- [x] **Soporte Dual de Motor OCR (RapidOCR ONNX / PaddleOCR)**:
  - Integración de `rapidocr-onnxruntime` como motor OCR nativo para Python 3.14+, eliminando la dependencia rígida de `paddlepaddle` en sistemas modernos.
  - Conmutación automática y transparente entre RapidOCR y PaddleOCR en `alpr/ocr_engine.py`.
- [x] **Optimización para Lectura de Patentes Impresas en Papel**:
  - **Identificación de País Independiente del Color (`identify_country`)**: Priorización de coincidencia regex de patrones MERCOSUR/Antiguos para reconocer patentes impresas en papel en blanco y negro sin franja azul.
  - **Detección Azul HSV Adaptativa (`is_mercosur_candidate`)**: Tolerancia ampliada (`lower_blue` = `[90, 40, 40]`) para capturar la franja azul en hojas de papel impresas con tinta de inyección o láser.
  - **Consenso Rápido de 1 Voto para Pruebas**: Validación instantánea en 1 voto si la patente coincide con un formato conocido (`KNOWN_PLATE_FORMATS`) y confianza alta: $\ge 0.75$ para vehículos no moto y $\ge 0.85$ (`MOTO_MIN_CONFIDENCE`) para motos. Las lecturas de baja confianza requieren `CONSENSUS_REQUIRED` (2) votos en la ventana de 4s.
- [x] **Extracción Prioritaria de 7 Caracteres & Escalado ROI**:
  - **Priorización de 7 Caracteres (`full_7_pattern`)**: Combinación de bloques de texto antes de evaluar substrings de 6 caracteres, evitando truncar patentes como `AG 536 CR` en `AG 536 C`.
  - **Escalado Inteligente de ROI (`_ocr_single_roi`)**: Re-escalado automático por interpolación cúbica a 80px de alto para cultivos pequeños, afinando bordes y previniendo la confusión de dígitos como `6` vs `5`.
- [x] **Generador de Patentes de Prueba Imprimibles (`scripts/generate_test_plates.py`)**:
  - Creación del script utilitario que genera [static/test_plates.html](file:///C:/Users/usuario.DESKTOP-P7MEQGK/Desktop/AUTOPASS/static/test_plates.html) con patentes MERCOSUR (Auto/Moto/Camioneta/Brasil) listas para imprimir en A4 o proyectar en pantallas.
- [x] **Resolución de Bug de Interrupción en Hilo Worker (`ocr_worker`)**:
  - Reemplazo del comando `break` por `continue` con pausa de `0.5s` al enviar evento de patente, manteniendo el hilo de captura y escaneo en vivo activo indefinidamente.

### 🚀 Hitos Recientes (Agosto 2026) - Versión 9.9.0+ (Dashboard Settings Responsive & Setup Modernization)
- [x] **Rediseño Responsive de Configuración del Dashboard (`settings.html`)**:
  - **Navegación e Interfaz**: Incorporación de `flex-wrap` en contenedores de botones (`.btn-tab-mini` y `.btn-tab-sub`) para distribución fluida en móviles sin scroll horizontal.
  - **Grilla de Tarifas (`rates-form-grid`)**: Ajuste de ancho de campo en modo edición (`170px`) para adaptar inputs con íconos sin comprimir cifras numéricas.
  - **Gestión de Plazas Simplificada**: Eliminación de insignias redundantes en Planta Baja (`#level-block-pb`). Presentación limpia centrada de capacidades por vehículo (Autos, Motos, Camionetas) y botón lateral `EDITAR` / `APLICAR`.
  - **Tarjetas de Monitoreo de Cámaras (`camera-settings-grid`)**: Reemplazo de tabla HTML por grilla adaptativa de tarjetas glassmorphic (`.camera-card-premium`) (2 columnas en desktop, 1 columna en móvil). Botón `AGREGAR CÁMARA` y nombres de cámara centrados en responsive, y eliminación de etiquetas de sucursal redundantes.
  - **Diagnóstico del Sistema (`diag-grid-premium`)**: Transformación a 1 columna en pantallas móviles (< 580px) previniendo desbordamiento de indicadores.
- [x] **Rediseño Proporcional de Notificaciones Flotantes (`style.css`)**:
  - Reducción del tamaño de fuente de `1.7rem` a `0.85rem` y de íconos de `2.4rem` a `1.2rem`.
  - Ajuste de `min-width` de `640px` a `260px` y `max-width` a `420px`.
  - Adaptación móvil en `@media (max-width: 768px)` flotando al tope con márgenes de `16px` y ancho adaptativo de `400px`.

### 🚀 Hitos Recientes (Agosto 2026) - Versión 9.9.9 (Interactive Feature Tours Engine & Smooth UI Transitions)
- [x] **Guías Rápidas e Interactivas por Función (`ayuda.html`)**: Incorporación de tours interactivos guiados en tiempo real para las funciones clave del cliente:
  - **Alta de Vehículo (`startAddVehicleTour()`)**: Recorrido interactivo desplegando `#add-vehicle-form` en la pestaña *Mis Vehículos* para registrar patentes en vivo.
  - **Crear Reserva (`startCreateReservationTour()`)**: Guía paso a paso en *Inicio* para cotización por hora/período y selección de sucursal.
  - **Cargar Saldo (`startRechargeBalanceTour()`)**: Guía interactiva destacando la Billetera Virtual y el modal `#rechargeModal`.
  - **Canjear Puntos (`startRedeemPointsTour()`)**: Recorrido guiado por el catálogo de promociones y cupones en *Mis Puntos*.
  - **Pase Digital QR (`startQrPassTour()`)**: Guía interactiva enfocada de 3 componentes en `#modal-pase-digital` (**Código QR**, **Datos de Estadía** y **Botón Compartir/Descargar** en PNG/WhatsApp).
- [x] **Selector Inteligente de Elementos Visibles (`getVisibleTarget`)**: Implementación de resolución de selectores múltiples en `tour.js` para filtrar y seleccionar únicamente elementos con visibilidad real en el DOM (`offsetWidth > 0 && offsetHeight > 0`), evitando desvíos hacia elementos ocultos en pestañas inactivas.
- [x] **Animaciones Fluidas de Transición (Morphing & Fade)**: Incorporación de curvas de aceleración CSS (`cubic-bezier(0.25, 1, 0.5, 1)`) en `profile-tour.css` para lograr un movimiento fluido del marco dorado de resaltado (`#autopass-tour-highlight-rect`), morphing de la máscara SVG (`path`) y desplazamiento suave de la tarjeta explicativa (`.tour-tooltip-premium`) y la flecha indicadora (`.tour-arrow-premium`).
- [x] **Apertura Asíncrona Sincronizada del Pase Digital**: `showTourStep` convertido a `async` evaluando `await step.beforeShow()`, garantizando visibilidad inmediata del modal en 0ms y previniendo cierres/reaperturas o disparos involuntarios de modales de pago.

### 🚀 Hitos Recientes (Agosto 2026) - Versión 9.9.8 (System Integrity Validations & Toast Notification Overhaul)
- [x] **Protección en Eliminación de Vehículos**: Bloqueo estricto en `delete_vehicle` (`services/user_service.py`) si la patente posee reservas en estado `PENDIENTE_PAGO`, `PAGADA` o `EN_USO`, previniendo inconsistencias en pases QR y accesos ALPR.
- [x] **Validaciones en Baja de Usuarios**: Verificación previa en `delete_user` para impedir eliminar cuentas con reservas activas o estadías impagas pendientes.
- [x] **Control Anti-Doble Reserva**: Detección de solapamiento de horarios en `create_reservation` para evitar reservas duplicadas simultáneas sobre el mismo vehículo.
- [x] **Sincronización Aforo en Salidas Manuales**: `manual_exit` ajusta la ocupación física únicamente tras validar la presencia previa del vehículo en la sede.
- [x] **Validaciones en Eliminación de Pisos**: Restricción en `delete_floor` / `update_floor` para impedir reducir o eliminar pisos si la ocupación física actual supera la nueva capacidad.
- [x] **Refactor de Notificaciones Flotantes (Toasts)**: Eliminación del banner/sidebar invasivo (`#notif-alert-banner`). Notificaciones en tiempo real canalizadas por toasts flotantes compactos en la esquina superior derecha (`showToast`), con permanencia de **5 segundos exactos** sin cierre por clics accidentales en pantalla.

### 🚀 Hitos Recientes (Agosto 2026) - Versión 9.9.5 (Smart Tour System Overhaul & UI Refinements)
- [x] **Rediseño del Sistema de Posicionamiento del Tour (`tour.js`)**: Modificación del cálculo de coordenadas de tooltip y flecha a `position: fixed` relativo a `(0, 0)` del viewport, eliminando desviaciones al scrollear. Incorporación de abrazamiento a bordes de pantalla (`margin: 12px`), fallback responsive en pantallas angostas (`vw < 680px`), cálculo seguro de recorte SVG con `Math.max(0, ...)` y soporte de navegación por teclado (Esc, Flechas).
- [x] **Configuración de Auto-Arranque por Primer Logueo**: Implementación de `checkFirstLoginOnboarding(user)` en `onboarding_helpers.js` con clave por usuario `autopass_tour_seen_${userId}` en `localStorage`. El tour solo se dispara automáticamente en el primer inicio de sesión del usuario. Luego se puede reactivar manualmente desde el Centro de Ayuda y Soporte (`ayuda.html`). Removido el botón obsoleto "TOUR APP" de `inicio.html`.
- [x] **Tour Adaptativo e Inteligente según Vehículos Registrados**:
  - **Primer Logueo (0 vehículos)**: Guía rápida *Quick-Add* en pestaña Inicio -> `startPostAddReservationTour()` continúa sin interrupción la reserva en Inicio -> Mapa -> Reservas -> Puntos, sin enviar al usuario a la pestaña de vehículos.
  - **Repetición Manual desde Ayuda (0 vehículos)**: `noVehiclesTourSteps` abre en la pestaña Mis Vehículos -> Formulario -> Mapa -> Puntos.
  - **Repetición Manual desde Ayuda (1+ vehículos)**: `existingVehiclesTourSteps` inicia en la pestaña Mis Vehículos -> despliega `#vehicle-form-container` ofreciendo la opción `¿Agregar un Nuevo Vehículo?` (con botón *Continuar*) -> formulario de reserva en Inicio -> Mapa -> Reservas -> Puntos.
- [x] **Evaluador de Visibilidad para Selectores Múltiples**: Actualización de `waitForVisible(sel)` en `tour.js` para iterar selectores separados por coma y retornar únicamente aquel que se encuentre visualmente activo en el DOM (`offsetWidth > 0 && offsetHeight > 0`), evitando salteos cuando el primer selector está oculto.
- [x] **Remoción de Ícono de Despliegue en Inputs de Patente**: Reemplazo de `.select-wrapper-premium` por `.input-wrapper-premium` alrededor del campo de patente en `inicio.html`, `vehiculos.html` y `admin_reservations.html`. Adición de salvaguarda CSS `.select-wrapper-premium:not(:has(select))::after, .select-wrapper-premium:has(input)::after { display: none !important; }` en `profile-reservations.css`.

### 🚀 Hitos Recientes (Agosto 2026) - Versión 9.9.2 (Migración a Neon/Postgres en sa-east-1)
- [x] **Migración de Turso/libSQL a Neon (Postgres)**: La base online pasó de Turso (`aws-us-west-2`, Oregón, ~1200 ms/query) a **Neon en São Paulo (`sa-east-1`)** con latencia medida de ~100 ms (12× más rápida). Migración realizada con `scripts/migrate_turso_to_neon.py` preservando IDs y sincronizando secuencias.
- [x] **Driver Postgres (psycopg 3)**: `psycopg[binary]==3.3.4` agregado a `requirements.txt`. `core/database.py` normaliza `postgresql://` → `postgresql+psycopg://` automáticamente.
- [x] **Benchmark y Verificación**: `SELECT 1` ×5 a Neon en ~100 ms cada uno; suite completa 24/24 tests pasando contra Neon; datos verificados (11 access_logs, 24 reservations, 11 users).
- [x] **Actualización de Configuración y Documentación**: `.env` actualizado con la connection string de Neon (se quitó `TURSO_AUTH_TOKEN`); se actualizaron `DEPENDENCIAS.md`, `INICIALIZACION.md` y `Readme.md`.
- [x] **Optimización de Carga del Dashboard**: `/parking/current-occupancy` sin N+1 (salidas y reservas en bloque + tarifas precargadas en cache; ~349 → ~269 ms). En el frontend, `loadLiveStats` y `loadOccupancy` lanzan sus llamadas en paralelo (`Promise.all`) → la pestaña "live" pasa de ~1.4 s a ~500-600 ms.
- [x] **Arranque Rápido del Servidor**: `run_server.bat` sin `--reload` (evita proceso duplicado y reinicios al guardar archivos) y abre el navegador **solo cuando el servidor responde** (waiter TCP con `TcpClient`, bypasea el proxy de sistema que hacía fallar `Invoke-WebRequest` a localhost). Ya no hace falta recargar la página al arrancar.

### 🚀 Hitos Recientes (Agosto 2026) - Versión 9.9.1 (Base de Datos Online con Turso/libSQL)
- [x] **Base de Datos en la Nube (Turso/libSQL)**: Integración de una base SQLite en la nube de Turso para compartir los mismos datos desde múltiples PC. Configurable vía `DATABASE_URL=libsql://...?secure=true` y `TURSO_AUTH_TOKEN` en `.env`. (Superado en 9.9.2 por Neon/Postgres)
- [x] **Driver libSQL para Windows**: Instalación de `libsql==0.1.11` (wheel nativo Windows) + `sqlalchemy-libsql==0.2.0` con `--no-deps` (el `libsql-experimental` no compila en Windows). Se creó el shim `libsql_experimental.py` en la raíz para que el dialecto SQLAlchemy funcione con el driver nuevo.
- [x] **Soporte Multi-PC**: `core/database.py` detecta el prefijo `libsql://`, usa `QueuePool` y pasa el auth token automáticamente. Varias PC corriendo el backend comparten la misma base; cada una conserva local solo imágenes, logos y tiempo virtual.
- [x] **Actualización de Instalador y Documentación**: `setup_backend.bat` instala el dialecto Turso, `requirements.txt` incluye `libsql`, y se actualizaron `DEPENDENCIAS.md` e `INICIALIZACION.md` con la configuración y verificación de la base online.

### 🚀 Hitos Recientes (Agosto 2026) - Versión 9.9.0 (Interactive Map Overhaul, Google Maps Integration & Trimodal Status Dots UI)
- [x] **Mosaicos de Google Maps 100% Gratuitos sin API Key**: Integración de capas de mapas base de Google Maps (`Google Calles`, `Google Satélite`, `Google Híbrido`) y `CartoDB Oscuro` con un selector multicapa interactivo en `landing.js` y `dashboard-admin-branches-crud.js`.
- [x] **Indicadores Circulares de Disponibilidad por Vehículo**: Remoción de textos genéricos (`"ALTA DISPONIBILIDAD"`, `"Hay lugares disponibles para vos."`) y sustitución de la cantidad numérica de plazas por círculos de estado luminosos (`status dots`) discriminados para **Auto**, **Moto** y **Camioneta** (Verde: Alta, Amarillo: Media, Naranja: Baja, Rojo: Agotado).
- [x] **Rediseño Proporcional & Botón de Cierre Glassmorphic**: Optimización de las dimensiones de la tarjeta emergente a `250px` con padding interior equilibrado y reubicación del botón de cierre (`top: 10px`, `right: 12px`) con estilo circular translúcido.
- [x] **Formateador de Direcciones en Puntos de Interés**: Implementación de la función `formatPoiAddress` para extracción en cascada de direcciones en OpenStreetMap y asignación de direcciones reales exactas para los estadios deportivos fijados.

### 🚀 Hitos Previos (Agosto 2026) - Versión 9.8.6 (Notification Engine Overhaul & User Notification Center Redesign)
- [x] **Solución de Duplicidad en Recordatorios (`WorkerService`)**: Incorporación de verificación previa de notificaciones existentes en `WorkerService._process_reminders`. Se eliminó la generación de notificaciones in-app y correos electrónicos duplicados cada 30 segundos previa al inicio de reservas.
- [x] **Notificaciones In-App Automáticas por Evento**: Disparo automático de notificaciones in-app ante respuesta de soporte (`SUPPORT_RESPONSE`), recarga de saldo (`BALANCE_RECHARGED`), confirmación de pago de reserva (`RESERVATION_CONFIRMED`) y cancelación de reserva (`RESERVATION_CANCELLED`).
- [x] **Nuevos Endpoints de Borrado & Conteo Preciso**: Adición de endpoints `DELETE /v1/user/profile/notifications/{notif_id}` (borrado individual) y `DELETE /v1/user/profile/notifications/clear-read` (borrado masivo de leídas) en `routes/user/notifications.py`, junto con cálculo exacto `get_total_count`.
- [x] **Rediseño UI del Centro de Notificaciones (`notificaciones.html` & `profile-notifications.css`)**: Integración con la estructura de tarjeta premium del portal (`welcome-card`), icono de campanita dorada alineada con el título, botón estilizad `Borrar leídas` en el extremo derecho de la barra de filtros y eliminación de bordes de colores por categoría en las tarjetas a favor de bordes limpios de cristal.
- [x] **Centrado de Estados Vacíos & Pestañas de Filtro (`notifications.js`)**: Sistema de chips de filtrado en el cliente (*Todas*, *No leídas*, *Reservas*, *Pagos & Saldo*, *Soporte*), y ajuste CSS Flexbox para centrar perfectamente icono y mensaje de estado vacío al navegar entre filtros.
- [x] **Expansión de Suite de Tests (`test_notifications.py`)**: Incorporación de pruebas unitarias para el ciclo de vida completo de notificaciones y respuestas de soporte (subiendo a 19 pruebas de integración ejecutadas exitosamente).

### 🚀 Hitos Previos (Agosto 2026) - Versión 9.8.5 (Trimodal Capacity Management & Customer Support Ticket System)
- [x] **Sistema Integral de Tickets de Soporte (`SupportTicket`)**: Creación del modelo `SupportTicket` en DB, servicio `SupportService`, esquemas Pydantic y endpoints FastAPI (`/v1/user/support-tickets` y `/v1/admin/support-tickets`). Permite a los usuarios enviar consultas filtradas por sucursal y categoría desde su portal, y a los Administradores gestionar y responder tickets.
- [x] **Aislamiento por Rol & Actualización en Tiempo Real de Tickets**: Filtrado automático estricto por sucursal para Administradores Locales y vista por defecto de Consultas Generales para Administradores Globales. Actualización automática de la tabla en tiempo real mediante notificaciones push WebSockets y polling en segundo plano cada 10s.
- [x] **Solución de Pestaña Inicial para Admin Principal (`dashboard.js`)**: Corrección de la inicialización de pestaña al iniciar sesión como Administrador Global (`admin`). Ahora redirige automáticamente a la pestaña de **Gestión de Usuarios** (`users`) en lugar de enviar a Monitoreo (`live`), manteniendo coherencia estricta con los permisos del Administrador Principal (acceso únicamente a Gestión de Usuarios, Promociones, Soporte & Tickets y Sucursales).
- [x] **Rediseño UI Premium de Soporte & Búsqueda en Vivo (`tickets.html` & `dashboard-tickets.js`)**: Adaptación estética 100% fiel al sistema de diseño AUTOPASS (`tab-view`, `kpi-grid`, `card-header-premium`, `table-centered`). Incorporación de buscador en tiempo real por asunto, cliente, email o categoría, remoción de botones redundantes y simplificación del filtro de estados a `"Todos"`.
- [x] **Gestión de Plazas de Camionetas (`capacidad_camionetas`)**: Integración completa de edición y almacenamiento de plazas para Camionetas en endpoints `/v1/admin/settings/prices`, `POST /v1/admin/{branch_id}/floors` y `PATCH /v1/admin/floors/{floor_id}`.
- [x] **Rediseño UI de la Pestaña Plazas (`settings_floors.html`)**: Ampliación del ancho del contenedor del tarifario/plazas a `820px` y eliminación del recuadro PB redundante en el bloque de Planta Baja para maximizar el espacio horizontal de los campos de Autos, Motos y Camionetas.
- [x] **Estilización de Botones y Normalización de Cámaras (`buttons.css` & `dashboard-ui.js`)**: Creación de estilos CSS `.btn-action-mini` (`.success`, `.danger`), normalización de nombres de dispositivos con `toTitle` y remoción del botón redundante Play/Stop de la tabla de configuración.
- [x] **Rediseño Monitoreo Multi-Cámara & Categorías de Cámara**: Posicionamiento flotante del nombre de cámara arriba a la izquierda (`.cctv-hud-header`) sin franjas negras laterales y con texto de alto contraste. Reestructuración de categorías de cámaras: `PATENTE_INGRESO` (Lectura de Patente - Entrada), `PATENTE_EGRESO` (Lectura de Patente - Salida), `QR_INGRESO` (Lector de QR - Entrada), `QR_EGRESO` (Lector de QR - Salida) y `PREDIO` (Vigilancia).

### 🚀 Hitos Previos (Agosto 2026) - Versión 9.8.0 (Database Migrations with Alembic & Automated Testing Overhaul)
- [x] **Framework de Migraciones de DB (`alembic/`)**: Integración completa de Alembic para control de versiones de esquema SQLite/Postgres. Creación de `alembic.ini`, `alembic/env.py` con `render_as_batch=True` para SQLite, y generación de la primera migración inicial `c833a3129266_initial_schema.py`. Estampado del esquema con `alembic stamp head`.
- [x] **Expansión de la Suite de Pruebas (`tests/`)**: Ampliación de la cobertura de tests unitarios e integración pasando de 6 a 15 pruebas automatizadas (rutas de autenticación con `TestClient`, motor ALPR/patentes, cortesía de 10 min, duplicate entry, control de aforo).
- [x] **Integración Continua CI/CD (`.github/workflows/ci.yml`)**: Creación de pipeline de GitHub Actions para verificación automática de dependencias, parches de entorno, migraciones de Alembic y ejecución de Pytest en cada push/PR.

### 🚀 Hitos Previos (Julio 2026) - Versión 9.7.0 (Granular Modularization Overhaul)
- [x] **Modularización Granular de Reservas JS (`static/js/modules/reservas-*.js`)**: Descomposición del monolito `reservas.js` (903 líneas / 45 KB) en 4 submódulos ES6 especializados: `reservas-form.js` (formularios, validación, tarifas), `reservas-list.js` (renderizado de tarjetas, timeline, historial y paginación), `reservas-actions.js` (pago con saldo y simulación de reembolso) y `reservas-pass.js` (Pase Digital, QR `QRCode.js` y compartir ticket). `reservas.js` actúa como fachada re-exportando todo el API.
- [x] **Modularización Granular de Sucursales JS (`static/js/modules/dashboard-admin-branches-*.js`)**: Separación de `dashboard-admin-branches.js` (705 líneas / 30 KB) en dos submódulos: `dashboard-admin-branches-crud.js` (CRUD sucursales, mapa Leaflet, geocoding, logo upload) y `dashboard-admin-branches-floors.js` (gestión de pisos `ParkingFloor`, aforos por piso y Planta Baja). `dashboard-admin-branches.js` actúa como fachada.
- [x] **Partials de Modales HTML (`templates/dashboard/modals/` y `templates/profile/modals/`)**: Extracción de modales HTML embebidos hacia componentes partials reutilizables: `profile/modals/onboarding_modal.html`, `dashboard/modals/user_modals.html`, `dashboard/modals/branch_modals.html` y `dashboard/modals/promotion_modal.html`, incluidos mediante `{% include %}` en las vistas principales.

### 🚀 Hitos Previos (Julio 2026) - Versión 9.6.0 (Modularización & Code Quality Overhaul)
- [x] **Paquete ALPR (`alpr/`)**: Refactorización del script monolítico `alpr_service.py` (29 KB) en el paquete `alpr/` (`config`, `preprocessor`, `video_streamer`, `ws_client`, `ocr_engine`, `runner`). Se preserva `alpr_service.py` como wrapper ejecutable.
- [x] **Servicio de Analítica (`ReportService`)**: Creación de `services/report_service.py` para abstraer agregación financiera y transacciones, convirtiendo `routes/reports.py` en un controlador delgado (Clean Architecture).
- [x] **Paquete de Sistema (`routes/system/`)**: Modularización de `routes/system.py` (22 KB) en submódulos especializados (`common.py`, `health.py`, `cameras.py`, `video.py`).
- [x] **Modularización Frontend Dashboard**: Separación del monolito `dashboard.js` en módulos ES6: `dashboard-ui.js` (UI/navegación/cámaras), `dashboard-stats.js` (estadísticas/aforo/WebSocket), `dashboard-admin.js` (CRUD usuarios/sucursales/config), `dashboard-promotions.js` (CRUD promociones). `dashboard.js` actúa como puente/orquestador exponiendo funciones al scope global.
- [x] **Fix Navegación de Pestañas**: Corrección de error de sintaxis (`}` sobrante en `dashboard-admin.js:1325`) que impedía la carga del módulo y rompía `window.switchTab`. Mejora en `switchTab` para gestionar explícitamente `style.display` en lugar de depender solo de CSS `!important`.
- [x] **Revisión y Actualización Documentación**: Sincronización de `ESTADO_PROYECTO.md`, `ARQUITECTURA_DETALLADA.md`, `GUIA_DESARROLLO.md` y `DEPENDENCIAS.md` con el estado real del código (v9.6.0).

### 🚀 Hitos Previos (Julio 2026) - Versión 9.5.0 (Cortesía & Ocupación Refactor)
- [x] **Fix ALPR "ya está en la sede"**: Misma corrección que en `manual_entry` — ahora verifica si hay SALIDA posterior a la última ENTRADA en lugar de solo el último registro.
- [x] **Cortesía 10 min en ALPR y manual**: `exit_plate` y `manual_exit` chequean el tiempo de cortesía antes de denegar por deuda. Dentro de los 10 min la salida es sin cargo.
- [x] **Ocupación solo física**: Las reservas no horarias ya no pre-ocupan plaza. El ALPR de entrada/salida maneja el conteo para todos los vehículos, reflejando solo autos físicamente presentes.

### 🚀 Hitos Previos (Julio 2026) - Versión 9.4.0 (DVR CCTV Overhaul & Dynamic Layout)

### 🚀 Hitos Previos (Junio 2026) - Versión 9.2.0 (Reservas & Aforo Inteligente)
- [x] **Reserva de Aforo en Pago**: Las reservas de tipo Día, Semana, Quincena y Mes descuentan la plaza del aforo al momento del pago, liberándola solo al vencimiento o cancelación.
- [x] **Tránsito Libre con Reserva**: Los clientes con reserva no horaria pueden entrar y salir libremente durante el período sin perder la plaza reservada.
- [x] **Liberación Automática al Vencer**: El sistema libera la plaza automáticamente cuando la reserva expira, incluso si el vehículo nunca ingresó.
- [x] **Restricción de Anticipación por Tipo**: Las reservas por hora requieren 1 hora de anticipación; las de Día/Semana/Quincena/Mes no tienen restricción horaria.
- [x] **Parametrización de Tiempo Mínimo**: El tiempo mínimo de anticipación para reservas por hora ahora es configurable vía variable de entorno (`RESERVA_HORA_MIN_SEGUNDOS`).
- [x] **Validación Sincronizada Frontend/Backend**: Las validaciones de anticipación en el frontend se actualizaron para coincidir con la lógica del backend (solo por hora, 1 hora).

### 🚀 Hitos Previos (Junio 2026) - Versión 9.1.5 (UX/UI Refinement & RBAC)
- [x] **Monitoring UI Redesign**: Rediseño total de la pestaña de Monitoreo en Ajustes usando un layout de grilla bimodal, iconografía técnica mejorada y tipografía monospace para fuentes de video.
- [x] **Financial Filter Expansion**: Integración de "Camionetas" en los filtros de reportes financieros para auditoría trimodal completa.
- [x] **RBAC UI Hardening**: Restricción física de opciones de "Administrador General" para usuarios con rol de Admin Local en filtros y edición de roles.
- [x] **Trimodal Pricing Model**: Expansión del motor de tarifas para soportar una tercera categoría: **Camionetas**, con configuración independiente de hora, día, semana y mes.
- [x] **Enhanced Vehicle Registration**: Actualización de los formularios de registro (Mis Vehículos y Quick Add) para permitir la selección manual de Camionetas, incluyendo nueva iconografía (`fa-truck-pickup`).
- [x] **Real-time Occupancy WebSocket**: Implementación de un sistema de notificaciones push para el aforo, eliminando el polling y permitiendo actualizaciones instantáneas en el dashboard.

### 🚀 Hitos Previos (Junio 2026) - Versión 9.0.0 (Real-time & Settings Overhaul)
- [x] **Settings Monitoring Tab**: Migración de la configuración de cámaras IP y control de servicios ALPR a una nueva pestaña dedicada en Ajustes.
- [x] **WebSocket Notification Service**: Nueva arquitectura desacoplada para gestionar eventos asíncronos en el backend.
- [x] **UI Tab Fix**: Corrección de la estructura HTML en ajustes para evitar solapamiento de secciones.
- [x] **Video Stream Visibility Fix**: Corregida la lógica de opacidad y carga de frames en el Dashboard para asegurar la visualización inmediata.
- [x] **Dynamic WS Token Validation**: Implementada validación de token en el cliente WS para diferenciar visualizadores de nodos ALPR.

### 🚀 Hitos Previos (Junio 2026) - Versión 8.9.5 (Video Stream Optimization)
- [x] **Placeholder Refinement**: Implementación de placeholders transparentes para evitar errores de carga (404) antes de la conexión del stream.
- [x] **Camera Remote Control**: Implementación de gestión de servicios ALPR desde el UI (Start/Stop/Config).
- [x] **Dynamic Video Source**: Soporte para cambio de IPs de cámaras en tiempo real sin reiniciar el servidor.
- [x] **Settings Expansion**: Extensión del modelo de base de datos para soportar configuraciones de texto (IPs, URLs).
- [x] **Form Normalization**: Estandarización de inputs de reserva y vehículos (48px height, 0.9rem font).
- [x] **Minimalist Alerts**: Rediseño de alertas de confirmación sin marcos internos y con jerarquía financiera mejorada.
- [x] **Direct Swap Vehicles**: Nueva interacción para el registro de flota eliminando colapsables por intercambio de componentes.
- [x] **Unified Visual Style**: Sincronización estética total entre el formulario de inicio ("Quick Add") y la gestión de flota.
- [x] **Clean Empty States**: Estados vacíos simplificados con iconos neutros (#444) y sin ruido visual.

### 🛠️ Arquitectura Actual (v9.9.0+)
- **Backend**: Clean Architecture con Servicios y Repositories. 13 servicios en `services/`, ~77 archivos Python en paquetes (`core/`, `models/`, `schemas/`, `routes/`, `services/`, `repositories/`, `alpr/`).
- **Frontend**: Dashboard Premium modularizado. 36 módulos ES6 en `static/js/modules/`, 9 scripts puente en `static/js/`, 47 templates HTML, 39 archivos CSS organizados en `base/`, `layout/`, `components/`, `pages/` (con subdirectorios `dashboard/`, `landing/`, `profile/`).
- **Seguridad**: JWT + RBAC (4 roles: admin, local_admin, staff, user).
- **Real-time**: WebSocket (aforo), MQTT (barreras), Polling (notificaciones 30s), Virtual Time (sync 1min).
- **Modelo Vehicular**: Trimodal (Auto, Moto, Camioneta).
- **Multi-sucursal**: Full isolation por sucursal con gestión de pisos, aforos y configuración independiente.
- **ALPR**: Pipeline completo de visión artificial (PaddleOCR + OpenCV) con consenso de votos y streaming de video.
- **Base de Datos**: **Neon/Postgres online** (`postgresql://...@ep-silent-math-acirnekl.sa-east-1.aws.neon.tech/neondb`) en región `sa-east-1` (São Paulo), compartida entre varias PC, con fallback a SQLite local (`parking.db`). Migraciones versionadas con **Alembic** (`alembic/`, primera migración `c833a3129266_initial_schema`).

### 📊 Cobertura de Funcionalidades
- **Gestión**: Multi-sucursal y Multi-piso con restricciones de seguridad por sede.
- **Facturación**: Trimodal (Auto/Moto/Camioneta) con filtros avanzados de canal de pago.
- **Monitoreo**: ALPR en vivo con gestión centralizada, aforo real-time vía WebSocket y streaming de video multi-cámara.
- **Fidelización**: Sistema de puntos (10 pts/$1000), promociones canjeables y cupones.
- **Frontend**: Dashboard modular con 8 pestañas (Monitoreo, Reservas, Gestión de Usuarios, Reporte Financiero, Promociones, Soporte & Tickets, Sucursales, Configuración).

### Cambios técnicos recientes (2026-07-06)
- ALPR: Fix en `validate_plate` y `validate_qr` — ahora buscan la última ENTRADA y verifican SALIDA posterior (mismo patrón que `manual_entry`), en lugar de solo mirar el último registro de cualquier tipo.
- ALPR/Manual exit: Se agregó chequeo de cortesía de 10 minutos tanto en `exit_plate` como en `manual_exit`. Si el tiempo desde la entrada es ≤10 min, se permite la salida sin exigir pago (`costo_estadia=0.0`).
- Ocupación: Se eliminó la pre-ocupación de plazas por reservas no horarias. Las funciones `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` quedaron como no-ops. El ALPR de entrada incrementa `ocupacion_actual` para todos los vehículos (con o sin reserva); el ALPR de salida la decrementa igualmente. Así el aforo refleja solo autos físicamente presentes.

### Cambios técnicos recientes (2026-07-02)
- Monitoreo: Refactorizado `monitoreo_live.html` utilizando CSS Grid dinámico autogestionado por JavaScript (N cámaras adaptadas en columnas/filas variables).
- HUD: Modificados los metadatos de superposición visual para incluir prefijo de grabación `■` en duraciones y concatenar la función de la cámara (`cam.tipo`) al nombre del dispositivo.
- Controles: Movidos los controles de backend de la vista de video a un div con `position: fixed` en la esquina superior derecha del viewport.

### Cambios técnicos recientes (2026-06-23)
- ALPR: Quick QR detection añadido para captura rápida de códigos QR; cooldown/debounce de **10s** para suprimir eventos duplicados.
- ALPR: Cola de frames con `maxsize=4` y política "drop-oldest" para evitar stalls en cámaras de alto FPS.
- Normalización: Se agregó `normalized_patente` (columna e índice) y se ejecutaron scripts de backfill para normalizar accesos y vincular reservas pagas.
- Manual entry/exit: Reuso de registro ENTRADA y asociación automática a reserva pagada (marca `pago_confirmado`) evitando duplicados.
- Notifications / WS: `NotificationService` ahora registra el loop de uvicorn y usa `run_coroutine_threadsafe` para programar broadcasts. Logs en conexión: `[WS] Conexión establecida: user=... sucursal=...`.
- Frontend: El dashboard oculta el botón "Cancelar estadía" para reservas no horarias pagas y requiere conexión WS para actualizaciones automáticas (sin F5).

**Operacional:** Reiniciar backend (uvicorn) y proceso ALPR tras desplegar cambios; verificar WS abierto en `/v1/parking/ws` para recibir actualizaciones en tiempo real.

