"""Tests ronda #13: alpr/video_streamer.py (VideoStreamer).

Cubre captura en __init__ (URL http → CAP_FFMPEG + timeouts; fuente local), start() en hilo,
_update() con reescalado/no-rescale, reintentos de frames vacíos, excepción de lectura,
get_frame() thread-safe (copia / None) y stop() con liberación del VideoCapture.
"""
import threading

import numpy as np
import pytest

import alpr.video_streamer as vs_mod
from alpr.video_streamer import VideoStreamer


class FakeCap:
    """VideoCapture sintético: consume una lista de respuestas de read()."""

    def __init__(self, reads=None, is_opened=True):
        self._reads = list(reads or [])
        self._i = 0
        self.set_calls = []
        self.is_opened = is_opened
        self.released = False
        self.streamer = None

    def set(self, key, value):
        self.set_calls.append((key, value))

    def read(self):
        if self._i < len(self._reads):
            item = self._reads[self._i]
            self._i += 1
            if isinstance(item, Exception):
                raise item
            return item
        if self.streamer is not None:
            self.streamer.is_running = False
        return False, None

    def isOpened(self):
        return self.is_opened

    def release(self):
        self.released = True


class FakeThread:
    """Remplaza threading.Thread para no ejecutar _update en paralelo."""
    instances = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.started = False
        FakeThread.instances.append(self)

    def start(self):
        self.started = True

    def join(self, timeout=None):
        return None


def _small_frame():
    return np.full((180, 240, 3), 90, dtype=np.uint8)


def _wide_frame():
    return np.full((900, 1600, 3), 60, dtype=np.uint8)


def _no_frame():
    return False, None


@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr(vs_mod.time, "sleep", lambda s: None)


def _make_streamer(reads, with_streamer_link=True, is_opened=True):
    cap = FakeCap(reads, is_opened=is_opened)
    streamer = VideoStreamer.__new__(VideoStreamer)
    streamer.cap = cap
    streamer.target_width = 1280
    streamer.current_frame = None
    streamer.is_running = True
    streamer.lock = threading.Lock()
    if with_streamer_link:
        cap.streamer = streamer
    return streamer, cap


def test_init_http_source_usa_ffmpeg_y_timeouts(monkeypatch):
    captured = {}

    def fake_capture(source, *args, **kwargs):
        captured["source"] = source
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeCap()

    monkeypatch.setattr(vs_mod.cv2, "VideoCapture", fake_capture)
    streamer = VideoStreamer("http://192.168.1.10:8080/video")
    assert captured["source"] == "http://192.168.1.10:8080/video"
    assert captured["args"][0] == vs_mod.cv2.CAP_FFMPEG
    cap = streamer.cap
    assert cap.set_calls.count((vs_mod.cv2.CAP_PROP_BUFFERSIZE, 1)) == 1
    assert cap.set_calls.count((vs_mod.cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)) == 1
    assert cap.set_calls.count((vs_mod.cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)) == 1
    assert (1280, 720) in cap.set_calls or (vs_mod.cv2.CAP_PROP_FRAME_WIDTH, 1280) in cap.set_calls


def test_init_fuente_local_usa_videocapture_simple(monkeypatch):
    captured = {}

    def fake_capture(source, *args, **kwargs):
        captured["source"] = source
        captured["args"] = args
        return FakeCap()

    monkeypatch.setattr(vs_mod.cv2, "VideoCapture", fake_capture)
    streamer = VideoStreamer(int(0))
    assert captured["source"] == 0
    assert captured["args"] == ()
    assert streamer.is_running is True


def test_start_lanza_hilo_daemon(monkeypatch):
    monkeypatch.setattr(vs_mod.threading, "Thread", FakeThread)
    FakeThread.instances.clear()
    streamer, cap = _make_streamer([])
    result = streamer.start()
    assert result is streamer
    assert len(FakeThread.instances) == 1
    thread = FakeThread.instances[0]
    assert thread.started is True
    assert thread.kwargs.get("daemon") is True
    assert thread.kwargs.get("target") == streamer._update


def test_update_guarda_frame_y_resetea_retries(no_sleep, monkeypatch, capsys):
    reads = [_no_frame(), _no_frame(), _no_frame(), (True, _small_frame()), (True, _wide_frame())]
    streamer, cap = _make_streamer(reads)
    streamer._update()
    assert streamer.is_running is False
    assert streamer.current_frame.shape == (720, 1280, 3)  # reescalado de la frame ancha


def test_update_sin_reescalado_guarda_frame_small(no_sleep, monkeypatch):
    streamer, cap = _make_streamer([(True, _small_frame())])
    streamer.target_width = 640
    streamer._update()
    assert streamer.current_frame.shape == (180, 240, 3)


def test_update_frame_vacio_reintenta_y_loguea(no_sleep, monkeypatch, capsys):
    streamer, cap = _make_streamer([_no_frame(), _no_frame(), (True, _small_frame())])
    streamer._update()
    out = capsys.readouterr().out
    assert "[VideoStreamer] Frame no recibido (intento 1/3)" in out
    assert "[VideoStreamer] Frame no recibido (intento 2/3)" in out
    assert streamer.current_frame is not None


def test_update_excepcion_de_read_no_frena(no_sleep, monkeypatch, capsys):
    streamer, cap = _make_streamer([RuntimeError("boom"), (True, _small_frame())])
    streamer.target_width = 640
    streamer._update()
    out = capsys.readouterr().out
    assert "[VideoStreamer] Excepción: RuntimeError - boom" in out
    assert streamer.current_frame is not None


def test_get_frame_none_sin_frame():
    streamer, cap = _make_streamer([])
    assert streamer.get_frame() is None


def test_get_frame_devuelve_copia():
    streamer, cap = _make_streamer([])
    frame = _small_frame()
    streamer.current_frame = frame
    out = streamer.get_frame()
    out[0, 0, 0] = 255
    assert streamer.current_frame[0, 0, 0] == 90


def test_stop_libera_capture_si_abierta():
    streamer, cap = _make_streamer([])
    streamer.stop()
    assert streamer.is_running is False
    assert cap.released is True


def test_stop_no_libera_si_cerrada():
    streamer, cap = _make_streamer([], is_opened=False)
    streamer.stop()
    assert streamer.is_running is False
    assert cap.released is False


def test_stop_cap_none_no_crashea():
    streamer, cap = _make_streamer([])
    streamer.cap = None
    streamer.stop()
    assert streamer.is_running is False