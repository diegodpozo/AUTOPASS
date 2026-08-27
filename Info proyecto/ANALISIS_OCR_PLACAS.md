# Analisis del Pipeline OCR de Reconocimiento de Patentes

> **Nota**: Este documento fue actualizado para reflejar el **motor OCR dual (RapidOCR/PaddleOCR)** y la arquitectura modular de `alpr/`. La versión previa describía un pipeline con EasyOCR, *Haar cascade* y 3 variantes de preprocesamiento, que fue reemplazado por completo en la modularización v9.6.0+ y la incorporación del motor dual v9.10.0.

## Arquitectura General

```
IP Webcam / Cámara IP (RTSP / HTTP MJPEG)
    |  stream
    v
VideoStreamer (alpr/video_streamer.py)
    |  OpenCV VideoCapture (CAP_FFMPEG para HTTP/RTSP)
    |  Resiza a 1280px de ancho, ~30fps
    |  Hilo daemon, comparte el último frame thread-safe
    v
Runner (alpr/runner.py)
    |  Loop principal cada ~10ms
    |  Chequea QR directo por frame
    |  Chequea movimiento cada 350ms (OCR_INTERVAL)
    v
Motion Detection (alpr/ocr_engine.py -> detect_motion)
    |  absdiff en ROI central (25-85% alto, 10-90% ancho)
    |  Gaussian blur + countNonZero
    |  Considera movimiento si > 800 píxeles cambiados
    v
Frame Queue (max 12 frames pendientes, drop-oldest)
    v
ALPREngine.ocr_worker (alpr/ocr_engine.py)
    |  Hilo separado
    |  1. Deteccion QR
    |  2. Deteccion MERCOSUR (franja azul) + recorte
    |  3. OCR sobre main_roi (motor dual)
    |  4. Extraccion de patente por prioridades (7 chars, formatos)
    |  5. Fallback find_plate_roi por franjas/contornos
    |  6. Regex + validacion de formato conocido
    |  7. Sistema de consenso (1 voto alta conf / 2+ baja conf)
    v
HTTP POST al Backend FastAPI
    |  /v1/access/validate-plate (entrada)
    |  /v1/access/exit-plate (salida)
    |  /v1/access/validate-qr (QR)
    v
Validacion en Backend (services/access_service.py)
    |  Busca reserva activa, verifica estado
    |  Registra en access_logs
    +-> Responde con mensaje + accion (abrir barrera)
```

## Archivos del Pipeline

| Archivo | Lineas | Responsabilidad |
|---------|--------|-----------------|
| `alpr/config.py` | 57 | Parametros tuneables, patrones de patente |
| `alpr/video_streamer.py` | 58 | Captura de frames en hilo separado |
| `alpr/preprocessor.py` | 202 | Movimiento (estatico), ROI fallback, Mercosur, preprocesamiento |
| `alpr/ocr_engine.py` | 498 | Motor dual, consenso, despacho HTTP, overlay HUD |
| `alpr/runner.py` | 84 | Orquestador principal del loop |
| `alpr/ws_client.py` | 27 | Streaming WebSocket para vista en vivo |
| `alpr_service.py` | 12 | Wrapper / punto de entrada independiente |

---

## 1. Captura de Frames (video_streamer.py)

### Como funciona
- `cv2.VideoCapture(source, cv2.CAP_FFMPEG)` para URLs HTTP/RTSP
- `Buffer=1` (solo ultimo frame), timeouts de aperture/lectura de 5s
- Resiza a **1280px** de ancho manteniendo aspecto (`target_width=1280`)
- Hilo daemon que lee frames continuamente
- `get_frame()` retorna una **copia** del ultimo frame
- Reintentos de captura (3 intentos) ante fallos de stream

### Parametros de IP Webcam recomendados
- URL del stream: `http://<ip>:8080/video` (MJPEG)
- Snapshot: `http://<ip>:8080/shot.jpg` (JPEG unico)
- Resolucion: configurable en la app (720p-1080p para mejor OCR)

---

## 2. Deteccion de Movimiento (ocr_engine.py `detect_motion`)

### Algoritmo
```python
1. Si FORCE_OCR=True -> siempre True (procesa todos los frames)
2. ROI central: [25%-85% alto] x [10%-90% ancho]
3. Convertir a escala de grises + GaussianBlur (21x21)
4. Si es el primer frame -> True (procesar el primero)
5. cv2.absdiff(prev_gray, gray)  # Diferencia pixel a pixel
6. threshold(diff, 25, 255, THRESH_BINARY)
7. countNonZero -> si > 800 => hay movimiento
```

### Analisis de umbrales
- ROI central reduce el costo vs el frame completo
- Umbral fijo de **800 píxeles** cambiados
- Nota: existe un método estático en `preprocessor.py` (`detect_motion`, resize 320x240 con umbral `ALPR_MOTION_THRESHOLD=3000`) que **no se usa** en el flujo principal actual.

### Patentes impresas en papel
- La patente de papel esta **quieta** en la imagen -> sin cambio de pixeles -> no detecta movimiento
- Solucion: `ALPR_FORCE_OCR=true` para bypass total de movimiento en pruebas con papel

---

## 3. Busqueda de ROI (`find_plate_roi`, preprocessor.py) — FALLBACK

> El pipeline **no usa *Haar cascade*** (el detector de placas de OpenCV fue removido del flujo en la modularización).

### Estrategias (solo usadas como fallback en `ocr_worker`)
1. **Franjas fijas** (`strip_bottom` 0.55-0.75h, `strip_center` 0.30-0.50h) segmentadas en bloques de 320px
2. **Contornos**: bilateral -> Canny(50,200) -> cierre morfológico -> `findContours`
   - Filtra por area > 0.1% ROI, aspect ratio 1.5-8.0, ancho > 8% ROI
   - Padding: 10% ancho, 25% alto
   - Prioridad: `contour` > `strip_center` > `strip_bottom`
   - Deduplicacion con IoU > 0.4

### ROI principal
- 77% del alto (15%→92%) x 90% del ancho (5%→95%)
- Fallback: toda la ROI principal si no se encuentra nada

### Validacion de ROI (`_is_valid_plate_roi`)
- Ancho minimo: 70px, Alto minimo: 18px
- Aspect ratio: 1.5 - 6.0
- No puede ser mas ancho que 85% del frame

---

## 4. Manejo de Patentes Mercosur (preprocessor.py)

### Deteccion (`is_mercosur_candidate`)
- Espacio HSV, rango azul: H=90-135, S=40-255, V=40-255
- Revisa top **35%** de la ROI
- Si > **6%** de pixeles son azul -> es Mercosur
- Rango ampliado (S>=40, V>=40) para capturar la franja azul en hojas de papel impresas con tinta de inyeccion/laser

### Recorte (`crop_below_blue`)
- Encuentra el pixel azul mas bajo en top 50% de ROI
- Recorta a partir de ese punto (+5px margen)
- Guardas: no recorta si azul pasa 45% de altura, o si resultado < 25% original
- Elimina el texto "REPUBLICA ARGENTINA" / MERCOSUR de la franja azul que confunde al OCR

---

## 5. Preprocesamiento de Imagen

A diferencia del pipeline antiguo (3 variantes con EasyOCR), el pipeline actual **procesa el ROI directamente** en el motor dual. El metodo `preprocess_for_screen` (que generaba 3 variantes: sharpened, binaria, invertida) queda disponible en `preprocessor.py` pero **no se ejecuta** en el flujo principal.

En su lugar, `_ocr_single_roi` aplica:
- **Escalado inteligente ROI**: re-escalado a 80px de alto por interpolacion cubica (`INTER_CUBIC`) si el recorte tiene menos de 80px de alto, afinando bordes y previniendo confusiones de digitos (ej. `6` vs `5`)

---

## 6. OCR con Motor Dual (ocr_engine.py)
- **RapidOCR ONNX**: motor primario, instalado por defecto en `requirements.txt` (`rapidocr-onnxruntime>=1.2.0`)
- **PaddleOCR**: fallback automatico si RapidOCR no esta disponible (solo para Python < 3.14; `paddleocr`/`paddlepaddle` quedan fuera en Python 3.14+)
- Seleccion de motor en el import de `ocr_engine.py` (`OCR_ENGINE_NAME`)

### Escaneo por frame
```
Frame
  +-- Deteccion QR rapida (cv2.QRCodeDetector)  -> send_event qr
  +-- main_roi -> MERCOSUR? -> crop_below_blue
       +-- _ocr_single_roi(main_roi)  [RapidOCR o PaddleOCR]
  +-- Extraccion de patente por prioridades
  +-- Fallback find_plate_roi + _ocr_single_roi por candidato
```

### Filtrado de ruido de cabecera
- `HEADER_NOISE_WORDS`: elimina palabras como `REPUBLICA`, `ARGENTINA`, `MERCOSUR`, `BRASIL`, `URUGUAY`, `PARAGUAY`, `TINA`, `MERCO`, `SUR` que confunden al OCR

---

## 7. Extraccion y Validacion de Texto (ocr_engine.py)

### Extraccion de patente (orden de prioridad)
1. **7 caracteres combinando multiples detecciones** por X: `full_7_pattern`
2. **7 caracteres en deteccion unica**: `full_7_pattern`
3. **Formato general** en deteccion unica: `LATAM_PLATE_PATTERN`
4. **Combinacion por Y y luego X** de ≥2 detecciones: `LATAM_PLATE_PATTERN`
5. **Fallback de caza de contornos** (papel / fuera de centro): `find_plate_roi` con confianza minima `FALLBACK_MIN_CONFIDENCE=0.65`

### Validacion con regex
```python
KNOWN_PLATE_FORMATS soporta:
- AA123AA     -> Argentina Auto Mercosur
- ABC123      -> Argentina Auto Antigua
- AB123       -> Argentina Moto Antigua
- AB123A      -> Argentina Moto Mercosur (6c)
- A123AAA     -> Argentina Moto Mercosur (7c)
- ABC1D23     -> Brasil Mercosur
- ABC1234     -> Uruguay
- ABCD123     -> Paraguay Auto Mercosur
```

### Reglas de rechazo
- Longitud < 2 caracteres o sin letras/digitos
- Texto que no coincida con un formato conocido (`KNOWN_PLATE_FORMATS`) -> `continue`
- **Truncamiento de moto**: patente de moto con bbox rectangular horizontal de auto (aspect ratio `> 2.2`) -> descartada como recorte incompleto

### Identificacion de pais (`identify_country`)
- Prioriza coincidencia regex de patrones MERCOSUR/antiguos, **independiente del color** (funciona con patentes impresas en B&N sin franja azul)
- Reconoce: Argentina (Auto/Moto Mercosur, Auto/Moto Antigua), Brasil, Uruguay, Paraguay

---

## 8. Sistema de Consenso (ocr_engine.py)

### Como funciona
- Buffer de votos `vote_buffer` con ventana de `CONSENSUS_WINDOW` (4s)
- Cada lectura valida agrega un voto: `(plate, confidence, timestamp)`
- Se descartan votos fuera de la ventana

### Condicion de aceptacion
```python
if alta_confianza and formato_valido:
    req_votes = 1     # consenso rapido (1 voto)
else:
    req_votes = max(2, CONSENSUS_REQUIRED)  # baja conf -> 2+ votos

alta_confianza = (avg_conf >= 0.75) si no es moto
               = (avg_conf >= MOTO_MIN_CONFIDENCE) si es moto (0.85)
```

- **Alta confianza**: acepta inmediatamente en 1 voto
- **Baja confianza**: necesita `CONSENSUS_REQUIRED` (2) lecturas iguales en la ventana
- `MOTO_PATTERN` identifica patentes de moto para aplicar su umbral especifico

### Cooldown / anti-duplicados
- `COOLDOWN_SECONDS` (10s) entre eventos normales de la misma patente
- `_plate_close()` permite variantes fuzzy: ≤1 caracter de diferencia **o** comparticion de bloque numerico (≥3 digitos iguales), ej. `NVZ087` vs `VZ087AR`
- Normalizacion: `re.sub(r'[^A-Z0-9]', '', plate).upper()`

---

## 9. Despacho HTTP (ocr_engine.py `_dispatch_request`)

### Endpoint segun tipo de porton
| Tipo | Endpoint |
|------|----------|
| Entrada | `POST /v1/access/validate-plate` |
| Salida | `POST /v1/access/exit-plate` |
| QR | `POST /v1/access/validate-qr` |

### Payload
```json
{
    "gate_id": "ITUZAINGO_PATENTE_ENTRADA_3",
    "image_base64": "<jpeg base64>",
    "plate": "AB123CD",
    "ocr_time": 0.35
}
```

### Detalles
- JPEG calidad 70, enviado desde `ThreadPoolExecutor` (no bloquea el OCR)
- Timeout de 5 segundos para la respuesta del backend
- Determinacion entrada/salida por `GATE_TYPE` (ausencia de "salida"/"egreso")

---

## 10. Streaming WebSocket para Vista en Vivo (ws_client.py)

### Funcionamiento
- Se conecta al backend via WebSocket (`/v1/system/ws/video/{gate_id}`)
- Envia frames JPEG (640x360, calidad 50) a ~20fps
- `asyncio.sleep(0.05)` = 50ms entre frames
- Auto-reconnect con backoff de 5s
- Con `engine` presente superpone el overlay HUD (bounding boxes, banner de confirmacion)

### Proposito
- Solo para visualizacion en el dashboard del admin
- No afecta el pipeline de OCR

---

## Parametros Tuneables (config.py)

| Parametro | Default | Env Var | Uso real |
|-----------|---------|---------|----------|
| `OCR_INTERVAL` | 0.35s | `ALPR_OCR_INTERVAL` | Minimo tiempo entre intentos OCR en runner |
| `CONFIDENCE_THRESHOLD` | 0.45 | `ALPR_CONFIDENCE_THRESHOLD` | **Sin efecto** (definida pero no usada en la logica real) |
| `CONSENSUS_REQUIRED` | 2 | `ALPR_CONSENSUS_REQUIRED` | Votos necesarios para aceptar baja confianza |
| `CONSENSUS_WINDOW` | 4.0s | `ALPR_CONSENSUS_WINDOW` | Ventana deslizante de votos |
| `MOTION_THRESHOLD` | 3000 | `ALPR_MOTION_THRESHOLD` | Umbral del metodo estatico (preprocessor, no usado en flujo principal) |
| `COOLDOWN_SECONDS` | 10 | `ALPR_COOLDOWN` | Anti-duplicados entre eventos |
| `FRAME_QUEUE_MAXSIZE` | 12 | `ALPR_FRAMEQ_MAXSIZE` | Max frames pendientes en cola |
| `FORCE_OCR` | false | `ALPR_FORCE_OCR` | Bypass total de deteccion de movimiento |
| `MOTO_MIN_CONFIDENCE` | 0.85 | `ALPR_MOTO_CONFIDENCE` | Confianza alta minima para patente de moto |
| `MIN_CONFIDENCE_VOTES` | 1 | `ALPR_MIN_CONFIDENCE` | **Sin efecto** (definida pero no usada) |

---

## Analisis de Cuellos de Botella (estado actual)

### 1. Motor OCR en CPU (ALTO)
- El motor dual (RapidOCR/PaddleOCR) es significativamente mas rapido que EasyOCR, pero sigue siendo el componente dominante
- Solo se procesa **un ROI principal** (no multiples variantes), reduciendo el costo vs el pipeline antiguo
- El escalado a 80px ayuda a patentes pequenas manteniendo el costo acotado

### 2. Consenso de 1 voto (MEJORA)
- Para alta confianza + formato valido ya no se necesita esperar 2 votos, agilizando la validacion en condiciones favorables
- Solo las lecturas de baja confianza esperan acumular 2 votos

### 3. Deteccion de movimiento con papel (ALTO para testing)
- Patente quieta = sin cambio de pixeles = no detecta
- `ALPR_FORCE_OCR=true` lo resuelve procesando todos los frames

### 4. Resolucion (BAJO/MEDIO)
- 1280px de ancho (doble que el pipeline antiguo) da mas pixeles a patentes pequenas

---

## Mejoras Propuestas (ordenadas por impacto)

### Prioridad 1: Afinar umbrales de consenso por entorno
- Para entornos ruidosos subir `ALPR_CONSENSUS_REQUIRED` a 3
- Para papel con baja calidad, ajustar las constantes de alta confianza (0.75 / 0.85) si se observan falsos positivos

### Prioridad 2: Entrenar/afinar el detector de ROI
- El fallback actual (franjas + contornos) es generico
- Un modelo YOLO pre-entrenado en placas argentinas mejoraria deteccion en papel

### Prioridad 3: Optimizar el flujo de deteccion de movimiento
- Unificar los dos metodos (`ocr_engine.detect_motion` fijo 800 vs `preprocessor.detect_motion` 3000) en uno solo configurable
- Eliminar el dead code (`CONFIDENCE_THRESHOLD`, `MIN_CONFIDENCE_VOTES`, `preprocess_for_screen` si no se va a usar)

### Prioridad 4: Paralelizar el OCR
- Si la camara es de alta resolucion y el OCR es el cuello de botella, evaluar `ThreadPoolExecutor` para procesar multiples ROIs del fallback en paralelo

---

## Conclusión: Que hacer primero

### Para pruebas con papel (5 minutos)
1. Setear `ALPR_FORCE_OCR=true` en `.env` para testing con papel
2. Configurar IP Webcam a la resolucion mas alta posible (720p+)

### Para robustez (1 hora)
3. Limpiar dead code en `config.py` (`CONFIDENCE_THRESHOLD`, `MIN_CONFIDENCE_VOTES`) y `preprocessor.py` (`preprocess_for_screen`, `detect_motion` estatico) o documentar su estado
4. Unificar la logica de deteccion de movimiento en un unico metodo

### Para precision (medio dia)
5. Ajustar umbrales de confianza de consenso segun el entorno real
6. Evaluar un detector de ROI entrenado en patentes argentinas

---

## Nota sobre USB y velocidad

Conectar el celular a la PC con cable USB **no mejoraria significativamente** la velocidad.

**Razon**: El cuello de botella no es la transferencia de frames (WiFi ya entrega ~30fps), sino el procesamiento OCR.

| Componente | Latencia |
|------------|----------|
| WiFi frame transfer | ~10-30ms |
| USB frame transfer | ~5-15ms |
| OpenCV read + resize | ~10-20ms |
| OCR (RapidOCR/PaddleOCR CPU) | ~50-500ms |
| HTTP POST al backend | ~50-100ms |
