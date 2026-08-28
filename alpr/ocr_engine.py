import cv2
import requests
import time
import os
import re
import base64
import queue
import threading
import numpy as np
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

class ReadingStatusNotifier:
    """NOTIFICA AL BACKEND QUE LA CAMARA ESTA LEYENDO ACTIVAMENTE UNA PATENTE.
    Con debounce para no spamear (max 1 cada INTERVALO s) y en hilo aparte
    para no bloquear el bucle de captura de frames del runner."""

    def __init__(self, interval: float = 1.5):
        self.interval = interval
        self._last_notify = 0.0

    def notify_reading(self):
        now = time.time()
        if now - self._last_notify < self.interval:
            return
        self._last_notify = now
        threading.Thread(target=self._fire, daemon=True).start()

    def _fire(self):
        try:
            requests.post(f"{BACKEND_URL}/v1/system/camera-reading/{GATE_ID}", timeout=0.8)
        except Exception:
            pass

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
        self.active_detections = []
        self.last_detection_time = 0
        self.accepted_event = None

    def flush_queue(self):
        """Descarta todos los frames obsoletos acumulados en la cola de escaneo."""
        try:
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except Exception:
                    break
        except Exception:
            pass

    def detect_motion(self, frame) -> bool:
        """Detecta variacion significativa entre frames consecutivos en la zona de patente."""
        try:
            h, w = frame.shape[:2]
            roi = frame[int(h*0.25):int(h*0.85), int(w*0.10):int(w*0.90)]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if self.prev_gray is None:
                self.prev_gray = gray
                return True
            diff = cv2.absdiff(self.prev_gray, gray)
            self.prev_gray = gray
            non_zero = cv2.countNonZero(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1])
            return non_zero > 800
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
            r'[A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d[A-Z]\d{2}|[A-Z]{3}\d{4}|[A-Z]{4}\d{3}|[A-Z]\d{3}[A-Z]{3}'
        )
        HEADER_NOISE_WORDS = re.compile(
            r'\b(REPUBLICA|ARGENTINA|MERCOSUR|BRASIL|URUGUAY|PARAGUAY|GENTINA|TINA|REPU|MERCO|SUR)\b',
            re.IGNORECASE
        )

        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=1)
                t_start = time.time()

                # Descarte de frames en negro / tapados
                gray_check = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if cv2.mean(gray_check)[0] < 12:
                    self.vote_buffer = []
                    continue

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

                is_mercosur = ImagePreprocessor.is_mercosur_candidate(main_roi)
                if is_mercosur:
                    main_roi = ImagePreprocessor.crop_below_blue(main_roi)

                texts, scores, polys = self._ocr_single_roi(main_roi)
                t_ocr = time.time() - t_start

                if not texts:
                    continue

                detections = []
                for i, text in enumerate(texts):
                    t = text.strip()
                    if not t or len(t) < 2:
                        continue
                    # Limpiar texto del borde/cabecera (ej: ARGENTINA, REPUBLICA, TINA)
                    clean_header_text = HEADER_NOISE_WORDS.sub('', t.upper()).strip()
                    if not clean_header_text or len(clean_header_text) < 2:
                        continue
                    conf = float(scores[i]) if i < len(scores) else 0.0
                    if i < len(polys):
                        bbox = [[int(p[0]), int(p[1])] for p in polys[i]]
                    else:
                        bbox = [[0,0],[10,0],[10,10],[0,10]]
                    detections.append({"text": clean_header_text, "confidence": conf, "bbox": bbox})

                if not detections:
                    continue

                self.active_detections = detections
                self.last_detection_time = time.time()

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
                    # Se exige confianza más alta (0.65) ya que estas son detecciones
                    # de menor calidad obtenidas por caza de contornos.
                    FALLBACK_MIN_CONFIDENCE = 0.65
                    try:
                        candidates = ImagePreprocessor.find_plate_roi(frame)
                        for cand in candidates:
                            c_texts, c_scores, c_polys = self._ocr_single_roi(cand)
                            if not c_texts:
                                continue
                            for i, text in enumerate(c_texts):
                                t = re.sub(r'[^A-Z0-9]', '', text.strip().upper())
                                match = re.search(LATAM_PLATE_PATTERN, t)
                                c_conf = float(c_scores[i]) if i < len(c_scores) else 0.0
                                if match and c_conf >= FALLBACK_MIN_CONFIDENCE:
                                    plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
                                    avg_conf = c_conf
                                    break
                            if plate:
                                break
                    except Exception:
                        pass

                if not plate:
                    continue

                country = ImagePreprocessor.identify_country(plate, is_mercosur)

                KNOWN_PLATE_FORMATS = re.compile(
                    r'^[A-Z]{2}\d{3}[A-Z]{2}$'   # ARG Mercosur (AA 123 AA)
                    r'|^[A-Z]{3}\d{3}$'            # ARG Antigua (ABC 123)
                    r'|^[A-Z]{2}\d{3}$'            # ARG Moto Antigua (AB 123)
                    r'|^[A-Z]{2}\d{3}[A-Z]$'       # ARG Moto Mercosur (AB 123 A)
                    r'|^[A-Z]\d{3}[A-Z]{3}$'       # ARG Moto Mercosur alternativo (A 123 AAA)
                    r'|^[A-Z]{3}\d[A-Z]\d{2}$'     # Brasil (ABC 1D23)
                    r'|^[A-Z]{3}\d{4}$'            # Uruguay (ABC 1234)
                    r'|^[A-Z]{4}\d{3}$'            # Paraguay Auto Mercosur (ABCD 123)
                )
                if not KNOWN_PLATE_FORMATS.match(plate):
                    continue

                now = time.time()
                self.vote_buffer.append((plate, avg_conf, now))
                self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
                same_votes = [v for v in self.vote_buffer if v[0] == plate]

                is_moto = bool(MOTO_PATTERN.match(plate))
                is_valid_format = bool(re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$|^[A-Z]{3}\d{3}$|^[A-Z]{2}\d{3}[A-Z]$|^[A-Z]\d{3}[A-Z]{3}$|^[A-Z]{3}\d[A-Z]\d{2}$|^[A-Z]{4}\d{3}$', plate))

                if detections:
                    det = detections[0]
                    xs = [p[0] for p in det["bbox"]]
                    ys = [p[1] for p in det["bbox"]]
                    bbox_w = max(xs) - min(xs)
                    bbox_h = max(ys) - min(ys)
                    if bbox_h > 0:
                        aspect = bbox_w / bbox_h
                        # Si coincide con patrón de moto (ej: AC404) pero la caja es rectangular horizontal de auto (> 2.2), es un recorte incompleto.
                        if is_moto and aspect > 2.2:
                            continue

                if is_moto:
                    high_conf = avg_conf >= MOTO_MIN_CONFIDENCE
                else:
                    high_conf = avg_conf >= 0.75

                if high_conf and is_valid_format:
                    req_votes = 1
                else:
                    req_votes = max(2, CONSENSUS_REQUIRED)

                if len(same_votes) < req_votes:
                    continue

                try:
                    if 'ARGENTINA' in country.upper():
                        os.makedirs('alpr_debug', exist_ok=True)
                        debug_path = os.path.join('alpr_debug', f'accepted_plate_{GATE_ID}_{plate}_{int(time.time()*1000)}.jpg')
                        cv2.imwrite(debug_path, main_roi)
                except Exception:
                    pass

                print(f"[ALPR] Patente aceptada: {plate} [{country}] (Conf: {avg_conf:.2f})")
                self.accepted_event = {
                    "plate": plate,
                    "country": country,
                    "conf": avg_conf,
                    "time": time.time()
                }
                self.send_event("plate", plate, frame, ocr_time=t_ocr)
                self.vote_buffer = []
                self.active_detections = []
                self.flush_queue()

                # Vaciado activo de la cola durante el cooldown de 5 segundos
                for _ in range(10):
                    time.sleep(0.5)
                    self.flush_queue()
                continue

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ALPR OCR] Exception en ocr_worker: {type(e).__name__} - {e}")

    def get_frame_with_overlay(self, frame):
        """Superpone bounding boxes, HUD de OCR y banner de confirmacion sobre el frame para el streaming."""
        if frame is None:
            return frame
        
        now = time.time()
        active_dets = self.active_detections if (now - self.last_detection_time <= 1.5) else []
        accepted_ev = self.accepted_event if (self.accepted_event and (now - self.accepted_event.get("time", 0) <= 3.0)) else None

        if not active_dets and not accepted_ev:
            return frame

        return self.draw_overlay(frame, active_detections=active_dets, accepted_event=accepted_ev)

    @staticmethod
    def draw_overlay(frame, active_detections=None, accepted_event=None):
        """Dibuja recuadros verde neon, esquinas HUD CCTV y etiqueta de texto sobre el frame."""
        if frame is None:
            return frame

        out_frame = frame.copy()
        h, w = out_frame.shape[:2]
        roi_offset_x = int(w * 0.05)
        roi_offset_y = int(h * 0.15)

        if active_detections:
            for det in active_detections:
                raw_bbox = det.get("bbox", [])
                text = det.get("text", "")
                conf = det.get("confidence", 0.0)

                if not raw_bbox or len(raw_bbox) < 4:
                    continue

                pts = []
                for p in raw_bbox:
                    px = int(p[0] + roi_offset_x)
                    py = int(p[1] + roi_offset_y)
                    pts.append([px, py])

                pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))

                # Caja principal (Verde Neón)
                cv2.polylines(out_frame, [pts_arr], isClosed=True, color=(0, 255, 127), thickness=2)

                min_x = max(0, min(p[0] for p in pts))
                max_x = min(w - 1, max(p[0] for p in pts))
                min_y = max(0, min(p[1] for p in pts))
                max_y = min(h - 1, max(p[1] for p in pts))
                corner_len = max(6, int((max_x - min_x) * 0.2))

                # Esquinas estilo HUD CCTV (Amarillo Dorado)
                hud_color = (0, 215, 255)
                # Top-Left
                cv2.line(out_frame, (min_x, min_y), (min_x + corner_len, min_y), hud_color, 2)
                cv2.line(out_frame, (min_x, min_y), (min_x, min_y + corner_len), hud_color, 2)
                # Top-Right
                cv2.line(out_frame, (max_x, min_y), (max_x - corner_len, min_y), hud_color, 2)
                cv2.line(out_frame, (max_x, min_y), (max_x, min_y + corner_len), hud_color, 2)
                # Bottom-Left
                cv2.line(out_frame, (min_x, max_y), (min_x + corner_len, max_y), hud_color, 2)
                cv2.line(out_frame, (min_x, max_y), (min_x, max_y + corner_len), hud_color, 2)
                # Bottom-Right
                cv2.line(out_frame, (max_x, max_y), (max_x - corner_len, max_y), hud_color, 2)
                cv2.line(out_frame, (max_x, max_y), (max_x, max_y - corner_len), hud_color, 2)

                # Banner de información de la patente arriba de la caja
                clean_text = re.sub(r'[^A-Z0-9]', '', text)
                if len(clean_text) >= 3:
                    label = f"{clean_text} ({int(conf * 100)}%)"
                    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    label_y = max(min_y - 6, text_h + 6)

                    # Fondo translúcido oscuro
                    cv2.rectangle(out_frame, (min_x, label_y - text_h - 4), (min_x + text_w + 6, label_y + 4), (15, 23, 42), -1)
                    cv2.rectangle(out_frame, (min_x, label_y - text_h - 4), (min_x + text_w + 6, label_y + 4), (0, 255, 127), 1)
                    cv2.putText(out_frame, label, (min_x + 3, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        if accepted_event and (time.time() - accepted_event.get("time", 0) <= 3.0):
            plate = accepted_event.get("plate", "")
            country = accepted_event.get("country", "")
            conf = accepted_event.get("conf", 0.0)

            banner_h = 38
            overlay_sub = out_frame.copy()
            cv2.rectangle(overlay_sub, (0, 0), (w, banner_h), (16, 185, 129), -1)
            cv2.addWeighted(overlay_sub, 0.85, out_frame, 0.15, 0, out_frame)

            msg = f"[OK] LECTURA CONFIRMADA: {plate} [{country}] ({int(conf * 100)}%)"
            cv2.putText(out_frame, msg, (12, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        return out_frame

    @staticmethod
    def _plate_close(a: str, b: str, max_dist: int = 1) -> bool:
        """Compara dos patentes normalizadas, permitiendo hasta max_dist caracteres de diferencia o coincidencia de bloque numérico."""
        if a == b:
            return True
        # Si comparten los mismos 3+ dígitos (ej: NVZ087 vs VZ087AR vs TINA087), es una variante/alucinación en la misma escena
        digits_a = re.sub(r'\D', '', a)
        digits_b = re.sub(r'\D', '', b)
        if len(digits_a) >= 3 and digits_a == digits_b:
            return True
        if len(a) != len(b) or abs(len(a) - len(b)) > max_dist:
            return False
        diff = sum(1 for x, y in zip(a, b) if x != y)
        return diff <= max_dist

    def send_event(self, type, data, frame, ocr_time=None):
        """Evita duplicados con debounce y delega el envio HTTP al pool de hilos."""
        try:
            key = re.sub(r'[^A-Z0-9]', '', str(data)).upper()
            now = time.time()
            last_key = re.sub(r'[^A-Z0-9]', '', self.last_validated_plate).upper()
            elapsed = now - getattr(self, 'last_validation_time', 0)
            if elapsed < COOLDOWN_SECONDS and self._plate_close(key, last_key):
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
