import cv2
import re
import numpy as np
from alpr.config import FORCE_OCR, MOTION_THRESHOLD

class ImagePreprocessor:
    """Utilidades de procesamiento de imagen, detección de ROI y movimiento para ALPR."""

    @staticmethod
    def identify_country(plate: str, is_mercosur: bool) -> str:
        """Identifica el país probable basado en el formato y la franja azul (compatible con impresiones en papel B&N)."""
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', plate):
            return "ARGENTINA (Mercosur)"
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]$|^[A-Z]\d{3}[A-Z]{3}$|^[A-Z]\d{3}[A-Z]{2}$', plate):
            return "ARGENTINA (Moto Mercosur)"
        if re.match(r'^[A-Z]{3}\d{3}$', plate):
            return "ARGENTINA (Antigua)"
        if re.match(r'^[A-Z]{2}\d{3}$', plate):
            return "ARGENTINA (Moto Antigua)"
        if re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', plate):
            return "BRASIL"
        if re.match(r'^[A-Z]{3}\d{4}$', plate):
            return "URUGUAY"
        if re.match(r'^[A-Z]{4}\d{3}$|^\d{3}[A-Z]{4}$', plate):
            return "PARAGUAY"
        
        if is_mercosur:
            return "MERCOSUR (Otro)"
        return "DESCONOCIDO"

    @staticmethod
    def detect_motion(frame, prev_gray) -> tuple[bool, np.ndarray]:
        """Calcula si hay movimiento entre el frame actual y el anterior."""
        if FORCE_OCR:
            return True, prev_gray
        small = cv2.resize(frame, (320, 240))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if prev_gray is None:
            return True, gray
        frame_delta = cv2.absdiff(prev_gray, gray)
        motion_score = np.sum(cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]) / 255
        return motion_score > MOTION_THRESHOLD, gray

    @staticmethod
    def preprocess_for_screen(img) -> list:
        """Optimizado para quitar el efecto moiré y ruido de píxeles de pantallas."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LANCZOS4)
        
        # 1. Filtro de mediana
        gray = cv2.medianBlur(gray, 3)
        
        # 2. Aumento de contraste
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
        contrast = clahe.apply(gray)
        
        # 3. Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(contrast, -1, kernel)
        
        # 4. Umbralización adaptativa
        v2 = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 5)
        
        # 5. Inversión
        v2_inv = cv2.bitwise_not(v2)
        
        return [sharpened, v2, v2_inv]

    @staticmethod
    def _iou(b1, b2):
        x0 = max(b1[0], b2[0]); y0 = max(b1[1], b2[1])
        x1 = min(b1[2], b2[2]); y1 = min(b1[3], b2[3])
        inter = max(0, x1-x0) * max(0, y1-y0)
        a1 = (b1[2]-b1[0]) * (b1[3]-b1[1])
        a2 = (b2[2]-b2[0]) * (b2[3]-b2[1])
        union = a1 + a2 - inter
        return inter / union if union > 0 else 0

    @staticmethod
    def _is_valid_plate_roi(crop, frame_w, frame_h):
        ch, cw = crop.shape[:2]
        if cw < 80 or ch < 20:
            return False
        if cw > frame_w * 0.85:
            return False
        aspect = cw / max(ch, 1)
        return 1.5 <= aspect <= 8.0

    @staticmethod
    def find_plate_roi(frame, plate_cascade=None) -> list:
        """Encuentra regiones de interés donde puede ubicarse una patente."""
        h, w = frame.shape[:2]
        main_roi = frame[int(h*0.15):int(h*0.92), int(w*0.05):int(w*0.95)]
        rh, rw = main_roi.shape[:2]
        gray = cv2.cvtColor(main_roi, cv2.COLOR_BGR2GRAY)

        raw_boxes = []

        strip_configs = [
            (0.55, 0.75, "strip_bottom"),
            (0.30, 0.50, "strip_center"),
        ]
        SEGMENT_W = 320
        for y_pct0, y_pct1, tag in strip_configs:
            sy0, sy1 = int(rh*y_pct0), int(rh*y_pct1)
            strip_h = sy1 - sy0
            if strip_h < 20:
                continue
            n_segs = max(1, (rw + SEGMENT_W - 1) // SEGMENT_W)
            seg_w = rw // n_segs
            for i in range(n_segs):
                sx0 = i * seg_w
                sx1 = min(rw, sx0 + seg_w)
                raw_boxes.append((sx0, sy0, sx1, sy1, tag))

        try:
            blur = cv2.bilateralFilter(gray, 9, 75, 75)
            edged = cv2.Canny(blur, 50, 200)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
            closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < (rw * rh) * 0.001:
                    continue
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect = (cw / float(ch)) if ch > 0 else 0
                if not (1.5 <= aspect <= 8.0 and cw > rw * 0.08):
                    continue
                pad_x, pad_y = int(cw * 0.10), int(ch * 0.25)
                bx0 = max(0, x-pad_x); by0 = max(0, y-pad_y)
                bx1 = min(rw, x+cw+pad_x); by1 = min(rh, y+ch+pad_y)
                raw_boxes.append((bx0, by0, bx1, by1, "contour"))
        except Exception:
            pass

        priority = {"contour": 0, "strip_center": 1, "strip_bottom": 2}
        raw_boxes.sort(key=lambda b: (priority.get(b[4], 9), -(b[2]-b[0])*(b[3]-b[1])))

        merged = []
        for box in raw_boxes[:20]:
            b = box[:4]
            crop = main_roi[b[1]:b[3], b[0]:b[2]]
            if not ImagePreprocessor._is_valid_plate_roi(crop, rw, rh):
                continue
            skip = False
            for existing in merged:
                if ImagePreprocessor._iou(b, existing) > 0.4:
                    skip = True
                    break
            if not skip:
                merged.append(b)
                if len(merged) >= 10:
                    break

        candidates = [main_roi[b[1]:b[3], b[0]:b[2]] for b in merged]
        if not candidates:
            candidates.append(main_roi)

        return candidates

    @staticmethod
    def is_mercosur_candidate(roi) -> bool:
        """Detecta si un ROI tiene la franja azul característica del MERCOSUR (adaptado para papel e impresiones)."""
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([90, 40, 40])
            upper_blue = np.array([135, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            h, w = mask.shape[:2]
            top_strip = mask[0:int(h*0.35), :]
            blue_ratio = np.sum(top_strip > 0) / max(1, top_strip.size)
            return blue_ratio > 0.06
        except Exception:
            return False

    @staticmethod
    def crop_below_blue(roi):
        """Recorta por debajo de la franja azul MERCOSUR si está presente."""
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([90, 40, 40])
            upper_blue = np.array([135, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            h, w = mask.shape[:2]
            top_mask = mask[0:int(h*0.5), :]
            if np.sum(top_mask) == 0:
                return roi
            ys, xs = np.where(top_mask > 0)
            if len(ys) == 0:
                return roi
            y_max = int(np.max(ys))
            new_y0 = min(h-1, int((y_max + 5)))
            if y_max > int(h*0.45):
                return roi
            cropped = roi[new_y0: , :]
            if cropped.shape[0] < int(h*0.25):
                return roi
            return cropped
        except Exception:
            return roi
