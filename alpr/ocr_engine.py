import cv2
import requests
import time
import os
import re
import base64
import queue
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
from paddleocr import PaddleOCR
from concurrent.futures import ThreadPoolExecutor
from alpr.config import (
    GATE_ID, GATE_TYPE, BACKEND_URL, COOLDOWN_SECONDS, OCR_INTERVAL,
    CONFIDENCE_THRESHOLD, FRAME_QUEUE_MAXSIZE, CONSENSUS_REQUIRED,
    CONSENSUS_WINDOW, LATAM_PLATE_PATTERN, MOTO_PATTERN, MOTO_MIN_CONFIDENCE
)
from alpr.preprocessor import ImagePreprocessor


class ALPREngine:
    """Motor principal de vision artificial: PaddleOCR, QR, consenso y despacho de eventos."""

    def __init__(self):
        print("[*] Cargando motores de IA...")
        self.reader = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )
        self.qr_detector = cv2.QRCodeDetector()

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

    def _ocr_single_roi(self, roi_color):
        """Ejecuta PaddleOCR sobre un ROI en color y retorna textos+scores."""
        try:
            raw = self.reader.ocr(roi_color)
        except Exception as e:
            print(f"[ALPR OCR] Error PaddleOCR: {type(e).__name__} - {e}")
            return [], [], []

        if not raw or not raw[0]:
            return [], [], []
        jd = raw[0].json['res']
        texts = jd.get('rec_texts', [])
        scores = jd.get('rec_scores', [])
        polys = jd.get('rec_polys', [])
        return texts, scores, polys

    def ocr_worker(self):
        print(f"[ALPR OCR] Worker iniciado. Motor=PaddleOCR | GATE_TYPE={GATE_TYPE}")
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=1)
                t_start = time.time()
                print(f"[ALPR OCR] Frame recibido, procesando...")

                qr_data, _, _ = self.qr_detector.detectAndDecode(frame)
                if qr_data:
                    qr_text = qr_data[0] if isinstance(qr_data, (list, tuple)) and len(qr_data) > 0 else str(qr_data)
                    elapsed = time.time() - t_start
                    print(f"[ALPR OCR] QR detectado: {qr_text[:80]} ({elapsed:.2f}s)")
                    self.send_event("qr", qr_text, frame)
                    time.sleep(1)
                    continue

                h, w = frame.shape[:2]
                main_roi = frame[int(h*0.15):int(h*0.92), int(w*0.05):int(w*0.95)]

                texts, scores, polys = self._ocr_single_roi(main_roi)
                t_ocr = time.time() - t_start

                if texts:
                    print(f"[ALPR OCR] {len(texts)} textos detectados: {texts} (OCR: {t_ocr:.2f}s)")
                else:
                    print(f"[ALPR OCR] Nada detectado en frame (OCR: {t_ocr:.2f}s)")
                    continue

                detections = []
                for i, text in enumerate(texts):
                    t = text.strip()
                    if not t or len(t) < 2:
                        continue
                    conf = float(scores[i]) if i < len(scores) else 0.0
                    if i < len(polys):
                        bbox = [[int(p[0]), int(p[1])] for p in polys[i]]
                    else:
                        bbox = [[0, 0], [0, 0], [0, 0], [0, 0]]
                    detections.append({"text": t.upper(), "confidence": conf, "bbox": bbox})

                is_mercosur = ImagePreprocessor.is_mercosur_candidate(main_roi)

                plate = None
                avg_conf = 0.0

                for det in detections:
                    t = re.sub(r'[^A-Z0-9]', '', det["text"])
                    if re.search(LATAM_PLATE_PATTERN, t):
                        plate = t
                        avg_conf = det["confidence"]
                        print(f"[ALPR OCR] Patente directa: {plate} (conf={avg_conf:.2f})")
                        break

                if not plate and len(detections) >= 2:
                    try:
                        by_y = sorted(detections, key=lambda d: sum(p[1] for p in d["bbox"]) / max(1, len(d["bbox"])))
                        combined = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_y)
                        match = re.search(LATAM_PLATE_PATTERN, combined)
                        if match:
                            plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
                            avg_conf = sum(d["confidence"] for d in by_y) / max(1, len(by_y))
                            print(f"[ALPR OCR] Patente combinada (y-axis): {plate} (conf={avg_conf:.2f})")
                    except Exception:
                        pass

                if not plate and len(detections) >= 2:
                    try:
                        by_x = sorted(detections, key=lambda d: d["bbox"][0][0])
                        combined = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_x)
                        match = re.search(LATAM_PLATE_PATTERN, combined)
                        if match:
                            plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
                            avg_conf = sum(d["confidence"] for d in by_x) / max(1, len(by_x))
                            print(f"[ALPR OCR] Patente combinada (x-axis): {plate} (conf={avg_conf:.2f})")
                    except Exception:
                        pass

                if not plate:
                    continue

                country = ImagePreprocessor.identify_country(plate, is_mercosur)

                if len(plate) < 5 or len(plate) > 8 or not re.search(r'[A-Z]', plate) or not re.search(r'\d', plate):
                    print(f"[ALPR] Rechazada: '{plate}' (largo/formato inválido)")
                    continue

                print(f"[ALPR] Patente detectada: {plate} (Conf: {avg_conf:.2f}) [PaddleOCR] ({t_ocr:.2f}s OCR + {(time.time()-t_start-t_ocr):.2f}s post)")

                now = time.time()
                self.vote_buffer.append((plate, avg_conf, now))
                self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
                same_votes = [v for v in self.vote_buffer if v[0] == plate]

                is_moto = bool(MOTO_PATTERN.match(plate))

                if is_moto:
                    if avg_conf < MOTO_MIN_CONFIDENCE or len(same_votes) < CONSENSUS_REQUIRED:
                        print(f"[ALPR] Moto '{plate}' pendiente: conf={avg_conf:.2f} (min={MOTO_MIN_CONFIDENCE}) votos={len(same_votes)}/{CONSENSUS_REQUIRED}")
                        continue
                else:
                    if avg_conf < CONFIDENCE_THRESHOLD and len(same_votes) < CONSENSUS_REQUIRED:
                        continue

                try:
                    if 'ARGENTINA' in country.upper():
                        os.makedirs('alpr_debug', exist_ok=True)
                        debug_path = os.path.join('alpr_debug', f'accepted_plate_{GATE_ID}_{plate}_{int(time.time()*1000)}.jpg')
                        cv2.imwrite(debug_path, main_roi)
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
        """Evita duplicados con debounce y delega el envio HTTP al pool de hilos."""
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
        """Codifica el frame y envia la peticion HTTP al backend."""
        t_dispatch = time.time()
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
                elapsed = time.time() - t_dispatch
                if resp.ok:
                    msg = resp.json().get("message", "")
                    if "bienvenido" in msg.lower():
                        print(f"[OK] Ingreso: Bienvenido {data}! (backend: {elapsed:.2f}s)")
                    elif "hasta luego" in msg.lower() or "salida" in msg.lower():
                        print(f"[OK] Salida: Hasta luego {data}! (backend: {elapsed:.2f}s)")
                    else:
                        print(f"[OK] {msg} (backend: {elapsed:.2f}s)")
                else:
                    print(f"[ERROR] {resp.status_code}: {resp.text[:200]} (backend: {elapsed:.2f}s)")
            except Exception as re:
                elapsed = time.time() - t_dispatch
                print(f"[ALPR ERROR] Error enviando peticion al backend: {type(re).__name__} - {re} (backend: {elapsed:.2f}s)")
        except Exception as e:
            print(f"[ALPR ERROR] Error preparando/serializando frame: {type(e).__name__} - {e}")
