import cv2
import re
import numpy as np
from alpr.config import FORCE_OCR, MOTION_THRESHOLD

class ImagePreprocessor:
    """Utilidades de procesamiento de imagen, detección de ROI y movimiento para ALPR."""

    @staticmethod
    def identify_country(plate: str, is_mercosur: bool) -> str:
        """Identifica el país probable basado en el formato y la franja azul."""
        if not is_mercosur:
            if re.match(r'^[A-Z]{3}\d{3}$', plate):
                return "ARGENTINA (Antigua)"
            return "DESCONOCIDO"
        
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', plate):
            return "ARGENTINA (Mercosur)"
        if re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', plate):
            return "BRASIL"
        if re.match(r'^[A-Z]{3}\d{4}$', plate):
            return "URUGUAY"
        if re.match(r'^[A-Z]{4}\d{3}$|^\d{3}[A-Z]{4}$', plate):
            return "PARAGUAY"
        
        return "MERCOSUR (Otro)"

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
    def find_plate_roi(frame, plate_cascade) -> list:
        """Encuentra regiones de interés (ROI) donde puede ubicarse una patente."""
        h, w = frame.shape[:2]
        main_roi = frame[int(h*0.1):int(h*0.9), int(w*0.05):int(w*0.95)]
        rh, rw = main_roi.shape[:2]
        gray = cv2.cvtColor(main_roi, cv2.COLOR_BGR2GRAY)
        
        candidates = []
        seen_boxes = set()

        # 1) Cascada Haar
        try:
            plates = plate_cascade.detectMultiScale(gray, 1.1, 4)
        except Exception:
            plates = []

        for (x, y, pw, ph) in plates:
            pad_w = int(pw*0.15)
            pad_h = int(ph*0.2)
            x0 = max(0, x-pad_w); y0 = max(0, y-pad_h)
            x1 = min(rw, x+pw+pad_w); y1 = min(rh, y+ph+pad_h)
            box = (x0, y0, x1, y1)
            if box not in seen_boxes:
                candidates.append(main_roi[y0:y1, x0:x1])
                seen_boxes.add(box)

        # 2) Franjas útiles
        try:
            bottom_strip = main_roi[int(rh*0.55):int(rh*0.95), :]
            cbox = (0, int(rh*0.55), rw, int(rh*0.95))
            if cbox not in seen_boxes:
                candidates.append(bottom_strip)
                seen_boxes.add(cbox)
        except Exception:
            pass

        try:
            central_strip = main_roi[int(rh*0.3):int(rh*0.7), :]
            cbox = (0, int(rh*0.3), rw, int(rh*0.7))
            if cbox not in seen_boxes:
                candidates.append(central_strip)
                seen_boxes.add(cbox)
        except Exception:
            pass

        # 3) Detección basada en contornos
        try:
            blur = cv2.bilateralFilter(gray, 9, 75, 75)
            edged = cv2.Canny(blur, 50, 200)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,3))
            closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < (rw*rh)*0.001:
                    continue
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect = (cw / float(ch)) if ch > 0 else 0
                if 0.6 <= aspect <= 6.0 and cw > rw*0.12:
                    pad_x = int(cw * 0.12)
                    pad_y = int(ch * 0.25)
                    x0 = max(0, x-pad_x); y0 = max(0, y-pad_y)
                    x1 = min(rw, x+cw+pad_x); y1 = min(rh, y+ch+pad_y)
                    box = (x0, y0, x1, y1)
                    if box not in seen_boxes:
                        candidates.append(main_roi[y0:y1, x0:x1])
                        seen_boxes.add(box)
        except Exception:
            pass

        if not candidates:
            candidates.append(main_roi)

        return candidates

    @staticmethod
    def is_mercosur_candidate(roi) -> bool:
        """Detecta si un ROI tiene la franja azul característica del MERCOSUR."""
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([100, 100, 50])
            upper_blue = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            h, w = mask.shape[:2]
            top_strip = mask[0:int(h*0.3), :]
            blue_ratio = np.sum(top_strip > 0) / top_strip.size
            return blue_ratio > 0.1
        except Exception:
            return False

    @staticmethod
    def crop_below_blue(roi):
        """Recorta por debajo de la franja azul MERCOSUR si está presente."""
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([100, 80, 50])
            upper_blue = np.array([130, 255, 255])
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
