"""Ronda #14 de la auditoría A3: cobertura profunda de alpr/ocr_engine.py.

Cubre ramas de: detección del motor OCR (import tiempo de carga), ReadingStatusNotifier,
CorregirPatente (motos/brasil/clásicas), flush_queue, detect_motion, _ocr_single_roi
(RapidOCR/PaddleOCR y guards), QR, is_mercosur, consenso de 6 caracteres, combinación
de fragmentos (prioridades 2/3/4/5), fallback find_plate_roi, motos (aspecto y consenso),
get_frame_with_overlay/draw_overlay, y _dispatch_request (endpoints y errores).
"""
import contextlib
import itertools
import queue
import re
import sys
import threading
import time
import types
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

import alpr.ocr_engine as ocr_engine
from alpr.ocr_engine import ALPREngine, CorregirPatente, ReadingStatusNotifier

REQ_VOTES = ocr_engine.CONSENSUS_REQUIRED
_REAL_SLEEP = time.sleep

_MISSING = object()


# ---------------------------------------------------------------------------
# Helpers compartidos
# ---------------------------------------------------------------------------

class FakeQRDetector:
    """detectAndDecode determinista: devuelve el resultado configurado."""
    def __init__(self, result=None):
        self.result = result

    def detectAndDecode(self, frame):
        return self.result, None, None


class FakeReader:
    """Reader estilo rapidocr: __call__(roi) -> (resultado, None).

    spec puede ser None (resultado None), un resultado fijo, o un callable
    que recibe el número de llamada y devuelve el resultado de esa llamada.
    """
    def __init__(self, spec=None):
        self._spec = spec
        self.calls = 0

    def __call__(self, roi):
        self.calls += 1
        if callable(self._spec):
            result = self._spec(self.calls)
        else:
            result = self._spec
        return result, None


class FakePaddleReader:
    """Reader estilo paddleocr: método .ocr(img, cls=False)."""
    def __init__(self, result=None, raise_on_call=False):
        self.result = result
        self.raise_on_call = raise_on_call
        self.calls = 0

    def ocr(self, img, cls=False):
        self.calls += 1
        if self.raise_on_call:
            raise RuntimeError("paddle falló")
        return self.result


POLY = [[10, 10], [200, 10], [200, 50], [10, 50]]


def _result(texts, conf=0.95, polys=None):
    """Construye un resultado rapidocr: [[poly, texto, conf], ...]."""
    out = []
    for i, t in enumerate(texts):
        poly = polys[i] if polys else POLY
        out.append([poly, t, conf])
    return out


def _frame(fill=128):
    return np.full((480, 640, 3), fill, dtype=np.uint8)


def _make_engine(reader=None, dispatch=None, qr_result=None):
    eng = ALPREngine.__new__(ALPREngine)
    eng.reader = reader
    eng.engine_type = "RapidOCR"
    eng.ocr_error = None
    eng.qr_detector = FakeQRDetector(qr_result)
    eng.frame_queue = queue.Queue(maxsize=8)
    eng.vote_buffer = []
    eng.last_validated_plate = ""
    eng.last_validation_time = 0
    eng.is_running = True
    eng.active_detections = []
    eng.last_detection_time = 0
    eng.accepted_event = None
    eng.prev_gray = None
    eng.executor = ThreadPoolExecutor(max_workers=2)
    if dispatch is None:
        eng._dispatch_request = lambda *a, **k: None
    else:
        eng._dispatch_request = dispatch
    return eng


def _wait_for(pred, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        _REAL_SLEEP(0.01)
    return False


def _stop_worker(eng, thread):
    eng.is_running = False
    thread.join(timeout=3)
    eng.executor.shutdown(wait=False)


def _run_worker(eng, monkeypatch, q=None, n_frames=REQ_VOTES):
    """Parcha sleep, encola frames por defecto y arranca el worker."""
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)
    if q is not None:
        eng.frame_queue = q
    else:
        for _ in range(n_frames):
            eng.frame_queue.put(_frame())
    t = threading.Thread(target=eng.ocr_worker, daemon=True)
    t.start()
    return t


def _encerar_frames(eng, n_frames=REQ_VOTES):
    for _ in range(n_frames):
        eng.frame_queue.put(_frame())


@contextlib.contextmanager
def _scenario(rapid=_MISSING, paddle=_MISSING):
    """Reloadea ocr_engine forzando fallo/éxito de importación de los motores OCR.

    rapid/paddle: _MISSING → fuera de sys.modules (import error del módulo real),
    None → marcado con None en sys.modules (import interrumpido), o un módulo fake.
    Restaura el entorno real al salir.
    """
    saved_r = sys.modules.get("rapidocr_onnxruntime", _MISSING)
    saved_p = sys.modules.get("paddleocr", _MISSING)
    try:
        for name, v in (("rapidocr_onnxruntime", rapid), ("paddleocr", paddle)):
            if v is _MISSING:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = v
        importlib_reload = __import__("importlib").reload
        importlib_reload(ocr_engine)
        yield ocr_engine
    finally:
        for name, v in (("rapidocr_onnxruntime", saved_r), ("paddleocr", saved_p)):
            if v is _MISSING:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = v
        __import__("importlib").reload(ocr_engine)


def _fake_module(name, cls, klass="RapidOCR"):
    m = types.ModuleType(name)
    setattr(m, klass, cls)
    return m


class FakeResp:
    def __init__(self, ok=True, status=200, text="", message=""):
        self.ok = ok
        self.status_code = status
        self.text = text
        self._msg = message

    def json(self):
        return {"message": self._msg}


# ---------------------------------------------------------------------------
# Importación de motores OCR (times de carga) e init de ALPREngine
# ---------------------------------------------------------------------------

def test_import_rapid_falla_paddle_ok(monkeypatch):
    """Sin rapidocr, con paddleocr disponible → OCR_ENGINE_NAME PaddleOCR e init PaddleOCR."""
    class Paddle:
        def __init__(self, *a, **k):
            self.mode = "paddle"

    fake = _fake_module("paddleocr", Paddle, klass="PaddleOCR")
    with _scenario(rapid=None, paddle=fake):
        assert ocr_engine.OCR_ENGINE_NAME == "PaddleOCR"
        inst = ocr_engine.ALPREngine()
        assert inst.engine_type == "PaddleOCR"
        assert isinstance(inst.reader, Paddle)
        assert inst.ocr_error is None
        inst.executor.shutdown(wait=False)


def test_import_ambos_motores_fallan(capsys):
    """Sin rapidocr ni paddle → OCR_ENGINE_NAME None, warning y ALPREngine sin reader."""
    with _scenario(rapid=None, paddle=None):
        assert ocr_engine.OCR_ENGINE_NAME is None
        assert "rapidocr" in ocr_engine.OCR_ENGINE_ERROR.lower()
        assert "paddleocr" in ocr_engine.OCR_ENGINE_ERROR.lower()
        inst = ocr_engine.ALPREngine()
        assert inst.reader is None
        assert inst.engine_type is None
        inst.executor.shutdown(wait=False)
    out = capsys.readouterr().out
    assert "warning" in out.lower()


def test_init_rapid_constructor_falla():
    """RapidOCR importa bien pero falla al instanciar → ocr_error con detalle."""
    class BoomRapid:
        def __init__(self, *a, **k):
            raise RuntimeError("sin runtime")

    fake = _fake_module("rapidocr_onnxruntime", BoomRapid)
    with _scenario(rapid=fake):
        assert ocr_engine.OCR_ENGINE_NAME == "RapidOCR"
        inst = ocr_engine.ALPREngine()
        assert inst.reader is None
        assert "RapidOCR" in inst.ocr_error
        inst.executor.shutdown(wait=False)


def test_init_paddle_constructor_falla():
    """PaddleOCR importa bien pero falla al instanciar → ocr_error con detalle."""
    class BoomPaddle:
        def __init__(self, *a, **k):
            raise ValueError("modelo no descargado")

    fake = _fake_module("paddleocr", BoomPaddle, klass="PaddleOCR")
    with _scenario(rapid=None, paddle=fake):
        assert ocr_engine.OCR_ENGINE_NAME == "PaddleOCR"
        inst = ocr_engine.ALPREngine()
        assert inst.reader is None
        assert "PaddleOCR" in inst.ocr_error
        inst.executor.shutdown(wait=False)


# ---------------------------------------------------------------------------
# ReadingStatusNotifier
# ---------------------------------------------------------------------------

def test_notifier_debounce_y_fire(monkeypatch):
    """notify_reading con debounce (segunda llamada silenciada) y _fire con error."""
    fired = []

    class FakeThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            fired.append(self)
            self.target()  # ejecución inline y determinista

    monkeypatch.setattr(ocr_engine.threading, "Thread", FakeThread)
    monkeypatch.setattr(
        ocr_engine.requests, "post",
        lambda *a, **k: (_ for _ in ()).throw(ConnectionError("backend caído"))
    )
    n = ReadingStatusNotifier(interval=0.5)
    n.notify_reading()   # primer aviso → dispara hilo
    n.notify_reading()   # dentro del intervalo → debounce (return)
    assert len(fired) == 1


def test_notifier_segundo_aviso_fuera_de_intervalo(monkeypatch):
    """Tras pasar el intervalo, notify_reading vuelve a notificar."""
    fired = []

    class FakeThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            fired.append(self)
            self.target()

    monkeypatch.setattr(ocr_engine.threading, "Thread", FakeThread)
    monkeypatch.setattr(
        ocr_engine.requests, "post",
        lambda *a, **k: (_ for _ in ()).throw(OSError("timeout"))
    )
    n = ReadingStatusNotifier(interval=0.02)
    n.notify_reading()
    time.sleep(0.03)
    n.notify_reading()
    assert len(fired) == 2


# ---------------------------------------------------------------------------
# CorregirPatente: ramas restantes
# ---------------------------------------------------------------------------

def test_corregir_patente_vacia():
    assert CorregirPatente("") == ""
    assert CorregirPatente(None) == ""


def test_corregir_patente_moto_mercosur_con_digito_ambiguo():
    """A0ABCDE y AO1BCDE → moto MERCOSUR Argentina A048CDE / A018CDE."""
    assert CorregirPatente("A0ABCDE") == "A048CDE"
    assert CorregirPatente("AO1BCDE") == "A018CDE"


def test_corregir_patente_moto_general():
    """B012CDE no es 'A' inicial → pasa por la corrección general de moto."""
    assert CorregirPatente("B012CDE") == "B012CDE"


def test_corregir_patente_brasil_mercosur():
    """ABCID23 → ABC1D23 (formato Brasil MERCOSUR)."""
    assert CorregirPatente("ABCID23") == "ABC1D23"


def test_corregir_patente_clasica_auto():
    """ABC12D → ABC120: formato antiguo de auto (LLL NNN)."""
    assert CorregirPatente("ABC12D") == "ABC120"


def test_corregir_patente_moto_clasica():
    """012BCD → 012BCD: formato antiguo de moto (NNN LLL)."""
    assert CorregirPatente("012BCD") == "012BCD"


# ---------------------------------------------------------------------------
# flush_queue y detect_motion
# ---------------------------------------------------------------------------

class _FlakyGetQueue:
    """Fake de la cola para ejercitar los except de flush_queue."""
    def empty(self):
        return False

    def get_nowait(self):
        raise ValueError("burst")


def test_flush_queue_descarta_item_que_falla_en_get():
    """Un error en get_nowait corta el vaciado (except interno → break)."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.frame_queue = _FlakyGetQueue()
    eng.flush_queue()  # no debe propagar


def test_flush_queue_empty_que_levanta_error():
    """Si empty() falla, flush_queue lo silencia (except externo)."""
    eng = ALPREngine.__new__(ALPREngine)

    class _BoomEmpty:
        def empty(self):
            raise RuntimeError("queue rota")

    eng.frame_queue = _BoomEmpty()
    eng.flush_queue()


def test_detect_motion_primera_vez_y_cambios():
    """Primer frame → True; frame idéntico → False; frame distinto → True."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.prev_gray = None
    f1 = np.full((240, 320, 3), 120, dtype=np.uint8)
    assert eng.detect_motion(f1) is True      # prev_gray None → True
    assert eng.detect_motion(f1) is False     # sin cambios → count 0
    f2 = np.full((240, 320, 3), 255, dtype=np.uint8)
    assert eng.detect_motion(f2) is True      # cambio fuerte → >800


def test_detect_motion_error_cv2_devuelve_true(monkeypatch):
    """Si cvtColor falla, detect_motion degrada a True (seguro)."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.prev_gray = None
    monkeypatch.setattr(
        ocr_engine.cv2, "cvtColor",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("canal inválido"))
    )
    assert eng.detect_motion(_frame()) is True


# ---------------------------------------------------------------------------
# _ocr_single_roi
# ---------------------------------------------------------------------------

def test_ocr_single_roi_guardas():
    """ROI None/vacío y reader ausente devuelven listas vacías."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.reader = FakeReader(_result(["AA123BB"]))
    eng.engine_type = "RapidOCR"
    assert eng._ocr_single_roi(None) == ([], [], [])
    assert eng._ocr_single_roi(np.array([], dtype=np.uint8)) == ([], [], [])
    eng.reader = None
    assert eng._ocr_single_roi(_frame()) == ([], [], [])


def test_ocr_single_roi_resize_y_rapid_ok():
    """ROI pequeña (<80px) se amplía antes del OCR (30x30 → 80 de alto)."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.reader = FakeReader(_result(["AA123BB"], conf=0.90))
    eng.engine_type = "RapidOCR"
    roi = np.full((30, 30, 3), 200, dtype=np.uint8)
    texts, scores, polys = eng._ocr_single_roi(roi)
    assert texts == ["AA123BB"]
    assert scores == [0.90]
    assert len(polys) == 1
    assert eng.reader.calls == 1
    assert roi.shape[0] == 30  # el original no se modifica (resize crea copia)


def test_ocr_single_roi_resultado_vacio():
    """Si el reader devuelve None, _ocr_single_roi retorna vacío."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.reader = FakeReader(None)
    eng.engine_type = "RapidOCR"
    assert eng._ocr_single_roi(_frame()) == ([], [], [])


def test_ocr_single_roi_paddle_ok():
    """Rama PaddleOCR con resultado completo."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.reader = FakePaddleReader([[[POLY, ["ABC123", 0.88]]]])
    eng.engine_type = "PaddleOCR"
    texts, scores, polys = eng._ocr_single_roi(_frame())
    assert texts == ["ABC123"]
    assert scores == [0.88]
    assert polys == [POLY]


def test_ocr_single_roi_paddle_sin_resultado():
    """PaddleOCR sin líneas → vacío."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.reader = FakePaddleReader(None)
    eng.engine_type = "PaddleOCR"
    assert eng._ocr_single_roi(_frame()) == ([], [], [])


def test_ocr_single_roi_paddle_falla():
    """PaddleOCR que lanza excepción → vacío."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.reader = FakePaddleReader(None, raise_on_call=True)
    eng.engine_type = "PaddleOCR"
    assert eng._ocr_single_roi(_frame()) == ([], [], [])


# ---------------------------------------------------------------------------
# ocr_worker: motor ausente, QR, etc.
# ---------------------------------------------------------------------------

def test_ocr_worker_sin_motor_retorna(monkeypatch):
    """reader None → ocr_worker imprime y retorna sin loop."""
    eng = _make_engine(None)
    eng.ocr_worker()
    eng.executor.shutdown(wait=False)


def test_ocr_worker_codigo_qr_string(monkeypatch):
    """Un QR string genera evento 'qr' y continua el loop."""
    dispatched = []
    eng = _make_engine(FakeReader(_result(["AA123BB"])),
                       dispatch=lambda *a, **k: dispatched.append(a),
                       qr_result="QRCODE42")
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: len(dispatched) >= 1)
        assert dispatched[0][0] == "qr"
        assert dispatched[0][1] == "QRCODE42"
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_codigo_qr_lista(monkeypatch):
    """Un QR devuelto como lista se toma por su primer elemento."""
    dispatched = []
    eng = _make_engine(FakeReader(_result(["AA123BB"])),
                       dispatch=lambda *a, **k: dispatched.append(a),
                       qr_result=["AB12CD"])
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: len(dispatched) >= 1)
        assert dispatched[0][1] == "AB12CD"
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_is_mercosur_recorta_y_consenso(monkeypatch):
    """ROI MERCOSUR se recorta bajo la franja azul y se acepta la patente."""
    monkeypatch.setattr(ocr_engine.ImagePreprocessor, "is_mercosur_candidate", lambda roi: True)
    monkeypatch.setattr(ocr_engine.ImagePreprocessor, "crop_below_blue", lambda roi: roi)
    monkeypatch.setattr(ocr_engine.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(ocr_engine.cv2, "imwrite", lambda *a, **k: True)
    dispatched = []
    eng = _make_engine(FakeReader(_result(["AA123BB"])), dispatch=dispatched.append)
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.accepted_event is not None)
        assert eng.accepted_event["plate"] == "AA123BB"
        assert "ARGENTINA" in eng.accepted_event["country"].upper()
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_resultado_vacio_continua(monkeypatch):
    """Reader que devuelve None (textos vacíos) → continue sin evento."""
    eng = _make_engine(FakeReader(None))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.reader.calls >= 1)
        assert eng.accepted_event is None
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_texto_muy_corto_descarta(monkeypatch):
    """Textos de 1 carácter no forman detecciones (continue)."""
    def spec(call):
        return _result(["A"])
    eng = _make_engine(FakeReader(spec))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.reader.calls >= 1)
        assert eng.accepted_event is None
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_noise_header_descarta(monkeypatch):
    """Textos tipo REPUBLICA/ARGENTINA se descartan del buffer de detecciones."""
    def spec(call):
        return _result(["REPUBLICA"])
    eng = _make_engine(FakeReader(spec))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.reader.calls >= 1)
        assert eng.accepted_event is None
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_polys_menos_que_textos(monkeypatch):
    """Si hay menos polígonos que textos, el bbox cae al por defecto."""
    eng = _make_engine(FakeReader(None))
    eng._ocr_single_roi = lambda roi: (["AA123BB", "CC123BB"], [0.95, 0.9], [POLY])
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.accepted_event is not None)
        assert eng.accepted_event["plate"] == "AA123BB"
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_consenso_6_caracteres(monkeypatch):
    """Patente clásica de 6 caracteres (ABC123) se acepta por match_6."""
    monkeypatch.setattr(ocr_engine.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(ocr_engine.cv2, "imwrite", lambda *a, **k: True)
    dispatched = []
    eng = _make_engine(FakeReader(_result(["ABC123"])), dispatch=dispatched.append)
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.accepted_event is not None)
        assert eng.accepted_event["plate"] == "ABC123"
        assert eng.accepted_event["country"] == "ARGENTINA (Antigua)"
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_combina_fragmentos_by_x(monkeypatch):
    """Fragmentos AB + C123 (orden X) se concatenan en ABC123."""
    monkeypatch.setattr(ocr_engine.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(ocr_engine.cv2, "imwrite", lambda *a, **k: True)
    eng = _make_engine(FakeReader(_result(["AB", "C123"])))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.accepted_event is not None)
        assert eng.accepted_event["plate"] == "ABC123"
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_al_sin_formato_cae_fallback_vacio(monkeypatch):
    """Un texto sin formato no genera patente y el fallback de ROI no aporta."""
    monkeypatch.setattr(ocr_engine.ImagePreprocessor, "find_plate_roi", lambda frame: [])
    eng = _make_engine(FakeReader(_result(["NOPE09"])))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.reader.calls >= 1)
        assert eng.accepted_event is None
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_priority4_combina_por_y(monkeypatch):
    """Si el orden por X no matchea, el orden por Y sí (ABC123)."""
    monkeypatch.setattr(ocr_engine.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(ocr_engine.cv2, "imwrite", lambda *a, **k: True)
    polys = [
        [[100, 0], [180, 0], [180, 40], [100, 40]],   # "AB" x alto, y bajo
        [[0, 60], [80, 60], [80, 100], [0, 100]],      # "C123" x bajo, y alto
    ]
    eng = _make_engine(FakeReader(_result(["AB", "C123"], polys=polys)))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.accepted_event is not None)
        assert eng.accepted_event["plate"] == "ABC123"
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_fallback_roi_detecta(monkeypatch):
    """find_plate_roi entrega candidatos y uno de ellos confirma la patente."""
    monkeypatch.setattr(ocr_engine.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(ocr_engine.cv2, "imwrite", lambda *a, **k: True)
    monkeypatch.setattr(ocr_engine.ImagePreprocessor, "find_plate_roi",
                        lambda frame: ["cand1", "cand2"])

    def ocr_plan(roi):
        if isinstance(roi, str):
            if roi == "cand1":
                return [], [], []
            return ["ABC123"], [0.90], [POLY]
        return ["NOPE09"], [0.95], [POLY]   # detección sin formato en la ROI principal

    eng = _make_engine(FakeReader(None))
    eng._ocr_single_roi = ocr_plan
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.accepted_event is not None)
        assert eng.accepted_event["plate"] == "ABC123"
        assert eng.accepted_event["conf"] >= 0.65
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_fallback_roi_error_ignorado(monkeypatch):
    """Si find_plate_roi lanza, se ignora y el frame no emite evento."""
    monkeypatch.setattr(ocr_engine.ImagePreprocessor, "find_plate_roi",
                        lambda frame: (_ for _ in ()).throw(RuntimeError("ROI roto")))
    polys = [
        [],                                  # bbox vacío → excepción en orden X/Y
        [[5, 5], [50, 5], [50, 20], [5, 20]],
    ]
    eng = _make_engine(FakeReader(_result(["HELLO", "WORLD"], polys=polys)))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.reader.calls >= 1)
        assert eng.accepted_event is None
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_moto_descartada_sin_motos(monkeypatch):
    """Con detección de motos desactivada, una patente de moto se descarta."""
    eng = _make_engine(FakeReader(_result(["A012BCD"])))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.reader.calls >= REQ_VOTES)
        assert eng.accepted_event is None
    finally:
        _stop_worker(eng, t)


@pytest.mark.parametrize("conf,aceptada", [(0.95, True), (0.50, False)])
def test_ocr_worker_moto_con_motos_habilitadas(monkeypatch, conf, aceptada):
    """Con motos activadas: aspecto bueno y confianza alta acepta; conf baja no."""
    monkeypatch.setattr(ocr_engine, "ENABLE_MOTO_RECOGNITION", True)
    monkeypatch.setattr(ocr_engine.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(ocr_engine.cv2, "imwrite", lambda *a, **k: True)
    poly = [[0, 0], [90, 0], [90, 50], [0, 50]]  # aspecto 1.8 (< 2.2)
    eng = _make_engine(FakeReader(_result(["A012BCD"], conf=conf, polys=[poly])))
    t = _run_worker(eng, monkeypatch)
    try:
        if aceptada:
            assert _wait_for(lambda: eng.accepted_event is not None)
            assert eng.accepted_event["plate"] == "A012BCD"
        else:
            assert _wait_for(lambda: eng.reader.calls >= REQ_VOTES)
            assert eng.accepted_event is None
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_moto_aspecto_ancho_descarta(monkeypatch):
    """Una caja horizontal (>2.2) de una 'moto' se filtra como recorte de auto."""
    monkeypatch.setattr(ocr_engine, "ENABLE_MOTO_RECOGNITION", True)
    eng = _make_engine(FakeReader(_result(["A012BCD"])))  # POLY ancho 190/40 = 4.75
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.reader.calls >= REQ_VOTES)
        assert eng.accepted_event is None
    finally:
        _stop_worker(eng, t)


@pytest.mark.parametrize("texto,patron,motivo", [
    ("A1B2C3", r'\b[A-Z]\d[A-Z]\d[A-Z]\d\b', "is_valid_format"),
    ("AB123456", r'\b[A-Z]{2}\d{6}\b', "longitud"),
])
def test_ocr_worker_latam_personalizado_cae_en_validaciones(monkeypatch, texto, patron, motivo):
    """Con LATAM_PLATE_PATTERN acotado, el plate cae a is_valid_format (458) o longitud (414)."""
    monkeypatch.setattr(ocr_engine, "LATAM_PLATE_PATTERN", re.compile(patron))
    eng = _make_engine(FakeReader(_result([texto])))
    t = _run_worker(eng, monkeypatch)
    try:
        assert _wait_for(lambda: eng.reader.calls >= REQ_VOTES)
        assert eng.accepted_event is None
        assert eng.vote_buffer == [] if motivo == "longitud" else True
    finally:
        _stop_worker(eng, t)


def test_ocr_worker_excepcion_interna_continua(monkeypatch):
    """Una excepción dentro del loop se loguea y el loop sigue."""

    class FakeQueue:
        def __init__(self):
            self.calls = 0

        def get(self, timeout=1):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("get reventó")
            raise queue.Empty()

    eng = _make_engine(FakeReader(_result(["AA123BB"])))
    t = _run_worker(eng, monkeypatch, q=FakeQueue())
    _stop_worker(eng, t)


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------

def test_get_frame_with_overlay_none():
    """Frame None se devuelve tal cual."""
    eng = ALPREngine.__new__(ALPREngine)
    eng.active_detections = []
    eng.last_detection_time = 0
    eng.accepted_event = None
    assert eng.get_frame_with_overlay(None) is None


def test_get_frame_with_overlay_dibuja_deteccion(monkeypatch):
    """Detección reciente dispara draw_overlay."""
    monkeypatch.setattr(time, "time", lambda: 1000.0)
    eng = ALPREngine.__new__(ALPREngine)
    eng.active_detections = [{"text": "ABC123", "confidence": 0.9, "bbox": POLY}]
    eng.last_detection_time = 999.0   # 1s dentro de la ventana
    eng.accepted_event = None
    frame = np.zeros((200, 320, 3), dtype=np.uint8)
    out = eng.get_frame_with_overlay(frame)
    assert out is not None
    assert out.shape == frame.shape
    assert np.any(out != frame)  # dibujó algo


def test_draw_overlay_none():
    """draw_overlay con frame None → None."""
    assert ALPREngine.draw_overlay(None, active_detections=[]) is None


def test_draw_overlay_bbox_corto_omite():
    """Un bbox con menos de 4 puntos se salta (continue)."""
    frame = np.zeros((200, 320, 3), dtype=np.uint8)
    dets = [
        {"text": "ABC123", "confidence": 0.9, "bbox": [[0, 0], [10, 10]]},
        {"text": "XYZ987", "confidence": 0.9, "bbox": POLY},
    ]
    out = ALPREngine.draw_overlay(frame, active_detections=dets)
    assert np.any(out != frame)  # el segundo sí dibujó


# ---------------------------------------------------------------------------
# send_event y _dispatch_request
# ---------------------------------------------------------------------------

class _BoomStr:
    def __str__(self):
        raise ValueError("no serializable")


def test_send_event_error_str_ignorado():
    """Si str(data) falla, send_event no despacha y no rompe."""
    eng = _make_engine(FakeReader(None))
    eng.send_event("plate", _BoomStr(), _frame())
    eng.executor.shutdown(wait=False)


def _make_dispatch_engine(monkeypatch, resp=None, exc=None, gate_type="entrada"):
    eng = _make_engine(FakeReader(_result(["AA123BB"])))
    if "_dispatch_request" in eng.__dict__:
        del eng.__dict__["_dispatch_request"]   # usar el dispatch real de la clase
    calls = []

    def fake_post(*a, **k):
        calls.append((a, k))
        if exc is not None:
            raise exc
        return resp

    monkeypatch.setattr(ocr_engine.requests, "post", fake_post)
    monkeypatch.setattr(ocr_engine, "GATE_TYPE", gate_type)
    monkeypatch.setattr(ocr_engine, "GATE_ID", "CAM01")
    monkeypatch.setattr(ocr_engine, "BACKEND_URL", "http://backend.test")
    return eng, calls


def test_dispatch_entrada_bienvenido(monkeypatch):
    """validate-plate + mensaje bienvenido."""
    eng, calls = _make_dispatch_engine(
        monkeypatch, resp=FakeResp(message="Bienvenido AA123BB!"), gate_type="entrada")
    eng.send_event("plate", "AA123BB", _frame(), ocr_time=0.12)
    assert _wait_for(lambda: calls)
    url, kwargs = calls[0]
    assert url[0] == "http://backend.test/v1/access/validate-plate"
    payload = kwargs["json"]
    assert payload["gate_id"] == "CAM01"
    assert payload["plate"] == "AA123BB"
    assert abs(payload["ocr_time"] - 0.12) < 1e-6
    assert "image_base64" in payload
    eng.executor.shutdown(wait=False)


def test_dispatch_salida_hasta_luego(monkeypatch):
    """exit-plate + mensaje de salida."""
    eng, calls = _make_dispatch_engine(
        monkeypatch, resp=FakeResp(message="Hasta luego AA123BB!"), gate_type="salida")
    eng.send_event("plate", "AA123BB", _frame())
    assert _wait_for(lambda: calls)
    assert calls[0][0][0] == "http://backend.test/v1/access/exit-plate"
    eng.executor.shutdown(wait=False)


def test_dispatch_mensaje_otro(monkeypatch):
    """Respuesta ok con mensaje genérico."""
    eng, calls = _make_dispatch_engine(
        monkeypatch, resp=FakeResp(message="Patente en proceso"), gate_type="entrada")
    eng.send_event("plate", "AA123BB", _frame())
    assert _wait_for(lambda: calls)
    assert calls[0][1]["json"]["plate"] == "AA123BB"
    eng.executor.shutdown(wait=False)


def test_dispatch_respuesta_error(monkeypatch):
    """Respuesta !ok se informa sin romper."""
    eng, calls = _make_dispatch_engine(
        monkeypatch, resp=FakeResp(ok=False, status=404, text="no existe"), gate_type="entrada")
    eng.send_event("plate", "AA123BB", _frame())
    assert _wait_for(lambda: calls)
    assert calls[0][1]["json"]["plate"] == "AA123BB"
    eng.executor.shutdown(wait=False)


def test_dispatch_error_post(monkeypatch):
    """Si requests.post lanza, se loguea el error."""
    eng, calls = _make_dispatch_engine(
        monkeypatch, exc=RuntimeError("backend inaccesible"), gate_type="entrada")
    eng.send_event("plate", "AA123BB", _frame())
    assert _wait_for(lambda: calls)  # el post se intentó
    eng.executor.shutdown(wait=False)


def test_dispatch_qr_endpoint(monkeypatch):
    """Eventos QR usan validate-qr y la clave qr_data."""
    eng, calls = _make_dispatch_engine(
        monkeypatch, resp=FakeResp(message="QR procesado"), gate_type="entrada")
    eng.send_event("qr", "TOK123", _frame())
    assert _wait_for(lambda: calls)
    url, kwargs = calls[0]
    assert url[0] == "http://backend.test/v1/access/validate-qr"
    assert kwargs["json"]["qr_data"] == "TOK123"
    assert "plate" not in kwargs["json"]
    eng.executor.shutdown(wait=False)


def test_dispatch_error_al_codificar_frame(monkeypatch):
    """Si imencode falla, el dispatch se aborta sin romper."""
    monkeypatch.setattr(
        ocr_engine.cv2, "imencode",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("jpeg no soportado"))
    )
    eng, calls = _make_dispatch_engine(
        monkeypatch, resp=FakeResp(message="ok"), gate_type="entrada")
    eng.send_event("plate", "AA123BB", _frame())
    eng.executor.shutdown(wait=False)
    time.sleep(0.2)