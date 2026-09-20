"""Test #8 de la auditoría A3: CRUD de sucursales y pisos (routes/admin/branches.py).

Cubre GET /v1/admin/branches, gestión de pisos (alta/baja/capacidad), y CRUD de
sucursales incluyendo validaciones de ocupación física, reservas activas, renombres
y toggle de estado.
"""
import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from main import app
from core.database import get_db, Base
from core.limiter import limiter
from core.security import get_super_admin, get_local_manager
from models.enums import ReservationStatus, PaymentStatus

BRANCHES_URL = "/v1/admin/branches"
FLOORS_URL = "/v1/admin/floors"
ADMIN = type("AdminUser", (), {"rol": "admin", "id": 1})()
LOCAL = type("LocalUser", (), {"rol": "local_admin", "id": 2})()


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
    app.dependency_overrides[get_super_admin] = lambda: ADMIN
    app.dependency_overrides[get_local_manager] = lambda: LOCAL
    limiter.reset()
    yield TestClient(app), TestSession
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    limiter.reset()


def _seed_branch(TestSession, nombre="Centro", ocupacion=0, activa=True):
    db = TestSession()
    b = models.ParkingBranch(nombre=nombre, direccion="Av. X", telefono="123",
                             horario="07:00-23:00", activa=activa)
    db.add(b)
    db.add(models.ParkingAforo(sucursal=nombre, capacidad_total=50, ocupacion_actual=ocupacion,
                               capacidad_motos=10, ocupacion_motos=0, capacidad_camionetas=5,
                               ocupacion_camionetas=0))
    db.commit()
    db.refresh(b)
    db.close()
    return b


# ---------------------------------------------------------------------------
# listado
# ---------------------------------------------------------------------------

def test_list_branches_con_resumen(client):
    tc, TestSession = client
    _seed_branch(TestSession, "Centro")
    _seed_branch(TestSession, "Norte")
    r = tc.get(BRANCHES_URL)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    names = {b["nombre"] for b in data}
    assert names == {"Centro", "Norte"}


# ---------------------------------------------------------------------------
# pisos
# ---------------------------------------------------------------------------

def test_add_floor(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession)
    payload = {"nombre": "PISO 1", "capacidad_total": 20, "capacidad_motos": 5,
               "capacidad_camionetas": 3, "capacidad_reservas": 4,
               "capacidad_reservas_autos": 2, "capacidad_reservas_motos": 1,
               "capacidad_reservas_camionetas": 1}
    r = tc.post(f"/v1/admin/{branch.id}/floors", json=payload)
    assert r.status_code == 200
    assert r.json()["nombre"] == "PISO 1"
    db = TestSession()
    floor = db.query(models.ParkingFloor).filter_by(branch_id=branch.id).first()
    db.close()
    assert floor.capacidad_total == 20
    assert floor.capacidad_reservas == 4


def test_add_floor_sucursal_inexistente_404(client):
    tc, _ = client
    r = tc.post("/v1/admin/999/floors", json={"nombre": "PISO 1", "capacidad_total": 20})
    assert r.status_code == 404


def _seed_floor(TestSession, branch_id, ocupacion=0):
    db = TestSession()
    floor = models.ParkingFloor(branch_id=branch_id, nombre="PISO 1", capacidad_total=20,
                                capacidad_motos=5, capacidad_camionetas=5,
                                capacidad_reservas_autos=2, capacidad_reservas_motos=1,
                                capacidad_reservas_camionetas=1, capacidad_reservas=4,
                                ocupacion_actual=ocupacion)
    db.add(floor)
    db.commit()
    db.refresh(floor)
    db.close()
    return floor


def test_delete_floor_ok(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession)
    floor = _seed_floor(TestSession, branch.id)
    r = tc.delete(f"{FLOORS_URL}/{floor.id}")
    assert r.status_code == 200
    db = TestSession()
    assert db.query(models.ParkingFloor).filter_by(id=floor.id).first() is None
    db.close()


def test_delete_floor_con_vehiculos_400(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession)
    floor = _seed_floor(TestSession, branch.id, ocupacion=3)
    r = tc.delete(f"{FLOORS_URL}/{floor.id}")
    assert r.status_code == 400


def test_delete_floor_inexistente_404(client):
    tc, _ = client
    assert tc.delete(f"{FLOORS_URL}/999").status_code == 404


def test_update_floor_capacity(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession)
    floor = _seed_floor(TestSession, branch.id)
    r = tc.patch(f"{FLOORS_URL}/{floor.id}",
                 params={"cap_autos": 30, "cap_motos": 8, "cap_camionetas": 5,
                         "cap_reservas_autos": 3})
    assert r.status_code == 200
    db = TestSession()
    updated = db.query(models.ParkingFloor).filter_by(id=floor.id).first()
    db.close()
    assert updated.capacidad_total == 30
    assert updated.capacidad_motos == 8
    assert updated.capacidad_reservas == 5


def test_update_floor_capacidad_menor_a_ocupacion_400(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession)
    floor = _seed_floor(TestSession, branch.id, ocupacion=10)
    r = tc.patch(f"{FLOORS_URL}/{floor.id}", params={"cap_autos": 5, "cap_motos": 5})
    assert r.status_code == 400
    assert "ocupación actual" in r.json()["detail"]


def test_update_floor_inexistente_404(client):
    tc, _ = client
    assert tc.patch(f"{FLOORS_URL}/999", params={"cap_autos": 10, "cap_motos": 10}).status_code == 404


# ---------------------------------------------------------------------------
# sucursales
# ---------------------------------------------------------------------------

def test_create_branch_ok(client):
    tc, TestSession = client
    r = tc.post(BRANCHES_URL, data={"nombre": "Oeste", "direccion": "Av. Y",
                                    "telefono": "456", "horario": "24hs", "is_24h": "true"})
    assert r.status_code == 200
    db = TestSession()
    branch = db.query(models.ParkingBranch).filter_by(nombre="Oeste").first()
    db.close()
    assert branch is not None and branch.activa is True
    assert branch.logo_url == "/static/images/logo.png"


def test_create_branch_duplicado_400(client):
    tc, TestSession = client
    _seed_branch(TestSession, "Centro")
    r = tc.post(BRANCHES_URL, data={"nombre": "Centro", "direccion": "Av. X",
                                    "telefono": "456", "horario": "24hs"})
    assert r.status_code == 400
    assert "ya existe" in r.json()["detail"]


def test_delete_branch_ok(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession)
    r = tc.delete(f"{BRANCHES_URL}/{branch.id}")
    assert r.status_code == 200
    db = TestSession()
    assert db.query(models.ParkingBranch).filter_by(id=branch.id).first() is None
    db.close()


def test_delete_branch_con_ocupacion_400(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession, ocupacion=2)
    r = tc.delete(f"{BRANCHES_URL}/{branch.id}")
    assert r.status_code == 400
    assert "vehículos" in r.json()["detail"]


def test_delete_branch_con_reservas_activas_400(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession)
    db = TestSession()
    now = datetime.datetime.now()
    db.add(models.Reservation(patente="AA123BB",
                              fecha_inicio=(now - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                              fecha_fin=(now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                              estado_reserva=ReservationStatus.PENDIENTE.value,
                              estado_pago=PaymentStatus.PAGADO.value,
                              sucursal_nombre="Centro", monto_total=100.0))
    db.commit()
    db.close()
    r = tc.delete(f"{BRANCHES_URL}/{branch.id}")
    assert r.status_code == 400
    assert "reservas activas" in r.json()["detail"]


def test_delete_branch_inexistente_404(client):
    tc, _ = client
    assert tc.delete(f"{BRANCHES_URL}/999").status_code == 404


def test_update_branch_ok_renombra(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession, "Centro")
    r = tc.patch(f"{BRANCHES_URL}/{branch.id}",
                 data={"nombre": "Centro Norte", "direccion": "Av. X 2",
                       "telefono": "789", "horario": "08:00-20:00"})
    assert r.status_code == 200
    db = TestSession()
    updated = db.query(models.ParkingBranch).filter_by(id=branch.id).first()
    db.close()
    assert updated.nombre == "Centro Norte"
    assert updated.direccion == "Av. X 2"
    db = TestSession()
    aforo = db.query(models.ParkingAforo).filter_by(sucursal="Centro Norte").first()
    db.close()
    assert aforo is not None


def test_update_branch_nombre_existente_400(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession, "Centro")
    _seed_branch(TestSession, "Norte")
    r = tc.patch(f"{BRANCHES_URL}/{branch.id}",
                 data={"nombre": "Norte", "direccion": "Av. X", "telefono": "789",
                       "horario": "08:00-20:00"})
    assert r.status_code == 400
    assert "Ya existe" in r.json()["detail"]


def test_update_branch_inexistente_404(client):
    tc, _ = client
    assert tc.patch(f"{BRANCHES_URL}/999",
                    data={"nombre": "X", "direccion": "A", "telefono": "1", "horario": "h"}).status_code == 404


def test_toggle_branch_ok(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession)
    r = tc.post(f"{BRANCHES_URL}/{branch.id}/toggle")
    assert r.status_code == 200
    assert r.json()["activa"] is False
    r = tc.post(f"{BRANCHES_URL}/{branch.id}/toggle")
    assert r.json()["activa"] is True


def test_toggle_branch_con_vehiculos_400(client):
    tc, TestSession = client
    branch = _seed_branch(TestSession, ocupacion=1)
    r = tc.post(f"{BRANCHES_URL}/{branch.id}/toggle")
    assert r.status_code == 400
    assert "vehículos" in r.json()["detail"]


def test_toggle_branch_inexistente_404(client):
    tc, _ = client
    assert tc.post(f"{BRANCHES_URL}/999/toggle").status_code == 404