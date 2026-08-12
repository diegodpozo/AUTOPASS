# 🚀 Guía de Inicialización: AUTOPASS

Sigue estos pasos para poner en marcha el sistema bajo la nueva arquitectura modular.

## 1. Requisitos Previos
- Python 3.14 (probado en Windows) e instalar dependencias:
```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

> **⚠️ POST-INSTALACIÓN:** Después de instalar dependencias, ejecutá el siguiente parche para evitar un error de importación de EasyOCR:
> ```bash
> .\venv\Scripts\python.exe scripts\patch_bidi.py
> ```

## 2. Configuración de Entorno
Crea o edita el archivo `.env` en la raíz:
```env
DATABASE_URL=sqlite:///./parking.db
SECRET_KEY=tu_secreto_aqui
MQTT_BROKER=broker.hivemq.com
MQTT_TOPIC_ENTRADA=autopass/entrada
MQTT_TOPIC_SALIDA=autopass/salida
IMAGE_DIR=captured_images
RESERVA_HORA_MIN_SEGUNDOS=1800  # Tiempo mínimo de anticipación para reservas por hora (en segundos, default 30 min)
MAINTENANCE_INTERVAL_SECONDS=300  # Intervalo de limpieza de reservas vencidas

# Email (para recuperación de contraseña y confirmaciones)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_password
SMTP_FROM=noreply@autopass.com.ar

# Opcional: Base de datos online (Neon/Postgres) para compartir datos entre varias PC
# DATABASE_URL=postgresql://usuario:password@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

> **Base online (v9.9.2+):** Para usar una base en la nube en vez del SQLite local, completá `DATABASE_URL` con la connection string de Neon/Postgres (región recomendada `sa-east-1`). El sistema detecta el prefijo `postgresql://` y usa psycopg 3 automáticamente. Varias PC pueden apuntar a la misma URL y compartir los datos. La migración desde Turso/libSQL se hace con `scripts/migrate_turso_to_neon.py --to-url "<URL_NEON>"`.

## 3. Preparación y Migración de Base de Datos
Este paso crea las tablas, los roles iniciales (Admin Global) y sincroniza las migraciones con Alembic:
```bash
# 1. Crear tablas y seed inicial
venv\Scripts\python.exe init_db.py

# 2. Sellar e inspeccionar migraciones de Alembic
venv\Scripts\alembic.exe stamp head
venv\Scripts\alembic.exe upgrade head
```

## 4. Credenciales por Defecto

Para el primer acceso y testeo del sistema, utilizá las siguientes credenciales:

| Rol | Email | Contraseña | Sucursal |
| :--- | :--- | :--- | :--- |
| **Admin Global** | `admin@autopass.com` | `admin123` | *Todas* |
| **Local Admin** | `admmoron@autopass.com` | `admin123` | AUTOPASS Morón |
| **Local Admin** | `admituzaingo@autopass.com` | `admin123` | AUTOPASS Ituzaingó |
| **Local Admin** | `admcastelar@autopass.com` | `admin123` | AUTOPASS Castelar |

### Gestión de otros Roles (Admin Locales y Staff)
El sistema utiliza una arquitectura **RBAC** (Control de Acceso Basado en Roles). Una vez dentro como Administrador Global, podés crear y gestionar los demás niveles desde la pestaña **Usuarios** del Dashboard:

1.  **Administrador de Sucursal (local_admin):** Gestiona una sucursal específica (Tarifas, Empleados, Reportes).
2.  **Empleado (staff):** Perfil operativo para monitoreo de barreras y registros manuales.
3.  **Cliente (user):** Usuarios finales que realizan reservas y acumulan puntos.

> **⚠️ SEGURIDAD:** Las contraseñas se guardan de forma encriptada (hashing) en la base de datos. Si olvidás la contraseña de un usuario administrativo, el Administrador Global puede restablecerla directamente desde el Dashboard.

## 5. Ejecución del Servidor y Cámaras

### Iniciar Servidor Principal
```bash
# Opción 1: Batch (Recomendado)
.\run_server.bat

# Opción 2: Manual
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

### Iniciar Cámaras (ALPR)

Las cámaras se configuran y controlan directamente desde el Dashboard en **Ajustes > Monitoreo**:

1. Ingresá la IP de la cámara en el campo correspondiente (Entrada/Salida).
2. Presioná **Guardar**.
3. Presioná **Play** (▶) en la cámara deseada — el backend inicia automáticamente el servicio `alpr_service.py` como proceso hijo.

No es necesario ejecutar nada en terminal.

## 6. Verificación de Integridad
Ejecutá los tests automáticos para asegurar que todos los módulos e integraciones están operativos:
```bash
.\venv\Scripts\python.exe -m pytest tests/ --verbose
```

### Verificación de Base Online (Turso)
Si configuraste Turso, podés verificar la conexión ejecutando:
```bash
.\venv\Scripts\python.exe -c "from core.database import engine; from sqlalchemy import text; c=engine.connect(); print(c.execute(text(\"SELECT name FROM sqlite_master WHERE type='table'\")).fetchall()); c.close()"
```
Debe listar las 15 tablas del sistema (users, reservations, access_logs, etc.). Si da error `308 redirect`, falta `?secure=true` en `DATABASE_URL`.

---
### 🚦 Flujo de Prueba Rápido (ALPR)
1. Inicia el servidor.
2. Abre una terminal nueva y corre `python alpr_service.py` (configurá `GATE_TYPE` y `VIDEO_SOURCE` en `.env` para simular con video de archivo).
3. Entra a `http://localhost:8000/dashboard` como admin (admin@autopass.com / admin123).
4. En la pestaña **Live**, deberías ver el stream y las detecciones ingresando a la base de datos.

### Modo Simulación (Sin Cámaras)
Si no tenés cámaras IP, configurá en `.env`:
```
GATE_TYPE=entrada
VIDEO_SOURCE=path/to/video.mp4
```
Y ejecutá `python alpr_service.py`. Esto reproduce un video y simula detecciones. Las patentes se enviarán al backend como si fueran de una cámara real.

### 🔄 Scripts de Migración y Utilidad
```bash
# Normalizar todas las patentes en access_logs
python scripts/backfill_normalize_all_access_logs.py

# Vincular reservas pagadas a access_logs existentes
python scripts/backfill_attach_reservations.py

# Consultar patente específica en access_logs
python scripts/query_access_logs.py
```
