# Dependencias del Proyecto: AUTOPASS (v9.9.0+)

Este documento detalla las librerías y herramientas necesarias para el funcionamiento del sistema.

## Requisitos de Entorno
- **Python**: 3.14+ (probado en Windows).
- **Gestor de paquetes**: pip (actualizado).
- **Base de datos**: Neon/Postgres en la nube (región `sa-east-1`) **o** SQLite local (`parking.db`).

---

## Archivos de Dependencias

Las dependencias se encuentran en un único archivo `requirements.txt` (~65 paquetes), organizado por secciones. Las dependencias de IA (PaddleOCR, Gemini) están incluidas pero pueden fallar en Python 3.14+ sin afectar el sistema core.

---

## Librerías Core (`requirements-core.txt`)

### Backend y Servidor
- **`fastapi`** (0.135.1): Framework ASGI para la API REST.
- **`uvicorn`** (0.42.0): Servidor ASGI de alto rendimiento.
- **`starlette`** (0.52.1): Utilidades ASGI (base de FastAPI).
- **`python-multipart`**: Soporte para subida de archivos (logos de sucursales).
- **`python-dotenv`** (1.2.2): Gestión de variables de entorno (archivo `.env`).
- **`jinja2`** (3.1.6): Motor de plantillas para renderizado de HTML con herencia.
- **`websockets`** (16.0): Comunicación WebSocket para streaming de video y aforo en tiempo real.
- **`httptools`**: Aceleración de parsing HTTP.

### Base de Datos
- **`sqlalchemy`** (2.0.48): ORM para la gestión de la base de datos.
- **`alembic`** (1.19.0): Migraciones versionadas del esquema de base de datos (`alembic/`).
- **`psycopg[binary]`** (3.3.4): Driver Postgres para la base en la nube Neon (compatible con Windows). `core/database.py` normaliza `postgresql://` → `postgresql+psycopg://` automáticamente.
- **`dnspython`**: Resolución DNS para connection strings de Postgres.

### Seguridad y Autenticación
- **`python-jose`** (3.5.0): Generación y validación de tokens JWT.
- **`passlib`** (1.7.4): Hashing seguro de contraseñas.
- **`bcrypt`** (5.0.0): Backend de hashing para passlib (usado directamente por `core/security.py`).
- **`slowapi`** (0.1.9): Rate limiting por IP en endpoints públicos de auth (login/register/recuperación) y límite global por defecto 300/min.
- **`cryptography`** (46.0.5): Dependencia de python-jose.

### Visión Artificial (CV)
- **`opencv-python`** (4.13.0.92): Procesamiento de imágenes y manejo de streams de video.
- **`opencv-python-headless`** (4.13.0.92): Versión headless para servidores sin GUI.
- **`numpy`**: Operaciones numéricas para arrays de imagen.
- **`scipy`** (1.15.0): Procesamiento científico de imágenes.
- **`scikit-image`** (0.26.0): Procesamiento de imágenes para preprocesamiento ALPR.
- **`shapely`** (2.10.0): Geometría para detección de regiones de placa.
- **`pyclipper`** (1.3.0.6): Clippath para contornos de patentes.
- **`Pillow`** (12.2.0): Manipulación de imágenes.
- **`qrcode`** (8.2): Generación de códigos QR para pases digitales.

### Hardware e IoT
- **`paho-mqtt`** (2.1.0): Cliente MQTT para comunicación con barreras físicas. Usa `CallbackAPIVersion.VERSION2`.
- **`pyserial`** (3.5): Comunicación serial con Arduino/ESP32.

### Utilidades
- **`pydantic`** (2.12.5): Validación y serialización de datos (schemas).
- **`requests`** (2.32.5): HTTP client para servicios externos.
- **`httpx`** (0.28.0): HTTP client async.
- **`email-validator`** (2.3.0): Validación de direcciones de email.
- **`protobuf`** (4.25.0): Serialización (dependencia de submódulos Google).
- **`pyyaml`**: parsing de YAML.
- **`colorama`**: Colores en terminal.
- **`click`**: CLI utilities.
- **`tqdm`**: Barras de progreso.
- **`setuptools`**: Build tools.

### Testing
- **`pytest`** (9.1.1): Framework de pruebas.

---

## Librerías de OCR (Visión Artificial)

> El motor OCR es **dual** (v9.10.0). `rapidocr-onnxruntime` es obligatorio (compatible con Python 3.14+). `paddleocr`/`paddlepaddle` no tienen wheel para Python 3.14+ y solo se instalan en Python < 3.14; en ese caso actúan como fallback automático.

### OCR (Motor Dual)
- **`rapidocr-onnxruntime`** (>=1.2.0): Motor primario, optimizado para Python 3.14+ (sin dependencia de paddlepaddle).
- **`paddleocr`** (3.7.0): Motor de OCR fallback (solo `python_version < '3.14'`).
- **`paddlepaddle`** (3.2.2): Backend de Deep Learning para PaddleOCR (solo `python_version < '3.14'`).

### Google Gemini
- **`google-generativeai`** (0.8.6): Integración con Gemini para funcionalidades AI.
- **`google-api-python-client`**, **`google-auth`**, **`google-auth-httplib2`**, **`google-ai-generativelanguage`**, **`googleapis-common-protos`**: SDK de Google.

---

## Frontend (CDN - no requieren instalación pip)
- **Leaflet.js** (1.9.4): Mapa interactivo para selector de coordenadas de sucursales.
- **Chart.js**: Gráficos en dashboard de reportes financieros.
- **Flatpickr**: Selector de fecha/hora estilizado para reservas.
- **QRCode.js**: Generación de QR en el navegador para pases digitales.
- **html2canvas**: Captura de screenshots para exportación de tickets.

---

## Instalación

### Instalación Automática (Recomendada)
```powershell
.\setup_backend.bat
```
El instalador crea el entorno virtual, instala dependencias core, intenta instalar IA (opcional), configura `.env`, inicializa la BD y ejecuta los tests.

### Instalación Manual
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Base de Datos Online (Neon/Postgres) — Default

El sistema usa **por defecto** la base Postgres en la nube de Neon para que varias PC compartan los mismos datos. El `.env.example` viene con la connection string de Neon activa, y el setup automático (`setup_backend.bat`) la copia a `.env` si esta no existe. Por eso **toda PC nueva instalada se conecta automáticamente a la base compartida** (región recomendada `sa-east-1`, São Paulo):

```env
DATABASE_URL=postgresql://usuario:password@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

- La URL puede venir como `postgresql://` (sin driver): `core/database.py` la normaliza a `postgresql+psycopg://` usando psycopg 3.
- En el dashboard de Neon, usar **Connection pooling: OFF** (direct connection), que es la adecuada para SQLAlchemy.
- ⚠️ Como todas las PC apuntan a la misma base, los cambios afectan a todas las instalaciones.
- Si se prefiere una base local aislada en una PC, reemplazar `DATABASE_URL` por `sqlite:///./parking.db` en su `.env` (ya no es el default).

### Ejecución
```powershell
# Arranque rápido (recomendado)
.\run_server.bat

# Producción manual
.\venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

---

## Notas de Compatibilidad
- `rapidocr-onnxruntime` (motor primario) funciona en Python 3.14+ sin `paddlepaddle`.
- `paddleocr`/`paddlepaddle` (~2GB) no tienen wheel para Python 3.14+. Solo se instalan en Python < 3.14 y actúan como fallback si RapidOCR no está disponible.
- `scripts/patch_bidi.py` fue eliminado — era un parche legacy de EasyOCR que ya no se necesita con RapidOCR/PaddleOCR.
