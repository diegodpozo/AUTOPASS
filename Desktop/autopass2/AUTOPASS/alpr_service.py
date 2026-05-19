import cv2
import easyocr
import requests
import time
import os
import re
import base64
import threading
import numpy as np
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE SEGURIDAD Y RENDIMIENTO ---
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
os.environ["FFMPEG_LOG_LEVEL"] = "quiet"
load_dotenv()

# --- CONFIGURACIÓN DEL SERVICIO ---
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")
if isinstance(VIDEO_SOURCE, str) and VIDEO_SOURCE.isdigit():
    VIDEO_SOURCE = int(VIDEO_SOURCE)

# Forzamos los IDs que el dashboard espera
GATE_TYPE = os.getenv("GATE_TYPE", "entrada").lower()
GATE_ID = "ENTRADA_PRINCIPAL" if GATE_TYPE == "entrada" else "SALIDA_PRINCIPAL"

print(f"[*] Configurando Nodo: {GATE_ID}")
print(f"[*] Fuente de Video: {VIDEO_SOURCE}")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
COOLDOWN_SECONDS = 15 

# --- INICIALIZACIÓN DE MOTORES ---
print(f"[*] Cargando Inteligencia Artificial...")
reader = easyocr.Reader(['es', 'en'], gpu=False)
qr_detector = cv2.QRCodeDetector()

# --- VARIABLES DE ESTADO ---
frame_to_process = None
frame_to_stream = None
last_detected_plate = ""
last_detection_time = 0
plate_buffer = [] 

def video_stream_worker():
    global frame_to_stream
    while True:
        if frame_to_stream is not None:
            try:
                frame = frame_to_stream.copy()
                frame_to_stream = None
                view_frame = cv2.resize(frame, (640, 480))
                _, buffer = cv2.imencode('.jpg', view_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                requests.post(f"{BACKEND_URL}/v1/system/update-frame/{GATE_ID}",
                              json={"image": img_base64}, timeout=0.5)
            except: pass
        time.sleep(0.1)

def ocr_worker():
    global frame_to_process, last_detected_plate, last_detection_time, plate_buffer
    print(f"[*] Escaneando accesos (QR/ALPR) en: {GATE_ID}")
    
    while True:
        if frame_to_process is not None:
            img_orig = frame_to_process
            frame_to_process = None 
            start_time = time.time()
            
            try:
                # 1. INTENTO DE LECTURA QR (Prioridad absoluta)
                data, bbox, _ = qr_detector.detectAndDecode(img_orig)
                if data and data.startswith("AUTOPASS"):
                    print(f"✅ [QR DETECTADO] >>> {data}")
                    send_qr_to_backend(data)
                    time.sleep(3) # Pausa larga para evitar lecturas dobles
                    continue

                # 2. INTENTO DE LECTURA DE PATENTE (ALPR)
                gray = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY)
                res = reader.readtext(gray, detail=0, paragraph=False)
                
                for text in res:
                    plate = normalize_plate(text)
                    if plate:
                        plate_buffer.append(plate)
                        if len(plate_buffer) > 5: plate_buffer.pop(0)
                        
                        if plate_buffer.count(plate) >= 2:
                            now = time.time()
                            if plate != last_detected_plate or (now - last_detection_time > COOLDOWN_SECONDS):
                                print(f"🚗 [PATENTE DETECTADA] >>> {plate}")
                                send_to_backend_async(plate, img_orig)
                                last_detected_plate = plate
                                last_detection_time = now
                                plate_buffer = [] 
            except: pass
            
            elapsed = time.time() - start_time
            time.sleep(max(0.1, 0.4 - elapsed))
        else:
            time.sleep(0.1)

def normalize_plate(plate_text):
    clean = re.sub(r'[^A-Z0-9]', '', plate_text.upper())
    if len(clean) < 6 or len(clean) > 8: return None
    return clean

def send_qr_to_backend(qr_data):
    def _send():
        try:
            resp = requests.post(f"{BACKEND_URL}/v1/access/validate-qr", 
                         json={"qr_data": qr_data, "gate_id": GATE_ID}, 
                         timeout=5)
            if resp.status_code == 200:
                print(f"📡 [SERVER] QR validado correctamente.")
            else:
                print(f"⚠️ [SERVER] Error validando QR: {resp.text}")
        except: pass
    threading.Thread(target=_send, daemon=True).start()

def send_to_backend_async(plate, frame):
    def _send():
        try:
            _, buffer = cv2.imencode(".jpg", frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            endpoint = "/v1/access/validate-plate" if GATE_TYPE == "entrada" else "/v1/access/exit-plate"
            requests.post(f"{BACKEND_URL}{endpoint}", 
                         json={"plate": plate, "gate_id": GATE_ID, "image_base64": img_base64}, 
                         timeout=5)
        except: pass
    threading.Thread(target=_send, daemon=True).start()

def main():
    global frame_to_process, frame_to_stream
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir la fuente de video")
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
    threading.Thread(target=ocr_worker, daemon=True).start()
    threading.Thread(target=video_stream_worker, daemon=True).start()
    
    print("[*] Sistema Híbrido Listo. Presione 'q' para salir.")
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame_to_process = frame
        frame_to_stream = frame
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()

if __name__ == "__main__":
    main()
