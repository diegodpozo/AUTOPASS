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
    *   `routes/auth.py`: Autenticación, registro y gestión de tokens JWT.
    *   `routes/admin/`: **Modular** — `users.py`, `branches.py`, `reservations.py`, `promotions.py`, `operations.py`, `settings.py`.
    *   `routes/user/`: **Modular** — `profile.py`, `reservations.py`, `vehicles.py`, `balance.py`, `fidelization.py`.
    *   `routes/parking/`: **Modular** — `access.py` (ALPR/QR), `status.py` (aforo + WebSockets), `utils.py`.
    *   `routes/reports.py`: Analítica financiera segmentada por sucursal.
    *   `routes/system.py`: Salud del sistema, control de cámaras.
    *   `routes/views.py`: Router dedicado exclusivamente para el frontend Jinja2.

3.  **Lógica de Negocio (`services/`)**:
    *   `services/access_service.py`: Validación de patentes, gestión de entrada/salida e integración con aforo.
    *   `services/reservation_service.py`: Ciclo de vida de reservas (creación, pago, cancelación, reembolso, cleanup). Gestiona la reserva de plazas en el aforo para reservas no horarias.
    *   `services/billing_service.py`: Lógica de cobro inteligente, tarifas por sucursal y tipo de vehículo.
    *   `services/notification_service.py`: Sistema de notificaciones asíncronas vía WebSockets para actualización en tiempo real del aforo.
    *   `services/worker_service.py`: Procesos de fondo para limpieza de reservas y tareas programadas (`start_reservation_cleanup`).
    *   `services/branch_service.py`: Lógica de gestión de sucursales y aforo multi-piso.
    *   `services/user_service.py`: Gestión de usuarios y validaciones de seguridad.
    *   `services/email_service.py`: Envío de emails transaccionales (confirmación de reserva, recuperación de contraseña).

4.  **Capa de Datos (`repositories/`)**:
    *   `repositories/user_repository.py`: Acceso a datos de usuarios.
    *   `repositories/reservation_repository.py`: Acceso a datos de reservas.

5.  **Gestión de Accesos ALPR**:
    *   `alpr_service.py`: Servicio independiente de visión artificial (OpenCV + EasyOCR) que consume la API modular.

##  Configuración y Seguridad
- **Variables de Entorno**: Configuración centralizada en `core/config.py` (consume de `.env`). Incluye `RESERVA_HORA_MIN_SEGUNDOS` para tiempo mínimo de anticipación en reservas por hora.
- **Token JWT**: Protección robusta de endpoints con validación de roles en tiempo real.

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

---

