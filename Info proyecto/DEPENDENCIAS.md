# Dependencias del Proyecto: AUTOPASS (v9.9.0+)

Este documento detalla las librerías y herramientas necesarias para el funcionamiento del sistema.

## Requisitos de Entorno
- **Python**: 3.14+ (probado en Windows).
- **Gestor de paquetes**: pip (actualizado).
- **Base de datos**: Neon/Postgres en la nube (región `sa-east-1`) **o** SQLite local (`parking.db`).

---

## Archivos de Dependencias

Las dependencias se encuentran en un único archivo `requirements.txt` (~42 dependencias directas), organizado por secciones (`CORE`, `DATABASE`, `AUTH & SECURITY`, `CV/IMAGING`, `SCIENTIFIC`, `HARDWARE`, `AI/OCR`, `TESTING`). Las dependencias de IA (PaddleOCR/paddlepaddle) solo se instalan en Python < 3.14 y pueden fallar sin afectar el sistema core.

---

## Librerías Core (secciones `CORE`/`DATABASE`/`AUTH`/`CV`/`HARDWARE`/`TESTING` de `requirements.txt`)

### Backend y Servidor
- **`fastapi`** (0.141.1): Framework ASGI para la API REST.
- **`uvicorn`** (0.42.0): Servidor ASGI de alto rendimiento.
- **`starlette`** (1.6.0): Utilidades ASGI (base de FastAPI). ⚠️ Subió desde 0.52.1 a la rama 1.x en la auditoría A2 (P2) para fijar 5 CVEs (BadHost/DoS); verificado con suite completa + WS. El único CVE restante del venv es `ecdsa` (transitorio, sin fix, no explotable).
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
- **`python-jose`** (3.5.0): Generación y validación de tokens JWT (solo HS256). ⚠️ Su dependencia transitiva `ecdsa` (0.19.2) arrastra CVE-2024-23342 (Minerva, P-256) **sin fix upstream**; no es explotable aquí porque el proyecto nunca usa ES256/ECDSA. A futuro se puede migrar a `PyJWT` para eliminar `ecdsa` de la cadena.
- **`passlib`** (1.7.4): Hashing seguro de contraseñas.
- **`bcrypt`** (5.0.0): Backend de hashing para passlib (usado directamente por `core/security.py`).
- **`slowapi`** (0.1.10): Rate limiting por IP en endpoints públicos de auth (login/register/recuperación) y límite global por defecto 300/min.
- **`cryptography`** (50.0.1): Dependencia de python-jose. Subido en A2 (P2) para fijar todos los CVEs (incluido el crítico 9.8 de 46.0.5 y los de PKCS#7/wildcard/OpenSSL de ≥46).

### Visión Artificial (CV)
- **`opencv-python`** (4.13.0.92): Procesamiento de imágenes y manejo de streams de video.
- **`numpy`**: Operaciones numéricas para arrays de imagen. Marcado por versión de Python: `>=1.26.0,<2.3.0` para Python < 3.14 y `>=2.3.0,<2.5.0` para Python ≥ 3.14 (numpy < 2.3.0 no tiene wheels para Python 3.14).
- **`scipy`** (>=1.13.0): Procesamiento científico de imágenes.
- **`scikit-image`** (>=0.22.0): Procesamiento de imágenes para preprocesamiento ALPR.
- **`shapely`** (>=2.0.0): Geometría para detección de regiones de placa.
- **`pyclipper`** (>=1.3.0): Clippath para contornos de patentes.
- **`Pillow`** (>=10.0.0): Manipulación de imágenes.
- **`qrcode`** (8.2): Generación de códigos QR para pases digitales.

### Hardware e IoT
- **`paho-mqtt`** (2.1.0): Cliente MQTT para comunicación con barreras físicas. Usa `CallbackAPIVersion.VERSION2`.
- **`pyserial`** (3.5): Comunicación serial con Arduino/ESP32.

### Utilidades
- **`pydantic`** (>=2.10.0): Validación y serialización de datos (schemas).
- **`pydantic_core`** (>=2.27.0): Core en Rust de Pydantic v2.
- **`requests`** (2.33.0): HTTP client para servicios externos.
- **`httpx`** (0.28.1): HTTP client async.
- **`email-validator`** (2.3.0): Validación de direcciones de email.
- **`protobuf`** (>=4.25.0): Serialización (dependencia de PaddleOCR).
- **`colorama`** (0.4.6): Colores en terminal.
- **`click`** (8.3.1): Utilidades CLI.
- **`setuptools`** (>=70.0.0): Build tools.

### Testing
- **`pytest`** (>=8.0.0): Framework de pruebas.
- **`pytest-timeout`** (>=2.3.0): Timeout por test (evita bloqueos de la suite).

---

## Librerías de OCR (Visión Artificial)

> El motor OCR es **dual** (v9.10.0). `rapidocr-onnxruntime` es obligatorio (compatible con Python 3.14+). `paddleocr`/`paddlepaddle` no tienen wheel para Python 3.14+ y solo se instalan en Python < 3.14; en ese caso actúan como fallback automático.

### OCR (Motor Dual)
- **`rapidocr-onnxruntime`** (>=1.2.0): Motor primario, optimizado para Python 3.14+ (sin dependencia de paddlepaddle).
- **`paddleocr`** (3.7.0): Motor de OCR fallback (solo `python_version < '3.14'`).
- **`paddlepaddle`** (3.2.2): Backend de Deep Learning para PaddleOCR (solo `python_version < '3.14'`).

> Nota: Las dependencias sin uso (Google Gemini AI SDK suite: `google-generativeai`, `google-api-python-client`, `google-auth`, etc., `tqdm`, `pyyaml`, `annotated-doc`) y las declaraciones redundantes (`opencv-python-headless` junto a `opencv-python`, `psycopg-binary` junto a `psycopg[binary]`) fueron depuradas de `requirements.txt`.

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
El instalador crea el entorno virtual, instala las dependencias de `requirements.txt`, configura `.env`, inicializa la BD y ejecuta los tests.

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
