"""Tests #1 y #2 de la auditoría A3: pipeline ALPR completo.

1. runner.py (antes 0%): arranque fatal de VideoStreamer y bucle principal en modo ENTRADA.
2. ocr_engine.py: consenso mínimos (CONSENSUS_REQUIRED), cooldown/debounce de send_event,
   descarte de frames en negro y corrección posicional de patentes.
"""
import queue
import threading
import time
import numpy as np

import pytest

import alpr.ocr_engine as ocr_engine
import alpr.runner as runner_mod
from alpr.ocr_engine import ALPREngine, CorregirPatente

REQ_VOTES = ocr_engine.CONSENSUS_REQUIRED


class FakeQRDetector:
    """QR detector que nunca encuentra códigos."""
    def detectAndDecode(self, frame):
        return None, None, None


class FakeReader:
    """Reader RapidOCR sintético: retorna (result, None) estilo rapidocr_onnxruntime."""
    def __init__(self, texts, conf=0.95):
        self._texts = list(texts)
        self._conf = conf
        self.calls = 0

    def __call__(self, roi):
        self.calls += 1
        tex = self._texts[(self.calls - 1) % len(self._texts)]
        poly = [[10, 10], [200, 10], [200, 50], [10, 50]]
        return [[poly, tex, self._conf]], None


def _make_engine(reader, dispatch=None):
    """Construye un ALPREngine sin instanciar el motor OCR real (rápido y aislado)."""
    engine = ALPREngine.__new__(ALPREngine)
    engine.reader = reader
    engine.engine_type = "RapidOCR"
    engine.ocr_error = None
    engine.qr_detector = FakeQRDetector()
    engine.frame_queue = queue.Queue(maxsize=8)
    engine.vote_buffer = []
    engine.last_validated_plate = ""
    engine.last_validation_time = 0
    engine.is_running = True
    engine.prev_gray = None
    engine.active_detections = []
    engine.last_detection_time = 0
    engine.accepted_event = None
    from concurrent.futures import ThreadPoolExecutor
    engine.executor = ThreadPoolExecutor(max_workers=2)
    if dispatch is not None:
        engine._dispatch_request = dispatch
    return engine


def _frame(fill=128):
    return np.full((480, 640, 3), fill, dtype=np.uint8)


def _wait_for(pred, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(0.01)
    return False


def _stop_worker(engine, thread):
    engine.is_running = False
    thread.join(timeout=2)
    engine.executor.shutdown(wait=False)


# ---------------------------------------------------------------------------
# ocr_worker: consenso y cooldown (test #2)
# ---------------------------------------------------------------------------

def test_ocr_consenso_dos_votos_emite_evento(monkeypatch):
    """Con CONSENSUS_REQUIRED votos de la misma patente se acepta la lectura."""
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(ocr_engine.os, "makedirs", lambda *a, **k: (_ for _ in ()).throw(OSError("no debug")))
    q = queue.Queue(maxsize=8)
    for _ in range(REQ_VOTES):
        q.put(_frame())
    dispatched = []
    engine = _make_engine(FakeReader(["AA123BB"]), dispatch=lambda *a, **k: dispatched.append(a))
    engine.frame_queue = q

    t = threading.Thread(target=engine.ocr_worker, daemon=True)
    t.start()
    try:
        assert _wait_for(lambda: engine.accepted_event is not None), "el consenso no emitió evento"
        assert engine.accepted_event["plate"] == "AA123BB"
        assert engine.accepted_event["conf"] >= ocr_engine.CONFIDENCE_THRESHOLD
        assert _wait_for(lambda: engine.vote_buffer == [])
        assert _wait_for(lambda: len(dispatched) >= 1)
        assert dispatched[0][0] == "plate"
        assert dispatched[0][1] == "AA123BB"
        assert engine.vote_buffer == []
    finally:
        _stop_worker(engine, t)


def test_ocr_sin_consenso_patentes_distintas_no_emite(monkeypatch):
    """Dos patentes distintas en la ventana no alcanzan consenso: no se emite evento."""
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)
    q = queue.Queue(maxsize=8)
    for _ in range(REQ_VOTES):
        q.put(_frame())
    engine = _make_engine(FakeReader(["AA123BB", "CC123DD"]))
    engine.frame_queue = q

    t = threading.Thread(target=engine.ocr_worker, daemon=True)
    t.start()
    try:
        assert _wait_for(lambda: engine.reader.calls >= REQ_VOTES)
        time.sleep(0.1)
        assert engine.accepted_event is None
        assert len(engine.vote_buffer) == REQ_VOTES
    finally:
        _stop_worker(engine, t)


def test_ocr_frame_negro_descarta_votos(monkeypatch):
    """Un frame en negro (media < 12) resetea el buffer de votos sin emitir evento."""
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)
    q = queue.Queue(maxsize=8)
    q.put(_frame())          # voto AA123BB
    q.put(_frame(fill=0))   # frame negro → reset
    engine = _make_engine(FakeReader(["AA123BB"]))
    engine.frame_queue = q

    t = threading.Thread(target=engine.ocr_worker, daemon=True)
    t.start()
    try:
        assert _wait_for(lambda: engine.reader.calls >= 1)
        assert _wait_for(lambda: engine.vote_buffer == [])
        assert engine.reader.calls == 1
        assert engine.accepted_event is None
    finally:
        _stop_worker(engine, t)


def test_send_event_debounce_suprime_duplicado_por_cooldown():
    """Dentro del cooldown, la misma patente no re-envía al backend."""
    dispatched = []
    engine = _make_engine(FakeReader(["AA123BB"]), dispatch=lambda *a, **k: dispatched.append(a))

    frame = _frame()
    engine.send_event("plate", "AA123BB", frame)
    engine.send_event("plate", "AA123BB", frame)
    time.sleep(0.3)
    assert len(dispatched) == 1


def test_send_event_patente_distinta_en_cooldown_si_envia():
    """Dentro del cooldown, una patente diferente sí se despacha (no es duplicado)."""
    dispatched = []
    engine = _make_engine(FakeReader(["AA123BB"]), dispatch=lambda *a, **k: dispatched.append(a))

    frame = _frame()
    engine.send_event("plate", "AA123BB", frame)
    engine.send_event("plate", "ZZ904ZZ", frame)
    time.sleep(0.3)
    plates = [a[1] for a in dispatched]
    assert "AA123BB" in plates
    assert "ZZ904ZZ" in plates


# ---------------------------------------------------------------------------
# Corrección posicional de patentes (helpers de ocr_engine)
# ---------------------------------------------------------------------------

def test_corregir_patente_mercosur_auto_con_digitos_ambiguos():
    """AAI23BB → AA123BB: I→1 en posición numérica del MERCOSUR."""
    assert CorregirPatente("AAI23BB") == "AA123BB"
    assert CorregirPatente("AA12OBB") == "AA120BB"


def test_corregir_patente_antigua_llllll_a_nnn():
    """AB23CD es un formato de 6 válido: se retorna sin cambios."""
    assert CorregirPatente("AB23CD") == "AB23CD"


def test_corregir_patente_limpia_ruido_header():
    """RUIDO tipo ARGENTINA/TINA se elimina antes de corregir."""
    assert CorregirPatente("ARGENTINA") == ""
    assert CorregirPatente("TINA") == ""


def test_corregir_patente_larga_sin_formato_queda_limpia_solo():
    assert CorregirPatente("ABC123DEF") == "ABC123DEF"


# ---------------------------------------------------------------------------
# runner (test #1)
# ---------------------------------------------------------------------------

def test_runner_videostreamer_fatal_no_crashea(monkeypatch):
    """Si VideoStreamer falla al arrancar, run_alpr_service loguea y retorna."""

    class FatalStreamer:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("cámara no disponible")

    monkeypatch.setattr(runner_mod, "VideoStreamer", FatalStreamer)
    assert runner_mod.run_alpr_service() is None


def test_runner_bucle_principal_modo_entrada(monkeypatch):
    """El bucle principal encola frames de ALPR y continúa hasta que el loop se corta."""
    dispatched = []
    created = {}

    class FakeStreamer:
        def __init__(self, source, target_width=1280):
            self.source = source

        def start(self):
            return self

        def get_frame(self):
            return np.full((240, 320, 3), 100, dtype=np.uint8)

    class FakeEngine:
        def __init__(self):
            self.qr_detector = FakeQRDetector()
            self.frame_queue = queue.Queue(maxsize=12)
            self.engine_type = "Fake"
            self.ocr_error = None
            self.motion_detects = 0

        def detect_motion(self, frame):
            self.motion_detects += 1
            return True

        def send_event(self, *a, **k):
            dispatched.append(a)

        def ocr_worker(self):
            pass

    async def noop_ws(*args, **kwargs):
        return None

    def fake_engine_factory():
        inst = FakeEngine()
        created["engine"] = inst
        return inst

    monkeypatch.setattr(runner_mod, "VideoStreamer", FakeStreamer)
    monkeypatch.setattr(runner_mod, "ALPREngine", fake_engine_factory)
    monkeypatch.setattr(runner_mod, "ws_monitoring_worker", lambda *a, **k: noop_ws(*a, **k))
    monkeypatch.setattr(runner_mod, "_reading_notifier", type("N", (), {"notify_reading": lambda self: None})())
    monkeypatch.setattr(runner_mod, "GATE_TYPE", "entrada")
    monkeypatch.setattr(runner_mod, "FORCE_OCR", True)

    real_sleep = time.sleep
    state = {"calls": 0}

    def fake_sleep(s):
        state["calls"] += 1
        if state["calls"] >= 5:
            raise RuntimeError("detener loop de pruebas")
        real_sleep(min(s, 0.01))

    monkeypatch.setattr(time, "sleep", fake_sleep)

    runner_mod.run_alpr_service()

    assert state["calls"] >= 5, "el loop principal debería haber estado activo"
    engine = created["engine"]
    assert not engine.frame_queue.empty()