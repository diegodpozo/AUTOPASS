import pytest
from alpr.ocr_engine import ALPREngine

def test_flush_queue_clears_all_stale_frames():
    """VERIFICA QUE FLUSH_QUEUE LIMPIE LA COLA DE FRAMES ACUMULADOS DE INMEDIATO."""
    engine = ALPREngine()
    
    # Encolar 5 items de prueba
    for i in range(5):
        engine.frame_queue.put(f"dummy_frame_{i}")
    
    assert engine.frame_queue.qsize() == 5
    
    # Vaciar cola
    engine.flush_queue()
    
    assert engine.frame_queue.empty() is True
    assert engine.frame_queue.qsize() == 0
