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
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE SEGURIDAD Y RENDIMIENTO ---
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
os.environ["FFMPEG_LOG_LEVEL"] = "quiet"
load_dotenv()

# --- CONFIGURACIÓN DEL SERVICIO ---
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")
if isinstance(VIDEO_SOURCE, str) and VIDEO_SOURCE.isdigit():
    VIDEO_SOURCE = int(VIDEO_SOURCE)

GATE_TYPE = os.getenv("GATE_TYPE", "entrada").lower()
RAW_GATE_ID = os.getenv("GATE_ID", "ENTRADA_PRINCIPAL" if GATE_TYPE == "entrada" else "SALIDA_PRINCIPAL")

def normalize_id(text):
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

GATE_ID = normalize_id(RAW_GATE_ID)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
WS_BACKEND_URL = BACKEND_URL.replace("http", "ws") + f"/v1/system/ws/video/{GATE_ID}"

print(f"[*] Nodo ALPR v8.1.0 (Screen-to-Screen) Iniciado: {GATE_ID}")

# Parámetros Sensibles
COOLDOWN_SECONDS = int(os.getenv("ALPR_COOLDOWN", 6))
CONSENSUS_WINDOW = int(os.getenv("ALPR_CONSENSUS_WINDOW", 4))
MIN_CONFIDENCE_VOTES = int(os.getenv("ALPR_MIN_CONFIDENCE", 1)) 
OCR_INTERVAL = float(os.getenv("ALPR_OCR_INTERVAL", 0.15))
CONFIDENCE_THRESHOLD = float(os.getenv("ALPR_CONFIDENCE_THRESHOLD", 0.20))
MOTION_THRESHOLD = int(os.getenv("ALPR_MOTION_THRESHOLD", 3000)) 
PLATE_ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
# Patrones específicos de Mercosur y Argentina: 
# 1. AAA 111 (Arg Antiguo) 
# 2. AB 123 CD (Arg Mercosur)
# 3. ABC1D23 (Brasil Mercosur)
# 4. ABC 1234 (Uruguay Mercosur)
# 5. ABCD 123 / 123 ABCD (Paraguay Mercosur)
LATAM_PLATE_PATTERN = r'\b([A-Z]{3}\d{3}|[A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d[A-Z]\d{2}|[A-Z]{3}\d{4}|[A-Z]{4}\d{3}|\d{3}[A-Z]{4})\b'

class ALPREngine:
    def __init__(self):
        print("[*] Cargando motores de IA...")
        # ... (unchanged)
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
        """Identifica el país probable basado en el formato y la franja azul."""
        if not is_mercosur:
            if re.match(r'^[A-Z]{3}\d{3}$', plate): return "ARGENTINA (Antigua)"
            return "DESCONOCIDO"
        
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', plate): return "ARGENTINA (Mercosur)"
        if re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', plate): return "BRASIL"
        if re.match(r'^[A-Z]{3}\d{4}$', plate): return "URUGUAY"
        if re.match(r'^[A-Z]{4}\d{3}$|^\d{3}[A-Z]{4}$', plate): return "PARAGUAY"
        
        return "MERCOSUR (Otro)"

    def detect_motion(self, frame):
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
        """Optimizado para quitar el efecto Moiré y ruido de píxeles de pantallas."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LANCZOS4)
        
        # 1. Filtro de Mediana
        gray = cv2.medianBlur(gray, 3)
        
        # 2. Aumento de contraste radical
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
        contrast = clahe.apply(gray)
        
        # 3. Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(contrast, -1, kernel)
        
        # 4. Umbralización Adaptativa
        # v2 resultará en texto negro sobre fondo blanco si el original era oscuro sobre claro
        v2 = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 5)
        
        # 5. Inversión (Crucial para patentes viejas: letras blancas sobre fondo negro)
        v2_inv = cv2.bitwise_not(v2)
        
        return [sharpened, v2, v2_inv]

    def find_plate_roi(self, frame):
        h, w = frame.shape[:2]
        # Enfocamos en el centro de la imagen donde suele estar el vehículo
        main_roi = frame[int(h*0.1):int(h*0.9), int(w*0.05):int(w*0.95)]
        rh, rw = main_roi.shape[:2]
        gray = cv2.cvtColor(main_roi, cv2.COLOR_BGR2GRAY)
        
        # Intentar detectar la patente con cascada
        plates = self.plate_cascade.detectMultiScale(gray, 1.1, 4)
        candidates = []
        for (x, y, pw, ph) in plates:
            pad_w = int(pw*0.15)
            pad_h = int(ph*0.2)
            candidates.append(main_roi[max(0,y-pad_h):min(rh,y+ph+pad_h), max(0,x-pad_w):min(rw,x+pw+pad_w)])
            
        # Si no hay candidatos por cascada, devolvemos el ROI principal y recortes centrales
        if not candidates:
            # Candidato 1: ROI completo
            candidates.append(main_roi)
            # Candidato 2: Franja central horizontal
            candidates.append(main_roi[int(rh*0.3):int(rh*0.7), :])
            
        return candidates

    def is_mercosur_candidate(self, roi):
        """Detecta si un ROI tiene la franja azul característica del Mercosur."""
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            # Azul Mercosur (aproximado en HSV)
            lower_blue = np.array([100, 100, 50])
            upper_blue = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # Verificamos si hay una concentración de azul en la parte superior
            h, w = mask.shape[:2]
            top_strip = mask[0:int(h*0.3), :]
            blue_ratio = np.sum(top_strip > 0) / top_strip.size
            return blue_ratio > 0.1 # Al menos 10% de la franja superior es azul
        except: return False

    def ocr_worker(self):
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=1)
                
                # QR detection
                qr_data, _, _ = self.qr_detector.detectAndDecode(frame)
                if qr_data:
                    self.send_event("qr", qr_data, frame)
                    time.sleep(1); continue
                
                rois = self.find_plate_roi(frame)
                for roi in rois:
                    is_mercosur = self.is_mercosur_candidate(roi)
                    variants = self.preprocess_for_screen(roi)
                    
                    for var_idx, processed in enumerate(variants):
                        # Si detectamos que es Mercosur, priorizamos la versión normal (negro sobre blanco)
                        # Si NO es Mercosur, la versión invertida (v2_inv) podría ser la clave para patentes viejas
                        results = self.reader.readtext(processed, detail=1, allowlist=PLATE_ALLOWLIST)
                        if not results: continue
                        
                        results.sort(key=lambda x: x[0][0][0]) 
                        combined = "".join([r[1] for r in results])
                        avg_conf = sum([r[2] for r in results]) / len(results)
                        
                        # Regex pesca
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
        self.executor.submit(self._dispatch_request, type, data, frame)

    def _dispatch_request(self, type, data, frame):
        try:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_b64 = base64.b64encode(buffer).decode('utf-8')
            endpoint = "/v1/access/validate-plate" if GATE_TYPE == "entrada" else "/v1/access/exit-plate"
            if type == "qr": endpoint = "/v1/access/validate-qr"
            requests.post(f"{BACKEND_URL}{endpoint}", json={"gate_id": GATE_ID, "image_base64": img_b64, "plate" if type!="qr" else "qr_data": data}, timeout=3)
        except: pass

class VideoStreamer:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.current_frame = None
        self.is_running = True
        self.lock = threading.Lock()
    def start(self):
        threading.Thread(target=self._update, daemon=True).start()
        return self
    def _update(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret: break
            with self.lock: self.current_frame = frame
    def get_frame(self):
        with self.lock: return self.current_frame.copy() if self.current_frame is not None else None

async def ws_monitoring_worker(streamer):
    while streamer.is_running:
        try:
            async with websockets.connect(WS_BACKEND_URL) as websocket:
                while streamer.is_running:
                    frame = streamer.get_frame()
                    if frame is not None:
                        view_frame = cv2.resize(frame, (640, 360))
                        _, buffer = cv2.imencode('.jpg', view_frame, [cv2.IMWRITE_JPEG_QUALITY, 45])
                        await websocket.send(base64.b64encode(buffer).decode('utf-8'))
                    await asyncio.sleep(0.12)
        except Exception: await asyncio.sleep(5)

def main():
    streamer = VideoStreamer(VIDEO_SOURCE).start()
    engine = ALPREngine()
    threading.Thread(target=engine.ocr_worker, daemon=True).start()
    threading.Thread(target=asyncio.run, args=(ws_monitoring_worker(streamer),), daemon=True).start()
    print(f"[*] Escaneando en {GATE_ID}. 'Ctrl+C' para salir.")
    last_ocr_time = 0
    while True:
        frame = streamer.get_frame()
        if frame is None:
            time.sleep(0.1); continue
        now = time.time()
        if now - last_ocr_time > OCR_INTERVAL:
            if engine.detect_motion(frame):
                if not engine.frame_queue.full():
                    engine.frame_queue.put(frame)
                    last_ocr_time = now
        time.sleep(0.01)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass
