# Contexto del Sistema: AUTOPASS

Este documento describe la arquitectura de comunicación y el flujo de datos del ecosistema de estacionamiento inteligente tras su transición a una **Arquitectura Limpia**.

## Arquitectura del Ecosistema

El sistema opera bajo un modelo de **Centro de Comando Descentralizado** con una estructura modular por capas:

1. **Capa Core (`core/`)**:
  * `core/config.py`: Gestión centralizada de variables de entorno y constantes.
  * `core/security.py`: Motor de seguridad con **RBAC (Role-Based Access Control)** y JWT.
  * `core/database.py`: Gestión de persistencia y sesiones.
  * `core/mqtt.py`: Orquestador de comunicación con barreras físicas.

2. **Backend Multi-Sede (FastAPI - `routes/`)**:
  * `routes/admin.py`: Gestión de usuarios y reservas con **aislamiento por sucursal**.
  * `routes/reports.py`: Analítica financiera segmentada por sede.
  * `routes/views.py`: Router dedicado exclusivamente para el frontend Jinja2.

3. **Lógica de Negocio (`services/`)**:
  * `services/billing_service.py`: Lógica de cobro inteligente y tarifas por sede.
  * `services/worker_service.py`: Procesos de fondo para limpieza de reservas y tareas programadas.

4. **Gestión de Accesos ALPR**:
  * `alpr_service.py`: Servicio independiente de visión artificial que consume la API modular.

## Configuración y Seguridad
- **Variables de Entorno**: Configuración centralizada en `core/config.py` (consume de `.env`).
- **Token JWT**: Protección robusta de endpoints con validación de roles en tiempo real.

## Comandos de Inicio Rápido

### 1. Preparación del Env virtual
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Inicialización de Base de Datos
```powershell
python init_db.py # Ahora utiliza la estructura modular core/database
```

### 3. Ejecución del Servidor
```powershell
uvicorn main:app --reload
```

---

