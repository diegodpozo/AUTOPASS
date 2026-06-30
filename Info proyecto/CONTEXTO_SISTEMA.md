#  Contexto del Sistema: AUTOPASS

Este documento describe la arquitectura de comunicación y el flujo de datos del ecosistema de estacionamiento inteligente con **Arquitectura Limpia** (v9.2.0).

## 📐 Arquitectura del Ecosistema

El sistema opera bajo un modelo de **Centro de Comando Descentralizado** con una estructura modular por capas:

1.  **Capa Core (`core/`)**:
    *   `core/config.py`: Gestión centralizada de variables de entorno y constantes.
    *   `core/security.py`: Motor de seguridad con **RBAC (Role-Based Access Control)** y JWT.
    *   `core/database.py`: Gestión de persistencia y sesiones (SQLAlchemy).
    *   `core/mqtt.py`: Orquestador de comunicación con barreras físicas vía MQTT.
    *   `core/seed.py`: Poblado inicial de datos (roles, sucursales, tarifas).

2. **Backend Multi-Sucursal (FastAPI - `routes/`)**: 
    *   `routes/auth.py`: Autenticación, registro de usuarios, gestión de tokens JWT, recuperación de contraseña (`/forgot-password`, `/reset-password`).
    *   `routes/admin/`: **Modular** — `users.py` (CRUD, toggle-block, balance, password, delete, role), `branches.py` (CRUD con logo upload, toggle activo, floors), `reservations.py` (CRUD, confirm-payment, cancel, update), `promotions.py` (CRUD, toggle activo), `operations.py` (manual entry/exit, open-barrier, cancel-stay, manual-entry), `settings.py` (prices, capacity).
    *   `routes/user/`: **Modular** — `profile.py` (get/update profile, change-password), `reservations.py` (CRUD, modify, pay, cancel-simulation, cancel), `vehicles.py` (CRUD), `balance.py` (recharge, payment-history, active-stays, rates), `fidelization.py` (promotions, redeem, points-history).
    *   `routes/parking/`: **Modular** — `access.py` (ALPR/QR, validate-plate, pay-stay, exit-plate, validate-qr), `status.py` (aforo + WebSockets, current-occupancy, branches, ws), `utils.py` (normalize_plate, format_plate, normalize_dni).
    *   `routes/reports.py`: Analítica financiera segmentada por sucursal con filtros por `vehicle_type`, `payment_method`, `date_range`.
    *   `routes/system.py`: Salud del sistema (`/health`), heartbeat ALPR (`/heartbeat`), control de cámaras (config, start/stop service, list), video feeds (`/video-feed`, `/update-frame`, `/capture`), WebSocket de video ALPR (`/ws/video/{gate_id}`), reset del sistema.
    *   `routes/views.py`: Router dedicado exclusivamente para el frontend Jinja2.

3.  **Lógica de Negocio (`services/`)**:
    *   `services/access_service.py`: Validación de patentes, gestión de entrada/salida e integración con aforo. Soporta entrada con QR, pago de estadía en salida (`pay_stay`), verificación de deuda antes de salir (`exit_plate`), cancelación de estadía con cortesía de 10 min (`cancel_stay`).
    *   `services/reservation_service.py`: Ciclo de vida de reservas (creación, edición, pago, cancelación con reembolsos proporcionales, simulación de cancelación, cleanup). Gestiona la reserva de plazas en el aforo para reservas no horarias.
    *   `services/billing_service.py`: Motor de tarifas y cálculo de puntos por fidelización. Tarifas por sucursal, tipo de vehículo (Auto/Moto/Camioneta) y tipo de reserva (Hora/Día/Semana/Quincena/Mes).
    *   `services/notification_service.py`: Sistema de notificaciones asíncronas vía WebSockets con aislamiento por sucursal. Usa `asyncio.Queue` para broadcast eficiente del estado de ocupación.
    *   `services/worker_service.py`: Hilo de fondo que ejecuta `auto_finalize_all_reservations` cada `MAINTENANCE_INTERVAL_SECONDS` (300s). Libera plazas de aforo de reservas vencidas, limpia reservas expiradas no pagadas.
    *   `services/branch_service.py`: Lógica de gestión de sucursales (CRUD, toggle activo), aforo multi-piso (add/delete floors, update capacity) y branch isolation.
    *   `services/user_service.py`: Gestión de usuarios (CRUD, toggle-block, balance adjust, password change by admin, role change, delete), validaciones de seguridad.
    *   `services/email_service.py`: Envío de emails transaccionales con templates HTML Jinja2 (confirmación de reserva con QR embebido en base64, recuperación de contraseña con token).

4.  **Capa de Datos (`repositories/`)**:
    *   `repositories/user_repository.py`: Acceso a datos de usuarios.
    *   `repositories/reservation_repository.py`: Acceso a datos de reservas.

5.  **Gestión de Accesos ALPR**:
    *   `alpr_service.py`: Servicio independiente de visión artificial (OpenCV + EasyOCR) que consume la API modular. Modos `SCREEN_TO_SCREEN` (simulación con video) y `SCREEN_TO_CAMERA` (cámaras IP reales).
    *   **Arquitectura Interna**: Sistema de consenso con buffer de votos, cola de frames con política drop-oldest, detección de movimiento, recorte de banda azul MERCOSUR, detección de QR rápido, heartbeat periódico, envío de frames por WebSocket, persistencia de última patente aceptada con cooldown.
    *   **Heartbeat**: Las cámaras activas envían pulsos a `/v1/system/heartbeat` cada N segundos. El backend monitorea salud vía `ALPR_HEARTBEATS` (dict con timestamps) y expone en `/v1/system/health`.
    *   **Gestión de Cámaras**: Configuración de IP por puerta (entrada/salida) en DB vía `Settings`, start/stop de procesos ALPR desde dashboard, service restart.

##  Configuración y Seguridad
- **Variables de Entorno**: Configuración centralizada en `core/config.py` (consume de `.env`). Incluye `RESERVA_HORA_MIN_SEGUNDOS` para tiempo mínimo de anticipación en reservas por hora, `MAINTENANCE_INTERVAL_SECONDS` para intervalo de limpieza, `SMTP_*` para configuración de email.
- **Token JWT**: Protección robusta de endpoints con validación de roles en tiempo real. Decodificación vía `decode_access_token` en `core/security.py`.
- **RBAC**: Roles `ADMIN` (global), `LOCAL_ADMIN` (por sucursal), `STAFF` (operativo), `USER` (cliente). Dependencias: `get_local_manager` (ADMIN/LOCAL_ADMIN), `get_operational_user` (ADMIN/LOCAL_ADMIN/STAFF), `get_current_user` (todos autenticados).
- **Bloqueo de Usuarios**: `User.is_blocked` permite bloqueo administrativo. `authenticate_user` verifica el flag y rechaza login si está bloqueado.
- **Auth Endpoints**:
  - `POST /v1/auth/login`: Login con email/contraseña, retorna token + datos del usuario (nombre, apellido, sucursal, rol).
  - `POST /v1/auth/register`: Auto-registro de clientes.
  - `POST /v1/auth/forgot-password`: Envía email con token de recuperación.
  - `POST /v1/auth/reset-password`: Cambia contraseña con token válido.
  - `POST /v1/auth/refresh`: Renueva token JWT.

## 🛠️ Comandos de Inicio Rápido

### 1. Preparación del Env virtual
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Parche EasyOCR (Post-instalación)
```powershell
.\venv\Scripts\python.exe scripts\patch_bidi.py
```

### 3. Inicialización de Base de Datos
```powershell
python init_db.py  # Crea tablas y datos iniciales
```

### 4. Ejecución del Servidor
```powershell
uvicorn main:app --reload
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
- `patch_bidi.py`: Parche post-instalación de EasyOCR.

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

---

