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
from collections import Counter
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
GATE_ID = os.getenv("GATE_ID", "ENTRADA_PRINCIPAL" if GATE_TYPE == "entrada" else "SALIDA_PRINCIPAL")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Parámetros de Calidad y Consenso
COOLDOWN_SECONDS = 12
CONSENSUS_WINDOW = 6  # Número de frames para votar
MIN_CONFIDENCE_VOTES = 3 # Votos mínimos para validar una patente
OCR_INTERVAL = 0.3    # Intervalo entre escaneos de OCR (segundos)

print(f"[*] Nodo ALPR Iniciado: {GATE_ID} ({GATE_TYPE.upper()})")

class ALPREngine:
    def __init__(self):
        print("[*] Inicializando Motores de IA (EasyOCR)...")
        self.reader = easyocr.Reader(['es', 'en'], gpu=False)
        self.qr_detector = cv2.QRCodeDetector()
        self.plate_queue = queue.Queue(maxsize=10)
        self.vote_buffer = []
        self.last_validated_plate = ""
        self.last_validation_time = 0
        self.is_running = True

    def preprocess_image(self, frame):
        """Optimización de imagen para OCR usando OpenCV."""
        # 1. Conversión a escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. Reducción de ruido con filtro Gaussiano
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Mejora de contraste (CLAHE - Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast = clahe.apply(blur)
        
        # 4. Umbralización adaptativa para separar texto del fondo
        thresh = cv2.adaptiveThreshold(contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        return thresh

    def get_roi(self, frame):
        """Define la Región de Interés (típicamente el tercio inferior/central)."""
        h, w = frame.shape[:2]
        # Tomamos el área donde suelen estar las patentes (centro y abajo)
        roi = frame[int(h*0.2):int(h*0.9), int(w*0.1):int(w*0.9)]
        return roi

    def normalize_plate(self, text):
        """Limpia y valida el formato de la patente."""
        clean = re.sub(r'[^A-Z0-9]', '', text.upper())
        # Formatos: ABC123 (viejas) o AB123CD (Mercosur)
        if 6 <= len(clean) <= 7:
            return clean
        return None

    def process_consensus(self, plate):
        """Algoritmo de consenso por votación en ventana temporal."""
        self.vote_buffer.append(plate)
        if len(self.vote_buffer) > CONSENSUS_WINDOW:
            self.vote_buffer.pop(0)

        # Contar ocurrencias en la ventana actual
        counts = Counter(self.vote_buffer)
        most_common, num_votes = counts.most_common(1)[0]

        if num_votes >= MIN_CONFIDENCE_VOTES:
            now = time.time()
            # Evitar duplicados inmediatos (cooldown)
            if most_common != self.last_validated_plate or (now - self.last_validation_time > COOLDOWN_SECONDS):
                self.last_validated_plate = most_common
                self.last_validation_time = now
                self.vote_buffer = [] # Limpiar buffer tras validación exitosa
                return most_common
        return None

    def ocr_worker(self):
        """Worker principal que procesa la cola de frames asincrónicamente."""
        while self.is_running:
            try:
                frame = self.plate_queue.get(timeout=1)
                
                # 1. Detección de QR (Prioridad)
                qr_data, _, _ = self.qr_detector.detectAndDecode(frame)
                if qr_data and qr_data.startswith("AUTOPASS"):
                    print(f"✅ [QR] >>> {qr_data}")
                    self.send_event("qr", qr_data, frame)
                    time.sleep(2)
                    continue

                # 2. Detección de Patente
                roi = self.get_roi(frame)
                processed = self.preprocess_image(roi)
                
                # OCR sobre la imagen optimizada
                results = self.reader.readtext(processed, detail=0, paragraph=False)
                
                for text in results:
                    plate = self.normalize_plate(text)
                    if plate:
                        validated = self.process_consensus(plate)
                        if validated:
                            print(f"🚗 [ALPR] >>> {validated} (Votos: {MIN_CONFIDENCE_VOTES}+)")
                            self.send_event("plate", validated, frame)
                            break # Una patente por frame es suficiente

            except queue.Empty: continue
            except Exception as e:
                print(f"[!] Error en OCR Worker: {e}")

    def send_event(self, type, data, frame):
        """Envía la detección al backend de forma asíncrona."""
        def _request():
            try:
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                img_b64 = base64.b64encode(buffer).decode('utf-8')
                
                if type == "qr":
                    payload = {"qr_data": data, "gate_id": GATE_ID}
                    url = f"{BACKEND_URL}/v1/access/validate-qr"
                else:
                    payload = {"plate": data, "gate_id": GATE_ID, "image_base64": img_b64}
                    endpoint = "/v1/access/validate-plate" if GATE_TYPE == "entrada" else "/v1/access/exit-plate"
                    url = f"{BACKEND_URL}{endpoint}"
                
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                print(f"[!] Error enviando a backend: {e}")

        threading.Thread(target=_request, daemon=True).start()

# --- STREAMING DE VIDEO (MONITOREO) ---
def stream_worker(cap):
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        # Redimensionar para el dashboard (ahorro de ancho de banda)
        view_frame = cv2.resize(frame, (640, 480))
        _, buffer = cv2.imencode('.jpg', view_frame, [cv2.IMWRITE_JPEG_QUALITY, 35])
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        try:
            requests.post(f"{BACKEND_URL}/v1/system/update-frame/{GATE_ID}",
                          json={"image": img_b64}, timeout=0.2)
        except: pass
        time.sleep(0.1)

def main():
    engine = ALPREngine()
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    
    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir {VIDEO_SOURCE}")
        return

    # Iniciar workers
    threading.Thread(target=engine.ocr_worker, daemon=True).start()
    threading.Thread(target=stream_worker, args=(cap,), daemon=True).start()

    print(f"[*] Escaneando en {GATE_ID}. Presione 'q' para salir.")
    
    last_ocr_time = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Encolar frames para OCR con limitación de frecuencia
        now = time.time()
        if now - last_ocr_time > OCR_INTERVAL:
            if not engine.plate_queue.full():
                engine.plate_queue.put(frame.copy())
                last_ocr_time = now

        # Tecla de salida
        if cv2.waitKey(1) & 0xFF == ord('q'):
            engine.is_running = False
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
