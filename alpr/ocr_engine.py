import cv2
import requests
import time
import os
import re
import base64
import queue
OCR_ENGINE_NAME = None
try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_ENGINE_NAME = "RapidOCR"
except ImportError:
    try:
        from paddleocr import PaddleOCR
        OCR_ENGINE_NAME = "PaddleOCR"
    except ImportError:
        OCR_ENGINE_NAME = None

if not OCR_ENGINE_NAME:
    print("[ALPR] WARNING: Ni rapidocr-onnxruntime ni paddleocr están instalados.")

from concurrent.futures import ThreadPoolExecutor
from alpr.config import (
    GATE_ID, GATE_TYPE, BACKEND_URL, COOLDOWN_SECONDS, OCR_INTERVAL,
    CONFIDENCE_THRESHOLD, FRAME_QUEUE_MAXSIZE, CONSENSUS_REQUIRED,
    CONSENSUS_WINDOW, LATAM_PLATE_PATTERN, MOTO_PATTERN, MOTO_MIN_CONFIDENCE
)
from alpr.preprocessor import ImagePreprocessor

class ALPREngine:
    """Motor principal de vision artificial: RapidOCR / PaddleOCR, QR, consenso y despacho de eventos."""

    def __init__(self):
        if OCR_ENGINE_NAME == "RapidOCR":
            self.engine_type = "RapidOCR"
            self.reader = RapidOCR()
        elif OCR_ENGINE_NAME == "PaddleOCR":
            self.engine_type = "PaddleOCR"
            self.reader = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False
            )
        else:
            raise RuntimeError("No hay un motor OCR instalado. Ejecuta: pip install rapidocr-onnxruntime")

        self.qr_detector = cv2.QRCodeDetector()
        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_MAXSIZE)
        self.vote_buffer = []
        self.last_validated_plate = ""
        self.last_validation_time = 0
        self.is_running = True
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.prev_gray = None

    def detect_motion(self, frame) -> bool:
        """Detecta variacion significativa entre frames consecutivos."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if self.prev_gray is None:
                self.prev_gray = gray
                return True
            diff = cv2.absdiff(self.prev_gray, gray)
            self.prev_gray = gray
            non_zero = cv2.countNonZero(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1])
            return non_zero > 1500
        except Exception:
            return True

    def _ocr_single_roi(self, roi_img):
        """Ejecuta OCR sobre una ROI recortada."""
        if roi_img is None or roi_img.size == 0:
            return [], [], []
        try:
            h, w = roi_img.shape[:2]
            if h < 80 and h > 0:
                scale = 80.0 / h
                roi_img = cv2.resize(roi_img, (int(w * scale), 80), interpolation=cv2.INTER_CUBIC)
            if self.engine_type == "RapidOCR":
                result, _ = self.reader(roi_img)
                if not result:
                    return [], [], []
                texts = [res[1] for res in result]
                scores = [float(res[2]) for res in result]
                polys = [res[0] for res in result]
                return texts, scores, polys
            elif self.engine_type == "PaddleOCR":
                result = self.reader.ocr(roi_img, cls=False)
                if not result or not result[0]:
                    return [], [], []
                texts = [line[1][0] for line in result[0]]
                scores = [float(line[1][1]) for line in result[0]]
                polys = [line[0] for line in result[0]]
                return texts, scores, polys
        except Exception as e:
            print(f"[ALPR OCR] Error {self.engine_type}: {type(e).__name__} - {e}")
            return [], [], []

    def ocr_worker(self):
        full_7_pattern = re.compile(
            r'[A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d[A-Z]\d{2}|[A-Z]{3}\d{4}|[A-Z]{4}\d{3}|\d{3}[A-Z]{4}|[A-Z]\d{3}[A-Z]{3}'
        )

        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=1)
                t_start = time.time()

                qr_data, _, _ = self.qr_detector.detectAndDecode(frame)
                if qr_data:
                    qr_text = qr_data[0] if isinstance(qr_data, (list, tuple)) and len(qr_data) > 0 else str(qr_data)
                    elapsed = time.time() - t_start
                    print(f"[ALPR] Código QR leído: {qr_text[:80]}")
                    self.send_event("qr", qr_text, frame, ocr_time=elapsed)
                    time.sleep(1)
                    continue

                h, w = frame.shape[:2]
                main_roi = frame[int(h*0.15):int(h*0.92), int(w*0.05):int(w*0.95)]

                texts, scores, polys = self._ocr_single_roi(main_roi)
                t_ocr = time.time() - t_start

                if not texts:
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
                        bbox = [[0,0],[10,0],[10,10],[0,10]]
                    detections.append({"text": t, "confidence": conf, "bbox": bbox})

                if not detections:
                    continue

                is_mercosur = ImagePreprocessor.is_mercosur_candidate(main_roi)

                plate = None
                avg_conf = 0.0

                # 1. PRIORIDAD 1: SI HAY MULTIPLES DETECCIONES (EJ: "AG 536 C" Y "R"), PROBAR COMBINARLAS PARA OBTENER 7 CARACTERES
                if len(detections) >= 2:
                    try:
                        by_x = sorted(detections, key=lambda d: d["bbox"][0][0])
                        combined_x = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_x)
                        match_7 = full_7_pattern.search(combined_x)
                        if match_7:
                            plate = match_7.group(0)
                            avg_conf = sum(d["confidence"] for d in by_x) / max(1, len(by_x))
                    except Exception:
                        pass

                # 2. PRIORIDAD 2: BUSCAR 7 CARACTERES COMPLETOS EN DETECCION UNICA
                if not plate:
                    for det in detections:
                        t = re.sub(r'[^A-Z0-9]', '', det["text"])
                        match_7 = full_7_pattern.search(t)
                        if match_7:
                            plate = match_7.group(0)
                            avg_conf = det["confidence"]
                            break

                # 3. PRIORIDAD 3: PATRON GENERAL / 6 CARACTERES
                if not plate:
                    for det in detections:
                        t = re.sub(r'[^A-Z0-9]', '', det["text"])
                        match_gen = re.search(LATAM_PLATE_PATTERN, t)
                        if match_gen:
                            plate = match_gen.group(0)
                            avg_conf = det["confidence"]
                            break

                if not plate and len(detections) >= 2:
                    try:
                        by_y = sorted(detections, key=lambda d: sum(p[1] for p in d["bbox"]) / max(1, len(d["bbox"])))
                        combined = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_y)
                        match = re.search(LATAM_PLATE_PATTERN, combined)
                        if match:
                            plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
                            avg_conf = sum(d["confidence"] for d in by_y) / max(1, len(by_y))
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
                    except Exception:
                        pass

                if not plate:
                    # FALLBACK PARA PATENTES IMPRESAS EN PAPEL / POSICIONES FUERA DE CENTRO
                    try:
                        candidates = ImagePreprocessor.find_plate_roi(frame)
                        for cand in candidates:
                            c_texts, c_scores, c_polys = self._ocr_single_roi(cand)
                            if not c_texts:
                                continue
                            for i, text in enumerate(c_texts):
                                t = re.sub(r'[^A-Z0-9]', '', text.strip().upper())
                                match = re.search(LATAM_PLATE_PATTERN, t)
                                if match:
                                    plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
                                    avg_conf = float(c_scores[i]) if i < len(c_scores) else 0.50
                                    break
                            if plate:
                                break
                    except Exception:
                        pass

                if not plate:
                    continue

                country = ImagePreprocessor.identify_country(plate, is_mercosur)

                if len(plate) < 5 or len(plate) > 8 or not re.search(r'[A-Z]', plate) or not re.search(r'\d', plate):
                    continue

                now = time.time()
                self.vote_buffer.append((plate, avg_conf, now))
                self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
                same_votes = [v for v in self.vote_buffer if v[0] == plate]

                is_moto = bool(MOTO_PATTERN.match(plate))
                is_valid_format = bool(re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$|^[A-Z]{3}\d{3}$|^[A-Z]{2}\d{3}[A-Z]$|^[A-Z]\d{3}[A-Z]{3}$|^[A-Z]{3}\d[A-Z]\d{2}$', plate))
                req_votes = 1 if (is_valid_format and avg_conf >= 0.40) else CONSENSUS_REQUIRED

                if is_moto:
                    if avg_conf < MOTO_MIN_CONFIDENCE and len(same_votes) < req_votes:
                        continue
                else:
                    if avg_conf < CONFIDENCE_THRESHOLD and len(same_votes) < req_votes:
                        continue

                try:
                    if 'ARGENTINA' in country.upper():
                        os.makedirs('alpr_debug', exist_ok=True)
                        debug_path = os.path.join('alpr_debug', f'accepted_plate_{GATE_ID}_{plate}_{int(time.time()*1000)}.jpg')
                        cv2.imwrite(debug_path, main_roi)
                except Exception:
                    pass

                print(f"[ALPR] Patente aceptada: {plate} [{country}] (Conf: {avg_conf:.2f})")
                self.send_event("plate", plate, frame, ocr_time=t_ocr)
                self.vote_buffer = []
                time.sleep(0.5)
                continue

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ALPR OCR] Exception en ocr_worker: {type(e).__name__} - {e}")

    def send_event(self, type, data, frame, ocr_time=None):
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
        self.executor.submit(self._dispatch_request, type, data, frame, ocr_time)

    def _dispatch_request(self, type, data, frame, ocr_time=None):
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
            if ocr_time is not None:
                payload["ocr_time"] = round(ocr_time, 3)
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
