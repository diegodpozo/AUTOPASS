# Arquitectura del Sistema ALPR — AUTOPASS

## Visión General
El servicio ALPR está modularizado en el **paquete `alpr/`** (`config.py`, `preprocessor.py`, `video_streamer.py`, `ws_client.py`, `ocr_engine.py`, `runner.py`). `alpr_service.py` actúa como wrapper/entrypoint que lanza el `runner` y se ejecuta como proceso hijo del backend FastAPI. Se encarga de capturar video, procesar frames, detectar patentes y códigos QR, y comunicar los eventos al backend.

## Modos de Operación

El ALPR se configura mediante la variable de entorno `GATE_TYPE`:

| Valor de `GATE_TYPE` | Descripción | Uso |
|------|-------------|-----|
| `entrada` | Procesa patentes de entrada | Cámara de entrada al estacionamiento |
| `salida` | Procesa patentes de salida | Cámara de salida del estacionamiento |
| `patente` | Procesa patentes genérico | Modo dual (entrada+salida) |
| `qr` | Procesa códigos QR | Escáner QR |
| `predio` | Solo streaming WebSocket | Cámara de seguridad del predio (sin OCR) |

La fuente de video se configura con `VIDEO_SOURCE` (puede ser `0` para webcam local, una URL RTSP, o una URL HTTP MJPEG).

## Arquitectura Interna

```
┌─────────────────────────────────────────────────────────────────────┐
│                    paquete alpr/ (módulos)                          │
│  alpr_service.py (wrapper) + runner.py (orquestador)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │ video_streamer   │───►│  runner.py       │───►│  Queue        │  │
│  │ (Frame Capture)  │    │ Motion Detection │    │  maxsize=12   │  │
│  │  (OpenCV/FFmpeg) │    │ ROI central zone │    │  drop-oldest  │  │
│  └──────────────────┘    │ threshold=800    │    └──────┬────────┘  │
│                          └──────────────────┘           │           │
│                                    ┌────────────────────┘          │
│                                    ▼                               │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │              OCR Worker Thread                             │     │
│  │                                                            │     │
│  │  ┌───────────┐  ┌──────────────┐  ┌───────────────────┐  │     │
│  │  │ MERCOSUR  │─►│ ROI          │─►│ Dual OCR Engine   │  │     │
│  │  │ Blue Band │  │ Detection    │  │ RapidOCR (ONNX)   │  │     │
│  │  │ Crop      │  │ (contours+   │  │ + PaddleOCR       │  │     │
│  │  │           │  │  strips)     │  │ fallback           │  │     │
│  │  └───────────┘  └──────────────┘  └────────┬──────────┘  │     │
│  │                                             │             │     │
│  │  ┌───────────┐  ┌──────────────┐  ┌────────▼──────────┐  │     │
│  │  │ Quick QR  │  │ Consensus    │  │ Shape Validation  │  │     │
│  │  │ Detection │  │ Vote Buffer  │  │ (KNOWN_PLATE_     │  │     │
│  │  │           │  │ 1 voto alta  │  │   FORMATS + bbox) │  │     │
│  │  └───────────┘  │ conf / 2-3   │  └───────────────────┘  │     │
│  │                 │ baja conf    │                        │     │
│  │                 └──────┬───────┘                        │     │
│  │                        │                                  │     │
│  │                   ┌────▼─────────┐                        │     │
│  │                   │ Event Send   │                        │     │
│  │                   │ (HTTP POST)  │                        │     │
│  │                   │ + 5s pause   │                        │     │
│  │                   └──────────────┘                        │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │              Video WebSocket Thread                        │     │
│  │  ws_client: envía frames en tiempo real a                 │     │
│  │  /v1/system/ws/video/{camera_id}                          │     │
│  └───────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

## Componentes Clave

### 1. Captura de Frames (Frame Capture)
- Módulo `video_streamer.py`: Fuente Cámara IP (RTSP/HTTP) o archivo de video
- Resolución auto-escalada a 1280px de ancho
- Soporte FFmpeg backend para streams HTTP
- Reintentos automáticos en fallos de captura (3 intentos)

### 2. Detección de Movimiento (Motion Detection)
- Módulo `ocr_engine.py` (`detect_motion`) usado por `runner.py` como compuerta previa a encolar frames
- **Zona central de la ROI** (25%-85% alto, 10%-90% ancho) en vez del frame completo
- Frame differencing con Gaussian blur y `cv2.countNonZero` sobre un umbral fijo de **800 píxeles** (`non_zero > 800`)
- Contador de frames descartados con log periódico (~5s)
- **Método estático alternativo** en `preprocessor.py` (`detect_motion`, resize 320x240 + `ALPR_MOTION_THRESHOLD` default 3000): definido pero **no se usa** en el flujo principal actual
- Configurable: `ALPR_FORCE_OCR` para forzar OCR incluso sin movimiento
- Tras aceptar una patente, **pausa de 5 segundos** antes de volver a escanear

### 3. Cola de Frames (Frame Queue)
- `maxsize=12` (configurable) con política **drop-oldest**
- Prioriza frames recientes sobre antiguos
- Evita acumulación cuando el OCR es más lento que la captura

### 4. Detección de ROI (Region of Interest)
**ROI principal** (`main_roi`): 77% del alto (15%→92%) x 90% del ancho (5%→95%). Sobre él se aplican dos estrategias:

**Extracción de patente (en orden de prioridad dentro de `ocr_worker`)**:
1. **Prioridad 1**: Con ≥2 detecciones OCR, combinarlas por posición X → `full_7_pattern` (7 caracteres completos)
2. **Prioridad 2**: Detección individual con `full_7_pattern` (7 caracteres)
3. **Prioridad 3**: Match con `LATAM_PLATE_PATTERN` (formatos conocidos)
4. **Prioridad 4**: Combinación de ≥2 detecciones por orden Y, y luego por X, con `LATAM_PLATE_PATTERN`
5. **Fallback**: `ImagePreprocessor.find_plate_roi(frame)` — búsqueda por franjas fijas y contornos (Canny + cierre morfológico) con confianza mínima `FALLBACK_MIN_CONFIDENCE=0.65`

**`find_plate_roi` (fallback)**:
- Estrategia de franjas (`strip_bottom`, `strip_center`) con segmentación en bloques de 320px
- Detección por contornos (bilateral → Canny → cierre morfológico), filtrado por área y aspect ratio
- Elimina las franjas/contornos duplicados con IoU > 0.4
- No usa *Haar cascade* (el detector de placas de OpenCV fue removido del flujo)

Validación de ROI (`_is_valid_plate_roi`):
- Ancho mínimo: 70px, Alto mínimo: 18px
- Aspect ratio: 1.5 - 6.0
- No puede ser más ancho que 85% del frame

### 5. Recorte MERCOSUR (Blue Band Crop)
- `is_mercosur_candidate()`: Detección HSV (H:90-135), verifica top 35% de ROI, ratio azul > 0.06
- `crop_below_blue()`: Si detecta la franja azul, recorta por debajo de ella (+5px margen)
- Se aplica al **main_roi antes del OCR** para todas las patentes MERCOSUR candidatas
- Elimina texto "ARGENTINA" de la franja azul que confunde al OCR

### 6. Motor OCR Dual (RapidOCR / PaddleOCR)
- Módulo `ocr_engine.py`; conmutación automática entre motores
- **RapidOCR ONNX**: Motor primario, optimizado para Python 3.14+, instalado por defecto en `requirements.txt`
- **PaddleOCR**: Fallback automático si RapidOCR no está disponible (incompatible con Python 3.14+, se instala solo para Python < 3.14)
- Intervalo entre OCRs: `ALPR_OCR_INTERVAL=0.35s`
- **Escalado inteligente ROI**: Re-escalado automático a 80px de alto por interpolación cúbica en recortes pequeños (evita confusión de dígitos como `6` vs `5`)
- **Umbrales de alta confianza** (nota): la variable `ALPR_CONFIDENCE_THRESHOLD` queda definida en `config.py` pero **no se utiliza** en la lógica real del motor; los umbrales efectivos de alta confianza son `0.75` (no-moto) y `MOTO_MIN_CONFIDENCE=0.85` (moto), usados en el consenso rápido de 1 voto

### 7. Sistema de Consenso (Vote Buffer)
- Buffer temporal de lecturas de la misma patente
- Ventana de consenso: `ALPR_CONSENSUS_WINDOW` (default 4.0s)
- **Shortcut de 1 voto (consenso rápido para pruebas)**: si la confianza es alta **y** el formato es válido → `req_votes = 1` (aceptación instantánea)
  - Alta confianza (no-moto): `avg_conf >= 0.75`
  - Alta confianza (moto): `avg_conf >= MOTO_MIN_CONFIDENCE` (default 0.85)
  - Se exige además que el formato pertenezca a los formatos conocidos (`is_valid_format`)
- Si confianza baja o formato inválido: `req_votes = max(2, CONSENSUS_REQUIRED)` (default 2)
- Placas fuzzy: `_plate_close()` permite ≤1 carácter de distancia o compartición de bloque numérico (≥3 dígitos iguales) para el debounce de cooldown

### 8. Validación de Formato de Patente
- `KNOWN_PLATE_FORMATS`: Validación estricta contra patrones regex conocidos (definido en `ocr_engine.py`)
- Acepta formatos: ARG Mercosur (Auto y Moto), ARG Antigua (Auto y Moto), Brasil, Uruguay **y Paraguay**
- **Validación de forma (shape)**: El `KNOWN_PLATE_FORMATS` descarta lecturas que no coincidan con ningún formato conocido (`continue`)
- **Filtro anti-truncamiento de moto**: si la patente coincide con patrón de moto pero la caja (`bbox`) del texto detectado es rectangular horizontal de auto (aspect ratio `> 2.2`), se descarta como recorte incompleto

### 9. Quick QR Detection
- Escaneo de QR en cada frame (previo al OCR)
- Usa `cv2.QRCodeDetector()` de OpenCV para decodificación rápida
- Cooldown/Debounce configurable (`ALPR_COOLDOWN`, default 10s) para evitar eventos duplicados

### 10. Cooldown entre validaciones
- `COOLDOWN_SECONDS` (default 10s): Evita procesar la misma patente en ventana corta
- **Deduplicación fuzzy**: `_plate_close()` compara patentes normalizadas (solo `[A-Z0-9]`) con ≤1 carácter de diferencia
- Normalización: `re.sub(r'[^A-Z0-9]', '', plate).upper()` antes de comparar
- Tras aceptar una patente: **pausa de 5 segundos** antes de volver a escanear

### 11. Video WebSocket
- Módulo `ws_client.py`; envía frames JPEG comprimidos en tiempo real
- Resolución: 640x360, calidad JPEG 50
- Endpoint: `/v1/system/ws/video/{camera_id}`
- Token JWT como query param (`?token=...`) para autenticación
- Auto-reconexión en fallos

## Formato de Patentes Soportado

| Tipo | Formato | Ejemplo | Regex |
|------|---------|---------|-------|
| ARG Mercosur Auto | `AA 123 AA` | `AB 536 CR` | `^[A-Z]{2}\d{3}[A-Z]{2}$` |
| ARG Antigua | `ABC 123` | `PHA 498` | `^[A-Z]{3}\d{3}$` |
| ARG Moto Antigua | `AB 123` | `AC 404` | `^[A-Z]{2}\d{3}$` |
| ARG Moto Mercosur (6c) | `AB 123 A` | `AC 404 S` | `^[A-Z]{2}\d{3}[A-Z]$` |
| ARG Moto Mercosur (7c) | `A 123 AAA` | `A 123 ABC` | `^[A-Z]\d{3}[A-Z]{3}$` |
| Brasil | `ABC 1D23` | `ABC 1D23` | `^[A-Z]{3}\d[A-Z]\d{2}$` |
| Uruguay | `ABC 1234` | `ABC 1234` | `^[A-Z]{3}\d{4}$` |
| Paraguay Auto Mercosur | `ABCD 123` | `ABCD 123` | `^[A-Z]{4}\d{3}$` |

## Variables de Entorno para ALPR

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GATE_TYPE` | `entrada` | Tipo de cámara: entrada, salida, patente, qr, predio |
| `VIDEO_SOURCE` | `0` | Fuente de video (0=webcam, URL RTSP, URL HTTP) |
| `ALPR_OCR_INTERVAL` | 0.35 | Intervalo entre procesamientos OCR (segundos) |
| `ALPR_FRAMEQ_MAXSIZE` | 12 | Tamaño máximo de la cola de frames |
| `ALPR_CONFIDENCE_THRESHOLD` | 0.45 | **Sin efecto** en la lógica real (definida pero no usada) |
| `ALPR_CONSENSUS_REQUIRED` | 2 | Votos requeridos para consenso de baja confianza |
| `ALPR_CONSENSUS_WINDOW` | 4.0 | Ventana de tiempo (s) para acumular votos de consenso |
| `ALPR_MOTION_THRESHOLD` | 3000 | Umbral de diferencia de píxeles (método estático de `preprocessor.py`; en `ocr_engine.detect_motion` se usa umbral fijo de 800 en ROI central) |
| `ALPR_FORCE_OCR` | false | Forzar OCR incluso sin detección de movimiento |
| `ALPR_COOLDOWN` | 10 | Segundos de cooldown entre validaciones de la misma patente |
| `ALPR_MOTO_CONFIDENCE` | 0.85 | Confianza mínima (alta) para aceptar patente de moto (`MOTO_MIN_CONFIDENCE`) |
| `ALPR_MIN_CONFIDENCE` | 1 | **Sin efecto** (definida como `MIN_CONFIDENCE_VOTES` pero no usada) |
| `BACKEND_URL` | — | URL del backend FastAPI |
| `GATE_ID` | — | ID de la cámara (normalizado: strip accents, uppercase) |

> **Nota de umbrales**: la alta confianza efectiva usada en el consenso rápido de 1 voto es `0.75` para vehículos no moto y `MOTO_MIN_CONFIDENCE` (0.85) para motos; `ALPR_CONFIDENCE_THRESHOLD` y `ALPR_MIN_CONFIDENCE` quedaron como dead code en `config.py`.

## Recomendaciones Operativas ALPR

1. **Cámaras**: Usar cámaras IP con resolución mínima 720p, ideal 1080p
2. **Iluminación**: Evitar contraluz; instalar iluminación infrarroja si es necesario
3. **Ángulo**: La cámara debe apuntar directamente a la patente, ángulo < 30°
4. **FPS**: 15 FPS es suficiente; FPS más altos saturan el procesamiento
5. **Celulares como cámara**: Fijar enfoque/exposición manual, bajar a 15 FPS
6. **Mantenimiento**: Limpiar lentes periódicamente; verificar ángulo tras tormentas
7. **Debug**: Las imágenes aceptadas se guardan en `alpr_debug/` para Argentina
8. **Consensus tuning**: Para entornos ruidosos, subir `ALPR_CONSENSUS_REQUIRED` a 3
