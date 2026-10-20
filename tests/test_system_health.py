"""Tests ronda #19: routes/system/health.py.

Cubre GET /health (DB online/offline, ALPR por heartbeats para admin global con
gates ONLINE/OFFLINE por antigüedad, staff sin cámaras usando prefijos
sucursal_ENTRADA/SALIDA, staff con cámaras usando proc_id sucursal_TIPO_id,
cámara sin sucursal → GLOBAL, perfil "user" → 403), POST /heartbeat
(normalización strip/upper y registro), POST /reset (super admin real con rate
limit, reset de datos + limpieza de IMAGE_DIR con/sin directorio y con unlink
fallido, 403 sin super admin) y GET /virtual-time.
"""
import datetime
import importlib
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.config import settings as core_settings
from core.database import Base
from core.limiter import limiter
from core.security import get_current_user
from models.enums import UserRole
from routes.system.common import ALPR_HEARTBEATS

health_mod = importlib.import_module("routes.system.health")


class FakeUser:
    def __init__(self, rol=UserRole.ADMIN.value, sucursal=None):
        self.rol = rol
        self.sucursal = sucursal


CURRENT = {"user": FakeUser()}


def _build_app(TestSession, db_breaker=None):
    def override_get_db():
        if db_breaker:
            yield db_breaker
            return
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(health_mod.router)
    app.dependency_overrides[health_mod.get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: CURRENT["user"]
    return app


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    _db = TestSession()
    _db.add(models.ParkingBranch(nombre="Centro", direccion="d", horario="24hs"))
    _db.commit()
    _db.close()
    limiter.reset()
    ALPR_HEARTBEATS.clear()
    app = _build_app(TestSession)
    with TestClient(app) as c:
        yield c, TestSession
    app.dependency_overrides.clear()
    ALPR_HEARTBEATS.clear()
    limiter.reset()


@pytest.fixture(autouse=True)
def _reset_user():
    yield
    CURRENT["user"] = FakeUser()


def _set_user(rol=UserRole.ADMIN, sucursal=None):
    value = rol.value if isinstance(rol, UserRole) else rol
    CURRENT["user"] = FakeUser(rol=value, sucursal=sucursal)


def _set_staff(sucursal=None):
    _set_user(rol=UserRole.STAFF, sucursal=sucursal)


def _seed_heartbeat(gate, seconds_ago):
    ALPR_HEARTBEATS[gate] = datetime.datetime.now() - datetime.timedelta(seconds=seconds_ago)


def _seed_camera(db_factory, tipo, sucursal="Centro", activa=True):
    db = db_factory()
    cam = models.ParkingCamera(nombre=f"Cam {tipo}", tipo=tipo, source="0",
                               sucursal=sucursal, activa=activa)
    db.add(cam)
    db.commit()
    cam_id = cam.id
    db.close()
    return cam_id


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health_admin_sin_heartbeats(client):
    c, _ = client
    body = c.get("/health").json()
    assert body == {"database": "ONLINE", "alpr": {}, "api": "ONLINE"}


def test_health_admin_gates_online_y_offline(client):
    c, _ = client
    _seed_heartbeat("PUERTA_A", seconds_ago=5)
    _seed_heartbeat("PUERTA_B", seconds_ago=300)
    body = c.get("/health").json()
    assert body["alpr"] == {"PUERTA_A": "ONLINE", "PUERTA_B": "OFFLINE"}
    assert body["database"] == "ONLINE"
    assert body["api"] == "ONLINE"


def test_health_database_fallida_devuelve_offline():
    class BrokenDB:
        def execute(self, *a, **k):
            raise RuntimeError("db caída")

        def query(self, *a, **k):  #  pragma: no cover - inesperado
            raise AssertionError

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    limiter.reset()
    ALPR_HEARTBEATS.clear()
    app = _build_app(TestSession, db_breaker=BrokenDB())
    with TestClient(app) as c:
        body = c.get("/health").json()
    app.dependency_overrides.clear()
    ALPR_HEARTBEATS.clear()
    limiter.reset()
    assert body["database"] == "OFFLINE"


def test_health_staff_sin_cameras_usa_prefijos_de_sucursal(client):
    c, _ = client
    _set_staff(sucursal="Centro")
    _seed_heartbeat("CENTRO_ENTRADA", seconds_ago=5)
    _seed_heartbeat("CENTRO_SALIDA", seconds_ago=500)
    body = c.get("/health").json()
    assert body["alpr"] == {"CENTRO_ENTRADA": "ONLINE", "CENTRO_SALIDA": "OFFLINE"}


def test_health_staff_con_camaras_usa_proc_id(client):
    c, db_factory = client
    _set_staff(sucursal="Centro")
    cam_id = _seed_camera(db_factory, "ENTRADA", sucursal="Centro")
    proc = f"CENTRO_ENTRADA_{cam_id}".upper()
    _seed_heartbeat(proc, seconds_ago=5)
    body = c.get("/health").json()
    assert body["alpr"][proc] == "ONLINE"


def test_health_staff_con_camaras_proc_id_offline_sin_heartbeat(client):
    c, db_factory = client
    _set_staff(sucursal="Centro")
    _seed_camera(db_factory, "SALIDA", sucursal="Centro")
    body = c.get("/health").json()
    key = [k for k in body["alpr"] if "SALIDA" in k][0]
    assert body["alpr"][key] == "OFFLINE"


def test_health_staff_camara_sin_sucursal_normaliza_global(client):
    c, db_factory = client
    _set_staff(sucursal=None)
    cam_id = _seed_camera(db_factory, "ENTRADA", sucursal=None)
    proc = f"GLOBAL_ENTRADA_{cam_id}".upper()
    _seed_heartbeat(proc, seconds_ago=10)
    body = c.get("/health").json()
    assert body["alpr"][proc] == "ONLINE"


def test_health_usuario_comun_403(client):
    c, _ = client
    _set_user(rol=UserRole.USER)
    assert c.get("/health").status_code == 403


# ---------------------------------------------------------------------------
# POST /heartbeat
# ---------------------------------------------------------------------------

def test_heartbeat_normaliza_y_registra(client, monkeypatch):
    c, _ = client
    monkeypatch.setattr(core_settings, "ALPR_NODE_SECRET", "secreto-de-prueba", raising=False)
    resp = c.post("/heartbeat", params={"gate_id": "  puerta-norte "},
                  headers={"x-node-secret": "secreto-de-prueba"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert "PUERTA-NORTE" in ALPR_HEARTBEATS
    age = (datetime.datetime.now() - ALPR_HEARTBEATS["PUERTA-NORTE"]).total_seconds()
    assert age < 5


def test_heartbeat_rechaza_nodo_no_autorizado(client, monkeypatch):
    """Sin node_secret (y host no loopback) el heartbeat debe rechazarse.

    Es el cierre del bug 2.4 de BUGS_A_RESOLVER.md: el endpoint era publico, asi
    que cualquiera podia escribir en ALPR_HEARTBEATS con un gate_id arbitrario,
    simular un nodo caido como ONLINE y hacer crecer el diccionario sin limite.
    """
    c, _ = client
    monkeypatch.setattr(core_settings, "ALPR_NODE_SECRET", "secreto-de-prueba", raising=False)
    resp = c.post("/heartbeat", params={"gate_id": "PUERTA_FALSA"})
    assert resp.status_code == 403
    assert "PUERTA_FALSA" not in ALPR_HEARTBEATS


def test_heartbeat_rechaza_secreto_incorrecto(client, monkeypatch):
    c, _ = client
    monkeypatch.setattr(core_settings, "ALPR_NODE_SECRET", "secreto-de-prueba", raising=False)
    resp = c.post("/heartbeat", params={"gate_id": "PUERTA_FALSA"},
                  headers={"x-node-secret": "secreto-erroneo"})
    assert resp.status_code == 403
    assert "PUERTA_FALSA" not in ALPR_HEARTBEATS


def test_heartbeat_acepta_query_param_node_secret(client, monkeypatch):
    """El secret tambien puede ir por query, como en el resto de endpoints ALPR."""
    c, _ = client
    monkeypatch.setattr(core_settings, "ALPR_NODE_SECRET", "secreto-de-prueba", raising=False)
    resp = c.post("/heartbeat", params={"gate_id": "PUERTA_OK", "node_secret": "secreto-de-prueba"})
    assert resp.status_code == 200
    assert "PUERTA_OK" in ALPR_HEARTBEATS


# ---------------------------------------------------------------------------
# POST /reset
# ---------------------------------------------------------------------------

def test_reset_borra_datos_y_archivos(client, monkeypatch, tmp_path):
    c, db_factory = client
    _set_user(rol=UserRole.ADMIN)
    db = db_factory()
    db.add(models.AccessLog(patente_detectada="ABC123", tipo_evento="ENTRADA",
                            fecha_hora="2026-09-20T10:00:00"))
    db.add(models.User(nombre="U", rol=UserRole.USER.value, email="u@x.com"))
    db.add(models.ParkingAforo(sucursal=None))
    db.commit()
    db.close()
    monkeypatch.setattr(core_settings, "IMAGE_DIR", str(tmp_path))
    (tmp_path / "img.jpg").write_bytes(b"x")
    resp = c.post("/reset")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    db = db_factory()
    assert db.query(models.AccessLog).count() == 0
    assert db.query(models.User).filter(models.User.rol == UserRole.USER.value).count() == 0
    assert db.query(models.ParkingAforo).count() == 0
    db.close()
    assert list(tmp_path.iterdir()) == []


def test_reset_sin_directorio_no_rompe(client, monkeypatch, tmp_path):
    c, db_factory = client
    _set_user(rol=UserRole.ADMIN)
    inexistente = tmp_path / "no_existe"
    monkeypatch.setattr(core_settings, "IMAGE_DIR", str(inexistente))
    resp = c.post("/reset")
    assert resp.status_code == 200
    db = db_factory()
    assert db.query(models.AccessLog).count() == 0
    db.close()


def test_reset_unlink_fallido_tolerado(client, monkeypatch, tmp_path):
    c, _ = client
    _set_user(rol=UserRole.ADMIN)
    monkeypatch.setattr(core_settings, "IMAGE_DIR", str(tmp_path))
    (tmp_path / "img.jpg").write_bytes(b"x")

    def boom_unlink(path):
        raise PermissionError("no se puede borrar")

    monkeypatch.setattr(health_mod.os, "unlink", boom_unlink)
    resp = c.post("/reset")
    assert resp.status_code == 200
    assert (tmp_path / "img.jpg").exists()


def test_reset_no_super_admin_403(client):
    c, _ = client
    _set_staff(sucursal="Centro")
    resp = c.post("/reset")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Requiere permisos de Administrador Global"


# ---------------------------------------------------------------------------
# GET /virtual-time
# ---------------------------------------------------------------------------

def test_get_virtual_time_publico(client):
    c, _ = client
    body = c.get("/virtual-time").json()
    assert isinstance(body, dict)
    assert "offset_seconds" in body or "time" in body