"""Tests ronda #13: routes/system/video.py.

Cubre el WebSocket /ws/video (nodos ALPR y espectadores con rol staff+), el aislado por
sucursal, /update-frame (nodo autorizado), /video-feed (MJPEG fallback), /capture y los
helpers _is_local_or_private / _is_trusted_alpr_node / _user_from_token.
"""
import asyncio
import importlib
import time

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

video_mod = importlib.import_module("routes.system.video")
manager = importlib.import_module("routes.system.common").manager

routes = video_mod.router
WebSocketDisconnect = video_mod.WebSocketDisconnect


class OnceDict(dict):
    """last_frames que devuelve cada valor una sola vez (permite cortar generadores)."""

    def get(self, key, default=None):
        value = super().get(key)
        if value is not None:
            self.pop(key, None)
        return value


class FakeUser:
    def __init__(self, rol="admin", sucursal=None, email="op@autopass.com.ar"):
        self.rol = rol
        self.sucursal = sucursal
        self.email = email


class FakeLog:
    def __init__(self, id=1, sucursal="Centro", imagen_path=None):
        self.id = id
        self.sucursal = sucursal
        self.imagen_path = imagen_path


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(routes)
    manager.active_connections.clear()
    manager.last_frames.clear()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def authed_staff(app_client):
    app_client.app.dependency_overrides[
        video_mod.get_operational_user
    ] = lambda: FakeUser(rol="admin")
    yield app_client
    app_client.app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# _is_local_or_private / _is_trusted_alpr_node
# ---------------------------------------------------------------------------

def test_is_local_or_private_loopback_y_privada():
    assert video_mod._is_local_or_private("127.0.0.1") is True
    assert video_mod._is_local_or_private("10.1.2.3") is True
    assert video_mod._is_local_or_private("192.168.1.9") is True
    assert video_mod._is_local_or_private("172.16.0.1") is True


def test_is_local_or_private_publica_e_invalida():
    assert video_mod._is_local_or_private("8.8.8.8") is False
    assert video_mod._is_local_or_private("testclient") is False
    assert video_mod._is_local_or_private("") is False


def test_is_trusted_alpr_node_con_secreto(monkeypatch):
    monkeypatch.setattr(video_mod.settings, "ALPR_NODE_SECRET", "s3cret")
    assert video_mod._is_trusted_alpr_node("1.1.1.1", "s3cret") is True
    assert video_mod._is_trusted_alpr_node("1.1.1.1", "malo") is False
    assert video_mod._is_trusted_alpr_node("1.1.1.1", "") is False


def test_is_trusted_alpr_node_sin_secreto_usa_red(monkeypatch):
    monkeypatch.setattr(video_mod.settings, "ALPR_NODE_SECRET", "")
    assert video_mod._is_trusted_alpr_node("127.0.0.1", "") is True
    assert video_mod._is_trusted_alpr_node("192.168.0.10", None) is True
    assert video_mod._is_trusted_alpr_node("200.100.10.1", "") is False


# ---------------------------------------------------------------------------
# WebSocket /ws/video
# ---------------------------------------------------------------------------

def test_ws_nodo_no_autorizado_cierra_4403(app_client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with app_client.websocket_connect("/ws/video/CAM01"):
            pass
    assert exc.value.code == 4403


def test_ws_nodo_autorizado_recibe_y_broadcast(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "_is_trusted_alpr_node", lambda *a, **k: True)
    with app_client.websocket_connect("/ws/video/cam01?node_secret=x") as ws:
        ws.send_text("BASE64DATA")
    assert manager.last_frames.get("CAM01") == "BASE64DATA"


def test_ws_nodo_error_en_broadcast_no_crashea(app_client, monkeypatch, caplog):
    monkeypatch.setattr(video_mod, "_is_trusted_alpr_node", lambda *a, **k: True)

    async def boom(*a, **k):
        raise RuntimeError("broadcast caído")

    monkeypatch.setattr(video_mod.manager, "broadcast_frame", boom)
    with app_client.websocket_connect("/ws/video/CAM01?node_secret=x") as ws:
        ws.send_text("DATA")
    joined = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "Error en nodo ALPR CAM01" in joined


def test_ws_espectador_role_denegado_cierra_4403(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: {"sub": "cli@x.com"})
    monkeypatch.setattr(
        video_mod.UserRepository, "get_active_by_email",
        lambda db, email: FakeUser(rol="cliente", email=email),
    )
    monkeypatch.setattr(video_mod, "get_db", lambda: iter([None]))
    with pytest.raises(WebSocketDisconnect) as exc:
        with app_client.websocket_connect("/ws/video/CAM01?token=abc"):
            pass
    assert exc.value.code == 4403


def test_ws_espectador_aceptado_recibe_ultimo_frame(app_client, monkeypatch):
    manager.last_frames["CAM01"] = "ULTIMOFRAME"
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: {"sub": "admin@x.com"})
    monkeypatch.setattr(
        video_mod.UserRepository, "get_active_by_email",
        lambda db, email: FakeUser(rol="admin", sucursal=None, email=email),
    )
    monkeypatch.setattr(video_mod, "get_db", lambda: iter([None]))
    with app_client.websocket_connect("/ws/video/CAM01?token=abc") as ws:
        assert ws.receive_text() == "ULTIMOFRAME"
        ws.send_text("pulse")
    deadline = time.time() + 3
    while manager.active_connections.get("CAM01") and time.time() < deadline:
        time.sleep(0.01)
    assert manager.active_connections.get("CAM01") == []


def test_ws_espectador_sucursal_distinta_cierra_4003(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: {"sub": "staff@x.com"})
    monkeypatch.setattr(
        video_mod.UserRepository, "get_active_by_email",
        lambda db, email: FakeUser(rol="staff", sucursal="Sur", email=email),
    )
    monkeypatch.setattr(video_mod, "get_db", lambda: iter([None]))
    with pytest.raises(WebSocketDisconnect) as exc:
        with app_client.websocket_connect("/ws/video/OTRA_1?token=abc"):
            pass
    assert exc.value.code == 4003


def test_ws_error_al_resolver_usuario_trata_como_nodo(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: {"sub": "x@y.z"})
    monkeypatch.setattr(
        video_mod, "get_db",
        lambda: (_ for _ in ()).throw(RuntimeError("db caída")),
    )
    monkeypatch.setattr(video_mod, "_is_trusted_alpr_node", lambda *a, **k: True)
    with app_client.websocket_connect("/ws/video/CAM01?token=abc") as ws:
        ws.send_text("DATA")
    assert manager.last_frames.get("CAM01") == "DATA"


# ---------------------------------------------------------------------------
# update-frame HTTP
# ---------------------------------------------------------------------------

def test_update_frame_nodo_autorizado(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "_is_trusted_alpr_node", lambda *a, **k: True)
    resp = app_client.post("/update-frame/CAM-2", json={"image": "frame64"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert manager.last_frames.get("CAM-2") == "frame64"


def test_update_frame_sin_imagen_ok_sin_broadcast(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "_is_trusted_alpr_node", lambda *a, **k: True)
    resp = app_client.post("/update-frame/CAM-3", json={"foo": 1})
    assert resp.status_code == 200
    assert "CAM-3" not in manager.last_frames


def test_update_frame_nodo_no_autorizado_403(app_client):
    resp = app_client.post("/update-frame/CAM-4")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# video-feed (MJPEG)
# ---------------------------------------------------------------------------

def _feed_gen(camera_id, staff, monkeypatch):
    resp = asyncio.run(video_mod.video_feed_legacy(camera_id, staff))
    return resp.body_iterator


def _drive_feed(gen, n_yields=0):
    """Consume n iteraciones del async generator en un único event loop."""

    async def collect():
        chunks = []
        for _ in range(n_yields):
            chunks.append(await gen.__anext__())
        return chunks

    return asyncio.run(collect())


def _drive_feed_raises(gen):
    """Consume hasta que el generador lance (RuntimeError o fin)."""

    async def collect():
        try:
            while True:
                await gen.__anext__()
            return False
        except (RuntimeError, StopAsyncIteration):
            return True

    return asyncio.run(collect())


def test_video_feed_genera_frames_y_corta(authed_staff, monkeypatch):
    manager.last_frames = OnceDict({"CAM-A": "anVwZ2RhdGE="})
    calls = {"n": 0}

    def fake_sleep(s):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise RuntimeError("fin del generador")

    monkeypatch.setattr(video_mod.time, "sleep", fake_sleep)
    gen = _feed_gen("CAM-A", FakeUser(rol="admin"), monkeypatch)
    chunks = _drive_feed(gen, 1)
    assert b"--frame\r" in chunks[0]
    assert b"jupgdata" in chunks[0]  # base64('anVwZ2RhdGE=') decodificado
    assert _drive_feed_raises(gen) is True


def test_video_feed_sin_frame_todavia_corta(authed_staff, monkeypatch):
    calls = {"n": 0}

    def fake_sleep(s):
        calls["n"] += 1
        if calls["n"] >= 3:
            raise RuntimeError("fin del generador")

    monkeypatch.setattr(video_mod.time, "sleep", fake_sleep)
    gen = _feed_gen("CAM-B", FakeUser(rol="admin"), monkeypatch)
    assert _drive_feed_raises(gen) is True


def test_video_feed_sucursal_distinta_403(app_client):
    app_client.app.dependency_overrides[
        video_mod.get_operational_user
    ] = lambda: FakeUser(rol="staff", sucursal="Centro")
    resp = app_client.get("/video-feed/OTRA_1")
    assert resp.status_code == 403
    app_client.app.dependency_overrides.clear()


def test_video_feed_sucursal_igual_ok(monkeypatch):
    calls = {"n": 0}

    def fake_sleep(s):
        calls["n"] += 1
        if calls["n"] >= 3:
            raise RuntimeError("fin del generador")

    monkeypatch.setattr(video_mod.time, "sleep", fake_sleep)
    gen = _feed_gen("CENTRO_1", FakeUser(rol="staff", sucursal="Centro"), monkeypatch)
    assert _drive_feed_raises(gen) is True


# ---------------------------------------------------------------------------
# _user_from_token / capture
# ---------------------------------------------------------------------------

def test_user_from_token_ok(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: {"sub": "staff@x.com"})
    monkeypatch.setattr(
        video_mod.UserRepository, "get_active_by_email",
        lambda db, email: FakeUser(rol="staff", email=email),
    )
    user = video_mod._user_from_token("abc", None)
    assert user.email == "staff@x.com"


def test_user_from_token_invalido_401(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: None)
    with pytest.raises(Exception) as exc:
        video_mod._user_from_token("abc", None)
    assert exc.value.status_code == 401


def test_user_from_token_usuario_no_encontrado_401(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: {"sub": "x@x.com"})
    monkeypatch.setattr(video_mod.UserRepository, "get_active_by_email", lambda *a, **k: None)
    with pytest.raises(Exception) as exc:
        video_mod._user_from_token("abc", None)
    assert exc.value.status_code == 401


def test_user_from_token_role_denegado_403(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: {"sub": "cli@x.com"})
    monkeypatch.setattr(
        video_mod.UserRepository, "get_active_by_email",
        lambda db, email: FakeUser(rol="cliente", email=email),
    )
    with pytest.raises(Exception) as exc:
        video_mod._user_from_token("abc", None)
    assert exc.value.status_code == 403


def _capture_setup(app_client, monkeypatch, log, token_decoder=None, user_factory=None):
    app_client.app.dependency_overrides[
        video_mod.get_db
    ] = lambda: iter([None])
    monkeypatch.setattr(
        video_mod.AccessRepository, "get_by_id",
        lambda db, log_id: log,
    )
    if token_decoder is None:
        token_decoder = lambda t: {"sub": "staff@x.com"}  # noqa: E731
    monkeypatch.setattr(video_mod, "decode_access_token", token_decoder)
    if user_factory is not None:
        monkeypatch.setattr(
            video_mod.UserRepository, "get_active_by_email",
            user_factory,
        )
    else:
        monkeypatch.setattr(
            video_mod.UserRepository, "get_active_by_email",
            lambda db, email: FakeUser(rol="admin", email=email),
        )


def test_capture_sin_token_401(app_client, monkeypatch):
    monkeypatch.setattr(video_mod, "decode_access_token", lambda t: {"sub": "a@b.c"})
    monkeypatch.setattr(video_mod.UserRepository, "get_active_by_email",
                        lambda db, e: FakeUser(rol="admin"))
    resp = app_client.get("/capture/1")
    assert resp.status_code == 401


def _fake_fileresponse(monkeypatch):
    def fake(path, **kwargs):
        return Response(content=path)

    monkeypatch.setattr(video_mod, "FileResponse", fake)


def test_capture_por_header_bearer_ok(app_client, monkeypatch):
    _capture_setup(
        app_client, monkeypatch,
        log=FakeLog(imagen_path="logs/1.jpg"),
    )
    _fake_fileresponse(monkeypatch)
    monkeypatch.setattr(video_mod.os.path, "exists", lambda p: True)
    resp = app_client.get("/capture/1", headers={"Authorization": "Bearer abc"})
    assert resp.status_code == 200
    assert "1.jpg" in resp.text


def test_capture_token_query_mal_401(app_client, monkeypatch):
    _capture_setup(app_client, monkeypatch, log=None, token_decoder=lambda t: None)
    resp = app_client.get("/capture/1?token=abc")
    assert resp.status_code == 401


def test_capture_log_no_existe_404(app_client, monkeypatch):
    _capture_setup(app_client, monkeypatch, log=None)
    resp = app_client.get("/capture/99?token=abc")
    assert resp.status_code == 404


def test_capture_role_cliente_403(app_client, monkeypatch):
    _capture_setup(
        app_client, monkeypatch,
        log=FakeLog(sucursal="Centro", imagen_path="x.jpg"),
        user_factory=lambda db, email: FakeUser(rol="cliente", email=email),
    )
    resp = app_client.get("/capture/1?token=abc")
    assert resp.status_code == 403


def test_capture_sucursal_distinta_403(app_client, monkeypatch):
    _capture_setup(
        app_client, monkeypatch,
        log=FakeLog(sucursal="Centro", imagen_path="x.jpg"),
        user_factory=lambda db, email: FakeUser(rol="staff", sucursal="Sur", email=email),
    )
    resp = app_client.get("/capture/1?token=abc")
    assert resp.status_code == 403


def test_capture_image_no_existe_devuelve_logo(app_client, monkeypatch):
    _capture_setup(app_client, monkeypatch, log=FakeLog(imagen_path="no/está.jpg"))
    _fake_fileresponse(monkeypatch)
    monkeypatch.setattr(video_mod.os.path, "exists", lambda p: False)
    resp = app_client.get("/capture/1?token=abc")
    assert resp.status_code == 200
    assert "logo.png" in resp.text


def test_capture_sin_imagen_path_devuelve_logo(app_client, monkeypatch):
    _capture_setup(app_client, monkeypatch, log=FakeLog(imagen_path=None))
    _fake_fileresponse(monkeypatch)
    resp = app_client.get("/capture/1?token=abc")
    assert resp.status_code == 200
    assert "logo.png" in resp.text