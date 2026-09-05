# Arquitectura del Sistema: AUTOPASS

Este documento detalla la estructura técnica y el flujo de datos del ecosistema de estacionamiento inteligente con **Arquitectura Limpia** (v9.14.0).

---

## Estructura de Directorios

El proyecto sigue una organización basada en la separación de responsabilidades:

```text
AUTOPASS/
├── alpr/               # Paquete modular ALPR (Vision, Preprocessing, Consensus, WS Streamer)
├── core/               # Infraestructura (Configuración, Seguridad/RBAC/JWT, Rate Limit, DB, MQTT, Logger, Time, Normalize, Seed, Caché TTL)
├── models/             # Entidades SQLAlchemy + Enums (Domain Layer)
├── schemas/            # Validación Pydantic
├── routes/             # Endpoints (Transport Layer - Delgados, organizados por submódulos)
│   ├── admin/          # Admin CRUD (users, branches, reservations, promotions, operations, settings, virtual_time, support)
│   ├── user/           # User portal (profile, vehicles, reservations, balance, fidelization, notifications, support, mercadopago)
│   ├── parking/        # Access control (access, status, utils)
│   └── system/         # System management (health, cameras, video, common)
├── services/           # Inteligencia de Negocio (14 servicios)
├── repositories/       # Data Access (user, reservation)
├── scripts/            # Utilidades (arduino_bridge, generate_test_plates, test_video, setup/run_server)
├── tests/              # Pruebas unitarias (pytest)
├── static/
│   ├── js/
│   │   ├── modules/    # 36 módulos ES6 (lógica de negocio frontend)
│   │   └── *.js        # 9 scripts puente (bridge: módulos → window.*)
│   ├── css/            # 39 archivos CSS organizados en base/layout/components/pages
│   └── images/
├── templates/
│   ├── dashboard/
│   │   ├── tabs/       # 9 pestañas del dashboard admin (incl. occupancy) + settings/ (4 sub-archivos)
│   │   └── modals/     # Modales reutilizables (user_modals, branch_modals, promotion_modal)
│   ├── profile/
│   │   ├── tabs/       # 7 pestañas del portal de usuario
│   │   └── modals/     # Modales reutilizables (onboarding_modal, modals.html)
│   ├── components/     # 7 componentes reutilizables (navbar, footer, modales globales, monitoreo_controls, etc.)
│   └── emails/         # 4 templates de email transaccional
├── Info proyecto/
│   └── Hardware/       # Firmware ESP32 (firmware_esp32.ino) + documentación
└── main.py             # Orquestador FastAPI
```

---

## Capas y Responsabilidades (v9.14.0)

### 1. Capa de Servicios (Service Layer)
Toda la lógica de negocio se ha centralizado en archivos bajo `services/`:
- **`ReportService`**: Encapsula toda la analítica financiera por sucursal/medio de pago/tipo de vehículo, agregaciones de ingresos proyectados, historial unificado de transacciones (UNION ALL) y auditoría de accesos.
- **`AccessService`**: Gestiona toda la lógica de validación de patentes, salidas y QR. Desde v9.5 la ocupación es **solo física**: el ALPR de entrada incrementa `ocupacion_actual` para todos los vehículos (con o sin reserva) y el de salida la decrementa. Incluye verificación de duplicados (evita registrar dos entradas seguidas) y cortesía de 10 minutos en salida.
- **`ReservationService`**: Gestiona el ciclo de vida de las reservas (creación, edición, cancelación con reembolsos proporcionales, simulación de refund, auto-activación y auto-cancelación). Desde v9.5 las reservas no horarias **no pre-ocupan plaza**: `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` quedaron como no-ops y el aforo refleja solo autos físicamente presentes.
- **`BillingService`**: Motor de tarifas y cálculo de puntos por fidelización.
- **`UserService`**: Gestión administrativa de usuarios y validaciones de seguridad.
- **`BranchService`**: Lógica de gestión de sucursales y aforos.
- **`HardwareService`**: Control de barreras físicas vía MQTT (ESP32) y comunicación Serie USB (pyserial) con Arduino Uno (auto-detección de puerto COM).
- **`EmailService`**: Envío de emails transaccionales con templates Jinja2 (confirmación de reserva con QR embebido, recuperación de contraseña, logo en base64).
- **`NotificationService`**: Sistema de notificaciones asíncronas vía WebSockets con aislamiento por sucursal para actualización en tiempo real del aforo. Usa un `OccupancyManager` con `broadcast_update` para distribuir cambios.
- **`UserNotificationService`**: CRUD de notificaciones in-app (create, get, unread count, mark read, mark all read). Almacena en tabla `user_notifications`.
- **`SupportService`**: CRUD de tickets de soporte (`SupportTicket`) con aislamiento por sucursal según rol: los clientes crean/consultan/responden sus tickets (`/v1/user/support-tickets`, con adjuntos jpg/jpeg/png/gif/webp/pdf hasta 1 MB) y los operadores/admin los gestionan y responden (`/v1/admin/support-tickets`, incl. `pending-count` y `read-notifs`).
- **`WorkerService`**: 2 hilos de fondo: (1) limpieza/mantenimiento cada `MAINTENANCE_INTERVAL_SECONDS` (`cleanup_overdue_reservations`, `auto_finalize_all_reservations` y purga de imágenes ALPR antiguas `_cleanup_old_alpr_images`); (2) notificaciones cada 30s (recordatorios 31 min antes del inicio, paso a ACTIVA de reservas iniciadas y auto-cancelación de reservas PENDIENTES no pagadas 30 min después del inicio).
- **`TimeService`**: Sistema de tiempo virtual para testing. Permite adelantar el reloj sin alterar el reloj real. Offset persistido en `data/virtual_time_offset.json`.
- **`MercadoPagoService`** (v9.14.0): Integración Checkout Pro por redirección. `create_payment` crea la preferencia (`MercadoPagoPayment`) y `confirm_payment` consulta MP (por `payment_id` o `external_reference`), valida `approved` + monto e **aplica de forma idempotente** (véase §6). No usa SDK: se llama a la API vía `requests` (`MP_API_BASE = https://api.mercadopago.com`).

### 2. Capa de Datos (Modelos y Enums)
- **Seguridad de Tipos:** Se han implementado Enums en `models/enums.py` para eliminar "strings mágicos" (ej: `UserRole`, `VehicleType`, `ReservationStatus`).
- **Gestión Vertical:** Soporte para sucursales con múltiples pisos (`ParkingFloor`), cada uno con capacidad independiente y trimodal para autos, motos y camionetas (`capacidad_total`, `ocupacion_actual`, `capacidad_motos`, `ocupacion_motos`, `capacidad_camionetas`, `ocupacion_camionetas`).
- **Fidelización:** Modelos `Promotion` (catálogo de beneficios con icono, categoría, sucursal, activa; incluye `tipo_canje` y `valor_descuento`), `Coupon` (cupones generados por canje de puntos) y `RedemptionTicket` (`redemption_tickets`: voucher con `codigo` de 16 caracteres, `qr_data = "AUTOPASS_REDEMPTION|ID:{codigo}"`, válido 30 días, o `descuento_reserva` que se aplica al pagar la próxima reserva).
- **Configuración Dinámica:** Modelo `Settings` (key-value store con `valor_str` para configuraciones de texto como IPs de cámaras, y aislamiento por sucursal).
- **Cámaras:** Modelo `ParkingCamera` (nombre, tipo: `PATENTE_INGRESO`, `PATENTE_EGRESO`, `QR_INGRESO`, `QR_EGRESO`, `PREDIO`, source/URL, sucursal, activa) para gestión dinámica de cámaras de seguridad.
- **Normalización de Patentes:** Campo `normalized_patente` en `AccessLog` para búsquedas eficientes, con funciones `normalize_plate`/`format_plate` en `routes/parking/utils.py` que soportan formatos MERCOSUR (Argentina, Brasil, Uruguay, Paraguay).
- **Soporte Trimodal:** `VehicleType` incluye `CAMIONETA` además de `AUTO` y `MOTO`. `ParkingAforo` y `ParkingFloor` tienen `capacidad_motos`/`ocupacion_motos` y `capacidad_camionetas`/`ocupacion_camionetas`.
- **Pago y Liquidación:** `AccessLog` incluye `costo_estadia`, `metodo_pago` ('DIGITAL'/'CAJA'), `fecha_pago`, `pago_confirmado`, `floor_id`.
- **Sucursales Geo-localizadas:** `ParkingBranch` incluye `logo_url`, `activa`, `latitude`, `longitude` para mapa interactivo y toggle de activación.
- **Reservas:** `Reservation` incluye `monto_reembolsado`, `sucursal_info` (JSON), `cliente_nombre`, `tipo_estadia`.
- **Usuarios:** `User` incluye `apellido`, `dni`, `telefono`, `direccion`, `saldo`, `is_blocked` (bloqueo administrativo, impide login) e `is_deleted` (borrado lógico/soft delete). `delete_user` marca `is_deleted = True` y todas las consultas filtran `is_deleted == False`.
- **Sesiones:** `UserSession` (`user_sessions`) registra cada login con `device_id`, `user_agent` e `ip_address`, habilitando la detección de inicios de sesión desde otros dispositivos (`NEW_DEVICE_LOGIN`).
- **Pagos MP (v9.14.0):** Modelo `MercadoPagoPayment` (`mercadopago_payments`): `tipo` (`reserva`/`estadia`), `reserva_id`, `access_log_id`, `redemption_ticket_id` (descuento), `patente`, `monto`, `moneda` (ARS), `external_reference` único, `preference_id`, `payment_id`, `estado` (PENDIENTE/APROBADO/FALLIDO/CANCELADO), `mp_status`, fechas. El autoincremental `id` se usa en la referencia `AP-{TIPO}-{id}-{uuid8}`.

---

### 3. Capa Frontend (Dashboard y Portal Modular - v9.9.0)

#### Patrón de Arquitectura: Bridge Pattern
El frontend utiliza un patrón de **dos capas** para compatibilizar módulos ES6 modernos con handlers `onclick` inline en HTML:

```
modules/*.js  →  bridge.js (dashboard.js, perfil.js, etc.)  →  window.*  →  HTML onclick
```

- **Módulos ES6** (`static/js/modules/`): Contienen la lógica real. Exportan funciones puras.
- **Scripts Puente** (`static/js/*.js`): Importan módulos y exponen funciones al scope global (`window.*`) para compatibilidad con handlers inline en templates Jinja2.
- **Carga**: Los scripts puente se cargan como `<script type="module">`. Los módulos se cargan en paralelo y se resuelven automáticamente.

#### Módulos Frontend (`static/js/modules/` - 36 módulos ES6)

| Módulo | Responsabilidad |
|---|---|
| `dashboard-ui.js` | Navegación de pestañas (`switchTab`), reloj, salud del sistema, streaming de video, gestión de cámaras |
| `dashboard-stats.js` | Estadísticas en vivo, logs recientes, tabla de ocupación, WebSocket de aforo, cancelar estadía |
| `dashboard-admin.js` | Orquestador del admin (importa sub-módulos y expone funciones globales) |
| `dashboard-admin-users.js` | CRUD usuarios (crear, editar, toggle-block, balance, password, rol, eliminar) |
| `dashboard-admin-branches.js` | Fachada de sucursales (re-exporta `crud` y `floors`) |
| `dashboard-admin-branches-crud.js` | CRUD sucursales, mapa Leaflet, geocoding, logo upload |
| `dashboard-admin-branches-floors.js` | Gestión de pisos (`ParkingFloor`), aforos por piso y Planta Baja |
| `dashboard-admin-settings.js` | Configuración del sistema, monitoreo de cámaras, control de barreras |
| `dashboard-finance.js` | Reportes financieros, filtros por fecha/tipo/método de pago, exportación CSV |
| `dashboard-operations.js` | Operaciones manuales (ingreso/egreso manual, abrir barrera, cancelar estadía) |
| `dashboard-reservations.js` | CRUD reservas admin, confirmar pago, cancelar, actualizar |
| `dashboard-promotions.js` | CRUD promociones, selección de iconos |
| `dashboard-tickets.js` | Gestión de tickets de soporte admin, auto-actualización real-time y búsqueda en vivo |
| `admin-tour.js` | Tour guiado interactivo para administradores |
| `monitoreo-live.js` | Monitoreo CCTV en vivo, grilla dinámica de cámaras, controles DVR |
| `profile-help.js` | Centro de ayuda al cliente, envío de tickets y FAQ acordeón |
| `api.js` | Cliente HTTP centralizado (GET/POST/PUT/PATCH/DELETE) with manejo de tokens y errores |
| `utils.js` | Utilidades: `formatNum`, `toTitle`, `formatDate`, `showToast`, `showConfirm`, `validatePlate`, `detectVehicleType` |
| `ui.js` | UI base: modales, sidebar, toggle password, logout |
| `virtual-time.js` | Tiempo virtual del servidor (sync periódica cada 60s) |
| `notifications.js` | Polling de notificaciones (30s), badge de unread |
| `auth.js` | Validación de forms, login, registro, recuperación |
| `profile.js` | Portal de usuario: perfil, puntos, promociones, historial |
| `reservas.js` | Fachada de reservas (re-exporta `form`, `list`, `actions`, `pass`) |
| `reservas-form.js` | Formulario de reserva, datepickers, estimador dinámico de tarifas, validaciones |
| `reservas-list.js` | Renderizado de tarjetas de reservas activas, timeline, historial y paginación |
| `reservas-actions.js` | Pago de reservas con saldo y cancelación con simulación de reembolso |
| `reservas-pass.js` | Renderizado de Pase Digital, QR `QRCode.js` y compartir ticket |
| `vehicles.js` | CRUD vehículos de usuario, auto-detección de tipo |
| `landing.js` | Landing page: mapa Leaflet, carrusel, header scroll |
| `landing-carousel.js` | Carrusel de imágenes de la landing |
| `landing-data.js` | Cache de POIs y datos de estadios |
| `landing-map.js` | Mapa interactivo Leaflet con selector multicapa (Google Maps, CartoDB) |
| `dashboard-cameras.js` | Configuración y control de cámaras del dashboard |
| `tour.js` | Tour guiado interactivo |
| `onboarding_helpers.js` | Helpers para onboarding de nuevos usuarios |

#### Scripts Puente del Dashboard (`static/js/dashboard.js`)
El orquestador centraliza todas las asignaciones `window.*`:
- Navegación: `window.switchTab`, `window.switchMonitorTab`, `window.toggleMobileNav`
- Datos: `window.loadTabData` (dispatcher por pestaña), `window.loadAdminReservations`, `window.loadFinanceData`
- CRUD: `window.handleAdminCreateUser`, `window.handleCreateBranch`, `window.handleCreatePromotion`
- Configuración: `window.switchSettingsTab`, `window.switchRatesTab`, `window.refreshSystemDiagnostics`
- Reservas: `window.openEditReservationModal`, `window.cancelReservationAdmin`

#### Estilo CSS
Organización en 4 capas bajo `static/css/` (39 archivos totales):
- `base/`: Variables CSS, reset, tipografía, utilidades (4 archivos)
- `layout/`: Sidebar, header, grid (3 archivos)
- `components/`: Botones, cards, badges, modals, forms, tables, footer, virtual_time (8 archivos)
- `pages/`: landing, profile, dashboard, contacto, legal (5 archivos + 18 sub-archivos)
  - `pages/dashboard/`: `dashboard-base.css`, `dashboard-cards.css`, `dashboard-live.css`, `dashboard-settings.css`, `dashboard-tables.css`, `dashboard-admin-tour.css`
  - `pages/landing/`: `landing-features.css`, `landing-hero.css`, `landing-map.css`, `landing-modals.css`, `landing-nav.css`
  - `pages/profile/`: `profile-base.css`, `profile-help.css`, `profile-notifications.css`, `profile-points.css`, `profile-reservations.css`, `profile-tour.css`, `profile-vehicles.css`
- `style.css` (raíz): Estilos globales adicionales

---

### 4. Capa de Servicio ALPR (`alpr/` + `alpr_service.py`)
Servicio independiente de visión artificial modularizado en el paquete `alpr/` (`config.py`, `preprocessor.py`, `video_streamer.py`, `ws_client.py`, `ocr_engine.py`, `runner.py`); `alpr_service.py` actúa como wrapper ejecutable en la raíz que delega en `alpr.runner.run_alpr_service()`.
- **Motor OCR Dual:** `RapidOCR` ONNX (optimizado para Python 3.14+) con fallback automático a `PaddleOCR`.
- **Extracción Prioritaria de 7 Caracteres:** Combina bloques de texto espacialmente (`full_7_pattern`) antes de evaluar 6 caracteres para evitar truncar letras finales.
- **Escalado Inteligente ROI:** Re-escalado automático a 80px de alto en recortes pequeños para evitar confusión entre dígitos (ej. `6` vs `5`).
- **Adaptación para Pruebas en Papel:** Reconocimiento de país por regex B&N (independiente del color) y consenso rápido de 1 voto si la confianza es alta ($\ge 0.75$ no-moto, $\ge 0.85$ moto) y el formato es válido.
- **Generador de Patentes:** Script `scripts/generate_test_plates.py` -> `static/test_plates.html` con patentes A4 imprimibles.
- **Sistema de Consenso:** Buffer de votos (múltiples lecturas de la misma patente) antes de enviar al backend para evitar falsos positivos.
- **Detección de QR:** Escaneo directo de QR en cada frame (Quick QR), alternativa a patente.
- **Video WebSocket:** Envía frames en tiempo real al backend (`/v1/system/ws/video/{gate_id}`) para visualización en dashboard.
- **Cola de Frames:** Política drop-oldest para no acumular frames sin procesar.
- **Detección de Movimiento:** Ignora frames estáticos para optimizar procesamiento.
- **Recorte MERCOSUR:** Detecta y recorta la banda azul de patentes MERCOSUR para mejorar OCR (adaptado a color y B&N).
- **ROI (Region of Interest):** Múltiples estrategias de detección de región de placa.
- **Imágenes de Debug:** Guarda imágenes de patentes aceptadas (solo Argentina).
- **Des-duplicación:** Cooldown por patente para no re-enviar la misma.
- **Modos de Operación:** Configurado via `GATE_TYPE`: `entrada`, `salida`, `patente`, `qr`, `predio`. Fuente de video via `VIDEO_SOURCE` (webcam, RTSP, HTTP MJPEG).

### 5. Capa de Hardware (ESP32 / Arduino Uno)
- **Firmware:** `Info proyecto/Hardware/firmware_esp32.ino` y `Info proyecto/Hardware/firmware_arduino_uno.ino`.
- **Comunicación:** MQTT con CallbackAPIVersion.VERSION2 (ESP32) y Serie USB vía pyserial (Arduino Uno, auto-detección de puerto con `arduino_bridge.py`).
- **Tópicos configurables vía .env:** `MQTT_TOPIC_ENTRADA`, `MQTT_TOPIC_SALIDA`.
- **Componentes:** Servomotor (barrera), sensor ultrasónico (detección de paso), pantalla LCD (mensajes al conductor).

---

### 6. Capa Mercado Pago (Checkout Pro - v9.14.0)

**Flujo de pago (reserva o estadía):**
1. `create_payment` (`POST /v1/user/mercadopago/checkout`, autenticado): valida propiedad y estados, calcula el monto (reserva: con descuento por canje `descuento_reserva` vigente; estadía: `BillingService.calculate_debt`), registra la intención `MercadoPagoPayment` (estado `PENDIENTE`, `external_reference` `AP-{TIPO}-{id}-{uuid8}`) y crea la preferencia en MP con `back_urls`, `auto_return=approved`, `expires=True`, devolviendo el `init_point` (sandbox en pruebas).
2. El usuario paga en el sitio de Mercado Pago.
3. **Confirmación** por **retorno** (`GET /v1/user/mercadopago/success|pending|failure`, sin auth → redirigen a `/perfil?mp_status=...&mp_tipo=...`) y/o **webhook** (`POST /v1/user/mercadopago/webhook`). `confirm_payment` consulta MP (por `payment_id` o `external_reference`) y:
   - `approved` + monto coincidente → `_aplicar_pago` (idempotente: si `estado == APROBADO` no re-aplica).
     - Reserva: `ReservationService.pay_reservation_mp` → `PAGADO`/`ACTIVA` + puntos + notificaciones (y consume el ticket de descuento si se usó).
     - Estadía: `BillingService.apply_stay_mp_payment` → `pago_confirmado=True`, `metodo_pago="MERCADOPAGO"`, `costo_estadia` = monto MP, acreditando puntos.
     - **En ningún caso se descuenta `users.saldo`.**
   - Otro estado (`rejected`/`pending`) → no aplica; marca `estado` (`FALLIDO` o pendiente) según corresponda.

**Reglas de extensión:**
- MP rechaza `http://` en los `back_urls` → `BASE_URL` debe ser `https://` (validación explícita en `create_payment`).
- `notification_url` solo se envía si `MP_WEBHOOK_URL` está definido (evita rechazos con URLs locales).
- Callbacks **públicos** (sin auth) + confirmación **idempotente** contra MP (nunca confiar solo en el payload del webhook).
- Tabla `mercadopago_payments` (migración Alembic `c9d8e7f6a5b4`). `external_reference` es nullable (el `id` se asigna al insertar).

**Endpoints Mercado Pago (v9.14.0):**
- `POST /v1/user/mercadopago/checkout` (autenticado): Crear preferencia Checkout Pro (pagar reserva o estadía). Retorna `init_point`.
- `GET /v1/user/mercadopago/success|pending|failure` (público, callback MP): Confirmación de retorno. Redirigen a `/perfil?mp_status=...&mp_tipo=...`.
- `POST /v1/user/mercadopago/webhook` (público, callback asíncrono): Webhook de MP para confirmación asíncrona. Ambos confirman el pago vía `confirm_payment` (idempotente).

---
1. **Rutas Delgadas:** Los controladores en `routes/` no deben contener lógica de negocio. Solo delegan a los servicios correspondientes.
2. **Independencia:** Los servicios deben importar modelos y esquemas, pero no routers.
3. **Tipo Seguro:** Usar siempre los Enums definidos en `models/enums.py` para cualquier estado o rol del sistema.
4. **Configuración Centralizada:** Cualquier parámetro, constante o URL externa debe ser configurada en `core/config.py` y, si es necesario, provista vía `.env`.
5. **Aforo Solo Físico (v9.5+):** Las reservas no horarias (Día/Semana/Quincena/Mes) **no** pre-ocupan plaza en el aforo. `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` son no-ops. El conteo de ocupación lo maneja exclusivamente el ALPR/manual de entrada y salida, reflejando solo vehículos físicamente presentes.
6. **Sin Liberación por Salida Física:** Para reservas no horarias, la salida física nunca libera plaza — no se pre-ocupa ninguna plaza, por lo que la liberación no aplica; el aforo se gestiona únicamente con los eventos de acceso.
7. **Modularización Frontend:** Toda lógica de negocio JS debe ir en `static/js/modules/` como módulo ES6 exportado. Los scripts puente en `static/js/` solo deben contener asignaciones `window.*` y event wiring. Nunca poner lógica de negocio en scripts puente.
