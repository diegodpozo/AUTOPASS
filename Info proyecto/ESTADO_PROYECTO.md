# Estado del Proyecto: AUTOPASS (Actualizado 2026-07-06)

### 🚀 Hitos Recientes (Julio 2026) - Versión 9.5.0 (Cortesía & Ocupación Refactor)
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

### 🛠️ Arquitectura Actual (v9.1.5)
- **Capas**: Clean Architecture con Servicios de Notificación Asíncronos.
- **Seguridad**: JWT + RBAC (Endurecido en UI).
- **Frontend**: Dashboard Premium, Vanilla JS, CSS Glassmorphism, WebSockets (Video/Aforo).
- **Modelo Vehicular**: Trimodal (Auto, Moto, Camioneta).

### 📊 Cobertura de Funcionalidades
- **Gestión**: Multi-sucursal y Multi-piso con restricciones de seguridad por sede.
- **Facturación**: Trimodal (Auto/Moto/Camioneta) con filtros avanzados de canal de pago.
- **Monitoreo**: ALPR en vivo con gestión centralizada y aforo real-time.

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

