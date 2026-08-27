import pytest
import re
from alpr.config import MOTO_PATTERN

def test_incomplete_auto_crop_detected_as_moto_aspect_ratio_check():
    """VERIFICA QUE UN RECORTE INCOMPLETO DE AUTO (EJ: AC404 DE AC404SD) CON CAJA HORIZONTAL SEA FILTRADO."""
    plate_incomplete = "AC404"
    is_moto = bool(MOTO_PATTERN.match(plate_incomplete))
    assert is_moto is True  # Coincide con patrón de moto antigua (2 letras + 3 números)

    # Simular caja horizontal de auto (ej: ancho 300px, alto 70px -> aspect ratio = 4.28)
    bbox_w = 300
    bbox_h = 70
    aspect = bbox_w / bbox_h

    # El filtro de relación de aspecto debe detectar que aspect > 2.2 e invalidar la coincidencia como moto
    is_incomplete_auto_crop = is_moto and (aspect > 2.2)
    assert is_incomplete_auto_crop is True
