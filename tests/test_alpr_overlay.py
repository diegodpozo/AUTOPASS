import pytest
import numpy as np
import time
from alpr.ocr_engine import ALPREngine

def test_draw_overlay_rendering():
    """VERIFICA QUE DRAW_OVERLAY DIBUJE RECUADROS BBOX, ETIQUETAS Y BANNER SIN ERRORES."""
    # Crear un frame ficticio de 720x1280 (3 canales BGR)
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    active_dets = [
        {
            "text": "AG 536 CR",
            "confidence": 0.95,
            "bbox": [[100, 100], [300, 100], [300, 180], [100, 180]]
        }
    ]

    accepted_ev = {
        "plate": "AG 536 CR",
        "country": "ARGENTINA",
        "conf": 0.95,
        "time": time.time()
    }

    # Probar renderizado de overlay
    out_frame = ALPREngine.draw_overlay(frame, active_detections=active_dets, accepted_event=accepted_ev)

    assert out_frame is not None
    assert out_frame.shape == frame.shape
    # Debe haber dibujado pixeles no negros en la imagen
    assert np.count_nonzero(out_frame) > 0

def test_get_frame_with_overlay_clears_expired():
    """VERIFICA QUE GET_FRAME_WITH_OVERLAY LIMPIE DETECCIONES EXPIRADAS."""
    engine = ALPREngine()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Detección antigua (> 1.5s)
    engine.active_detections = [{"text": "OLD123", "confidence": 0.8, "bbox": [[10, 10], [50, 10], [50, 30], [10, 30]]}]
    engine.last_detection_time = time.time() - 3.0

    res = engine.get_frame_with_overlay(frame)
    # Como está expirada, no debe modificar el frame limpio
    assert np.array_equal(res, frame)
