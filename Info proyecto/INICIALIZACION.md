# 🚀 Guía de Inicialización: AUTOPASS

Sigue estos pasos para poner en marcha el sistema bajo la nueva arquitectura modular.

## 1. Requisitos Previos
- Python 3.14 (probado en Windows) e instalar dependencias:
```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

> **Nota OCR (v9.10.0+):** El motor OCR es **RapidOCR ONNX** (compatible con Python 3.14+) con fallback a **PaddleOCR** en Python < 3.14. Ya no se usa EasyOCR, por lo que el parche legacy `scripts/patch_bidi.py` fue eliminado y no es necesario ejecutarlo.

## 2. Configuración de Entorno
Crea o edita el archivo `.env` en la raíz. **El setup automático** (`setup_backend.bat`) copia `.env.example → .env` si no existe, y `.env.example` viene **por defecto con la base online de Neon activa**, por lo que cualquier PC nueva se conecta automáticamente a la misma base compartida:

```env
# Base online (Neon/Postgres, sa-east-1 - Sao Paulo): default compartido entre varias PC.
# Para usar SQLite local, reemplazar por: DATABASE_URL=sqlite:///./parking.db
DATABASE_URL=postgresql://usuario:password@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=tu_secreto_aqui
MQTT_BROKER=broker.hivemq.com
MQTT_TOPIC_ENTRADA=parking/barrera/entrada/control
MQTT_TOPIC_SALIDA=parking/barrera/salida/control
IMAGE_DIR=captured_images
RESERVA_HORA_MIN_SEGUNDOS=1800  # Tiempo mínimo de anticipación para reservas por hora (en segundos, default 30 min)
MAINTENANCE_INTERVAL_SECONDS=300  # Intervalo de limpieza de reservas vencidas

# Email (para recuperación de contraseña y confirmaciones)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_password
SMTP_FROM=noreply@autopass.com.ar

# Mercado Pago (Checkout Pro) - ver Sección 7
BASE_URL=https://xxxx.trycloudflare.com      # OBLIGATORIO https:// (MP lo exige en los back_urls)
MP_ACCESS_TOKEN=APP_USR-...                   # Access Token de prueba (sandbox)
MP_PUBLIC_KEY=APP_USR-...                     # Public Key de prueba
MP_WEBHOOK_URL=https://xxxx.trycloudflare.com/v1/user/mercadopago/webhook
MP_PREFERENCE_EXPIRE_MINUTES=45               # Vigencia de la preferencia de pago
```

> **Base online (v9.9.2+):** El sistema usa por defecto la base compartida de **Neon/Postgres** (región `sa-east-1`). Varias PC que corran el backend apuntan a la misma URL y comparten los datos (afectará a todas las PC). El sistema detecta el prefijo `postgresql://` y usa psycopg 3 automáticamente. Si preferís una base local aislada en una PC, reemplazá `DATABASE_URL` por `sqlite:///./parking.db`.

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
# Opción 1: Batch (Recomendado) - abre el navegador cuando el server responde
.\run_server.bat

# Opción 2: Manual (sin --reload, arranque rapido)
.\venv\Scripts\python.exe -m uvicorn main:app --port 8000

# Opción 3: Desarrollo con auto-reload (reinicia al guardar cambios en code/)
.\venv\Scripts\python.exe -m uvicorn main:app --reload --reload-dir core --reload-dir routes --reload-dir services --reload-dir models --reload-dir schemas
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

### Verificación de Base Online (Neon/Postgres)
Si usás la base online, podés verificar la conexión listando las tablas:
```bash
.\venv\Scripts\python.exe -c "from core.database import engine; from sqlalchemy import text; c=engine.connect(); print(c.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name\")).fetchall()); c.close()"
```
Debe listar las tablas del sistema (users, reservations, access_logs, etc.). Si usás SQLite local, reemplazá la consulta por `SELECT name FROM sqlite_master WHERE type='table'`.

---
## 7. Mercado Pago (Checkout Pro) — Configuración y Pruebas (v9.14.0)
> La integración permite pagar **reservas** y **estadías en curso** de forma directa con Mercado Pago (redirección), sin descontar saldo de la billetera.

### 7.1 Obtener credenciales de prueba
1. Entrá a https://www.mercadopago.com.ar/developers/panel y creá una cuenta (o ingresá).
2. Creá una aplicación: **"Desarrollo propio"** → **"Pagos online"** → integrá por **API** → elegí **Cobros/Orders** (Checkout Pro).
3. En **Credenciales → Credenciales de prueba** copiá el **Access Token** y la **Public Key** (en el panel actual el prefijo puede ser `APP_USR-` incluso en modo prueba).
4. En **Cuenta → Usuarios de prueba** creá un vendedor y un comprador si querés simular el login en el sandbox.

### 7.2 Configurar `.env`
- `MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`, `MP_WEBHOOK_URL`, `MP_PREFERENCE_EXPIRE_MINUTES`.
- **`BASE_URL` debe ser `https://`**: Mercado Pago **rechaza** las URLs `http://` en los `back_urls`. Para pruebas locales usá un túnel público HTTPS:

```bash
# Levantar el túnel (cloudflared → server local en el puerto 8000)
.\acceso_remoto.bat     # o: cloudflared tunnel --url http://localhost:8000
# → te da algo como https://xxxx.trycloudflare.com
```
Luego en `.env`:
```
BASE_URL=https://xxxx.trycloudflare.com
MP_WEBHOOK_URL=https://xxxx.trycloudflare.com/v1/user/mercadopago/webhook
```
> ⚠️ El script `acceso_remoto.bat` actualiza `BASE_URL`/`MP_WEBHOOK_URL` automáticamente. Cloudflare es un quick tunnel gratuito, sin cuenta y sin interstitial (la PWA es instalable directamente).

### 7.3 Probar el flujo (sandbox)
1. Reiniciá el server para que tome el `.env` (la config se lee al arrancar): detené uvicorn y volvé a arrancarlo.
2. Ingresá **por el dominio del túnel** y **logueate ahí** — el retorno de MP vuelve al mismo origen; si iniciaste en `localhost`, al volver vas a quedar deslogueado (cada origen guarda su propia sesión).
3. En Reservas → **"PAGAR CON MP"** (o en Cuenta → **ESTADÍAS EN CURSO** → **"PAGAR CON MP"**).
4. En `sandbox.mercadopago.com.ar` pagá como **invitado** (o con usuario de prueba comprador) usando:
   - Tarjeta: `5031 7557 3453 0604` (Mastercard aprobada) · CVV cualquiera · Vencimiento futuro.
5. Al confirmar vuelve a `/perfil?mp_status=approved&mp_tipo=...`: toast de aprobación y la reserva/estadía marcada como pagada (sin tocar saldo; las reservas suman puntos).

> 💡 Verificación rápida en BD: `SELECT id, estado, payment_id FROM mercadopago_payments ORDER BY id DESC LIMIT 5;` — una intención debe quedar `APROBADO` con `payment_id` de MP.

### 7.4 Endpoints
| Método | Ruta | Descripción |
|:---|:---|:---|
| POST | `/v1/user/mercadopago/checkout` | Crea la preferencia (auth de usuario). Body: `{tipo: "reserva"\|"estadia", reserva_id?, access_log_id?, redemption_ticket_id?}` |
| GET | `/v1/user/mercadopago/success\|pending\|failure` | Retorno de MP (sin auth) → confirma y redirige a `/perfil?mp_status=...` |
| POST | `/v1/user/mercadopago/webhook` | Webhook de MP (sin auth) → confirmación alternativa en producción |

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

### 🔄 Scripts de Utilidad
```bash
# Generar patentes de prueba imprimibles (static/test_plates.html)
python scripts/generate_test_plates.py

# Puente de comunicación Serie USB con Arduino Uno (barrera)
python scripts/arduino_bridge.py

# Test de fuente de video para el pipeline ALPR
python scripts/test_video.py
```
> Los scripts legacy de migración/backfill (`backfill_*`, `migrate_add_normalized_patente`, `list_users`, `query_*`) fueron eliminados. La normalización de patentes se maneja vía `routes/parking/utils.py` y las migraciones de esquema con Alembic (`alembic/versions/*`).
