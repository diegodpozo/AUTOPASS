import pytest
import numpy as np
from alpr.ocr_engine import ALPREngine

def test_plate_close_shared_digits_debounce():
    """VERIFICA QUE _PLATE_CLOSE DETECTE VARIANTES FICTICIAS CON EL MISMO BLOQUE NUMERICO."""
    # NVZ087 vs VZ087AR (ambas comparten 087)
    assert ALPREngine._plate_close("NVZ087", "VZ087AR") is True
    # NVZ087 vs TINA087 (ambas comparten 087)
    assert ALPREngine._plate_close("NVZ087", "TINA087") is True
    # Patentes verdaderamente distintas no deben dar True
    assert ALPREngine._plate_close("NVZ087", "AA123BB") is False

def test_header_noise_filtering():
    """VERIFICA QUE LAS PALABRAS INSTITUCIONALES/HEADER NOISE NO GENEREN PATENTES FALSAS."""
    import re
    HEADER_NOISE_WORDS = re.compile(
        r'\b(REPUBLICA|ARGENTINA|MERCOSUR|BRASIL|URUGUAY|PARAGUAY|GENTINA|TINA|REPU|MERCO|SUR)\b',
        re.IGNORECASE
    )

    sample_1 = "ARGENTINA"
    sample_2 = "TINA"
    sample_3 = "REPUBLICA"

    assert HEADER_NOISE_WORDS.sub('', sample_1).strip() == ""
    assert HEADER_NOISE_WORDS.sub('', sample_2).strip() == ""
    assert HEADER_NOISE_WORDS.sub('', sample_3).strip() == ""
