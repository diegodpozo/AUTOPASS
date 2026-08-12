# Dependencias del Proyecto: AUTOPASS (v9.9.1)

Este documento detalla las librerías y herramientas necesarias para el funcionamiento del sistema.

## Requisitos de Entorno
- **Python**: 3.14 (probado en Windows).
- **Gestor de paquetes**: pip (actualizado).
- **Base de datos**: SQLite (incluida con Python, archivo `parking.db`) **o** Turso/libSQL en la nube (desde v9.9.1, la base online se configura vía `DATABASE_URL` en `.env`).

---

## Librerías Principales

### Backend y Servidor
- **`fastapi`** (0.135.1): Framework ASGI para la API REST.
- **`uvicorn`** (0.42.0): Servidor ASGI de alto rendimiento.
- **`sqlalchemy`** (2.0.48): ORM para la gestión de la base de datos SQLite.
- **`pydantic`** (2.12.5): Validación y serialización de datos (schemas).
- **`python-dotenv`** (1.2.2): Gestión de variables de entorno (archivo `.env`).
- **`jinja2`** (3.1.6): Motor de plantillas para renderizado de HTML con herencia.
- **`alembic`** (1.19.0): Migraciones versionadas del esquema de base de datos (`alembic/`).

### Seguridad y Autenticación
- **`passlib[bcrypt]`**: Hashing seguro de contraseñas.
- **`bcrypt`** (5.0.0): Backend de hashing para passlib.
- **`python-jose[cryptography]`**: Generación y validación de tokens JWT.
- **`cryptography`** (46.0.5): Dependencia de python-jose.

### Visión Artificial (ALPR)
- **`easyocr`** (1.7.2): Motor de OCR para lectura de patentes y QR.
- **`opencv-python`** (4.13.0.92): Procesamiento de imágenes y manejo de streams de video.
- **`torch`** (2.11.0) / **`torchvision`** (0.26.0): Motor de Deep Learning (instalados por EasyOCR).
- **`scikit-image`** (0.26.0): Procesamiento de imágenes para preprocesamiento.

### Comunicación y Utilidades
- **`paho-mqtt`** (2.1.0): Cliente MQTT para comunicación con barreras físicas. Usa `CallbackAPIVersion.VERSION2`.
- **`websockets`** (16.0): Comunicación WebSocket para streaming de video y aforo en tiempo real.
- **`psycopg[binary]`** (3.3.4): Driver Postgres para la base en la nube Neon (compatible con Windows). Se instala desde `requirements.txt`; `core/database.py` normaliza `postgresql://` → `postgresql+psycopg://` automáticamente.
- **`libsql`** (0.1.11): Driver oficial de Turso/libSQL para base de datos en la nube (compatible con Windows). Se instala desde `requirements.txt`.
- **`sqlalchemy-libsql`** (0.2.0): Dialecto SQLAlchemy para Turso. **Se instala con `--no-deps`** en `setup_backend.bat` porque su dependencia automática (`libsql-experimental`) no compila en Windows; el shim `libsql_experimental.py` en la raíz del proyecto provee la API que el dialecto espera usando el driver `libsql`.
- **`email-validator`** (2.3.0): Validación de direcciones de email.
- **`python-multipart`**: Soporte para subida de archivos (logos de sucursales).
- **`requests`** (2.32.5): HTTP client para servicios externos.
- **`qrcode`** (8.2): Generación de códigos QR para pases digitales.
- **`Pillow`** (12.2.0): Manipulación de imágenes.

### Inteligencia Artificial (Google)
- **`google-generativeai`** (0.8.6): Integración con Gemini para funcionalidades AI.

### Frontend (CDN - no requieren instalación pip)
- **Leaflet.js** (1.9.4): Mapa interactivo para selector de coordenadas de sucursales.
- **Chart.js**: Gráficos en dashboard de reportes financieros.
- **Flatpickr**: Selector de fecha/hora estilizado para reservas.
- **QRCode.js**: Generación de QR en el navegador para pases digitales.
- **html2canvas**: Captura de screenshots para exportación de tickets.

---

## Instalación

### Preparación del Entorno Virtual
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Post-instalación (Parche necesario)

EasyOCR 1.7.2 requiere `get_display` desde `bidi`, pero `python-bidi` no lo exporta a nivel de paquete. Ejecutá este script después de instalar dependencias:

```powershell
python scripts/patch_bidi.py
```

Esto agrega el import faltante en `bidi/__init__.py` automáticamente.

### Inicialización de Base de Datos
```powershell
python init_db.py  # Crea tablas y datos iniciales
```

### Base de Datos Online (Neon/Postgres, v9.9.2+)

El sistema soporta usar una base Postgres en la nube de Neon para que varias PC compartan los mismos datos. Solo hay que configurar `DATABASE_URL` en `.env` con la connection string (región recomendada `sa-east-1`, São Paulo):

```env
DATABASE_URL=postgresql://usuario:password@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

- La URL puede venir como `postgresql://` (sin driver): `core/database.py` la normaliza a `postgresql+psycopg://` usando psycopg 3.
- En el dashboard de Neon, usar **Connection pooling: OFF** (direct connection), que es la adecuada para SQLAlchemy.
- La migración desde Turso/libSQL se hace con `scripts/migrate_turso_to_neon.py --to-url "<URL_NEON>"` (preserva IDs y sincroniza secuencias).
- Si no se configura `DATABASE_URL` (o apunta a SQLite local), el sistema cae al default `sqlite:///./parking.db`.

### Ejecución
```powershell
# Producción (recomendado): arranque rapido, sin auto-reload
uvicorn main:app --host 127.0.0.1 --port 8000

# Desarrollo: auto-reload al modificar codigo
uvicorn main:app --reload --reload-dir core --reload-dir routes --reload-dir services
```

---

## Notas de Compatibilidad
- El `requirements.txt` incluye 88 dependencias pinneadas para reproducibilidad exacta.
- Para desarrollo, solo son estrictamente necesarias las librerías principales listadas arriba.
- Las dependencias de ALPR (`torch`, `easyocr`, `opencv`) son pesadas (~2GB). Se pueden omitir si no se usa reconocimiento de patentes.
