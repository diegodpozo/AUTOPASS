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
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

GATE_ID = normalize_id(RAW_GATE_ID)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
WS_BACKEND_URL = BACKEND_URL.replace("http", "ws") + f"/v1/system/ws/video/{GATE_ID}"

print(f"[*] Nodo ALPR v8.1.0 (Screen-to-Screen) Iniciado: {GATE_ID}")

# PARAMETROS SENSIBLES
COOLDOWN_SECONDS = int(os.getenv("ALPR_COOLDOWN", 10))
CONSENSUS_WINDOW = int(os.getenv("ALPR_CONSENSUS_WINDOW", 4))
MIN_CONFIDENCE_VOTES = int(os.getenv("ALPR_MIN_CONFIDENCE", 1)) 
OCR_INTERVAL = float(os.getenv("ALPR_OCR_INTERVAL", 0.15))
CONFIDENCE_THRESHOLD = float(os.getenv("ALPR_CONFIDENCE_THRESHOLD", 0.20))
MOTION_THRESHOLD = int(os.getenv("ALPR_MOTION_THRESHOLD", 3000)) 
PLATE_ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
# PATRONES ESPECIFICOS DE MERCOSUR Y ARGENTINA: 
# 1. AAA 111 (ARG ANTIGUO) 
# 2. AB 123 CD (ARG MERCOSUR)
# 3. ABC1D23 (BRASIL MERCOSUR)
# 4. ABC 1234 (URUGUAY MERCOSUR)
# 5. ABCD 123 / 123 ABCD (PARAGUAY MERCOSUR)
LATAM_PLATE_PATTERN = r'\b([A-Z]{3}\d{3}|[A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d[A-Z]\d{2}|[A-Z]{3}\d{4}|[A-Z]{4}\d{3}|\d{3}[A-Z]{4})\b'

class ALPREngine:
    def __init__(self):
        print("[*] Cargando motores de IA...")
        # ... (UNCHANGED)
        self.reader = easyocr.Reader(['en'], gpu=False) 
        self.qr_detector = cv2.QRCodeDetector()
        cascade_path = cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        self.plate_cascade = cv2.CascadeClassifier(cascade_path)
        
        self.frame_queue = queue.Queue(maxsize=4)
        self.vote_buffer = []
        self.last_validated_plate = ""
        self.last_validation_time = 0
        self.is_running = True
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
        
        # INTENTAR DETECTAR LA PATENTE CON CASCADA
        plates = self.plate_cascade.detectMultiScale(gray, 1.1, 4)
        candidates = []
        for (x, y, pw, ph) in plates:
            pad_w = int(pw*0.15)
            pad_h = int(ph*0.2)
            candidates.append(main_roi[max(0,y-pad_h):min(rh,y+ph+pad_h), max(0,x-pad_w):min(rw,x+pw+pad_w)])
            
        # SI NO HAY CANDIDATOS POR CASCADA, DEVOLVEMOS EL ROI PRINCIPAL Y RECORTES CENTRALES
        if not candidates:
            # CANDIDATO 1: ROI COMPLETO
            candidates.append(main_roi)
            # CANDIDATO 2: FRANJA CENTRAL HORIZONTAL
            candidates.append(main_roi[int(rh*0.3):int(rh*0.7), :])
            
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
        except: return False

    def ocr_worker(self):
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=1)
                print(f"[ALPR OCR] Procesando frame desde queue. queue_size={self.frame_queue.qsize()}")
                
                # QR DETECTION
                qr_data, _, _ = self.qr_detector.detectAndDecode(frame)
                if qr_data:
                    print(f"[ALPR OCR] QR detectado: len={len(qr_data)} preview={qr_data[:80]}")
                    self.send_event("qr", qr_data, frame)
                    time.sleep(1); continue
                
                rois = self.find_plate_roi(frame)
                for roi in rois:
                    is_mercosur = self.is_mercosur_candidate(roi)
                    variants = self.preprocess_for_screen(roi)
                    
                    for var_idx, processed in enumerate(variants):
                        # SI DETECTAMOS QUE ES MERCOSUR, PRIORIZAMOS LA VERSION NORMAL (NEGRO SOBRE BLANCO)
                        # SI NO ES MERCOSUR, LA VERSION INVERTIDA (V2_INV) PODRIA SER LA CLAVE PARA PATENTES VIEJAS
                        results = self.reader.readtext(processed, detail=1, allowlist=PLATE_ALLOWLIST)
                        if not results: continue
                        
                        results.sort(key=lambda x: x[0][0][0]) 
                        combined = "".join([r[1] for r in results])
                        avg_conf = sum([r[2] for r in results]) / len(results)
                        
                        # REGEX PESCA
                        match = re.search(LATAM_PLATE_PATTERN, combined)
                        if match:
                            plate = match.group(0)
                            country = self.identify_country(plate, is_mercosur)
                            print(f"🚗 [{country} MATCH] >>> {plate} (Conf: {avg_conf:.2f})")
                            self.send_event("plate", plate, frame)
                            return 
            except queue.Empty: continue
            except Exception as e: pass

    def send_event(self, type, data, frame):
        # Evitar reprocesar el mismo QR/patente en un corto periodo (debounce)
        try:
            key = f"{type}:" + re.sub(r'\s+', '', str(data)).upper()
            now = time.time()
            if self.last_validated_plate == key and (now - getattr(self, 'last_validation_time', 0)) < COOLDOWN_SECONDS:
                print(f"[ALPR] Ignorando evento duplicado {key} dentro de cooldown")
                return
            self.last_validated_plate = key
            self.last_validation_time = now
        except Exception:
            pass
        self.executor.submit(self._dispatch_request, type, data, frame)

    def _dispatch_request(self, type, data, frame):
        try:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_b64 = base64.b64encode(buffer).decode('utf-8')
            endpoint = "/v1/access/validate-plate" if GATE_TYPE == "entrada" else "/v1/access/exit-plate"
            if type == "qr": endpoint = "/v1/access/validate-qr"
            payload_key = "plate" if type != "qr" else "qr_data"
            payload = {"gate_id": GATE_ID, "image_base64": img_b64, payload_key: data}
            print(f"[ALPR -> BACKEND] POST {BACKEND_URL}{endpoint} payload_keys={list(payload.keys())}")
            try:
                resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=5)
                print(f"[ALPR -> BACKEND] Response {resp.status_code}: {resp.text[:200]}")
            except Exception as re:
                print(f"[ALPR ERROR] Error enviando petición al backend: {type(re).__name__} - {re}")
        except Exception as e:
            print(f"[ALPR ERROR] Error preparando/serializando frame: {type(e).__name__} - {e}")

class VideoStreamer:
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
                            if frame_count % 100 == 0:
                                print(f"[*] Streaming {GATE_ID}: {frame_count} frames enviados.")
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
        engine = ALPREngine()
        threading.Thread(target=engine.ocr_worker, daemon=True).start()
        threading.Thread(target=asyncio.run, args=(ws_monitoring_worker(streamer),), daemon=True).start()
        print(f"[*] Bucle de escaneo activo en {GATE_ID}. 'Ctrl+C' para salir.")
        last_ocr_time = 0
        while True:
            frame = streamer.get_frame()
            if frame is None:
                time.sleep(0.1); continue
            now = time.time()

            # QUICK QR CHECK: detect QR on a small fast-resized frame to react faster than OCR
            try:
                small = cv2.resize(frame, (320, 240))
                qr_data, _, _ = engine.qr_detector.detectAndDecode(small)
                if qr_data:
                    print(f"[ALPR QUICK QR] QR detectado en main loop: len={len(qr_data)} preview={qr_data[:80]}")
                    engine.send_event("qr", qr_data, frame)
                    last_ocr_time = now
                    time.sleep(0.05)
                    continue
            except Exception:
                pass

            if now - last_ocr_time > OCR_INTERVAL:
                if engine.detect_motion(frame):
                    # enqueue or drop-oldest policy when full (prefer recent frames)
                    try:
                        if not engine.frame_queue.full():
                            engine.frame_queue.put(frame)
                            print(f"[ALPR] Frame encolado. t={now:.3f} queue_size={engine.frame_queue.qsize()}")
                            last_ocr_time = now
                        else:
                            # drop the oldest frame to make room for newest
                            try:
                                engine.frame_queue.get_nowait()
                                engine.frame_queue.put(frame)
                                print(f"[ALPR] frame_queue lleno. descartado el más antiguo y encolado el nuevo. t={now:.3f} queue_size={engine.frame_queue.qsize()}")
                                last_ocr_time = now
                            except Exception:
                                print(f"[ALPR] frame_queue lleno. descartando frame. t={now:.3f}")
                    except Exception:
                        print(f"[ALPR] Error gestionando frame_queue. t={now:.3f}")
            time.sleep(0.01)
    except Exception as e:
        print(f"[!] Error FATAL en el bucle principal: {e}")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass
