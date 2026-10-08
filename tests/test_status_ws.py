"""Test #9 de la auditoría A3: estado de aforo y WebSocket (routes/parking/status.py).

Cubre /v1/parking/ws (conexión, broadcast por sucursal/GLOBAL, rechazo de tokens),
OccupancyManager (connect/disconnect/broadcast) y los endpoints HTTP
list_public_branches, get_parking_status y current_occupancy.
"""
import asyncio
import datetime
import importlib

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from main import app
from core.database import get_db, Base
from core.limiter import limiter
from core.security import get_operational_user

status_mod = importlib.import_module("routes.parking.status")
OccupancyManager = status_mod.OccupancyManager
occupancy_manager = status_mod.occupancy_manager

WS_URL = "/v1/parking/ws"


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    saved = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_get_db
    occupancy_manager.active_connections.clear()
    from core.cache import ttl_cache
    ttl_cache.invalidate("occupancy_")
    limiter.reset()
    yield TestClient(app), TestSession
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    occupancy_manager.active_connections.clear()
    limiter.reset()


class FakeUser:
    def __init__(self, rol="user", email="client@test.com", sucursal="Centro"):
        self.rol = rol
        self.email = email
        self.sucursal = sucursal


CURRENT_USER = None


def _fake_user_repo(db, sub):
    return CURRENT_USER


def _seed(TestSession, nombre="Centro", lat=None, lon=None):
    db = TestSession()
    b = models.ParkingBranch(nombre=nombre, direccion="Av. X", telefono="123",
                             horario="07-23", activa=True, latitude=lat, longitude=lon)
    db.add(b)
    db.add(models.ParkingAforo(sucursal=nombre, capacidad_total=50, ocupacion_actual=3,
                               capacidad_motos=10, ocupacion_motos=1, capacidad_camionetas=5,
                               ocupacion_camionetas=0))
    db.commit()
    db.refresh(b)
    db.close()
    return b


def _mock_ws(monkeypatch, TestSession, user):
    global CURRENT_USER
    CURRENT_USER = user
    monkeypatch.setattr(status_mod, "get_db", lambda: iter([TestSession()]))
    monkeypatch.setattr(status_mod, "decode_access_token", lambda t: {"sub": user.email})
    monkeypatch.setattr(status_mod, "UserRepository",
                        type("UR", (), {"get_active_by_email": staticmethod(_fake_user_repo)}))


# ---------------------------------------------------------------------------
# OccupancyManager unit
# ---------------------------------------------------------------------------

class FakeWS:
    def __init__(self):
        self.accepted = False
        self.sent = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        self.sent.append(data)


def test_manager_connect_admin_usa_global():
    m = OccupancyManager()
    ws = FakeWS()
    sucursal = asyncio.run(m.connect(ws, FakeUser(rol="admin", sucursal=None)))
    assert sucursal == "GLOBAL"
    assert ws.accepted
    assert ws in m.active_connections["GLOBAL"]


def test_manager_connect_user_normaliza_sucursal():
    m = OccupancyManager()
    ws = FakeWS()
    sucursal = asyncio.run(m.connect(ws, FakeUser(rol="user", sucursal="Centro")))
    assert sucursal == "CENTRO"
    assert ws in m.active_connections["CENTRO"]


def test_manager_disconnect_elimina():
    m = OccupancyManager()
    ws = FakeWS()
    asyncio.run(m.connect(ws, FakeUser(rol="admin", sucursal=None)))
    m.disconnect(ws, "GLOBAL")
    assert ws not in m.active_connections["GLOBAL"]
    m.disconnect(ws, "NOEXISTE")  # sin error


# ---------------------------------------------------------------------------
# broadcast (unit, sin TestClient)
# ---------------------------------------------------------------------------

def test_broadcast_branch_envia_a_sockets(client):
    _, TestSession = client
    _seed(TestSession)
    db = TestSession()
    ws = FakeWS()
    m = OccupancyManager()
    m.active_connections["CENTRO"] = [ws]
    asyncio.run(m.broadcast_update(db, "CENTRO"))
    db.close()
    assert len(ws.sent) == 1
    assert ws.sent[0]["type"] == "BRANCH_UPDATE"
    assert ws.sent[0]["data"]["ocupacion_actual"] == 3


def test_broadcast_global_envia_todas_sucursales(client):
    _, TestSession = client
    _seed(TestSession)
    db = TestSession()
    ws = FakeWS()
    m = OccupancyManager()
    m.active_connections["GLOBAL"] = [ws]
    asyncio.run(m.broadcast_update(db, None))
    db.close()
    assert ws.sent[0]["type"] == "GLOBAL_UPDATE"
    assert ws.sent[0]["branches"][0]["nombre"] == "Centro"


# ---------------------------------------------------------------------------
# WebSocket endpoint (integración)
# ---------------------------------------------------------------------------

def test_ws_sin_token_cierra_4008(client):
    tc, _ = client
    with pytest.raises(WebSocketDisconnect) as ei:
        with tc.websocket_connect(WS_URL) as ws:
            ws.receive_json()
    assert ei.value.code == 4008


def test_ws_token_invalido_cierra_4008(client, monkeypatch):
    tc, _ = client
    monkeypatch.setattr(status_mod, "decode_access_token",
                        lambda t: (_ for _ in ()).throw(Exception("bad")))
    monkeypatch.setattr(status_mod, "UserRepository",
                        type("UR", (), {"get_active_by_email": staticmethod(lambda db, sub: None)}))
    with pytest.raises(WebSocketDisconnect) as ei:
        with tc.websocket_connect(f"{WS_URL}?token=bad") as ws:
            ws.receive_json()
    assert ei.value.code == 4008


def test_ws_admin_recibe_global_update(client, monkeypatch):
    tc, TestSession = client
    _mock_ws(monkeypatch, TestSession, FakeUser(rol="admin", email="admin@test.com", sucursal=None))
    with tc.websocket_connect(f"{WS_URL}?token=valid") as ws:
        msg = ws.receive_json()
    assert msg["type"] == "GLOBAL_UPDATE"


def test_ws_staff_recibe_branch_update(client, monkeypatch):
    tc, TestSession = client
    _seed(TestSession)
    _mock_ws(monkeypatch, TestSession, FakeUser(rol="staff", email="staff@test.com", sucursal="Centro"))
    with tc.websocket_connect(f"{WS_URL}?token=valid") as ws:
        msg = ws.receive_json()
    assert msg["type"] == "BRANCH_UPDATE"
    assert msg["data"]["ocupacion_actual"] == 3


def test_ws_cliente_no_operativo_cierra_4003(client, monkeypatch):
    tc, TestSession = client
    _seed(TestSession)
    _mock_ws(monkeypatch, TestSession, FakeUser(rol="user", email="client@test.com", sucursal="Centro"))
    with pytest.raises(WebSocketDisconnect) as ei:
        with tc.websocket_connect(f"{WS_URL}?token=valid") as ws:
            ws.receive_json()
    assert ei.value.code == 4003
    assert occupancy_manager.active_connections.get("CENTRO") in (None, [])


def test_ws_dos_clientes_reciben_broadcast(client, monkeypatch):
    tc, TestSession = client
    _mock_ws(monkeypatch, TestSession, FakeUser(rol="admin", email="admin@test.com", sucursal=None))
    with tc.websocket_connect(f"{WS_URL}?token=one") as ws1:
        ws1.receive_json()  # primer broadcast
        with tc.websocket_connect(f"{WS_URL}?token=two") as ws2:
            ws2.receive_json()  # broadcast al conectar ws2
            msg = ws1.receive_json()  # ws1 también recibe el broadcast de ws2
            assert msg["type"] == "GLOBAL_UPDATE"


# ---------------------------------------------------------------------------
# Endpoints HTTP
# ---------------------------------------------------------------------------

def test_list_public_branches(client, monkeypatch):
    tc, TestSession = client
    from core.cache import ttl_cache
    monkeypatch.setattr(ttl_cache, "get", lambda k: None)
    monkeypatch.setattr(ttl_cache, "set", lambda *a, **k: None)
    _seed(TestSession, "Centro", lat=-38.0, lon=-57.5)
    r = tc.get("/v1/parking/branches")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Centro"
    assert data[0]["capacidad_total"] == 50
    assert data[0]["ocupacion_actual"] == 3


def test_get_parking_status_usuario_por_sucursal(client):
    tc, TestSession = client
    _seed(TestSession, "Centro")
    app.dependency_overrides[get_operational_user] = lambda: FakeUser(rol="user", sucursal="Centro")
    limiter.reset()
    r = tc.get("/v1/parking/status")
    assert r.status_code == 200
    assert r.json()["capacidad_total"] == 50
    assert r.json()["ocupacion_actual"] == 3
    del app.dependency_overrides[get_operational_user]


def test_get_parking_status_admin_fallback_primera_activa(client):
    tc, TestSession = client
    _seed(TestSession, "Centro")
    app.dependency_overrides[get_operational_user] = lambda: FakeUser(rol="admin", sucursal=None)
    limiter.reset()
    r = tc.get("/v1/parking/status")
    assert r.status_code == 200
    assert r.json()["capacidad_total"] == 50
    del app.dependency_overrides[get_operational_user]


def test_get_parking_status_sin_sucursales_default(client):
    tc, _ = client
    app.dependency_overrides[get_operational_user] = lambda: FakeUser(rol="admin", sucursal=None)
    limiter.reset()
    r = tc.get("/v1/parking/status")
    assert r.status_code == 200
    assert r.json()["capacidad_total"] == 20
    assert r.json()["disponibilidad"] == 20
    del app.dependency_overrides[get_operational_user]


def test_current_occupancy_sin_vehiculos(client):
    tc, TestSession = client
    _seed(TestSession, "Centro")
    app.dependency_overrides[get_operational_user] = lambda: FakeUser(rol="user", sucursal="Centro")
    limiter.reset()
    r = tc.get("/v1/parking/current-occupancy")
    assert r.status_code == 200
    assert r.json() == []
    del app.dependency_overrides[get_operational_user]


def test_current_occupancy_con_ingreso(client):
    tc, TestSession = client
    _seed(TestSession, "Centro")
    db = TestSession()
    db.add(models.AccessLog(patente_detectada="AA123BB", normalized_patente="AA123BB",
                            tipo_evento="ENTRADA", fecha_hora=(datetime.datetime.now()
                            - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M"),
                            pago_confirmado=False, sucursal="Centro", tipo_vehiculo="Auto"))
    db.commit()
    db.close()
    app.dependency_overrides[get_operational_user] = lambda: FakeUser(rol="user", sucursal="Centro")
    limiter.reset()
    r = tc.get("/v1/parking/current-occupancy")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["patente"] == "AA123BB"
    del app.dependency_overrides[get_operational_user]