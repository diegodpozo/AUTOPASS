# Analisis del Pipeline OCR de Reconocimiento de Patentes

## Arquitectura General

```
IP Webcam (Android)
    |  MJPEG stream via WiFi
    |  http://192.168.x.x:8080/video
    v
VideoStreamer (alpr/video_streamer.py)
    |  OpenCV VideoCapture, CAP_FFMPEG backend
    |  Resiza a 640px de ancho
    |  Hilo daemon, ~30fps reales
    v
Runner (alpr/runner.py)
    |  Loop principal cada 10ms
    |  Chequea QR cada frame
    |  Chequea movimiento cada 350ms (OCR_INTERVAL)
    v
Motion Detection (alpr/preprocessor.py)
    |  absdiff en 320x240, threshold 25
    |  Necesita >3000 pixeles cambiados (3.9%)
    v
Frame Queue (max 12 frames pendientes)
    v
ALPREngine.ocr_worker (alpr/ocr_engine.py)
    |  Hilo separado
    |  1. Deteccion QR
    |  2. Busqueda de ROI (3 estrategias)
    |  3. Preprocesamiento (3 variantes)
    |  4. EasyOCR.readtext() x cada variante
    |  5. Concatenacion de texto detectado
    |  6. Regex + validacion de patente
    |  7. Sistema de consenso (2 votos en 4s)
    v
HTTP POST al Backend FastAPI
    |  /v1/access/validate-plate (entrada)
    |  /v1/access/exit-plate (salida)
    v
Validacion en Backend (routes/access.py)
    |  Busca reserva activa, verifica estado
    |  Registra en access_logs
    +-> Responde con mensaje + accion (abrir barrera)
```

---

## Archivos del Pipeline

| Archivo | Lineas | Responsabilidad |
|---------|--------|-----------------|
| `alpr/config.py` | 51 | Parametros tuneables, patrones de patente |
| `alpr/video_streamer.py` | 58 | Captura de frames en hilo separado |
| `alpr/preprocessor.py` | 182 | Movimiento, ROI, Mercosur, preprocesamiento |
| `alpr/ocr_engine.py` | 188 | EasyOCR, consenso, despacho HTTP |
| `alpr/runner.py` | 81 | Orquestador principal del loop |
| `alpr/ws_client.py` | 27 | Streaming WebSocket para vista en vivo |
| `alpr_service.py` | 13 | Punto de entrada independiente |

---

## 1. Captura de Frames (video_streamer.py)

### Como funciona
- `cv2.VideoCapture(source, cv2.CAP_FFMPEG)` para URLs HTTP
- Buffer=1 (solo ultimo frame), timeouts de 5s para abrir y leer
- Resiza a **640px** de ancho manteniendo aspecto
- Hilo daemon que lee frames continuamente
- `get_frame()` retorna una **copia** del ultimo frame

### Parametros de IP Webcam recomendados
- URL del stream: `http://<ip>:8080/video` (MJPEG)
- Snapshot: `http://<ip>:8080/shot.jpg` (JPEG unico)
- Resolucion: configurable en la app (480p a 1080p)

### Bottleneck
- `cap.read()` es bloqueante. Si el stream cuelga, el hilo se bloquea
- La copia en `get_frame()` asigna memoria en cada llamada
- A 640px, patentes pequenas pueden no tener suficientes pixeles

---

## 2. Deteccion de Movimiento (preprocessor.py:29-39)

### Algoritmo
```python
1. Si FORCE_OCR=True -> siempre retorna True
2. Downscale a 320x240 (reduce 8x el calculo)
3. Convertir a escala de grises
4. Si es el primer frame -> True (siempre procesar el primero)
5. cv2.absdiff(prev_gray, gray)  # Diferencia pixel a pixel
6. cv2.threshold(diff, 25, 255)  # Binarizar
7. Contar pixeles blancos: np.sum(binary) / 255
8. Hay movimiento si changed_pixels > 3000
```

### Analisis de umbrales
- Imagen 320x240 = 76,800 pixeles
- Threshold de 3000 pixeles = **3.9%** de la imagen debe cambiar
- Threshold de intensidad 25 (sobre 255) = cambios moderados detectados

### Por que falla con patentes de papel
- La patente de papel esta **quieta** en la imagen
- No hay cambio de pixeles significativo entre frames
- El algoritmo necesita que **algo se mueva** en la escena
- Solucion inmediata: `FORCE_OCR=true` (bypass total de movimiento)

---

## 3. Busqueda de ROI (preprocessor.py:67-140)

### 3 estrategias en paralelo

#### Estrategia 1: Haar Cascade (lineas 78-91)
- Usa `haarcascade_russian_plate_number.xml` de OpenCV
- Parametros: `scaleFactor=1.1, minNeighbors=4`
- Agrega padding: 15% ancho, 20% alto
- Detecta patentes tipo russo/latinoamerica

#### Estrategia 2: Franjas horizontales fijas (lineas 93-110)
- Franja inferior 40% de la ROI (0.55h a 0.95h) - donde suelen estar patentes
- Franja central 40% (0.3h a 0.7h) - respaldo general
- Metodo simple pero efectivo para camaras fijas

#### Estrategia 3: Deteccion por contornos (lineas 112-135)
- Filtro bilateral -> Canny (50,200) -> cierre morfologico -> contornos
- Filtra por: area > 0.1% ROI, relacion aspecto 0.6-6.0, ancho > 12% ROI
- Agrega padding: 12% ancho, 25% alto

### ROI principal
- 80% del alto x 90% del ancho del frame
- Deduplicacion via set `seen_boxes`
- Fallback: toda la ROI principal si no encuentra nada

### Problema con patentes de papel
- El Haar cascade esta entrenado con patentes reales (reflejos, bordes metalicos)
- Las patentes de papel no tienen las mismas caracteristicas visuales
- Los contornos pueden detectar el bordel del papel en vez de la patente

---

## 4. Manejo de Patentes Mercosur (preprocessor.py:142-182)

### Deteccion
- Espacio HSV, rango azul: H=100-130, S=100-255, V=50-255
- Revisa top 30% de la ROI
- Si >10% de pixeles son azul -> es Mercosur

### Recorte
- Encuentra el pixel azul mas bajo en top 50% de ROI
- Recorta todo arriba de ese punto (+5px margen)
- Guardas: no recorta si azul pasa 45% de altura, o si resultado < 25% original

---

## 5. Preprocesamiento de Imagen (preprocessor.py:42-64)

### 3 variantes generadas por cada ROI

#### Variante 1: Gris sharpened (principal)
```python
1. Resize 2.5x con Lanczos (upscaling)
2. Median blur(3) - reducir ruido
3. CLAHE (clipLimit=4.0, grid=4x4) - ecualizacion adaptativa
4. Kernel sharpen: [[-1,-1,-1],[-1,9,-1],[-1,-1,-1]]
```

#### Variante 2: Umbral adaptativo
```python
Gaussian adaptive threshold, blockSize=13, C=5
-> Binaria (blanco y negro puro)
```

#### Variante 3: Umbral invertido
```python
bitwise_not de la variante 2
-> Invierte blanco/negro
```

### Costo
- Cada variante pasa por EasyOCR independientemente
- 3 variantes x N ROIs = multiples llamadas OCR por frame
- El upscaling 2.5x aumenta el tiempo de EasyOCR proporcionalmente

---

## 6. OCR con EasyOCR (ocr_engine.py)

### Configuracion actual
```python
reader = easyocr.Reader(['en'], gpu=False)  # CPU mode
results = reader.readtext(processed, detail=1, allowlist=PLATE_ALLOWLIST)
```

### Que hace EasyOCR internamente
1. **CRAFT** (Character Region Awareness For Text detection): detecta regiones de texto
2. **CRNN** (Convolutional Recurrent Neural Network): reconoce los caracteres

### Por que es lento en CPU
- CRAFT necesita pasar la imagen completa por una red neuronal
- CRNN necesita procesar cada region de texto detectada
- Sin GPU, todo se calcula en el procesador
- Tiempo promedio: **0.5-3 segundos por llamada** dependiendo del tamano

### Flujo de procesamiento por frame
```
Frame
 +-- ROI 1 (Haar cascade)
 |    +-- Variante Sharpened -> EasyOCR.readtext() -> 0.5-3s
 |    +-- Variante Binaria   -> EasyOCR.readtext() -> 0.5-3s
 |    +-- Variante Invertida -> EasyOCR.readtext() -> 0.5-3s
 +-- ROI 2 (Franja inferior)
 |    +-- Variante Sharpened -> EasyOCR.readtext() -> 0.5-3s
 |    +-- Variante Binaria   -> EasyOCR.readtext() -> 0.5-3s
 |    +-- Variante Invertida -> EasyOCR.readtext() -> 0.5-3s
 +-- ROI 3 (Contornos)
      +-- Variante Sharpened -> EasyOCR.readtext() -> 0.5-3s
      +-- Variante Binaria   -> EasyOCR.readtext() -> 0.5-3s
      +-- Variante Invertida -> EasyOCR.readtext() -> 0.5-3s
```

**Peor caso: 9 llamadas EasyOCR x 0.5-3s = 4.5-27 segundos por frame**
**Caso tipico: 2-3 ROIs x 3 variantes = 6-9 segundos**

---

## 7. Concatenacion y Validacion de Texto (ocr_engine.py:75-118)

### Concatenacion
- **Izquierda a derecha**: ordena resultados por coordenada X del bounding box
- **Arriba a abajo**: ordena por coordenada Y del centroide
- Usa la concatenacion **mas larga** de las dos

### Validacion con regex
```python
LATAM_PLATE_PATTERN soporta:
- ABC123     -> Argentina viejo estilo
- AB123CD    -> Argentina Mercosur
- ABC1D23    -> Brasil
- ABC1234    -> Uruguay
- ABCD123    -> Paraguay
- 123ABCD    -> Paraguay (alternativo)
```

### Filtros de rechazo
- Longitud < 5 o > 8 caracteres
- Sin al menos una letra
- Sin al menos un digito

---

## 8. Sistema de Consenso (ocr_engine.py:127-142)

### Como funciona
- Buffer de votos con ventana de 4 segundos
- Cada lectura valida agrega un voto: `(plate, confidence, timestamp)`
- Se descartan votos fuera de la ventana de 4s

### Condicion de aceptacion (OR logico)
```python
if avg_conf >= 0.45 OR votes_for_plate >= 2:
    # ACEPTAR patente
```

- **Alta confianza (>=0.45)**: acepta inmediatamente
- **Baja confianza**: necesita 2+ lecturas iguales en 4 segundos

### Cooldown
- 10 segundos entre eventos del mismo tipo
- Evita enviar la misma patente repetidamente

---

## 9. Despacho HTTP (ocr_engine.py:162-188)

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
    "plate": "AB123CD"
}
```

### Timeout
- 5 segundos para la respuesta del backend

---

## 10. Streaming WebSocket para Vista en Vivo (ws_client.py)

### Funcionamiento
- Se conecta al backend via WebSocket
- Envia frames JPEG (640x360, calidad 50) a ~20fps
- `asyncio.sleep(0.05)` = 50ms entre frames
- Auto-reconnect con backoff de 5s

### Proposito
- Solo para visualizacion en el dashboard del admin
- No afecta el pipeline de OCR

---

## Parametros Tuneables (config.py)

| Parametro | Default | Env Var | Descripcion |
|-----------|---------|---------|-------------|
| `OCR_INTERVAL` | 0.35s | `ALPR_OCR_INTERVAL` | Minimo tiempo entre intentos OCR |
| `CONFIDENCE_THRESHOLD` | 0.45 | `ALPR_CONFIDENCE_THRESHOLD` | Confianza minima EasyOCR para aceptar |
| `CONSENSUS_REQUIRED` | 2 | `ALPR_CONSENSUS_REQUIRED` | Votos necesarios para aceptar baja confianza |
| `CONSENSUS_WINDOW` | 4.0s | `ALPR_CONSENSUS_WINDOW` | Ventana deslizante de votos |
| `MOTION_THRESHOLD` | 3000 | `ALPR_MOTION_THRESHOLD` | Pixeles minimos de cambio para "movimiento" |
| `COOLDOWN_SECONDS` | 10 | `ALPR_COOLDOWN` | Anti-duplicados entre eventos |
| `FRAME_QUEUE_MAXSIZE` | 12 | `ALPR_FRAMEQ_MAXSIZE` | Max frames pendientes en cola |
| `FORCE_OCR` | false | `ALPR_FORCE_OCR` | Bypass total de deteccion de movimiento |

---

## Analisis de Cuellos de Botella

### 1. EasyOCR en CPU (CRITICO - 80% del tiempo)
- Cada `readtext()` tarda 0.5-3 segundos
- 3 variantes x N ROIs = multiplicas el tiempo
- **Cuello de botella principal del sistema**

### 2. Tres variantes de preprocesamiento (ALTO)
- Generar 3 variantes y pasarlas todas por OCR es redundante
- La variante sharpened/CLAHE generalmente es suficiente
- Reducir a 1 variante = 3x menos llamadas OCR

### 3. Multiples ROIs (MEDIO)
- 3 estrategias de deteccion pueden encontrar la misma patente
- Deduplicacion via `seen_boxes` ayuda pero no elimina el problema
- Los ROIs se procesan secuencialmente, no en paralelo

### 4. Deteccion de movimiento con papel (ALTO para testing)
- `absdiff` necesita cambio de pixeles -> patente quieta = no detecta
- FORCE_OCR=true lo resuelve pero procesa innecesariamente todos los frames

### 5. Resolucion baja (MEDIO)
- 640px ancho = patentes pequenas pueden no tener suficientes pixeles
- EasyOCR necesita texto de al menos ~20px de alto para leer confiablemente

---

## Mejoras Propuestas (ordenadas por impacto)

### Prioridad 1: Cambio de motor OCR

#### EasyOCR vs PaddleOCR vs OpenALPR

| Caracteristica | EasyOCR (actual) | PaddleOCR | OpenALPR |
|----------------|-------------------|-----------|----------|
| Velocidad CPU | 0.5-3s por lectura | 0.1-0.5s por lectura | 0.05-0.2s por lectura |
| Precision placas | Media | Alta | Muy alta (entrenado en placas) |
| Deteccion texto | CRAFT (lento) | DBNet (rapido) | Cascada dedicada |
| Reconocimiento | CRNN | SVTR_LCNet | CNN + post-procesamiento |
| GPU requerida | No (pero ayuda mucho) | No (pero ayuda) | No |
| Instalacion | `pip install easyocr` | `pip install paddleocr paddlepaddle` | Compilar desde fuente o DLL |
| Memoria RAM | ~2GB | ~500MB | ~300MB |
| Modelo specialize | General (textos) | General (textos) | **Entrenado en patentes** |

**Recomendacion: PaddleOCR** como reemplazo directo de EasyOCR.
- 3-5x mas rapido en CPU
- Menor uso de memoria
- Mismo API roughly: `reader.readtext(image)`
- Para placas especificamente, se puede usar el modelo `ch_PP-OCRv4` que es excelente

#### Si se quiere maximo rendimiento: OpenALPR
- Libreria C++ con bindings para Python
- Entrenada especificamente en placas de matriculas
- La mas rapida y precisa, pero requiere compilacion

### Prioridad 2: Reducir variantes de preprocesamiento

**Antes** (actual):
```python
variants = [sharpened, binaria, invertida]  # 3 variantes
for v in variants:
    reader.readtext(v)  # 3 llamadas OCR
```

**Despues** (optimizado):
```python
# Solo la variante sharpened/CLAHE es necesaria
processed = preprocess_for_reading(roi)  # 1 variante
reader.readtext(processed)  # 1 llamada OCR
```

**Impacto: 3x menos llamadas OCR por ROI.**

### Prioridad 3: Aumentar resolucion

**Antes**: 640px de ancho
**Despues**: 1280px de ancho (doble)

En IP Webcam se puede configurar la resolucion del stream. A 1280px:
- Patentes mas grandes en el frame
- Mas pixeles de texto para el OCR
- Costo: ~2x mas tiempo de procesamiento, pero PaddleOCR lo compensa

### Prioridad 4: Forzar OCR para testing con papel

Configurar en `.env`:
```
ALPR_FORCE_OCR=true
```

Esto elimina la deteccion de movimiento del flujo. El sistema procesara **todos los frames** sin importar si hay movimiento. Ideal para probar con patentes impresas quietas.

### Prioridad 5: Mejorar el Haar Cascade

El cascade actual (`haarcascade_russian_plate_number.xml`) no esta optimizado para patentes argentinas impresas en papel. Alternativas:
- Entrenar un cascade personalizado con imagenes de patentes argentinas
- Usar un modelo YOLOv8 pre-entrenado en placas (ultralytics)
- Usar easyocr directamente sin cascade (skip ROI detection, pasar frame completo)

### Prioridad 6: Paralelizar ROIs

Actualmente los ROIs se procesan secuencialmente. Se podrian procesar en paralelo usando `ThreadPoolExecutor` o `ProcessPoolExecutor`:

```python
# Actual: secuencial
for roi in rois:
    for variant in variants:
        reader.readtext(variant)

# Propuesto: paralelo
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(reader.readtext, v) for v in all_variants]
    results = [f.result() for f in futures]
```

---

## Conclusión: Que hacer primero

### Cambios inmediatos (5 minutos)
1. Setear `ALPR_FORCE_OCR=true` en `.env` para testing con papel
2. Configurar IP Webcam a la resolucion mas alta posible

### Cambios rapidos (1 hora)
3. Reducir variantes de 3 a 1 en `preprocessor.py`
4. Eliminar ROIs duplicados (mejorar deduplicacion)

### Cambios importantes (medio dia)
5. Instalar PaddleOCR y reemplazar EasyOCR
6. Ajustar parametros de PaddleOCR para patentes argentinas

### Cambios de fondo (1-2 dias)
7. Entrenar modelo YOLOv8 en dataset de patentes argentinas
8. Implementar pipeline completo con deteccion + OCR optimizado

---

## Nota sobre USB y velocidad

Conectar el celular a la PC con cable USB **no mejoraria significativamente** la velocidad.

**Razon**: El cuello de botella no es la transferencia de frames (WiFi ya entrega ~30fps), sino el procesamiento OCR que toma 0.5-3 segundos por frame.

| Componente | Latencia |
|------------|----------|
| WiFi frame transfer | ~10-30ms |
| USB frame transfer | ~5-15ms |
| OpenCV read + resize | ~10-20ms |
| EasyOCR readtext | **500-3000ms** |
| HTTP POST al backend | ~50-100ms |

El ahorro de 5-15ms con USB es irrelevante cuando el OCR toma 500-3000ms.
