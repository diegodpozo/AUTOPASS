"""Tests ronda #13: alpr/ws_client.py (ws_monitoring_worker).

Cubre el envío de frames por WebSocket con overlay opcional, frames vacíos, error al
procesar/enviar (break del bucle interno) y reconexión automática ante error de conexión.
"""
import asyncio
import base64

import numpy as np
import pytest

import alpr.ws_client as ws_mod
from alpr.ws_client import ws_monitoring_worker


class FakeStreamer:
    def __init__(self, frames=None):
        self.is_running = True
        self._frames = list(frames or [])

    def get_frame(self):
        if self._frames:
            return self._frames.pop(0)
        return np.zeros((180, 320, 3), dtype=np.uint8)


class FakeEngine:
    def __init__(self):
        self.overlay_calls = 0

    def get_frame_with_overlay(self, frame):
        self.overlay_calls += 1
        return frame


class FakeSocket:
    def __init__(self, streamer, on_send=None):
        self.streamer = streamer
        self.sent = []
        self.on_send = on_send

    async def send(self, data):
        self.sent.append(data)
        if self.on_send:
            await self.on_send(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakeBackendFactory:
    """Crea sockets por conexión; puede lanzar en las primeras conexiones y decidir
    en qué conexión terminar (marcar is_running=False)."""

    def __init__(self, streamer, raise_first=0, stop_on_connect=False, stop_at=None):
        self.streamer = streamer
        self.raise_first = raise_first
        self.stop_on_connect = stop_on_connect
        self.stop_at = stop_at
        self.connects = 0
        self.sockets = []

    def __call__(self, *args, **kwargs):
        self.connects += 1
        if self.connects <= self.raise_first:
            raise ConnectionRefusedError("server down")
        sock = FakeSocket(self.streamer, on_send=self._on_send)
        self.sockets.append(sock)
        if (self.stop_on_connect or self.stop_at == self.connects):
            self.streamer.is_running = False
        return sock

    async def _on_send(self, sock):
        pass


def _frame(fill=120, h=180, w=320):
    return np.full((h, w, 3), fill, dtype=np.uint8)


def _run(coro):
    return asyncio.run(coro)

@pytest.fixture
def no_sleep_cnt(monkeypatch):
    """asyncio.sleep no-op para mantener los bucles rápidos."""
    calls = {"n": 0}

    async def fake_sleep(s):
        calls["n"] += 1

    monkeypatch.setattr(ws_mod.asyncio, "sleep", fake_sleep)
    return calls


def test_envia_frames_sin_engine(monkeypatch):
    streamer = FakeStreamer(frames=[_frame()])
    factory = FakeBackendFactory(streamer, stop_on_connect=False)

    async def _on_send(sock):
        sock.streamer.is_running = False

    factory._on_send = _on_send
    monkeypatch.setattr(ws_mod.websockets, "connect", factory)

    async def test():
        await ws_monitoring_worker(streamer)
        return factory.sockets[0].sent

    sent = _run(test())
    assert len(sent) == 1
    raw = base64.b64decode(sent[0])
    assert raw[:2] == b"\xff\xd8"  # JPEG magic


def test_envia_frames_con_engine(monkeypatch):
    streamer = FakeStreamer(frames=[_frame()])
    engine = FakeEngine()
    factory = FakeBackendFactory(streamer, stop_on_connect=False)

    async def _on_send(sock):
        sock.streamer.is_running = False

    factory._on_send = _on_send
    monkeypatch.setattr(ws_mod.websockets, "connect", factory)

    async def test():
        await ws_monitoring_worker(streamer, engine)
        assert engine.overlay_calls == 1
        assert len(factory.sockets[0].sent) == 1

    _run(test())


def test_frame_none_no_envia(monkeypatch):
    streamer = FakeStreamer()

    class NoFrameStreamer:
        is_running = True

        def get_frame(self):
            return None

    no_frame = NoFrameStreamer()
    monkeypatch.setattr(ws_mod.websockets, "connect", FakeBackendFactory(no_frame, stop_on_connect=True))

    async def test():
        await ws_monitoring_worker(no_frame)

    _run(test())
    assert no_frame.is_running is False


def test_error_al_procesar_frame_breakea_bucle_interno(monkeypatch, no_sleep_cnt, capsys):
    streamer = FakeStreamer(frames=[_frame(), _frame(), _frame()])

    class ResizeThatFailsOnceStreamer(FakeStreamer):
        pass

    streamer = ResizeThatFailsOnceStreamer(frames=[_frame()])
    target = streamer
    calls = {"n": 0}
    real_resize = ws_mod.cv2.resize

    def fake_resize(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("dimension mismatch")
        return real_resize(*a, **k)

    monkeypatch.setattr(ws_mod.cv2, "resize", fake_resize)
    factory = FakeBackendFactory(streamer, stop_at=2)
    monkeypatch.setattr(ws_mod.websockets, "connect", factory)

    async def test():
        try:
            await ws_monitoring_worker(target)
            return True
        except Exception:
            return False

    ok = _run(test())
    assert ok
    out = capsys.readouterr().out
    assert "[!] Error al procesar/enviar frame" in out


def test_reconexion_tras_error_de_conexion(monkeypatch, no_sleep_cnt, capsys):
    streamer = FakeStreamer()
    factory = FakeBackendFactory(streamer, raise_first=2, stop_on_connect=True)
    monkeypatch.setattr(ws_mod.websockets, "connect", factory)

    async def test():
        await ws_monitoring_worker(streamer)
        return factory.connects

    connects = _run(test())
    out = capsys.readouterr().out
    assert connects == 3
    assert "[!] WS Streaming Error" in out
    assert "ConnectionRefusedError" in out