#  Guía de Inicialización: AUTOPASS

Sigue estos pasos para poner en marcha el sistema bajo la nueva arquitectura modular.

## 1. Requisitos Previos
- Python 3.9+ e instalar dependencias:
```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
# O el comando rápido:
.\venv\Scripts\python.exe -m pip install fastapi uvicorn sqlalchemy python-dotenv jinja2 passlib[bcrypt] python-jose[cryptography] paho-mqtt requests opencv-python easyocr httpx pytest
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
IMAGE_DIR=captured_images
```

## 3. Preparación de Base de Datos
Este paso crea las tablas y los roles iniciales (Admin Global).
```bash
python init_db.py
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

## 5. Verificación de Integridad
Ejecuta los tests automáticos para asegurar que la modularización está operativa:
```bash
.\venv\Scripts\python.exe test_user_flow.py
```

---
### 🚦 Flujo de Prueba Rápido (ALPR)
1. Inicia el servidor.
2. Abre una terminal nueva y corre `python alpr_service.py` (simulará una cámara).
3. Entra a `http://localhost:8000/dashboard` como admin (admin@autopass.com / admin123).
4. En la pestaña **Live**, deberías ver el stream simulado y las detecciones ingresando a la base de datos modular.
