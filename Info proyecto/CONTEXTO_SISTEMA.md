#  Contexto del Sistema: AUTOPASS

Este documento describe la arquitectura de comunicación y el flujo de datos del ecosistema de estacionamiento inteligente con **Arquitectura Limpia** (v10.0.0).

## 📐 Arquitectura del Ecosistema

El sistema opera bajo un modelo de **Centro de Comando Descentralizado** con una estructura modular por capas (v9.9.0).

1.  **Capa Core (`core/`)**:
    *   `core/config.py`: Gestión centralizada de variables de entorno y constantes.
    *   `core/security.py`: Motor de seguridad con **RBAC (Role-Based Access Control)**, JWT y dependencias de autenticación por rol.
    *   `core/database.py`: Gestión de persistencia y sesiones (SQLAlchemy).
    *   `core/mqtt.py`: Orquestador de comunicación con barreras físicas vía MQTT.
    *   `core/seed.py`: Poblado inicial de datos (roles, sucursales, tarifas).
    *   `core/limiter.py`: **Rate limiting (SlowAPI)** por IP — límite global default `300/min` y límites específicos en los endpoints de auth.
    *   `core/logger.py`: Configuración global de logging (`setup_logging`) y `get_logger`.
    *   `core/time.py`: `utcnow()` — fecha/hora UTC como datetime naive (base de timestamps).
    *   `core/normalize.py`: Normalización de nombres/sucursales (`normalize_name`, `normalize_branch_name`, `normalize_user_name`).

2. **Backend Multi-Sucursal (FastAPI - `routes/`)**: 
    *   `routes/auth.py`: Autenticación, registro de usuarios, gestión de tokens JWT, recuperación de contraseña (`/forgot-password`, `/reset-password`), registro de sesiones multi-dispositivo (`UserSession`) y rate limiting (SlowAPI).
    *   `routes/admin/`: **Modular** — `users.py` (CRUD, toggle-block, balance, password, delete, role), `branches.py` (CRUD con logo upload, toggle activo, floors), `reservations.py` (CRUD, confirm-payment, cancel, update), `promotions.py` (CRUD, toggle activo), `operations.py` (manual entry/exit, open-barrier, cancel-stay, manual-entry), `settings.py` (prices, capacity), `virtual_time.py` (status, advance, set, reset), `support.py` (listar y responder tickets de soporte).
    *   `routes/user/`: **Modular** — `profile.py` (get/update profile, change-password), `reservations.py` (CRUD, modify, pay, cancel-simulation, cancel), `vehicles.py` (CRUD), `balance.py` (recharge, payment-history, active-stays, rates), `fidelization.py` (promotions, redeem, points-history), `notifications.py` (CRUD notificaciones in-app, unread count, mark read, delete single, clear read), `support.py` (crear y consultar tickets de soporte).
    *   `routes/parking/`: **Modular** — `access.py` (ALPR/QR, validate-plate, pay-stay, exit-plate, validate-qr), `status.py` (aforo + WebSockets, current-occupancy, branches, ws), `utils.py` (normalize_plate, format_plate, normalize_dni).
    *   `routes/reports.py`: Controlador delgado delegando a `ReportService` para analítica financiera segmentada por sucursal, canal de pago y tipo de vehículo.
    *   `routes/system/`: **Modular** — `common.py` (ConnectionManager, stop_all_cameras), `health.py` (`/health`, `/heartbeat`, `/reset`, `/virtual-time`), `cameras.py` (CRUD y control dinámico de cámaras), `video.py` (WebSockets de video, streaming MJPEG, capturas).
    *   `routes/views.py`: Router dedicado exclusivamente para el frontend Jinja2.

3.  **Lógica de Negocio (`services/`)**:
    *   `services/access_service.py`: Validación de patentes, gestión de entrada/salida e integración con aforo. Soporta entrada con QR, verificación de deuda antes de salir (`exit_plate`), y validación de duplicados (evita registrar dos entradas seguidas).
    *   `services/report_service.py`: **Nuevo** — Inteligencia de negocio para analítica financiera, historial unificado de transacciones (UNION ALL) y auditoría de accesos.
    *   `services/reservation_service.py`: Ciclo de vida de reservas (creación, edición, pago, cancelación con reembolsos proporcionales, simulación de cancelación, cleanup). Desde v9.5 las reservas no horarias ya no pre-ocupan plaza: `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` quedaron como no-ops y el aforo refleja solo vehículos físicamente presentes.
    *   `services/billing_service.py`: Motor de tarifas y cálculo de puntos por fidelización. Tarifas por sucursal, tipo de vehículo (Auto/Moto/Camioneta) y tipo de reserva (Hora/Día/Semana/Quincena/Mes).
    *   `services/notification_service.py`: Sistema de notificaciones asíncronas vía WebSockets con aislamiento por sucursal. Usa `OccupancyManager` con `broadcast_update` para distribuir cambios de ocupación.
    *   `services/user_notification_service.py`: CRUD de notificaciones in-app (create, get, unread count, mark read, mark all read). Almacena en tabla `user_notifications`.
    *   `services/support_service.py`: CRUD de tickets de soporte (`SupportTicket`) con aislamiento por sucursal según rol del usuario.
    *   `services/worker_service.py`: 3 hilos de fondo: (1) limpieza de reservas cada 300s (`auto_finalize_all_reservations`), (2) recordatorios 31 min antes del inicio, (3) auto-cancelación de reservas PENDIENTES no pagadas 30 min después del inicio.
    *   `services/time_service.py`: Sistema de tiempo virtual para testing. Permite adelantar el reloj sin alterar el reloj real. Offset persistido en `data/virtual_time_offset.json`.
    *   `services/branch_service.py`: Lógica de gestión de sucursales (CRUD, toggle activo), aforo multi-piso (add/delete floors, update capacity) y branch isolation.
    *   `services/user_service.py`: Gestión de usuarios (CRUD, toggle-block, balance adjust, password change by admin, role change, delete), validaciones de seguridad.
    *   `services/email_service.py`: Envío de emails transaccionales con templates HTML Jinja2 (confirmación de reserva con QR embebido en base64, recuperación de contraseña con token).

4.  **Capa de Repositories (`repositories/`)**:
    *   `repositories/user_repository.py`: Acceso a datos de usuarios.
    *   `repositories/reservation_repository.py`: Acceso a datos de reservas.

5.  **Gestión de Accesos ALPR (`alpr/` + `alpr_service.py`)**:
    *   `alpr/`: Paquete modular desacoplado compuesto por `config.py` (variables y regexes), `preprocessor.py` (filtros Moiré, recorte MERCOSUR adaptativo B&N/color, ROI), `video_streamer.py` (captura thread-safe OpenCV), `ws_client.py` (WebSocket streamer), `ocr_engine.py` (RapidOCR ONNX / PaddleOCR dual, QR, prioridad de 7 caracteres y consenso de votación) y `runner.py` (orquestador).
    *   `alpr_service.py`: Script wrapper en la raíz que ejecuta `alpr.runner.run_alpr_service()`, garantizando compatibilidad 100% con ejecuciones de subproceso.
    *   **Arquitectura Interna**: Soporte dual RapidOCR (ONNX compatible con Python 3.14+) / PaddleOCR, prioridad de patentes completas de 7 caracteres (`full_7_pattern`), escalado ROI automático a 80px para precisión de dígitos, sistema de consenso con búfer de votos, cola de frames con política drop-oldest, detección de movimiento, recorte adaptativo MERCOSUR (compatible con hojas de papel impresas), detección de QR rápido, envío de frames por WebSocket, persistencia de última patente aceptada con cooldown.
    *   **Generador de Patentes de Prueba**: Script `scripts/generate_test_plates.py` para generar [static/test_plates.html](file:///C:/Users/usuario.DESKTOP-P7MEQGK/Desktop/AUTOPASS/static/test_plates.html) con patentes A4 imprimibles.
    *   **Gestión de Cámaras**: Configuración de IP por puerta (entrada/salida) en DB vía `Settings`, start/stop de procesos ALPR desde dashboard, service restart.

##  Configuración y Seguridad
- **Variables de Entorno**: Configuración centralizada en `core/config.py` (consume de `.env`). Incluye `RESERVA_HORA_MIN_SEGUNDOS`, `MAINTENANCE_INTERVAL_SECONDS`, `SMTP_*`, `ACCESS_TOKEN_EXPIRE_MINUTES` (default 1440 = 24h), `ALGORITHM` (HS256), `SECRET_KEY` y `ALLOWED_ORIGINS` para CORS.
- **Token JWT**: Protección robusta de endpoints con validación de roles en tiempo real. Decodificación vía `decode_access_token` en `core/security.py`. El payload incluye `sub` (email) y `rol`. `create_access_token` firma con expiración por defecto de 15 min si no se pasa `expires_delta` (pero el login usa `ACCESS_TOKEN_EXPIRE_MINUTES`, default 24h).
- **RBAC**: Roles `ADMIN` (global), `LOCAL_ADMIN` (por sucursal), `STAFF` (operativo), `USER` (cliente). Dependencias: `get_super_admin` (solo ADMIN), `get_local_manager` (ADMIN/LOCAL_ADMIN), `get_operational_user` (ADMIN/LOCAL_ADMIN/STAFF), `get_current_user` (todos autenticados).
- **Bloqueo de Usuarios**: `User.is_blocked` permite bloqueo administrativo. `authenticate_user` verifica el flag y rechaza login si está bloqueado (403).
- **Soft Delete**: `User.is_deleted` implementa borrado lógico; todos los queries de usuarios filtran `is_deleted == False` y `delete_user` marca `is_deleted = True` en vez de eliminar físicamente.
- **Rate Limiting (SlowAPI)**: Límite global default `300/min` por IP (`core/limiter.py`). Límites específicos en auth: `login` 15/min, `register` 10/min, `forgot-password` 5/min, `reset-password` 10/min. Se activa con `app.state.limiter` + exception handler en `main.py`.
- **Gestión de Sesiones Multi-Dispositivo (`UserSession`)**: En cada login con `device_id`, se registra en la tabla `user_sessions` (device_id, user_agent, ip_address). Detecta logins desde **otros dispositivos** (mismo user-agent + IP se absorben como el mismo PC) y dispara una notificación in-app `NEW_DEVICE_LOGIN` de seguridad. Migración Alembic: `b7e3a1d2c4f5_add_user_sessions.py`.
- **Auth Endpoints** (todos Públicos, con rate limit):
  - `POST /v1/auth/login`: Login con email/contraseña (email normalizado a minúsculas). Retorna `access_token`, `rol`, nombre, apellido, sucursal y `nuevo_dispositivo` (flag de detección multi-dispositivo). **Límite: 15/min**.
  - `POST /v1/auth/register`: Auto-registro de clientes (rol `USER`). **Límite: 10/min**.
  - `POST /v1/auth/forgot-password`: Envía email con token de recuperación. No revela si el email existe (respuesta neutra). El token lleva `purpose: "recovery"` y expira en `RECOVERY_TOKEN_EXPIRE_MINUTES` (30 min). **Límite: 5/min**.
  - `POST /v1/auth/reset-password`: Cambia contraseña con token de recuperación válido (valida `purpose == "recovery"`). **Límite: 10/min**.

## 🛠️ Comandos de Inicio Rápido

### 1. Preparación del Env virtual
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-core.txt
```

### 2. Inicialización de Base de Datos
```powershell
python init_db.py  # Crea tablas y datos iniciales
```

### 4. Ejecución del Servidor
```powershell
# Producción (recomendado) - o ejecutar run_server.bat que abre el navegador al estar listo
uvicorn main:app --host 127.0.0.1 --port 8000

# Desarrollo con auto-reload
uvicorn main:app --reload --reload-dir core --reload-dir routes --reload-dir services
```

##  Scripts de Utilidad (`scripts/`)
- `backfill_attach_reservations.py`: Vincula reservas pagadas a access_logs existentes.
- `backfill_normalize_all_access_logs.py`: Normaliza todas las patentes en access_logs.
- `migrate_add_normalized_patente.py`: Migración para agregar columna `normalized_patente`.
- `normalize_plate_in_access_logs.py`: Normaliza una patente específica.
- `list_users.py`: Lista usuarios de la DB.
- `query_access_logs.py`: Consulta access_logs por patente.
- `query_fg112.py`: Consulta específica para patente FG 112 LO.
- `query_res.py`: Consulta reservas por patente.
- `test_video.py`: Test de fuente de video.
- `patch_bidi.py`: (Legacy) Parche post-instalación de python-bidi para EasyOCR. Ya no se necesita con PaddleOCR.

##  Frontend Features No Documentadas Anteriormente
- **Sistema de Tour**: `tour.js` y `onboarding_helpers.js` para guiar nuevos usuarios.
- **Sidebar Toggle**: Sidebar colapsable con persistencia en localStorage.
- **Mapa Interactivo**: Selector de coordenadas con Leaflet.js para sucursales.
- **Auto-detección de Tipo**: Frontend detecta Moto vs Auto según formato de patente.
- **Pase Digital / QR**: Pantalla de pase digital con QR compartible.
- **Barra de Progreso de Puntos**: Metas visuales en 500, 1000, 2500, 5000, 10000 puntos.
- **UI de Gestión de Cámaras**: Start/stop/config desde dashboard.
- **Monitoreo de Salud**: Puntos de estado (verde/rojo) para servicios del sistema.
- **Gestión de Pisos**: Grid de arquitectura de building para admins locales.
- **Edición de Tarifas**: Grupos de tarifas por tipo de vehículo con modo edición.
- **Logo de Sucursal**: Upload de logo personalizado por sucursal.
- **Exportación CSV**: Exportar datos financieros a CSV.
- **Flujo de Registro Rápido de Vehículo**: Integración directa con flujo de reserva.
- **Dashboard Modular (v9.6.0+)**: Lógica JS del dashboard dividida en módulos ES6 especializados con scripts puente que orquestan la exposición global. Esto mejora mantenibilidad, permite tree-shaking futuro y separa responsabilidades claramente.

---

## Arquitectura Frontend (v9.6.0)

### Patrón Bridge
El frontend usa un patrón de **dos capas** para compatibilizar módulos ES6 con handlers inline:

```
modules/*.js (lógica)  →  bridge.js (asignaciones window.*)  →  HTML onclick handlers
```

### Módulos Frontend (36 módulos ES6)

| Módulo | Responsabilidad |
|---|---|
| `dashboard-ui.js` | Navegación (`switchTab`), reloj, salud del sistema, streaming de video, cámaras |
| `dashboard-stats.js` | Estadísticas en vivo, logs, ocupación, WebSocket de aforo |
| `dashboard-admin.js` | Orquestador del admin (importa sub-módulos y expone funciones globales) |
| `dashboard-admin-users.js` | CRUD usuarios (crear, editar, toggle-block, balance, password, rol, eliminar) |
| `dashboard-admin-branches.js` | Fachada de sucursales (re-exporta `crud` y `floors`) |
| `dashboard-admin-branches-crud.js` | CRUD sucursales, mapa Leaflet, geocoding, logo upload |
| `dashboard-admin-branches-floors.js` | Gestión de pisos (`ParkingFloor`), aforos por piso y Planta Baja |
| `dashboard-admin-settings.js` | Configuración del sistema, monitoreo de cámaras, control de barreras |
| `dashboard-finance.js` | Reportes financieros, filtros por fecha/tipo/método de pago, exportación CSV |
| `dashboard-operations.js` | Operaciones manuales (ingreso/egreso manual, abrir barrera, cancelar estadía) |
| `dashboard-reservations.js` | CRUD reservas admin, confirmar pago, cancelar, actualizar |
| `dashboard-promotions.js` | CRUD promociones, iconos |
| `dashboard-tickets.js` | Gestión de tickets de soporte admin, auto-actualización real-time y búsqueda en vivo |
| `admin-tour.js` | Tour guiado interactivo para administradores |
| `profile-help.js` | Centro de ayuda al cliente, envío de tickets y FAQ acordeón |
| `monitoreo-live.js` | Monitoreo CCTV en vivo, grilla dinámica de cámaras, controles DVR |
| `api.js` | Cliente HTTP centralizado con manejo de tokens y errores |
| `utils.js` | Utilidades: formatNum, formatDate, showToast, showConfirm, validatePlate, detectVehicleType |
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
| `tour.js` | Tour guiado interactivo para clientes |
| `onboarding_helpers.js` | Helpers para onboarding de nuevos usuarios |

### Scripts Puente (Orquestadores)

| Archivo | Página | Patrón |
|---|---|---|
| `dashboard.js` | Dashboard Admin | Importa módulos `dashboard-*` y expone `window.*` |
| `perfil.js` | Portal de Usuario | Importa `profile`, `vehicles`, `reservas`, `notifications` |
| `main.js` | Todas las páginas | Utilidades globales (modal, sidebar, auth) |

### CSS (39 archivos)
Organizado en `static/css/`:
- `base/`: Variables, reset, tipografía, utilidades (4 archivos)
- `layout/`: Sidebar, header, grid (3 archivos)
- `components/`: Botones, cards, badges, modals, forms, tables, footer, virtual_time (8 archivos)
- `pages/`: landing, profile, dashboard, contacto, legal (5 + 18 sub-archivos)
  - `pages/dashboard/`: dashboard-base, dashboard-cards, dashboard-live, dashboard-settings, dashboard-tables, dashboard-admin-tour
  - `pages/landing/`: landing-features, landing-hero, landing-map, landing-modals, landing-nav
  - `pages/profile/`: profile-base, profile-help, profile-notifications, profile-points, profile-reservations, profile-tour, profile-vehicles

---

