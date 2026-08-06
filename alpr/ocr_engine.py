import cv2
import easyocr
import requests
import time
import os
import re
import base64
import queue
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from alpr.config import (
    GATE_ID, GATE_TYPE, BACKEND_URL, COOLDOWN_SECONDS, OCR_INTERVAL,
    CONFIDENCE_THRESHOLD, FRAME_QUEUE_MAXSIZE, CONSENSUS_REQUIRED,
    CONSENSUS_WINDOW, PLATE_ALLOWLIST, LATAM_PLATE_PATTERN
)
from alpr.preprocessor import ImagePreprocessor

class ALPREngine:
    """Motor principal de visión artificial: EasyOCR, QR, consenso y despacho de eventos."""

    def __init__(self):
        print("[*] Cargando motores de IA...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        self.qr_detector = cv2.QRCodeDetector()
        cascade_path = cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        self.plate_cascade = cv2.CascadeClassifier(cascade_path)
        
        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_MAXSIZE)
        self.vote_buffer = []
        self.last_validated_plate = ""
        self.last_validation_time = 0
        self.is_running = True
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.prev_gray = None

    def detect_motion(self, frame) -> bool:
        has_motion, self.prev_gray = ImagePreprocessor.detect_motion(frame, self.prev_gray)
        return has_motion

    def ocr_worker(self):
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=1)
                
                # QR DETECTION
                qr_data, _, _ = self.qr_detector.detectAndDecode(frame)
                if qr_data:
                    print(f"[ALPR OCR] QR detectado: len={len(qr_data)} preview={qr_data[:80]}")
                    self.send_event("qr", qr_data, frame)
                    time.sleep(1)
                    continue
                
                rois = ImagePreprocessor.find_plate_roi(frame, self.plate_cascade)
                for roi in rois:
                    is_mercosur = ImagePreprocessor.is_mercosur_candidate(roi)
                    if is_mercosur:
                        roi = ImagePreprocessor.crop_below_blue(roi)
                    variants = ImagePreprocessor.preprocess_for_screen(roi)
                    
                    for processed in variants:
                        try:
                            results = self.reader.readtext(processed, detail=1, allowlist=PLATE_ALLOWLIST)
                        except Exception as e:
                            print(f"[ALPR OCR] Error reader.readtext: {type(e).__name__} - {e}")
                            results = []

                        if not results:
                            continue
                        
                        def _leftmost_x(rr):
                            try:
                                bbox = rr[0]
                                if hasattr(bbox, '__len__') and len(bbox) > 0:
                                    try:
                                        return float(bbox[0][0])
                                    except Exception:
                                        arr = np.array(bbox)
                                        return float(np.min(arr[:,0]))
                                return 0.0
                            except Exception:
                                return 0.0

                        try:
                            results.sort(key=_leftmost_x)
                        except Exception:
                            pass

                        combined_lr = "".join([str(r[1]) if len(r) > 1 else '' for r in results])

                        try:
                            def _centroid_y(rr):
                                bbox = rr[0]
                                ys = [pt[1] for pt in bbox]
                                return float(sum(ys) / len(ys))
                            results_by_y = sorted(results, key=_centroid_y)
                            combined_tb = "".join([str(r[1]) if len(r) > 1 else '' for r in results_by_y])
                        except Exception:
                            combined_tb = combined_lr

                        combined = combined_lr if len(combined_lr) >= len(combined_tb) else combined_tb

                        try:
                            avg_conf = sum([float(r[2]) for r in results if len(r) > 2]) / max(1, len([r for r in results if len(r) > 2]))
                        except Exception:
                            avg_conf = 0.0
                        
                        match = re.search(LATAM_PLATE_PATTERN, combined)
                        if match:
                            plate_raw = match.group(0)
                            plate = re.sub(r'[^A-Z0-9]', '', plate_raw.upper())
                            country = ImagePreprocessor.identify_country(plate, is_mercosur)

                            if len(plate) < 5 or len(plate) > 8 or not re.search(r'[A-Z]', plate) or not re.search(r'\d', plate):
                                print(f"[ALPR] Candidate rejected: raw='{plate_raw}' sanitized='{plate}' avg_conf={avg_conf:.3f}")
                                now = time.time()
                                self.vote_buffer.append((plate, avg_conf, now))
                                self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
                                continue

                            print(f"🚗 Patente detectada: {plate} (Conf: {avg_conf:.2f})")

                            now = time.time()
                            self.vote_buffer.append((plate, avg_conf, now))
                            self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
                            same_votes = [v for v in self.vote_buffer if v[0] == plate]
                            
                            if avg_conf >= CONFIDENCE_THRESHOLD or len(same_votes) >= CONSENSUS_REQUIRED:
                                try:
                                    if 'ARGENTINA' in country.upper():
                                        os.makedirs('alpr_debug', exist_ok=True)
                                        debug_path = os.path.join('alpr_debug', f'accepted_plate_{GATE_ID}_{plate}_{int(time.time()*1000)}.jpg')
                                        cv2.imwrite(debug_path, roi)
                                except Exception:
                                    pass

                                self.send_event("plate", plate, frame)
                                self.vote_buffer = []
                                break
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ALPR OCR] Exception en ocr_worker: {type(e).__name__} - {e}")

    def send_event(self, type, data, frame):
        """Evita duplicados con debounce y delega el envío HTTP al pool de hilos."""
        try:
            key = f"{type}:" + re.sub(r'\s+', '', str(data)).upper()
            now = time.time()
            if self.last_validated_plate == key and (now - getattr(self, 'last_validation_time', 0)) < COOLDOWN_SECONDS:
                return
            self.last_validated_plate = key
            self.last_validation_time = now
        except Exception:
            pass
        self.executor.submit(self._dispatch_request, type, data, frame)

    def _dispatch_request(self, type, data, frame):
        """Codifica el frame y envía la petición HTTP al backend."""
        try:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_b64 = base64.b64encode(buffer).decode('utf-8')
            is_entry_gate = "salida" not in GATE_TYPE and "egreso" not in GATE_TYPE
            endpoint = "/v1/access/validate-plate" if is_entry_gate else "/v1/access/exit-plate"
            if type == "qr":
                endpoint = "/v1/access/validate-qr"
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
