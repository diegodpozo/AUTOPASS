"""Tests ronda #15: routes/system/cameras.py.

Cubre la gestión de cámaras ALPR: config de fuente por gate (get/set), control del
servicio ALPR (start/stop por gate y por cámara dinámica), CRUD de cámaras, el
streaming de consola del subproceso al front (via WebSocket), `_schedule_async`,
el aviso de lectura al dashboard y los helpers de `routes/system/common.py`
(stop_all_cameras y broadcast de consola/frames).
"""
import asyncio
import importlib
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.config import settings
from core.database import Base
from core.normalize import normalize_name as normalize_system_name
from models.enums import UserRole
from services.notification_service import NotificationService

cam = importlib.import_module("routes.system.cameras")
common = importlib.import_module("routes.system.common")
CAMERA_PROCESSES = cam.CAMERA_PROCESSES
manager = common.manager


class FakeUser:
    def __init__(self, rol=UserRole.ADMIN, sucursal=None):
        self.rol = rol
        self.sucursal = sucursal


CURRENT = {"user": FakeUser()}


class FakeStream:
    """stdout del subproceso; readline devuelve lineas hasta la centinela b''."""

    def __init__(self, lines=(), exc=None):
        self.lines = list(lines)
        self.exc = exc
        self.closed = False

    def readline(self):
        if self.exc:
            raise self.exc
        if self.lines:
            return self.lines.pop(0)
        return b""

    def close(self):
        self.closed = True


class FakeProc:
    instances = []

    def __init__(self, cmd=None, env=None, stdout=None, stderr=None, creationflags=0):
        self.cmd = cmd
        self.env = env
        self.stdout = stdout or FakeStream()
        self.stderr = stderr
        self.creationflags = creationflags
        self.poll_ret = None
        self.exc_poll = False
        self.pid = 4321
        self.terminated = 0
        FakeProc.instances.append(self)

    def poll(self):
        if self.exc_poll:
            raise RuntimeError("poll boom")
        return self.poll_ret

    def terminate(self):
        self.terminated += 1


class FakeThread:
    instances = []

    def __init__(self, target=None, args=(), kwargs=None, daemon=None):
        self.target = target
        self.args = args
        self.started = False
        FakeThread.instances.append(self)

    def start(self):
        self.started = True


class FakeLoop:
    def __init__(self, running=False, exc=False):
        self._running = running
        self._exc = exc

    def is_running(self):
        if self._exc:
            raise RuntimeError("loop caido")
        return self._running


@pytest.fixture
def node_secret(monkeypatch):
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "s3cret")
    yield "s3cret"


@pytest.fixture
def client(node_secret):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(cam.router)
    app.dependency_overrides[cam.get_db] = override_get_db
    app.dependency_overrides[cam.get_operational_user] = lambda: CURRENT["user"]
    CAMERA_PROCESSES.clear()
    with TestClient(app) as c:
        yield c, TestSession
    app.dependency_overrides.clear()
    CAMERA_PROCESSES.clear()


def _set_staff(rol=UserRole.STAFF, sucursal="Centro"):
    CURRENT["user"] = FakeUser(rol=rol, sucursal=sucursal)


@pytest.fixture(autouse=True)
def _reset_staff():
    yield
    CURRENT["user"] = FakeUser()


def _seed_camera(db_factory, nombre="Entrada", tipo="ENTRADA", source="0",
                 sucursal="Centro", activa=True, cam_id=None, orden=None):
    db = db_factory()
    c = models.ParkingCamera(nombre=nombre, tipo=tipo, source=source,
                             sucursal=sucursal, activa=activa, orden=orden)
    if cam_id is not None:
        c.id = cam_id
    db.add(c)
    db.commit()
    db.refresh(c)
    db.close()
    return c


def _seed_setting(db_factory, clave, valor_str=None, sucursal=None):
    db = db_factory()
    s = models.Settings(clave=clave, valor_str=valor_str, sucursal=sucursal)
    db.add(s)
    db.commit()
    db.refresh(s)
    db.close()
    return s


def _get_setting(db_factory, clave):
    db = db_factory()
    s = db.query(models.Settings).filter(models.Settings.clave == clave).first()
    db.close()
    return s


def _proc_id_of(c):
    norm = normalize_system_name(c.sucursal) if c.sucursal else "GLOBAL"
    return f"{norm}_{c.tipo}_{c.id}".upper()


def _set_running(c, exc_poll=False):
    proc = FakeProc()
    proc.exc_poll = exc_poll
    CAMERA_PROCESSES[_proc_id_of(c)] = proc
    return proc


# ---------------------------------------------------------------------------
# _schedule_async
# ---------------------------------------------------------------------------

async def _dummy_coro():
    return None


def test_schedule_async_loop_corriendo_programa_coro(monkeypatch):
    loop_fake = FakeLoop(running=True)
    monkeypatch.setattr(NotificationService, "_loop", loop_fake)
    scheduled = []
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe",
                        lambda coro, loop: scheduled.append((coro, loop)))
    coro = _dummy_coro()
    assert cam._schedule_async(coro) is True
    assert scheduled  # programó la coroutine en el loop


def test_schedule_async_loop_no_corriendo_devuelve_false(monkeypatch):
    monkeypatch.setattr(NotificationService, "_loop", FakeLoop(running=False))
    assert cam._schedule_async(_dummy_coro()) is False


def test_schedule_async_sin_loop_devuelve_false(monkeypatch):
    monkeypatch.setattr(NotificationService, "_loop", None)
    assert cam._schedule_async(_dummy_coro()) is False


def test_schedule_async_excepcion_devuelve_false(monkeypatch):
    monkeypatch.setattr(NotificationService, "_loop", FakeLoop(exc=True))
    assert cam._schedule_async(_dummy_coro()) is False


# ---------------------------------------------------------------------------
# _stream_console_output
# ---------------------------------------------------------------------------

def test_stream_console_envia_linea_por_websocket(monkeypatch):
    proc = FakeProc(stdout=FakeStream(lines=[b"LEYENDO PATENTE ABC123\n", b""]))
    scheduled = []
    monkeypatch.setattr(cam, "_schedule_async", lambda coro: scheduled.append(coro))
    cam._stream_console_output(proc, "CENTRO_1")
    assert len(scheduled) == 1
    assert proc.stdout is None


def test_stream_console_lineas_vacias_no_reenvian(monkeypatch):
    proc = FakeProc(stdout=FakeStream(lines=[b"\n", b""]))
    scheduled = []
    monkeypatch.setattr(cam, "_schedule_async", lambda coro: scheduled.append(coro))
    cam._stream_console_output(proc, "CENTRO_1")
    assert scheduled == []
    assert proc.stdout is None


def test_stream_console_decode_con_errores_replace(monkeypatch):
    proc = FakeProc(stdout=FakeStream(lines=[b"\xff\xfe patente\n", b""]))
    scheduled = []
    monkeypatch.setattr(cam, "_schedule_async", lambda coro: scheduled.append(coro))
    cam._stream_console_output(proc, "CENTRO_1")
    assert len(scheduled) == 1


def test_stream_console_error_de_lectura_no_propaga(monkeypatch):
    proc = FakeProc(stdout=FakeStream(exc=RuntimeError("io boom")))
    cam._stream_console_output(proc, "CENTRO_1")
    assert proc.stdout is None


class ProcStdoutNoAsignable:
    """Defiende el except del finally (56-57): no permite reasignar stdout."""

    def __init__(self, stdout):
        self._s = stdout

    @property
    def stdout(self):
        return self._s

    @stdout.setter
    def stdout(self, value):
        raise AttributeError("readonly")


def test_stream_console_finally_no_asignable_no_propaga(monkeypatch):
    proc = ProcStdoutNoAsignable(FakeStream(exc=RuntimeError("io boom")))
    cam._stream_console_output(proc, "CENTRO_1")
    assert proc.stdout is not None


# ---------------------------------------------------------------------------
# get_camera_config
# ---------------------------------------------------------------------------

def test_get_camera_config_admin_sin_setting(client, monkeypatch):
    c, _ = client
    resp = c.get("/camera-config/centro_1")
    assert resp.status_code == 200
    assert resp.json() == {"gate_id": "CENTRO_1", "source": "0", "is_running": False}


def test_get_camera_config_con_setting(client):
    c, db_factory = client
    _seed_setting(db_factory, "CAMERA_SOURCE_CENTRO_1", valor_str="rtsp://cam")
    resp = c.get("/camera-config/CENTRO_1")
    assert resp.json()["source"] == "rtsp://cam"
    assert resp.json()["is_running"] is False
    assert resp.json()["gate_id"] == "CENTRO_1"


def test_get_camera_config_proceso_corriendo(client):
    c, db_factory = client
    _seed_setting(db_factory, "CAMERA_SOURCE_CENTRO_1", valor_str="1")
    gate = "CENTRO_1"
    CAMERA_PROCESSES[gate] = FakeProc()
    resp = c.get("/camera-config/CENTRO_1")
    assert resp.json()["is_running"] is True
    CAMERA_PROCESSES.pop(gate, None)


def test_get_camera_config_staff_misma_sucursal(client):
    _set_staff(sucursal="Centro")
    c, _ = client
    resp = c.get("/camera-config/CENTRO_1")
    assert resp.status_code == 200


def test_get_camera_config_staff_otra_sucursal_403(client):
    _set_staff(sucursal="Centro")
    c, _ = client
    resp = c.get("/camera-config/OTRA_1")
    assert resp.status_code == 403


def test_get_camera_config_staff_sin_sucursal_pasa(client):
    _set_staff(sucursal=None)
    c, _ = client
    resp = c.get("/camera-config/CENTRO_1")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# set_camera_config
# ---------------------------------------------------------------------------

def test_set_camera_config_admin_crea_setting(client):
    c, db_factory = client
    resp = c.post("/camera-config", json={"gate_id": "CENTRO_1", "source": "1"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "message": "Configuración guardada"}
    s = _get_setting(db_factory, "CAMERA_SOURCE_CENTRO_1")
    assert s.valor_str == "1"


def test_set_camera_config_admin_actualiza_existente(client):
    c, db_factory = client
    _seed_setting(db_factory, "CAMERA_SOURCE_CENTRO_1", valor_str="0")
    resp = c.post("/camera-config", json={"gate_id": "CENTRO_1", "source": "2"})
    assert resp.status_code == 200
    s = _get_setting(db_factory, "CAMERA_SOURCE_CENTRO_1")
    assert s.valor_str == "2"


def test_set_camera_config_staff_mismo_prefijo_ok(client):
    _set_staff(sucursal="Centro")
    c, _ = client
    resp = c.post("/camera-config", json={"gate_id": "CENTRO_2", "source": "1"})
    assert resp.status_code == 200


def test_set_camera_config_staff_otro_prefijo_403(client):
    _set_staff(sucursal="Centro")
    c, _ = client
    resp = c.post("/camera-config", json={"gate_id": "OTRA_2", "source": "1"})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# control_camera_service (start/stop por gate)
# ---------------------------------------------------------------------------

def test_control_start_ya_en_ejecucion_error(client):
    c, _ = client
    CAMERA_PROCESSES["CENTRO_1"] = FakeProc()
    resp = c.post("/camera-service/CENTRO_1/start")
    assert resp.json() == {"status": "error", "message": "Ya está en ejecución"}
    CAMERA_PROCESSES.pop("CENTRO_1", None)


def test_control_start_qr_configura_gate_type_qr(client, monkeypatch):
    c, db_factory = client
    _seed_setting(db_factory, "CAMERA_SOURCE_CENTRO_QR_1", valor_str="rtsp://c1")
    monkeypatch.setattr(cam.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(cam.threading, "Thread", FakeThread)
    resp = c.post("/camera-service/centro_qr_1/start")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    proc = FakeProc.instances[-1]
    assert proc.env["GATE_ID"] == "CENTRO_QR_1"
    assert proc.env["VIDEO_SOURCE"] == "rtsp://c1"
    assert proc.env["GATE_TYPE"] == "qr"
    assert proc.env["BACKEND_URL"] == "http://127.0.0.1:8000"
    assert proc.env["PYTHONUNBUFFERED"] == "1"
    assert proc.cmd == ["python", "alpr_service.py"] or "alpr_service.py" in proc.cmd
    assert CAMERA_PROCESSES["CENTRO_QR_1"] is proc
    thread = FakeThread.instances[-1]
    assert thread.started is True
    assert thread.args[0] is proc


def test_control_start_entrada_y_salida_determinan_gate_type(client, monkeypatch):
    c, _ = client
    monkeypatch.setattr(cam.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(cam.threading, "Thread", FakeThread)
    c.post("/camera-service/CENTRO_ENTRADA_1/start")
    assert FakeProc.instances[-1].env["GATE_TYPE"] == "entrada"
    c.post("/camera-service/CENTRO_SALIDA_1/start")
    assert FakeProc.instances[-1].env["GATE_TYPE"] == "salida"


def test_control_start_error_de_popen(client, monkeypatch):
    c, _ = client

    def boom(*a, **k):
        raise RuntimeError("no fork")

    monkeypatch.setattr(cam.subprocess, "Popen", boom)
    resp = c.post("/camera-service/CENTRO_1/start")
    assert resp.json() == {"status": "error", "message": "no fork"}
    assert "CENTRO_1" not in CAMERA_PROCESSES


def test_control_stop_no_en_ejecucion_error(client):
    c, _ = client
    resp = c.post("/camera-service/CENTRO_1/stop")
    assert resp.json() == {"status": "error", "message": "No está en ejecución"}


def test_control_stop_nt_taskkill(client, monkeypatch):
    c, _ = client
    proc = FakeProc()
    CAMERA_PROCESSES["CENTRO_1"] = proc
    kills = []
    monkeypatch.setattr(cam.os, "name", "nt")
    monkeypatch.setattr(cam.subprocess, "call",
                        lambda *a, **k: kills.append(a))
    resp = c.post("/camera-service/CENTRO_1/stop")
    assert resp.json() == {"status": "ok", "message": "Servicio detenido"}
    assert kills and "taskkill" in kills[0][0]
    assert "CENTRO_1" not in CAMERA_PROCESSES


def test_control_stop_posix_terminate(client, monkeypatch):
    c, _ = client
    proc = FakeProc()
    CAMERA_PROCESSES["CENTRO_1"] = proc
    monkeypatch.setattr(cam.os, "name", "posix")
    resp = c.post("/camera-service/CENTRO_1/stop")
    assert resp.json()["status"] == "ok"
    assert proc.terminated == 1
    assert "CENTRO_1" not in CAMERA_PROCESSES


def test_control_stop_fin_proceso_sin_detener(client, monkeypatch):
    c, _ = client
    proc = FakeProc()
    proc.poll_ret = 0  # el proceso ya terminó
    CAMERA_PROCESSES["CENTRO_1"] = proc
    monkeypatch.setattr(cam.os, "name", "nt")
    resp = c.post("/camera-service/CENTRO_1/stop")
    assert resp.json()["status"] == "ok"
    assert "CENTRO_1" not in CAMERA_PROCESSES


def test_control_stop_excepcion_error(client, monkeypatch):
    c, _ = client
    proc = FakeProc()
    proc.exc_poll = True
    CAMERA_PROCESSES["CENTRO_1"] = proc
    resp = c.post("/camera-service/CENTRO_1/stop")
    assert resp.json() == {"status": "error", "message": "poll boom"}


def test_control_accion_invalida(client):
    c, _ = client
    resp = c.post("/camera-service/CENTRO_1/reboot")
    assert resp.json() == {"status": "error", "message": "Acción no válida"}


def test_control_staff_otra_sucursal_403(client):
    _set_staff(sucursal="Centro")
    c, _ = client
    resp = c.post("/camera-service/OTRA_1/start")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# get_cameras
# ---------------------------------------------------------------------------

def test_get_cameras_admin_ve_todas_y_proceso_corriendo(client):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    cam_s = _seed_camera(db_factory, cam_id=2, tipo="SALIDA", sucursal="Sur")
    _set_running(cam_s)
    resp = c.get("/cameras")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    by_id = {r["id"]: r for r in rows}
    assert by_id[cam_c.id]["is_running"] is False
    assert by_id[cam_s.id]["is_running"] is True


def test_get_cameras_staff_solo_su_sucursal(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _seed_camera(db_factory, cam_id=2, tipo="ENTRADA", sucursal="Sur")
    _set_staff(sucursal="Centro")
    rows = c.get("/cameras").json()
    assert len(rows) == 1
    assert rows[0]["sucursal"] == "Centro"


def test_get_cameras_staff_sin_sucursal_todas(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _seed_camera(db_factory, cam_id=2, tipo="ENTRADA", sucursal=None)
    _set_staff(sucursal=None)
    rows = c.get("/cameras").json()
    assert len(rows) == 2


def test_get_cameras_vacio(client):
    c, _ = client
    assert c.get("/cameras").json() == []


def test_get_cameras_respeta_orden_manual(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro", orden=3)
    _seed_camera(db_factory, cam_id=2, tipo="ENTRADA", sucursal="Centro", orden=1)
    _seed_camera(db_factory, cam_id=3, tipo="ENTRADA", sucursal="Centro", orden=2)
    rows = c.get("/cameras").json()
    assert [r["id"] for r in rows] == [2, 3, 1]
    assert rows[0]["orden"] == 1


def test_get_cameras_orden_null_va_al_final(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro", orden=5)
    _seed_camera(db_factory, cam_id=2, tipo="ENTRADA", sucursal="Centro", orden=None)
    rows = c.get("/cameras").json()
    assert [r["id"] for r in rows] == [1, 2]


# ---------------------------------------------------------------------------
# reorder_cameras (PUT /cameras/order)
# ---------------------------------------------------------------------------

def test_reorder_cameras_admin_asigna_orden_secuencial(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _seed_camera(db_factory, cam_id=2, tipo="ENTRADA", sucursal="Centro")
    _seed_camera(db_factory, cam_id=3, tipo="ENTRADA", sucursal="Centro")
    resp = c.put("/cameras/order", json={"ids": [3, 1, 2]})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    rows = c.get("/cameras").json()
    assert [r["id"] for r in rows] == [3, 1, 2]
    db = db_factory()
    ordenes = {x.id: x.orden for x in db.query(models.ParkingCamera).all()}
    db.close()
    assert ordenes == {3: 1, 1: 2, 2: 3}


def test_reorder_cameras_id_inexistente_404(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    resp = c.put("/cameras/order", json={"ids": [1, 999]})
    assert resp.status_code == 404


def test_reorder_cameras_staff_misma_sucursal_ok(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _seed_camera(db_factory, cam_id=2, tipo="ENTRADA", sucursal="Centro")
    _set_staff(sucursal="Centro")
    resp = c.put("/cameras/order", json={"ids": [2, 1]})
    assert resp.status_code == 200
    rows = c.get("/cameras").json()
    assert [r["id"] for r in rows] == [2, 1]


def test_reorder_cameras_staff_otra_sucursal_403(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Sur")
    _set_staff(sucursal="Centro")
    resp = c.put("/cameras/order", json={"ids": [1]})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# create_camera
# ---------------------------------------------------------------------------

def test_create_camera_admin_usa_sucursal_del_payload(client):
    c, _ = client
    payload = {"nombre": "Entrada Norte", "tipo": "entrada", "source": "0",
               "sucursal": "Sur", "activa": True}
    resp = c.post("/cameras", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tipo"] == "ENTRADA"
    assert body["sucursal"] == "Sur"
    assert body["is_running"] is False
    assert body["id"] > 0


def test_create_camera_staff_fuerza_su_sucursal(client):
    _set_staff(sucursal="Centro")
    c, _ = client
    payload = {"nombre": "Nueva", "tipo": "ENTRADA", "source": "1",
               "sucursal": "Sur", "activa": False}
    resp = c.post("/cameras", json=payload)
    assert resp.json()["sucursal"] == "Centro"


# ---------------------------------------------------------------------------
# update_camera
# ---------------------------------------------------------------------------

def test_update_camera_404(client):
    c, _ = client
    payload = {"nombre": "X", "tipo": "ENTRADA", "source": "0", "activa": True}
    resp = c.put("/cameras/999", json=payload)
    assert resp.status_code == 404


def test_update_camera_staff_otra_sucursal_403(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_staff(sucursal="Sur")
    payload = {"nombre": "X", "tipo": "ENTRADA", "source": "0", "activa": True}
    assert c.put("/cameras/1", json=payload).status_code == 403


def test_update_camera_admin_ok_con_is_running(client):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    CAMERA_PROCESSES["CENTRO_PATENTE_1"] = FakeProc()  # proc_id con el tipo nuevo
    payload = {"nombre": "Patente Nueva", "tipo": "patente", "source": "rtsp://x",
               "sucursal": "Centro", "activa": False}
    resp = c.put(f"/cameras/{cam_c.id}", json=payload)
    body = resp.json()
    assert body["nombre"] == "Patente Nueva"
    assert body["tipo"] == "PATENTE"
    assert body["source"] == "rtsp://x"
    assert body["activa"] is False
    assert body["is_running"] is True
    CAMERA_PROCESSES.pop("CENTRO_PATENTE_1", None)


def test_update_camera_staff_no_permite_cambiar_sucursal(client):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_staff(sucursal="Centro")
    payload = {"nombre": "Renombrada", "tipo": "ENTRADA", "source": "0",
               "sucursal": "Sur", "activa": True}
    body = c.put(f"/cameras/{cam_c.id}", json=payload).json()
    assert body["sucursal"] == "Centro"


# ---------------------------------------------------------------------------
# delete_camera
# ---------------------------------------------------------------------------

def test_delete_camera_404(client):
    assert client[0].delete("/cameras/999").status_code == 404


def test_delete_camera_staff_otra_sucursal_403(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_staff(sucursal="Sur")
    assert c.delete("/cameras/1").status_code == 403


def test_delete_camera_sin_proceso(client):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    resp = c.delete(f"/cameras/{cam_c.id}")
    assert resp.json() == {"status": "ok", "message": "Cámara eliminada"}
    db = db_factory()
    assert db.query(models.ParkingCamera).filter(
        models.ParkingCamera.id == cam_c.id).first() is None
    db.close()


def test_delete_camera_con_proceso_nt_taskkill(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_running(cam_c)
    kills = []
    monkeypatch.setattr(cam.os, "name", "nt")
    monkeypatch.setattr(cam.subprocess, "call", lambda *a, **k: kills.append(a))
    resp = c.delete(f"/cameras/{cam_c.id}")
    assert resp.json()["status"] == "ok"
    assert "taskkill" in kills[0][0]
    assert _proc_id_of(cam_c) not in CAMERA_PROCESSES


def test_delete_camera_con_proceso_posix_terminate(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    proc = _set_running(cam_c)
    monkeypatch.setattr(cam.os, "name", "posix")
    resp = c.delete(f"/cameras/{cam_c.id}")
    assert resp.json()["status"] == "ok"
    assert proc.terminated == 1
    assert _proc_id_of(cam_c) not in CAMERA_PROCESSES


def test_delete_camera_proceso_con_error_en_poll(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_running(cam_c, exc_poll=True)
    monkeypatch.setattr(cam.os, "name", "posix")
    resp = c.delete(f"/cameras/{cam_c.id}")
    assert resp.json()["status"] == "ok"
    assert _proc_id_of(cam_c) not in CAMERA_PROCESSES


# ---------------------------------------------------------------------------
# control_dynamic_camera_service
# ---------------------------------------------------------------------------

def test_dynamic_404(client):
    assert client[0].post("/cameras/999/control/start").status_code == 404


def test_dynamic_staff_otra_sucursal_403(client):
    c, db_factory = client
    _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_staff(sucursal="Sur")
    assert c.post("/cameras/1/control/start").status_code == 403


def test_dynamic_start_ya_en_ejecucion_error(client):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_running(cam_c)
    resp = c.post(f"/cameras/{cam_c.id}/control/start")
    assert resp.json() == {"status": "error", "message": "Ya está en ejecución"}


def test_dynamic_start_qr(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=5, tipo="QR", source="rtsp://q",
                         sucursal="Centro")
    monkeypatch.setattr(cam.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(cam.threading, "Thread", FakeThread)
    resp = c.post(f"/cameras/{cam_c.id}/control/start")
    assert resp.json() == {"status": "ok",
                           "message": f"Servicio para {cam_c.nombre} iniciado"}
    proc = FakeProc.instances[-1]
    assert proc.env["GATE_ID"] == _proc_id_of(cam_c)
    assert proc.env["VIDEO_SOURCE"] == "rtsp://q"
    assert proc.env["GATE_TYPE"] == "qr"


def test_dynamic_start_egreso_gate_type_salida(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=6, tipo="EGRESO", source="0",
                         sucursal="Centro")
    monkeypatch.setattr(cam.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(cam.threading, "Thread", FakeThread)
    c.post(f"/cameras/{cam_c.id}/control/start")
    assert FakeProc.instances[-1].env["GATE_TYPE"] == "salida"


def test_dynamic_start_patente_gate_type_entrada(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=7, tipo="PATENTE", source="0",
                         sucursal="Centro")
    monkeypatch.setattr(cam.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(cam.threading, "Thread", FakeThread)
    c.post(f"/cameras/{cam_c.id}/control/start")
    assert FakeProc.instances[-1].env["GATE_TYPE"] == "entrada"


def test_dynamic_start_tipo_default(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=8, tipo="OTRO", source="0",
                         sucursal="Centro")
    monkeypatch.setattr(cam.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(cam.threading, "Thread", FakeThread)
    c.post(f"/cameras/{cam_c.id}/control/start")
    assert FakeProc.instances[-1].env["GATE_TYPE"] == "otro"


def test_dynamic_start_error_de_popen(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=9, tipo="ENTRADA", source="0",
                         sucursal="Centro")

    def boom(*a, **k):
        raise RuntimeError("fork fallo")

    monkeypatch.setattr(cam.subprocess, "Popen", boom)
    resp = c.post(f"/cameras/{cam_c.id}/control/start")
    assert resp.json() == {"status": "error", "message": "fork fallo"}
    assert _proc_id_of(cam_c) not in CAMERA_PROCESSES


def test_dynamic_stop_no_en_ejecucion_error(client):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    resp = c.post(f"/cameras/{cam_c.id}/control/stop")
    assert resp.json() == {"status": "error", "message": "No está en ejecución"}


def test_dynamic_stop_nt(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_running(cam_c)
    kills = []
    monkeypatch.setattr(cam.os, "name", "nt")
    monkeypatch.setattr(cam.subprocess, "call", lambda *a, **k: kills.append(a))
    resp = c.post(f"/cameras/{cam_c.id}/control/stop")
    assert resp.json()["status"] == "ok"
    assert "taskkill" in kills[0][0]
    assert _proc_id_of(cam_c) not in CAMERA_PROCESSES


def test_dynamic_stop_posix(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    proc = _set_running(cam_c)
    monkeypatch.setattr(cam.os, "name", "posix")
    resp = c.post(f"/cameras/{cam_c.id}/control/stop")
    assert resp.json()["status"] == "ok"
    assert proc.terminated == 1


def test_dynamic_stop_proceso_ya_fin(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    proc = _set_running(cam_c)
    proc.poll_ret = 0
    monkeypatch.setattr(cam.os, "name", "posix")
    resp = c.post(f"/cameras/{cam_c.id}/control/stop")
    assert resp.json()["status"] == "ok"
    assert proc.terminated == 0


def test_dynamic_stop_excepcion(client, monkeypatch):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    _set_running(cam_c, exc_poll=True)
    resp = c.post(f"/cameras/{cam_c.id}/control/stop")
    assert resp.json() == {"status": "error", "message": "poll boom"}


def test_dynamic_accion_invalida(client):
    c, db_factory = client
    cam_c = _seed_camera(db_factory, cam_id=1, tipo="ENTRADA", sucursal="Centro")
    resp = c.post(f"/cameras/{cam_c.id}/control/pause")
    assert resp.json() == {"status": "error", "message": "Acción no válida"}


# ---------------------------------------------------------------------------
# notify_camera_reading
# ---------------------------------------------------------------------------

def _capture_set_last_event(monkeypatch):
    calls = []
    monkeypatch.setattr(NotificationService, "set_last_event",
                        staticmethod(lambda sucursal_norm, event_type, plate,
                                     message, status="ok": calls.append(
                                         (sucursal_norm, event_type, plate,
                                          message, status))))
    return calls


class FakeBranch:
    def __init__(self, nombre):
        self.nombre = nombre


def test_reading_403_sin_secret(client):
    c, _ = client
    assert c.post("/camera-reading/CENTRO_1").status_code == 403


def test_reading_403_secret_invalido(client):
    c, _ = client
    resp = c.post("/camera-reading/CENTRO_1", headers={"X-Node-Secret": "malo"})
    assert resp.status_code == 403


def test_reading_con_sucursal_matcheada(client, monkeypatch):
    c, _ = client
    calls = _capture_set_last_event(monkeypatch)
    monkeypatch.setattr(cam.BranchRepository, "get_all",
                        lambda db: [FakeBranch("Centro")])
    resp = c.post("/camera-reading/CENTRO_1",
                  headers={"X-Node-Secret": "s3cret"})
    assert resp.json() == {"status": "ok"}
    assert calls == [("Centro", "READING", "", "LEYENDO PATENTE...", "reading")]


def test_reading_sin_match_de_sucursal_global(client, monkeypatch):
    c, _ = client
    calls = _capture_set_last_event(monkeypatch)
    monkeypatch.setattr(cam.BranchRepository, "get_all",
                        lambda db: [FakeBranch("Otra")])
    c.post("/camera-reading/CENTRO_1", headers={"X-Node-Secret": "s3cret"})
    assert calls[0][0] == "GLOBAL"


def test_reading_excepcion_de_repositorio_global(client, monkeypatch):
    c, _ = client
    calls = _capture_set_last_event(monkeypatch)

    def boom(db):
        raise RuntimeError("db caida")

    monkeypatch.setattr(cam.BranchRepository, "get_all", boom)
    c.post("/camera-reading/CENTRO_1", headers={"X-Node-Secret": "s3cret"})
    assert calls[0][0] == "GLOBAL"


def test_reading_gate_sin_guion_bajo_global(client, monkeypatch):
    c, _ = client
    calls = _capture_set_last_event(monkeypatch)
    c.post("/camera-reading/GLOBALCAM", headers={"X-Node-Secret": "s3cret"})
    assert calls[0][0] == "GLOBAL"


# ---------------------------------------------------------------------------
# routes/system/common.py: stop_all_cameras y broadcast de consola/frames
# ---------------------------------------------------------------------------

def test_stop_all_cameras_nt_taskkill(monkeypatch):
    proc = FakeProc()
    CAMERA_PROCESSES["CENTRO_1"] = proc
    kills = []
    monkeypatch.setattr(common.os, "name", "nt")
    monkeypatch.setattr(common.subprocess, "call", lambda *a, **k: kills.append(a))
    common.stop_all_cameras()
    assert kills and "taskkill" in kills[0][0]
    assert CAMERA_PROCESSES == {}


def test_stop_all_cameras_posix_terminate(monkeypatch):
    proc = FakeProc()
    CAMERA_PROCESSES["CENTRO_1"] = proc
    monkeypatch.setattr(common.os, "name", "posix")
    common.stop_all_cameras()
    assert proc.terminated == 1
    assert CAMERA_PROCESSES == {}


def test_stop_all_cameras_ignora_error_por_camara(monkeypatch):
    proc = FakeProc()
    proc.exc_poll = True
    CAMERA_PROCESSES["A"] = proc
    CAMERA_PROCESSES["B"] = FakeProc()
    kills = []
    monkeypatch.setattr(common.os, "name", "nt")
    monkeypatch.setattr(common.subprocess, "call",
                        lambda *a, **k: kills.append(a) or (_ for _ in ()).throw(
                            RuntimeError("kill fallo")))
    common.stop_all_cameras()
    assert CAMERA_PROCESSES == {}


class FakeWS:
    def __init__(self, exc=None):
        self.sent = []
        self.exc = exc

    async def send_text(self, data):
        if self.exc:
            raise self.exc
        self.sent.append(data)


def test_broadcast_console_sin_conexiones_no_envia():
    manager.active_connections.clear()
    asyncio.run(manager.broadcast_console("CAM", "linea"))
    manager.active_connections.clear()


def test_broadcast_console_envia_payload_json():
    manager.active_connections.clear()
    ws = FakeWS()
    manager.active_connections["CAM"] = [ws]
    asyncio.run(manager.broadcast_console("CAM", "linea"))
    payload = json.loads(ws.sent[0])
    assert payload == {"__console__": True, "gate": "CAM", "line": "linea"}
    manager.active_connections.clear()


def test_broadcast_console_error_desconecta():
    manager.active_connections.clear()
    ws = FakeWS(exc=RuntimeError("socket roto"))
    manager.active_connections["CAM"] = [ws]
    asyncio.run(manager.broadcast_console("CAM", "linea"))
    assert ws not in manager.active_connections
    manager.active_connections.clear()


def test_broadcast_frame_actualiza_ultimo_y_envia():
    manager.active_connections.clear()
    ws = FakeWS()
    manager.active_connections["CAM"] = [ws]
    asyncio.run(manager.broadcast_frame("CAM", "BASE64"))
    assert manager.last_frames["CAM"] == "BASE64"
    assert ws.sent == ["BASE64"]
    manager.active_connections.clear()
    manager.last_frames.clear()


def test_broadcast_frame_error_desconecta_y_sigue():
    manager.active_connections.clear()
    ws_ok = FakeWS()
    ws_bad = FakeWS(exc=RuntimeError("caido"))
    manager.active_connections["CAM"] = [ws_bad, ws_ok]
    asyncio.run(manager.broadcast_frame("CAM", "FRAME"))
    assert manager.active_connections["CAM"] == [ws_ok]
    manager.active_connections.clear()
    manager.last_frames.clear()


def test_disconnect_sin_conexion_no_rompe():
    manager.active_connections.clear()
    manager.active_connections["CAM"] = []
    try:
        manager.disconnect(FakeWS(), "CAM")
        manager.disconnect(FakeWS(), "NOEXISTE")
    finally:
        manager.active_connections.clear()


# ---------------------------------------------------------------------------
# locale fallback (líneas 25-26): reload con getpreferredencoding roto
# ---------------------------------------------------------------------------

def test_console_encoding_fallback_utf8(monkeypatch):
    def boom(encodings=False):
        raise RuntimeError("locale roto")

    monkeypatch.setattr(cam.locale, "getpreferredencoding", boom)
    importlib.reload(cam)
    assert cam._console_encoding == "utf-8"