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
OCR_ENGINE_ERROR = None
try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_ENGINE_NAME = "RapidOCR"
except Exception as _e_rapid:
    OCR_ENGINE_ERROR = f"rapidocr-onnxruntime: {type(_e_rapid).__name__}: {_e_rapid}"
    try:
        from paddleocr import PaddleOCR
        OCR_ENGINE_NAME = "PaddleOCR"
    except Exception as _e_paddle:
        OCR_ENGINE_ERROR = f"{OCR_ENGINE_ERROR} ; paddleocr: {type(_e_paddle).__name__}: {_e_paddle}"

if not OCR_ENGINE_NAME:
    print(f"[ALPR] WARNING: Ni rapidocr-onnxruntime ni paddleocr están disponibles. ({OCR_ENGINE_ERROR})")

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
    GATE_ID, GATE_TYPE, BACKEND_URL, ALPR_NODE_SECRET, COOLDOWN_SECONDS,
    CONFIDENCE_THRESHOLD, FRAME_QUEUE_MAXSIZE, CONSENSUS_REQUIRED,
    CONSENSUS_WINDOW, LATAM_PLATE_PATTERN, MOTO_PATTERN, MOTO_MIN_CONFIDENCE,
    ENABLE_MOTO_RECOGNITION
)
from alpr.preprocessor import ImagePreprocessor

MAPA_LETRAS = {'0': 'O', '1': 'I', '2': 'Z', '4': 'A', '5': 'S', '6': 'G', '8': 'B'}
MAPA_DIGITOS = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'A': '4', 'S': '5', 'G': '6', 'B': '8'}

def CorregirLetra(caracter: str) -> str:
    """REEMPLAZA DIGITOS COMUNES POR SUS LETRAS EQUIVALENTES EN POSICIONES ALFABETICAS."""
    return MAPA_LETRAS.get(caracter, caracter)

def CorregirDigito(caracter: str) -> str:
    """REEMPLAZA LETRAS COMUNES POR SUS DIGITOS EQUIVALENTES EN POSICIONES NUMERICAS."""
    return MAPA_DIGITOS.get(caracter, caracter)

def CorregirPatente(texto: str) -> str:
    """APLICA DESAMBIGUACION POSICIONAL DE CARACTERES PARA FORMATOS MERCOSUR Y CLASICOS."""
    if not texto:
        return ""
    t = re.sub(r'[^A-Z0-9]', '', texto.upper())

    # REMOVER MARCAS DE AGUA Y TEXTOS DE ENCABEZADO NACIONALES
    t = re.sub(r'^(ARGENTINA|REPUBLICA|MERCOSUR|BRASIL|URUGUAY|PARAGUAY|TINA|IINA)+', '', t)
    t = re.sub(r'(ARGENTINA|MERCOSUR|AR)$', '', t)

    # 1. SI YA CUMPLE CON UN FORMATO ESTRICTO DE 6 O 7 CARACTERES, SE RETORNA DIRECTAMENTE
    patron_estricto = (
        r'^[A-Z]{2}\d{3}[A-Z]{2}$|'
        r'^[A-Z]{3}\d{3}$|'
        r'^[A-Z]{3}\d[A-Z]\d{2}$' if not ENABLE_MOTO_RECOGNITION else
        r'^[A-Z]{2}\d{3}[A-Z]{2}$|'
        r'^[A-Z]{3}\d{3}$|'
        r'^[A-Z]\d{3}[A-Z]{3}$|'
        r'^\d{3}[A-Z]{3}$|'
        r'^[A-Z]{3}\d[A-Z]\d{2}$'
    )
    if re.match(patron_estricto, t):
        return t

    if len(t) == 7:
        # 1. MOTO MERCOSUR ARGENTINA: A NNN LLL (EJ: A012BCD, AO12BCD)
        if t[0] == 'A' and (t[4:].isalpha() or (t[5].isalpha() and t[6].isalpha())) and (t[1].isdigit() or t[1] in ('O', 'Q', 'D', 'I', 'L', 'Z', 'S')):
            cand_moto = (
                'A' +
                CorregirDigito(t[1]) + CorregirDigito(t[2]) + CorregirDigito(t[3]) +
                CorregirLetra(t[4]) + CorregirLetra(t[5]) + CorregirLetra(t[6])
            )
            if re.match(r'^[A-Z]\d{3}[A-Z]{3}$', cand_moto):
                return cand_moto

        # 2. AUTO MERCOSUR ARGENTINA: LL NNN LL (EJ: AA123BB, AAI23BB, AA12OBB)
        cand_auto = (
            CorregirLetra(t[0]) + CorregirLetra(t[1]) +
            CorregirDigito(t[2]) + CorregirDigito(t[3]) + CorregirDigito(t[4]) +
            CorregirLetra(t[5]) + CorregirLetra(t[6])
        )
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', cand_auto):
            return cand_auto

        # 3. MOTO MERCOSUR ARGENTINA GENERAL
        cand_moto = (
            CorregirLetra(t[0]) +
            CorregirDigito(t[1]) + CorregirDigito(t[2]) + CorregirDigito(t[3]) +
            CorregirLetra(t[4]) + CorregirLetra(t[5]) + CorregirLetra(t[6])
        )
        if re.match(r'^[A-Z]\d{3}[A-Z]{3}$', cand_moto):
            return cand_moto

        # 4. AUTO BRASIL MERCOSUR: LLL N L NN (EJ: ABC1D23)
        cand_br = (
            CorregirLetra(t[0]) + CorregirLetra(t[1]) + CorregirLetra(t[2]) +
            CorregirDigito(t[3]) +
            CorregirLetra(t[4]) +
            CorregirDigito(t[5]) + CorregirDigito(t[6])
        )
        if re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', cand_br):
            return cand_br

    elif len(t) == 6:
        # 1. AUTO CLASICO ARGENTINO: LLL NNN (ULTIMOS 3 SON DIGITOS / LETRAS AL INICIO)
        if t[4].isdigit() or t[5].isdigit() or (t[1].isalpha() and t[2].isalpha()):
            cand_auto_old = (
                CorregirLetra(t[0]) + CorregirLetra(t[1]) + CorregirLetra(t[2]) +
                CorregirDigito(t[3]) + CorregirDigito(t[4]) + CorregirDigito(t[5])
            )
            if re.match(r'^[A-Z]{3}\d{3}$', cand_auto_old):
                return cand_auto_old

        # 2. MOTO CLASICA ARGENTINA: NNN LLL (ULTIMOS 3 SON LETRAS / DIGITOS AL INICIO)
        if t[4].isalpha() or t[5].isalpha() or (t[1].isdigit() and t[2].isdigit()):
            cand_moto_old = (
                CorregirDigito(t[0]) + CorregirDigito(t[1]) + CorregirDigito(t[2]) +
                CorregirLetra(t[3]) + CorregirLetra(t[4]) + CorregirLetra(t[5])
            )
            if re.match(r'^\d{3}[A-Z]{3}$', cand_moto_old):
                return cand_moto_old

    return t

class ALPREngine:
    """Motor principal de vision artificial: RapidOCR / PaddleOCR, QR, consenso y despacho de eventos."""

    def __init__(self):
        self.reader = None
        self.engine_type = None
        self.ocr_error = OCR_ENGINE_ERROR or "No hay un motor OCR instalado. Ejecuta: pip install rapidocr-onnxruntime"
        if OCR_ENGINE_NAME == "RapidOCR":
            try:
                self.reader = RapidOCR()
                self.engine_type = "RapidOCR"
                self.ocr_error = None
            except Exception as e:
                self.ocr_error = f"RapidOCR: {type(e).__name__}: {e}"
        elif OCR_ENGINE_NAME == "PaddleOCR":
            try:
                self.reader = PaddleOCR(
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False
                )
                self.engine_type = "PaddleOCR"
                self.ocr_error = None
            except Exception as e:
                self.ocr_error = f"PaddleOCR: {type(e).__name__}: {e}"

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
        if self.reader is None or self.engine_type is None:
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
        if self.reader is None:
            print(f"[ALPR OCR] MOTOR NO DISPONIBLE: {self.ocr_error or 'ningún motor OCR importable'}")
            return
        full_7_pattern = re.compile(
            r'[A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d[A-Z]\d{2}|[A-Z]{3}\d{4}|[A-Z]{4}\d{3}|\d{3}[A-Z]{4}|[A-Z]\d{3}[A-Z]{3}'
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

                # 1. PRIORIDAD 1: BUSCAR SI ALGUNA DETECCION INDIVIDUAL CONTIENE UNA PATENTE COMPLETA
                # (EVITA CONCATENAR INDEBIDAMENTE CON TEXTOS DE FONDO O MARCAS DE AGUA)
                for det in detections:
                    t = re.sub(r'[^A-Z0-9]', '', det["text"].upper())
                    t_corr = CorregirPatente(t)
                    if full_7_pattern.search(t_corr):
                        plate = full_7_pattern.search(t_corr).group(0)
                        avg_conf = det["confidence"]
                        break
                    match_6 = re.search(r'^[A-Z]{3}\d{3}$|^\d{3}[A-Z]{3}$', t_corr)
                    if match_6:
                        plate = match_6.group(0)
                        avg_conf = det["confidence"]
                        break

                # 2. PRIORIDAD 2: SI NINGUNA DETECCION INDIVIDUAL FUE COMPLETA, PROBAR COMBINAR FRAGMENTOS
                if not plate and len(detections) >= 2:
                    try:
                        by_x = sorted(detections, key=lambda d: d["bbox"][0][0])
                        combined_x = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_x)
                        corrected_x = CorregirPatente(combined_x)
                        match_7 = full_7_pattern.search(corrected_x) or re.search(LATAM_PLATE_PATTERN, corrected_x)
                        if match_7:
                            plate = match_7.group(0)
                            avg_conf = sum(d["confidence"] for d in by_x) / max(1, len(by_x))
                    except Exception:
                        pass

                # 3. PRIORIDAD 3: FALLBACK PATRON GENERAL EN DETECCION UNICA
                if not plate:
                    for det in detections:
                        t = re.sub(r'[^A-Z0-9]', '', det["text"])
                        t_corr = CorregirPatente(t)
                        match_gen = re.search(LATAM_PLATE_PATTERN, t_corr)
                        if match_gen:
                            plate = match_gen.group(0)
                            avg_conf = det["confidence"]
                            break

                if not plate and len(detections) >= 2:
                    try:
                        by_y = sorted(detections, key=lambda d: sum(p[1] for p in d["bbox"]) / max(1, len(d["bbox"])))
                        combined = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_y)
                        corrected_y = CorregirPatente(combined)
                        match = re.search(LATAM_PLATE_PATTERN, corrected_y)
                        if match:
                            plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
                            avg_conf = sum(d["confidence"] for d in by_y) / max(1, len(by_y))
                    except Exception:
                        pass

                if not plate and len(detections) >= 2:
                    try:
                        by_x = sorted(detections, key=lambda d: d["bbox"][0][0])
                        combined = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_x)
                        corrected_x2 = CorregirPatente(combined)
                        match = re.search(LATAM_PLATE_PATTERN, corrected_x2)
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
                            c_texts, c_scores, _ = self._ocr_single_roi(cand)
                            if not c_texts:
                                continue
                            for i, text in enumerate(c_texts):
                                t = re.sub(r'[^A-Z0-9]', '', text.strip().upper())
                                t_corr = CorregirPatente(t)
                                match = re.search(LATAM_PLATE_PATTERN, t_corr)
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

                # EXIGIR ESTRICTAMENTE 6 O 7 CARACTERES Y COMBINACION LETRA-NUMERO
                if len(plate) < 6 or len(plate) > 7 or not re.search(r'[A-Z]', plate) or not re.search(r'\d', plate):
                    continue

                now = time.time()
                self.vote_buffer.append((plate, avg_conf, now))
                self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
                same_votes = [v for v in self.vote_buffer if v[0] == plate]

                is_moto = bool(MOTO_PATTERN.match(plate))

                # SI LA REGLA DE MOTOS ESTA DESHABILITADA, DESCARTAR DETECCIONES DE MOTOS
                if not ENABLE_MOTO_RECOGNITION and is_moto:
                    continue

                # Filtro de aspecto: un recorte incompleto de auto que coincida con patrón de moto
                # (ej: AC404 de AC404SD) con caja horizontal (> 2.2) es un recorte incompleto.
                if is_moto and detections:
                    det = detections[0]
                    xs = [p[0] for p in det["bbox"]]
                    ys = [p[1] for p in det["bbox"]]
                    bbox_w = max(xs) - min(xs)
                    bbox_h = max(ys) - min(ys)
                    if bbox_h > 0 and (bbox_w / bbox_h) > 2.2:
                        continue

                is_valid_format = bool(re.match(
                    r'^[A-Z]{2}\d{3}[A-Z]{2}$|'
                    r'^[A-Z]{3}\d{3}$|'
                    r'^[A-Z]{3}\d[A-Z]\d{2}$|'
                    r'^[A-Z]{3}\d{4}$|'
                    r'^[A-Z]{4}\d{3}$' if not ENABLE_MOTO_RECOGNITION else
                    r'^[A-Z]{2}\d{3}[A-Z]{2}$|'
                    r'^[A-Z]{3}\d{3}$|'
                    r'^[A-Z]{3}\d[A-Z]\d{2}$|'
                    r'^[A-Z]{3}\d{4}$|'
                    r'^[A-Z]{4}\d{3}$|'
                    r'^[A-Z]{2}\d{3}$|'
                    r'^[A-Z]{2}\d{3}[A-Z]$|'
                    r'^[A-Z]\d{3}[A-Z]{3}$|'
                    r'^\d{3}[A-Z]{3}$|'
                    r'^\d{3}[A-Z]{4}$',
                    plate
                ))

                if not is_valid_format:
                    continue

                # EXIGIR CONSENSO MINIMO PARA EVITAR QUE UN SOLO FOTOGRAMA CON RUIDO DE OCR GENERE INGRESOS
                req_votes = CONSENSUS_REQUIRED
                if is_moto:
                    if avg_conf < MOTO_MIN_CONFIDENCE or len(same_votes) < req_votes:
                        continue
                else:
                    if avg_conf < CONFIDENCE_THRESHOLD or len(same_votes) < req_votes:
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
                resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=5,
                                     headers={"X-Node-Secret": ALPR_NODE_SECRET} if ALPR_NODE_SECRET else None)
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
