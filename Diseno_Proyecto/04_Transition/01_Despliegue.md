# Plan de Despliegue — AUTOPASS

## Requisitos del Entorno

### Desarrollo
- **SO**: Windows 10/11
- **Python**: 3.14 (probado en Windows)
- **Base de datos**: SQLite (archivo local)
- **Migraciones**: Alembic (`alembic/`, migración inicial `c833a3129266_initial_schema`)
- **RAM**: 4 GB mínimo (8 GB recomendado para ALPR con EasyOCR)
- **Cámara**: Webcam o archivo de video para simulación

### Producción
- **SO**: Windows Server 2019+ / Ubuntu 20.04+
- **Python**: 3.14 (probado en Windows)
- **Base de datos**: PostgreSQL 13+
- **Migraciones**: Alembic
- **RAM**: 8 GB mínimo (16 GB recomendado para múltiples cámaras ALPR)
- **GPU**: Opcional (PyTorch puede usar CUDA para acelerar EasyOCR)
- **Disco**: 50 GB SSD mínimo
- **Red**: Conexión estable a cámaras IP (LAN) + broker MQTT

## Instalación Paso a Paso

### 1. Clonar repositorio
```powershell
git clone <repo-url> AUTOPASS
cd AUTOPASS
```

### 2. Crear entorno virtual
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar dependencias
```powershell
pip install -r requirements.txt
```

### 4. Parche EasyOCR (post-instalación obligatorio)
```powershell
.\venv\Scripts\python.exe scripts\patch_bidi.py
```

### 5. Configurar variables de entorno
Crear archivo `.env` en la raíz:
```env
SECRET_KEY=tu_clave_secreta_segura
DATABASE_URL=sqlite:///./parking.db

# SMTP (Mailtrap para pruebas)
SMTP_SERVER=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=tu_usuario
SMTP_PASSWORD=tu_password

# MQTT
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883

# Para PostgreSQL en producción:
# DATABASE_URL=postgresql://user:pass@localhost:5432/autopass
```

### 6. Inicializar base de datos
```powershell
.\venv\Scripts\python.exe init_db.py
```
Esto crea las tablas y datos iniciales:
- Usuario admin por defecto (admin@autopass.com / admin123)
- Sucursal por defecto
- Tarifas trimodales por defecto
- Promociones iniciales

### 7. Iniciar servidor
```powershell
.\venv\Scripts\uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Iniciar servicio ALPR (producción)
El ALPR se inicia desde el Dashboard > Ajustes > Monitoreo > Play.
O manualmente para pruebas:
```powershell
.\venv\Scripts\python.exe alpr_service.py
```

## Scripts de Automatización

| Script | Propósito |
|--------|-----------|
| `setup_backend.bat` | Crea venv, instala dependencias, aplica parche, inicializa DB |
| `run_server.bat` | Inicia Uvicorn con configuración de producción |

## Configuración de Producción (PostgreSQL)

### Migrar de SQLite a PostgreSQL
1. Instalar PostgreSQL y crear base de datos `autopass`
2. Actualizar `DATABASE_URL` en `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/autopass
   ```
3. Ejecutar `init_db.py` para crear tablas y seed data

### Configuración de Uvicorn en Producción
```powershell
.\venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 --limit-concurrency 100
```

## Arquitectura de Red (Producción)

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Cliente Web    │────►│  Internet    │────►│  Servidor       │
│  (Browser)      │     │              │     │  (FastAPI)      │
└─────────────────┘     └──────────────┘     └───────┬─────────┘
                                                      │
                                                      │ (LAN)
                                                      │
              ┌───────────────────────────────────────┼──────────┐
              │                                       │          │
              ▼                                       ▼          │
    ┌─────────────────┐                     ┌─────────────────┐  │
    │  Cámaras IP     │                     │  ESP32 (MQTT)   │  │
    │  (ALPR)         │                     │  Barreras       │  │
    └─────────────────┘                     └─────────────────┘  │
              │                                       │          │
              ▼                                       ▼          │
    ┌─────────────────┐                     ┌─────────────────┐  │
    │  Broker MQTT    │                     │  PostgreSQL     │  │
    │  (HiveMQ/Cloud) │                     │  (Datos)        │  │
    └─────────────────┘                     └─────────────────┘  │
              └──────────────────────────────────────────────────┘
```

## Recomendaciones Operativas

1. **Backups**: Programar backup diario de la base de datos
2. **Monitoreo**: Verificar heartbeats de cámaras en `/v1/system/health`
3. **Logs**: Revisar logs del servidor para detectar errores de conexión MQTT o DB
4. **Actualización**: Para actualizar, detener servidor, aplicar cambios, reiniciar
5. **Seguridad**: Cambiar `SECRET_KEY` por defecto, usar HTTPS en producción
6. **Mantenimiento**: El worker de limpieza corre cada 5 min; no requiere intervención

## Rollback Plan
1. Mantener backup de la base de datos anterior
2. Mantener versión anterior del código en una rama `release/vX.X.X`
3. Para revertir: detener servidor, restaurar backup DB, hacer checkout a versión anterior, reiniciar
