import cv2
import easyocr
import requests
import time
import os
import re
import base64
import threading
import queue
import numpy as np
import asyncio
import websockets
import json
import unicodedata
import warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# --- CONFIGURACION DE SEGURIDAD Y RENDIMIENTO ---
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
os.environ["FFMPEG_LOG_LEVEL"] = "quiet"
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
load_dotenv()

# --- CONFIGURACION DEL SERVICIO ---
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")
if isinstance(VIDEO_SOURCE, str) and VIDEO_SOURCE.isdigit():
    VIDEO_SOURCE = int(VIDEO_SOURCE)

GATE_TYPE = os.getenv("GATE_TYPE", "entrada").lower()
RAW_GATE_ID = os.getenv("GATE_ID", "ENTRADA_PRINCIPAL" if GATE_TYPE == "entrada" else "SALIDA_PRINCIPAL")
FORCE_OCR = os.getenv("ALPR_FORCE_OCR", "false").lower() in ("1", "true", "yes")
print(f"[ALPR CONFIG] VIDEO_SOURCE={VIDEO_SOURCE} GATE_TYPE={GATE_TYPE} GATE_ID={RAW_GATE_ID} FORCE_OCR={FORCE_OCR}")

def normalize_id(text):
    """Normaliza un GATE_ID eliminando prefijo, acentos y espacios."""
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

GATE_ID = normalize_id(RAW_GATE_ID)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
WS_BACKEND_URL = BACKEND_URL.replace("http", "ws") + f"/v1/system/ws/video/{GATE_ID}"

print(f"[*] Nodo ALPR v8.1.0 (Screen-to-Screen) Iniciado: {GATE_ID}")

# PARAMETROS SENSIBLES
COOLDOWN_SECONDS = int(os.getenv("ALPR_COOLDOWN", 10))
MIN_CONFIDENCE_VOTES = int(os.getenv("ALPR_MIN_CONFIDENCE", 1)) 
# Interval between OCR enqueues (segundos). Incrementado por defecto para reducir carga en CPUs modestos.
OCR_INTERVAL = float(os.getenv("ALPR_OCR_INTERVAL", 0.35))
# Umbral minimo de confianza para aceptar una lectura directamente
CONFIDENCE_THRESHOLD = float(os.getenv("ALPR_CONFIDENCE_THRESHOLD", 0.45))
MOTION_THRESHOLD = int(os.getenv("ALPR_MOTION_THRESHOLD", 3000)) 
# Tamaño maximo de la cola de frames (priorizar frames recientes). Se puede ajustar via env ALPR_FRAMEQ_MAXSIZE
FRAME_QUEUE_MAXSIZE = int(os.getenv("ALPR_FRAMEQ_MAXSIZE", 12))
# Consenso: cantidad mínima de apariciones en ventana temporal para validar una lectura de baja confianza
CONSENSUS_REQUIRED = int(os.getenv("ALPR_CONSENSUS_REQUIRED", 2))
CONSENSUS_WINDOW = float(os.getenv("ALPR_CONSENSUS_WINDOW", 4.0))
PLATE_ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
# PATRONES ESPECIFICOS DE MERCOSUR Y ARGENTINA: 
# 1. AAA 111 (ARG ANTIGUO) 
# 2. AB 123 CD (ARG MERCOSUR)
# 3. ABC1D23 (BRASIL MERCOSUR)
# 4. ABC 1234 (URUGUAY MERCOSUR)
# 5. ABCD 123 / 123 ABCD (PARAGUAY MERCOSUR)
# Regex base para placas comunes + patrones mixtos (incluye variantes motos de 2 filas)
LATAM_PLATE_PATTERN = (
    r'\b(' +
    r'[A-Z]{3}\d{3}' + r'|' +
    r'[A-Z]{2}\d{3}[A-Z]{2}' + r'|' +
    r'[A-Z]{3}\d[A-Z]\d{2}' + r'|' +
    r'[A-Z]{3}\d{4}' + r'|' +
    r'[A-Z]{4}\d{3}' + r'|' +
    r'\d{3}[A-Z]{4}' + r'|' +
    # Motos / patentes compactas (ej: fila superior 2 letras + digito; inferior digito + 3 letras -> formas combinadas)
    r'[A-Z]{2}\d{1,3}[A-Z]{3}' + r'|' +
    r'[A-Z]{1,2}\d{1,4}[A-Z]{1,3}' + r')\b'
)


class ALPREngine:
    def __init__(self):
        print("[*] Cargando motores de IA...")
        # EasyOCR lee en ingles para maximizar deteccion de caracteres alfanumericos
        self.reader = easyocr.Reader(['en'], gpu=False) 
        self.qr_detector = cv2.QRCodeDetector()
        cascade_path = cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        self.plate_cascade = cv2.CascadeClassifier(cascade_path)
        
        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_MAXSIZE)
        self.vote_buffer = []
        self.last_validated_plate = ""
        self.last_validation_time = 0
        self.is_running = True
        # Pool de hilos para enviar peticiones HTTP al backend sin bloquear el OCR
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.prev_gray = None

    def identify_country(self, plate, is_mercosur):
        """IDENTIFICA EL PAIS PROBABLE BASADO EN EL FORMATO Y LA FRANJA AZUL."""
        if not is_mercosur:
            if re.match(r'^[A-Z]{3}\d{3}$', plate): return "ARGENTINA (Antigua)"
            return "DESCONOCIDO"
        
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', plate): return "ARGENTINA (Mercosur)"
        if re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', plate): return "BRASIL"
        if re.match(r'^[A-Z]{3}\d{4}$', plate): return "URUGUAY"
        if re.match(r'^[A-Z]{4}\d{3}$|^\d{3}[A-Z]{4}$', plate): return "PARAGUAY"
        
        return "MERCOSUR (Otro)"

    def detect_motion(self, frame):
        if FORCE_OCR:
            return True
        small = cv2.resize(frame, (320, 240))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if self.prev_gray is None:
            self.prev_gray = gray
            return True
        frame_delta = cv2.absdiff(self.prev_gray, gray)
        motion_score = np.sum(cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]) / 255
        self.prev_gray = gray
        return motion_score > MOTION_THRESHOLD

    def preprocess_for_screen(self, img):
        """OPTIMIZADO PARA QUITAR EL EFECTO MOIRE Y RUIDO DE PIXELES DE PANTALLAS."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LANCZOS4)
        
        # 1. FILTRO DE MEDIANA
        gray = cv2.medianBlur(gray, 3)
        
        # 2. AUMENTO DE CONTRASTE RADICAL
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
        contrast = clahe.apply(gray)
        
        # 3. SHARPENING
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(contrast, -1, kernel)
        
        # 4. UMBRALIZACION ADAPTATIVA
        # V2 RESULTARA EN TEXTO NEGRO SOBRE FONDO BLANCO SI EL ORIGINAL ERA OSCURO SOBRE CLARO
        v2 = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 5)
        
        # 5. INVERSION (CRUCIAL PARA PATENTES VIEJAS: LETRAS BLANCAS SOBRE FONDO NEGRO)
        v2_inv = cv2.bitwise_not(v2)
        
        return [sharpened, v2, v2_inv]

    def find_plate_roi(self, frame):
        h, w = frame.shape[:2]
        # ENFOCAMOS EN EL CENTRO DE LA IMAGEN DONDE SUELE ESTAR EL VEHICULO
        main_roi = frame[int(h*0.1):int(h*0.9), int(w*0.05):int(w*0.95)]
        rh, rw = main_roi.shape[:2]
        gray = cv2.cvtColor(main_roi, cv2.COLOR_BGR2GRAY)
        
        candidates = []
        seen_boxes = set()

        # 1) INTENTAR DETECTAR LA PATENTE CON CASCADA (si funciona)
        try:
            plates = self.plate_cascade.detectMultiScale(gray, 1.1, 4)
        except Exception:
            plates = []

        for (x, y, pw, ph) in plates:
            pad_w = int(pw*0.15)
            pad_h = int(ph*0.2)
            x0 = max(0, x-pad_w); y0 = max(0, y-pad_h)
            x1 = min(rw, x+pw+pad_w); y1 = min(rh, y+ph+pad_h)
            box = (x0, y0, x1, y1)
            if box not in seen_boxes:
                candidates.append(main_roi[y0:y1, x0:x1])
                seen_boxes.add(box)

        # 2) Añadir franjas útiles: zona inferior y franja central (la inferior suele contener la matrícula)
        try:
            bottom_strip = main_roi[int(rh*0.55):int(rh*0.95), :]
            cbox = (0, int(rh*0.55), rw, int(rh*0.95))
            if cbox not in seen_boxes:
                candidates.append(bottom_strip)
                seen_boxes.add(cbox)
        except Exception:
            pass

        try:
            central_strip = main_roi[int(rh*0.3):int(rh*0.7), :]
            cbox = (0, int(rh*0.3), rw, int(rh*0.7))
            if cbox not in seen_boxes:
                candidates.append(central_strip)
                seen_boxes.add(cbox)
        except Exception:
            pass

        # 3) Detección basada en contornos: buscar rectángulos con aspecto de placa
        try:
            blur = cv2.bilateralFilter(gray, 9, 75, 75)
            edged = cv2.Canny(blur, 50, 200)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,3))
            closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < (rw*rh)*0.001:  # descartar contornos demasiado pequeños
                    continue
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect = (cw / float(ch)) if ch > 0 else 0
                # Placas autos: rectangulares anchas; placas moto: casi cuadradas. Soportar aspecto amplio 0.6 - 6.0
                if 0.6 <= aspect <= 6.0 and cw > rw*0.12:
                    pad_x = int(cw * 0.12)
                    pad_y = int(ch * 0.25)
                    x0 = max(0, x-pad_x); y0 = max(0, y-pad_y)
                    x1 = min(rw, x+cw+pad_x); y1 = min(rh, y+ch+pad_y)
                    box = (x0, y0, x1, y1)
                    if box not in seen_boxes:
                        candidates.append(main_roi[y0:y1, x0:x1])
                        seen_boxes.add(box)
        except Exception:
            pass

        # 4) Fallback: si no hay candidatos, devolvemos el ROI completo
        if not candidates:
            candidates.append(main_roi)

        return candidates

    def is_mercosur_candidate(self, roi):
        """DETECTA SI UN ROI TIENE LA FRANJA AZUL CARACTERISTICA DEL MERCOSUR."""
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            # AZUL MERCOSUR (APROXIMADO EN HSV)
            lower_blue = np.array([100, 100, 50])
            upper_blue = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # VERIFICAMOS SI HAY UNA CONCENTRACION DE AZUL EN LA PARTE SUPERIOR
            h, w = mask.shape[:2]
            top_strip = mask[0:int(h*0.3), :]
            blue_ratio = np.sum(top_strip > 0) / top_strip.size
            return blue_ratio > 0.1 # AL MENOS 10% DE LA FRANJA SUPERIOR ES AZUL
        except:
            return False

    def crop_below_blue(self, roi):
        """Si la franja azul ocupa la parte superior del ROI, recorta por debajo de ella.
        Devuelve el ROI recortado o el original si no se detecta la franja azul."""
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([100, 80, 50])
            upper_blue = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            # Encontrar el contorno azul más grande en la parte superior
            h, w = mask.shape[:2]
            # Solo mirar en la mitad superior
            top_mask = mask[0:int(h*0.5), :]
            if np.sum(top_mask) == 0:
                return roi
            # Obtener la coordenada Y máxima del azul
            ys, xs = np.where(top_mask > 0)
            if len(ys) == 0:
                return roi
            y_max = int(np.max(ys))
            # Añadir un pequeño offset y recortar solo si no eliminamos todo
            new_y0 = min(h-1, int((y_max + 5)))
            # Si la franja azul está muy baja (y_max > h*0.45), entonces no recortar
            if y_max > int(h*0.45):
                return roi
            cropped = roi[new_y0: , :]
            # Si el recorte resultante es demasiado pequeño, devolver original
            if cropped.shape[0] < int(h*0.25):
                return roi
            return cropped
        except Exception:
            return roi

    def ocr_worker(self):
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=1)
                found_plate = False
                
                # QR DETECTION
                qr_data, _, _ = self.qr_detector.detectAndDecode(frame)
                if qr_data:
                    print(f"[ALPR OCR] QR detectado: len={len(qr_data)} preview={qr_data[:80]}")
                    self.send_event("qr", qr_data, frame)
                    time.sleep(1); continue
                
                rois = self.find_plate_roi(frame)
                for roi_idx, roi in enumerate(rois):
                    is_mercosur = self.is_mercosur_candidate(roi)
                    # Si detectamos la franja azul, recortamos por debajo para evitar leer la leyenda superior
                    if is_mercosur:
                        roi = self.crop_below_blue(roi)
                    variants = self.preprocess_for_screen(roi)
                    
                    for var_idx, processed in enumerate(variants):
                        # SI DETECTAMOS QUE ES MERCOSUR, PRIORIZAMOS LA VERSION NORMAL (NEGRO SOBRE BLANCO)
                        # SI NO ES MERCOSUR, LA VERSION INVERTIDA (V2_INV) PODRIA SER LA CLAVE PARA PATENTES VIEJAS
                        try:
                            results = self.reader.readtext(processed, detail=1, allowlist=PLATE_ALLOWLIST)
                        except Exception as e:
                            print(f"[ALPR OCR] Error reader.readtext: {type(e).__name__} - {e}")
                            results = []

                        # NO LOGGEAR RESULTADOS CRUDOS PARA EVITAR RUIDO EN CONSOLA

                        if not results:
                            # No OCR results -> continuar sin guardar para evitar ruido
                            continue
                        
                        # Orden seguro por coordenada X izquierda del bbox (evita errores si la estructura es inesperada)
                        def _leftmost_x(rr):
                            try:
                                bbox = rr[0]
                                # bbox puede ser lista de puntos o array; intentar extraer la x del primer punto
                                if hasattr(bbox, '__len__') and len(bbox) > 0:
                                    try:
                                        return float(bbox[0][0])
                                    except Exception:
                                        try:
                                            import numpy as _np
                                            arr = _np.array(bbox)
                                            return float(_np.min(arr[:,0]))
                                        except Exception:
                                            return 0.0
                                return 0.0
                            except Exception:
                                return 0.0

                        try:
                            results.sort(key=_leftmost_x)
                        except Exception:
                            pass

                        # Construir texto combinado de forma segura (left->right)
                        combined_lr = "".join([str(r[1]) if len(r) > 1 else '' for r in results])

                        # Construir texto combinado top->bottom (usar coordenada Y media)
                        try:
                            def _centroid_y(rr):
                                try:
                                    bbox = rr[0]
                                    ys = [pt[1] for pt in bbox]
                                    return float(sum(ys) / len(ys))
                                except Exception:
                                    return 0.0
                            results_by_y = sorted(results, key=_centroid_y)
                            combined_tb = "".join([str(r[1]) if len(r) > 1 else '' for r in results_by_y])
                        except Exception:
                            combined_tb = combined_lr

                        # Preferir la forma con mayor longitud útil
                        combined = combined_lr if len(combined_lr) >= len(combined_tb) else combined_tb

                        # Calcular confianza promedio de forma segura
                        try:
                            avg_conf = sum([float(r[2]) for r in results if len(r) > 2]) / max(1, len([r for r in results if len(r) > 2]))
                        except Exception:
                            avg_conf = 0.0
                        
                        # REGEX PESCA
                        match = re.search(LATAM_PLATE_PATTERN, combined)
                        if match:
                            plate_raw = match.group(0)
                            # Sanitizar la placa: solo alfanuméricos y mayúsculas
                            plate = re.sub(r'[^A-Z0-9]', '', plate_raw.upper())
                            country = self.identify_country(plate, is_mercosur)

                            # Rechazar lecturas claramente no-plaque (longitud fuera de rango, sin letras o sin dígitos)
                            if len(plate) < 5 or len(plate) > 8 or not re.search(r'[A-Z]', plate) or not re.search(r'\d', plate):
                                print(f"[ALPR] Candidate rejected by basic heuristics: raw='{plate_raw}' sanitized='{plate}' len={len(plate)} combined_preview='{combined[:60]}' avg_conf={avg_conf:.3f}")
                                # registrar en buffer de votos pero no enviar inmediatamente
                                now = time.time()
                                self.vote_buffer.append((plate, avg_conf, now))
                                # limpiar buffer antiguo
                                self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
                                continue

                            print(f"🚗 Patente detectada: {plate} (Conf: {avg_conf:.2f})")

                            # CONSENSUS: aceptar si avg_conf >= threshold o si aparece CONSENSUS_REQUIRED veces en ventana
                            now = time.time()
                            self.vote_buffer.append((plate, avg_conf, now))
                            # limpiar buffer antiguo
                            self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
                            same_votes = [v for v in self.vote_buffer if v[0] == plate]
                            if avg_conf >= CONFIDENCE_THRESHOLD or len(same_votes) >= CONSENSUS_REQUIRED:
                                # Si la confianza promedio es baja pero se cumple consenso, lo aceptamos
                                # Antes de enviar al backend, guardar la evidencia solo si la lectura corresponde a Argentina (Mercosur)
                                try:
                                    if 'ARGENTINA' in country.upper():
                                        os.makedirs('alpr_debug', exist_ok=True)
                                        debug_path = os.path.join('alpr_debug', f'accepted_plate_{GATE_ID}_{plate}_{int(time.time()*1000)}.jpg')
                                        cv2.imwrite(debug_path, roi)
                                except Exception:
                                    pass

                                self.send_event("plate", plate, frame)
                                # limpiar buffer para evitar reenvíos inmediatos
                                self.vote_buffer = []
                                found_plate = True
                                break
                            else:
                                # Buffered for consensus, no log
                                # buffered for consensus; no debug image saved to avoid noise
                                continue
                        else:
                            # No se pudo extraer una placa con el regex: guardar para analisis
                            # No match -> no guardar para evitar ruido
                            pass
            except queue.Empty: continue
            except Exception as e:
                print(f"[ALPR OCR] Exception en ocr_worker: {type(e).__name__} - {e}")

    def send_event(self, type, data, frame):
        """Evita duplicados con debounce y delega el envio HTTP al pool de hilos."""
        try:
            key = f"{type}:" + re.sub(r'\s+', '', str(data)).upper()
            now = time.time()
            if self.last_validated_plate == key and (now - getattr(self, 'last_validation_time', 0)) < COOLDOWN_SECONDS:
                # Ignorando evento duplicado dentro de cooldown
                return
            self.last_validated_plate = key
            self.last_validation_time = now
        except Exception:
            pass
        self.executor.submit(self._dispatch_request, type, data, frame)

    def _dispatch_request(self, type, data, frame):
        """Codifica el frame, construye el payload y envia el POST al backend."""
        try:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_b64 = base64.b64encode(buffer).decode('utf-8')
            endpoint = "/v1/access/validate-plate" if GATE_TYPE in ("entrada", "patente") else "/v1/access/exit-plate"
            if type == "qr": endpoint = "/v1/access/validate-qr"
            payload_key = "plate" if type != "qr" else "qr_data"
            payload = {"gate_id": GATE_ID, "image_base64": img_b64, payload_key: data}
            try:
                resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=5)
                if resp.ok:
                    msg = resp.json().get("message", "")
                    if "bienvenido" in msg.lower():
                        print(f"✅ Ingreso: ¡Bienvenido {data}!")
                    elif "hasta luego" in msg.lower() or "salida" in msg.lower():
                        print(f"✅ Salida: ¡Hasta luego {data}!")
                    else:
                        print(f"✅ {msg}")
                else:
                    print(f"❌ Error {resp.status_code}: {resp.text[:200]}")
            except Exception as re:
                print(f"[ALPR ERROR] Error enviando petición al backend: {type(re).__name__} - {re}")
        except Exception as e:
            print(f"[ALPR ERROR] Error preparando/serializando frame: {type(e).__name__} - {e}")

class VideoStreamer:
    """Captura video en un hilo separado y provee acceso thread-safe al ultimo frame."""

    def __init__(self, source, target_width=640):
        self.cap = cv2.VideoCapture(source)
        if isinstance(source, str) and source.startswith("http"):
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.target_width = target_width
        self.current_frame = None
        self.is_running = True
        self.lock = threading.Lock()
    def start(self):
        threading.Thread(target=self._update, daemon=True).start()
        return self
    def _update(self):
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(1)
                    continue
                h, w = frame.shape[:2]
                if w > self.target_width:
                    scale = self.target_width / w
                    new_w = self.target_width
                    new_h = int(h * scale)
                    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                with self.lock: self.current_frame = frame
            except Exception:
                time.sleep(1)
    def get_frame(self):
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None

async def ws_monitoring_worker(streamer):
    """Streaming de frames por WebSocket al backend con reconexion automatica."""
    print(f"[*] Intentando conectar streaming a: {WS_BACKEND_URL}")
    while streamer.is_running:
        try:
            async with websockets.connect(WS_BACKEND_URL, ping_interval=20, ping_timeout=20) as websocket:
                print(f"[*] WS Conectado exitosamente para streaming en {GATE_ID}")
                frame_count = 0
                while streamer.is_running:
                    frame = streamer.get_frame()
                    if frame is not None:
                        try:
                            view_frame = cv2.resize(frame, (640, 360))
                            _, buffer = cv2.imencode('.jpg', view_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                            await websocket.send(base64.b64encode(buffer).decode('utf-8'))
                            frame_count += 1
                        except Exception as fe:
                            print(f"[!] Error al procesar/enviar frame ({GATE_ID}): {fe}")
                            break # ROMPER BUCLE INTERNO PARA RECONECTAR
                    await asyncio.sleep(0.05)
        except Exception as e: 
            print(f"[!] WS Streaming Error ({GATE_ID}): {type(e).__name__} - {e}")
            await asyncio.sleep(5)

def main():
    print(f"[*] Iniciando VideoStreamer con fuente: {VIDEO_SOURCE}")
    try:
        streamer = VideoStreamer(VIDEO_SOURCE, target_width=640).start()
    except Exception as e:
        print(f"[!] Error FATAL al iniciar VideoStreamer: {e}")
        return
    
    # VERIFICAR SI LA CAMARA REALMENTE ABRIO
    time.sleep(2)
    if streamer.get_frame() is None:
        print(f"[!] ADVERTENCIA: No se recibe imagen de la fuente {VIDEO_SOURCE}. Verificá la URL o el dispositivo.")

    try:
        # PREDIO: Solo streaming de video. No OCR, no QR.
        if GATE_TYPE == "predio":
            threading.Thread(target=asyncio.run, args=(ws_monitoring_worker(streamer),), daemon=True).start()
            print(f"[*] Modo PREDIO: Streaming activo en {GATE_ID}. Escaneo desactivado.")
            while True:
                time.sleep(1)

        engine = ALPREngine()
        
        # Iniciar worker OCR solo si el modo requiere lectura de patente (patente, entrada, salida)
        if GATE_TYPE in ("entrada", "salida", "patente"):
            threading.Thread(target=engine.ocr_worker, daemon=True).start()
            
        threading.Thread(target=asyncio.run, args=(ws_monitoring_worker(streamer),), daemon=True).start()
        print(f"[*] Bucle de escaneo activo en {GATE_ID} (Modo: {GATE_TYPE.upper()}). 'Ctrl+C' para salir.")
        
        last_ocr_time = 0
        while True:
            frame = streamer.get_frame()
            if frame is None:
                time.sleep(0.1); continue
            now = time.time()

            # QUICK QR CHECK: Solo si el modo requiere lectura de QR (qr, entrada, salida)
            if GATE_TYPE in ("entrada", "salida", "qr"):
                try:
                    small = cv2.resize(frame, (320, 240))
                    qr_data, _, _ = engine.qr_detector.detectAndDecode(small)
                    if qr_data:
                        engine.send_event("qr", qr_data, frame)
                        last_ocr_time = now
                        time.sleep(0.05)
                        continue
                except Exception:
                    pass

            # OCR CHECK: Solo si el modo requiere lectura de patente (patente, entrada, salida)
            if GATE_TYPE in ("entrada", "salida", "patente"):
                if now - last_ocr_time > OCR_INTERVAL:
                    if engine.detect_motion(frame):
                        try:
                            if not engine.frame_queue.full():
                                engine.frame_queue.put(frame)
                                last_ocr_time = now
                            else:
                                try:
                                    engine.frame_queue.get_nowait()
                                    engine.frame_queue.put(frame)
                                    last_ocr_time = now
                                except Exception:
                                    pass
                        except Exception:
                            pass
            time.sleep(0.01)
    except Exception as e:
        print(f"[!] Error FATAL en el bucle principal: {e}")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass
