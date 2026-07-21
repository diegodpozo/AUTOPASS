# Arquitectura del Sistema ALPR — AUTOPASS

## Visión General
El servicio ALPR (`alpr_service.py`) es un proceso independiente que corre como hijo del backend FastAPI. Se encarga de capturar video, procesar frames, detectar patentes y códigos QR, y comunicar los eventos al backend.

## Modos de Operación

El ALPR se configura mediante la variable de entorno `GATE_TYPE`:

| Valor de `GATE_TYPE` | Descripción | Uso |
|------|-------------|-----|
| `entrada` | Procesa patentes de entrada | Cámara de entrada al estacionamiento |
| `salida` | Procesa patentes de salida | Cámara de salida del estacionamiento |
| `patente` | Procesa patentes genérico | Modo dual (entrada+salida) |
| `qr` | Procesa códigos QR | Escáner QR |
| `predio` | Vigilancia general | Cámara de seguridad del predio |

La fuente de video se configura con `VIDEO_SOURCE` (puede ser `0` para webcam local, una URL RTSP, o una URL HTTP MJPEG).

## Arquitectura Interna

```
┌─────────────────────────────────────────────────────────────────────┐
│                        alpr_service.py                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐ │
│  │  Frame Capture    │───►│  Motion Detection│───►│  Queue         │ │
│  │  (OpenCV)         │    │  (Skip static)   │    │  maxsize=12    │ │
│  │                   │    │                  │    │  drop-oldest   │ │
│  └──────────────────┘    └──────────────────┘    └───────┬────────┘ │
│                                                           │          │
│                              ┌────────────────────────────┘          │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────┐           │
│  │              OCR Worker Thread (asyncio)               │           │
│  │                                                         │           │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │           │
│  │  │ ROI         │─►│ EasyOCR      │─►│ Consensus    │ │           │
│  │  │ Detection   │  │ (OCR)        │  │ Vote Buffer  │ │           │
│  │  │             │  │              │  │ min_votes=2  │ │           │
│  │  └─────────────┘  └──────────────┘  └──────┬───────┘ │           │
│  │                                             │          │           │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────▼───────┐ │           │
│  │  │ Quick QR    │  │ QR Decode    │  │ Event Send   │ │           │
│  │  │ Detection   │─►│ (pyzbar)     │─►│ (HTTP POST)  │ │           │
│  │  └─────────────┘  └──────────────┘  └──────────────┘ │           │
│  └───────────────────────────────────────────────────────┘           │
│                                                                      │
│  ┌───────────────────────────────────────────────────────┐           │
│  │              Video WebSocket Thread                    │           │
│  │  Envía frames en tiempo real a /v1/system/ws/video/  │           │
│  └───────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

## Componentes Clave

### 1. Captura de Frames (Frame Capture)
- Fuente: Cámara IP (RTSP/HTTP) o archivo de video
- Resolución configurable
- FPS limitado para no saturar el procesamiento
- Soporta múltiples fuentes simultáneas

### 2. Detección de Movimiento (Motion Detection)
- Compara frames consecutivos
- Si no hay cambios significativos, salta el frame
- Reduce drásticamente la carga de procesamiento OCR
- Configurable: `ALPR_FORCE_OCR` para forzar OCR incluso sin movimiento

### 3. Cola de Frames (Frame Queue)
- `maxsize=12` (configurable) con política **drop-oldest**
- Prioriza frames recientes sobre antiguos
- Evita acumulación cuando el OCR es más lento que la captura

### 4. Detección de ROI (Region of Interest)
Estrategias múltiples (en orden):
1. **Cascade Detector**: Usa clasificador en cascada para placas
2. **Bottom Third**: Busca en el tercio inferior de la imagen
3. **Center Strip**: Busca en la franja central
4. **Contour Detection**: Filtra por aspect ratio y área

### 5. Recorte MERCOSUR (Blue Band Crop)
- Detecta la banda azul característica de patentes MERCOSUR
- Recorta la zona por debajo de la banda
- Elimina texto "REPUBLICA ARGENTINA" que confunde al OCR

### 6. OCR (EasyOCR)
- Motor de Deep Learning
- Idiomas: español, inglés (soporta caracteres latinos)
- Umbral de confianza configurable: `ALPR_CONFIDENCE_THRESHOLD=0.45`
- Intervalo entre OCRs: `ALPR_OCR_INTERVAL=0.35s`

### 7. Sistema de Consenso (Vote Buffer)
- Buffer temporal de lecturas de la misma patente
- Ventana de consenso: N lecturas iguales en período de tiempo
- Si confianza > threshold: acepta directo
- Si confianza baja: requiere `ALPR_CONSENSUS_REQUIRED=2` votos iguales

### 8. Quick QR Detection
- Escaneo de QR en cada frame (previo al OCR)
- Usa pyzbar para decodificación rápida
- Cooldown/Debounce configurable (`ALPR_COOLDOWN`, default 10s) para evitar eventos duplicados

### 9. Cooldown entre validaciones
- `COOLDOWN_SECONDS` (default 6s): Evita procesar la misma patente en ventana corta
- `last_validated_plate`: Almacena última patente validada con timestamp
- Si la misma patente se detecta dentro del cooldown, se descarta

### 10. Video WebSocket
- Envía frames JPEG comprimidos en tiempo real
- Endpoint: `/v1/system/ws/video/{gate_id}`
- Token JWT como query param para autenticación

## Formato de Patentes Soportado

| Tipo | Formato | Ejemplo | Regex |
|------|---------|---------|-------|
| MERCOSUR Auto | `ABC 1D23` | `ABC 123` | `^[A-Z]{3}\s?\d{3}$` |
| MERCOSUR Moto | `A123BCD` | `A123BCD` | `^[A-Z]\d{3}[A-Z]{3}$` |
| Vieja argentina | `ABC 123` | `ABC 123` | `^[A-Z]{3}\s?\d{3}$` |
| Brasil | `ABC1D23` | `ABC1D23` | `^[A-Z]{3}\d[A-Z]\d{2}$` |
| Uruguay/Paraguay | `ABC 1234` | `ABC 1234` | `^[A-Z]{3}\s?\d{4}$` |

## Variables de Entorno para ALPR

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GATE_TYPE` | `entrada` | Tipo de cámara: entrada, salida, patente, qr, predio |
| `VIDEO_SOURCE` | `0` | Fuente de video (0=webcam, URL RTSP, URL HTTP) |
| `ALPR_OCR_INTERVAL` | 0.35 | Intervalo entre procesamientos OCR (segundos) |
| `ALPR_FRAMEQ_MAXSIZE` | 12 | Tamaño máximo de la cola de frames |
| `ALPR_CONFIDENCE_THRESHOLD` | 0.20 | Umbral de confianza para aceptar lectura directa |
| `ALPR_CONSENSUS_REQUIRED` | 2 | Votos requeridos para consenso con baja confianza |
| `ALPR_FORCE_OCR` | false | Forzar OCR incluso sin detección de movimiento |
| `ALPR_COOLDOWN` | 6 | Segundos de cooldown entre validaciones de la misma patente |

## Recomendaciones Operativas ALPR

1. **Cámaras**: Usar cámaras IP con resolución mínima 720p, ideal 1080p
2. **Iluminación**: Evitar contraluz; instalar iluminación infrarroja si es necesario
3. **Ángulo**: La cámara debe apuntar directamente a la patente, ángulo < 30°
4. **FPS**: 15 FPS es suficiente; FPS más altos saturan el procesamiento
5. **Celulares como cámara**: Fijar enfoque/exposición manual, bajar a 15 FPS
6. **Mantenimiento**: Limpiar lentes periódicamente; verificar ángulo tras tormentas
7. **Debug**: Las imágenes aceptadas se guardan en `alpr_debug/` para Argentina
