"""Auditoría A3 (cobertura): tests para alpr/preprocessor.py (ImagePreprocessor).

Cubre identificación de país por formato, detección de movimiento, preprocesado
anti-moiré, cálculo de IoU, validación de ROI, búsqueda de patentes, y detección/
recorte de la franja azul MERCOSUR.
"""
import numpy as np
import pytest

import alpr.preprocessor as preproc
from alpr.preprocessor import ImagePreprocessor


def _frame(h=480, w=640, fill=128):
    return np.full((h, w, 3), fill, dtype=np.uint8)


def _blue_strip(h, w, strip_h):
    """Imagen con una franja azul (BGR 255,0,0) en las primeras `strip_h` filas."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:strip_h, :] = (255, 0, 0)
    return img


# --- identify_country ---

def test_identify_country_folios_argentinos():
    assert ImagePreprocessor.identify_country("AA123BB", False) == "ARGENTINA (Mercosur)"
    assert ImagePreprocessor.identify_country("AF456GH", False) == "ARGENTINA (Mercosur)"


def test_identify_country_motos_argentinas():
    assert ImagePreprocessor.identify_country("A012BCD", False) == "ARGENTINA (Moto Mercosur)"
    assert ImagePreprocessor.identify_country("AB123A", False) == "ARGENTINA (Moto Mercosur)"
    assert ImagePreprocessor.identify_country("AB123", False) == "ARGENTINA (Moto Antigua)"


def test_identify_country_antigua():
    assert ImagePreprocessor.identify_country("AAA111", False) == "ARGENTINA (Antigua)"


def test_identify_country_brasil_uruguay_paraguay():
    assert ImagePreprocessor.identify_country("ABC1D23", False) == "BRASIL"
    assert ImagePreprocessor.identify_country("ABC1234", False) == "URUGUAY"
    assert ImagePreprocessor.identify_country("WXYZ789", False) == "PARAGUAY (Mercosur)"


def test_identify_country_fallbacks():
    assert ImagePreprocessor.identify_country("X1X", True) == "MERCOSUR (Otro)"
    assert ImagePreprocessor.identify_country("X1X", False) == "DESCONOCIDO"


# --- detect_motion ---

def test_detect_motion_force_ocr_short_circuit(monkeypatch):
    monkeypatch.setattr(preproc, "FORCE_OCR", True)
    prev = _frame()
    motion, returned = ImagePreprocessor.detect_motion(_frame(), prev)
    assert motion is True
    assert returned is prev


def test_detect_motion_primer_frame_siempre_movimiento(monkeypatch):
    monkeypatch.setattr(preproc, "FORCE_OCR", False)
    motion, gray = ImagePreprocessor.detect_motion(_frame(fill=100), None)
    assert motion is True
    assert gray.shape == (240, 320)


def test_detect_motion_frames_iguales_no_movimiento(monkeypatch):
    monkeypatch.setattr(preproc, "FORCE_OCR", False)
    frame = _frame(fill=120)
    _, prev_gray = ImagePreprocessor.detect_motion(frame, None)
    motion, _ = ImagePreprocessor.detect_motion(frame, prev_gray)
    assert not motion  # np.False_


def test_detect_motion_frames_distintos_si_movimiento(monkeypatch):
    monkeypatch.setattr(preproc, "FORCE_OCR", False)
    _, prev_gray = ImagePreprocessor.detect_motion(_frame(fill=120), None)
    motion, _ = ImagePreprocessor.detect_motion(_frame(fill=220), prev_gray)
    assert motion  # np.True_


# --- preprocess_for_screen ---

def test_preprocess_for_screen_devuelve_tres_variantes():
    img = _frame(h=100, w=300, fill=128)
    result = ImagePreprocessor.preprocess_for_screen(img)
    assert len(result) == 3
    sharp, binary, inverted = result
    assert sharp.shape == (250, 750)
    assert binary.shape == (250, 750)
    assert inverted.shape == (250, 750)
    assert set(np.unique(binary)) <= {0, 255}
    assert (inverted != binary).any()


# --- _iou ---

def test_iou_solapamiento_parcial():
    b1 = (0, 0, 100, 100)
    b2 = (50, 50, 150, 150)
    assert ImagePreprocessor._iou(b1, b2) == pytest.approx(2500 / 17500)


def test_iou_sin_solapamiento_cero():
    assert ImagePreprocessor._iou((0, 0, 10, 10), (50, 50, 60, 60)) == 0.0


def test_iou_contencion_total():
    # El rectángulo interno solapa todo su área: IoU = area_inner / area_outer.
    assert ImagePreprocessor._iou((0, 0, 100, 100), (10, 10, 90, 90)) == pytest.approx(0.64)


def test_iou_area_nula_cero():
    assert ImagePreprocessor._iou((0, 0, 0, 0), (0, 0, 10, 10)) == 0.0


# --- _is_valid_plate_roi ---

def test_roi_valida():
    crop = np.zeros((40, 120, 3), dtype=np.uint8)
    assert ImagePreprocessor._is_valid_plate_roi(crop, 640, 480) is True


def test_roi_angosta_rechazada():
    crop = np.zeros((40, 60, 3), dtype=np.uint8)
    assert ImagePreprocessor._is_valid_plate_roi(crop, 640, 480) is False


def test_roi_baja_rechazada():
    crop = np.zeros((10, 120, 3), dtype=np.uint8)
    assert ImagePreprocessor._is_valid_plate_roi(crop, 640, 480) is False


def test_roi_muy_ancha_rechazada():
    crop = np.zeros((40, 600, 3), dtype=np.uint8)
    assert ImagePreprocessor._is_valid_plate_roi(crop, 640, 480) is False


def test_roi_aspect_ratio_invalido_rechazado():
    crop = np.zeros((10, 200, 3), dtype=np.uint8)
    assert ImagePreprocessor._is_valid_plate_roi(crop, 640, 480) is False


# --- find_plate_roi ---

def test_find_plate_roi_frame_liso_devuelve_roi_principal():
    frame = _frame(fill=128)
    candidates = ImagePreprocessor.find_plate_roi(frame)
    assert len(candidates) >= 1
    for c in candidates:
        assert c.ndim == 3
        assert c.shape[2] == 3


def test_find_plate_roi_con_contorno_placa():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[200:260, 180:380] = (255, 255, 255)   # patente válida → pasa filtros
    frame[350:420, 60:536] = (200, 200, 200)    # ancha: no supera _is_valid_plate_roi
    frame[90:210, 200:220] = (180, 180, 180)    # alta y angosta: aspect inválido (se fusiona con la placa)
    frame[300:306, 400:406] = (160, 160, 160)   # contorno diminuto: área descartada
    candidates = ImagePreprocessor.find_plate_roi(frame)
    assert len(candidates) >= 1


def test_find_plate_roi_error_contorno_no_crashea(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("cv2 findContours falló")

    monkeypatch.setattr(preproc.cv2, "findContours", _boom)
    frame = _frame(h=200, w=300, fill=95)
    candidates = ImagePreprocessor.find_plate_roi(frame)
    assert len(candidates) >= 1


def test_find_plate_roi_cinta_pequena_sin_contornos_devuelve_roi_principal():
    frame = _frame(h=100, w=120, fill=128)
    candidates = ImagePreprocessor.find_plate_roi(frame)
    assert len(candidates) == 1
    assert candidates[0].shape[0] == int(100 * 0.77)


def test_find_plate_roi_dedupe_por_iou(monkeypatch):
    monkeypatch.setattr(ImagePreprocessor, "_is_valid_plate_roi", lambda *a, **k: True)
    monkeypatch.setattr(ImagePreprocessor, "_iou", lambda *a, **k: 0.99)
    frame = _frame(h=300, w=400, fill=90)
    candidates = ImagePreprocessor.find_plate_roi(frame)
    assert len(candidates) == 1


def test_find_plate_roi_limite_10_candidatos():
    frame = _frame(h=400, w=2200, fill=110)
    candidates = ImagePreprocessor.find_plate_roi(frame)
    assert len(candidates) == 10


# --- is_mercosur_candidate ---

def test_mercosur_con_franja_azul():
    roi = _blue_strip(h=200, w=400, strip_h=40)
    assert ImagePreprocessor.is_mercosur_candidate(roi)  # np.True_


def test_mercosur_sin_franja_azul():
    roi = _frame(h=200, w=400, fill=200)
    assert not ImagePreprocessor.is_mercosur_candidate(roi)  # np.False_


def test_mercosur_roi_vacia_no_crashea():
    roi = np.zeros((0, 0, 3), dtype=np.uint8)
    assert not ImagePreprocessor.is_mercosur_candidate(roi)


def test_mercosur_roi_escala_de_grises_retorna_false():
    roi = np.zeros((50, 60), dtype=np.uint8)
    assert not ImagePreprocessor.is_mercosur_candidate(roi)


# --- crop_below_blue ---

def test_crop_baja_franja_azul_recorta():
    roi = _blue_strip(h=200, w=400, strip_h=40)
    cropped = ImagePreprocessor.crop_below_blue(roi)
    assert cropped.shape[0] < roi.shape[0]
    assert cropped.shape[1] == roi.shape[1]


def test_crop_sin_franja_azul_no_modifica():
    roi = _frame(h=200, w=400, fill=200)
    cropped = ImagePreprocessor.crop_below_blue(roi)
    assert cropped is roi


def test_crop_franja_muy_baja_no_recorta():
    img = np.zeros((200, 400, 3), dtype=np.uint8)
    img[int(200 * 0.30):int(200 * 0.50), :] = (255, 0, 0)
    cropped = ImagePreprocessor.crop_below_blue(img)
    assert cropped.shape[0] == img.shape[0]


def test_crop_resto_muy_pequeno_devuelve_roi():
    img = _blue_strip(h=8, w=40, strip_h=4)
    cropped = ImagePreprocessor.crop_below_blue(img)
    assert cropped.shape == (8, 40, 3)


def test_crop_franja_en_mitad_inferior_no_recorta():
    img = np.zeros((200, 400, 3), dtype=np.uint8)
    img[int(200 * 0.60):int(200 * 0.70), :] = (255, 0, 0)
    cropped = ImagePreprocessor.crop_below_blue(img)
    assert cropped.shape == img.shape


def test_crop_roi_escala_de_grises_devuelve_roi():
    roi = np.zeros((50, 60), dtype=np.uint8)
    assert ImagePreprocessor.crop_below_blue(roi) is roi


def test_crop_where_vacio_devuelve_roi(monkeypatch):
    empty = (np.array([], dtype=np.int64), np.array([], dtype=np.int64))

    def fake_where(cond, *a, **k):
        return empty

    monkeypatch.setattr(preproc.np, "where", fake_where)
    img = _blue_strip(h=100, w=100, strip_h=30)
    assert ImagePreprocessor.crop_below_blue(img) is img