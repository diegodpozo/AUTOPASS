"""Tests ronda #16: routes/admin/settings.py.

Cubre GET /settings (visibilidad global vs por sede de local_admin, con y sin aforo,
getattr fallbacks de aforo), POST /settings/prices (capacidades de aforo con creación
automática, re-suma de reservas, settings por sede/global, notificación de ocupación
con excepción deseada, cache invalidada) y el rol real de local_manager vía
DependencyOverride de get_current_user (403 para staff).
"""
import datetime
import importlib
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from core.security import get_current_user
from models.enums import UserRole
from services.notification_service import NotificationService

settings_mod = importlib.import_module("routes.admin.settings")


class FakeUser:
    def __init__(self, rol=UserRole.ADMIN.value, sucursal=None):
        self.rol = rol
        self.sucursal = sucursal


CURRENT = {"user": FakeUser()}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    _db = TestSession()
    _db.add(models.ParkingBranch(nombre="Centro", direccion="d", horario="24hs"))
    _db.commit()
    _db.close()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(settings_mod.router)
    app.dependency_overrides[settings_mod.get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: CURRENT["user"]
    with TestClient(app) as c:
        yield c, TestSession
    app.dependency_overrides.clear()


def _set_user(rol=UserRole.ADMIN, sucursal=None):
    value = rol.value if isinstance(rol, UserRole) else rol
    CURRENT["user"] = FakeUser(rol=value, sucursal=sucursal)


@pytest.fixture(autouse=True)
def _reset_user():
    yield
    CURRENT["user"] = FakeUser()


def _seed_setting(db_factory, clave, valor, sucursal=None):
    db = db_factory()
    s = models.Settings(clave=clave, valor=valor, sucursal=sucursal)
    db.add(s)
    db.commit()
    db.refresh(s)
    db.close()
    return s


def _seed_aforo(db_factory, sucursal=None, **kw):
    db = db_factory()
    datos = dict(
        capacidad_total=20, capacidad_motos=10, capacidad_camionetas=5,
        capacidad_reservas=0, capacidad_reservas_autos=0, capacidad_reservas_motos=0,
        capacidad_reservas_camionetas=0, ocupacion_actual=0, ocupacion_motos=0,
        ocupacion_camionetas=0, ocupacion_reservas=0, ocupacion_reservas_autos=0,
        ocupacion_reservas_motos=0, ocupacion_reservas_camionetas=0,
        ultima_actualizacion=datetime.datetime.now().isoformat(), sucursal=sucursal,
    )
    datos.update(kw)
    a = models.ParkingAforo(**datos)
    db.add(a)
    db.commit()
    db.refresh(a)
    db.close()
    return a


def _get_aforo(db_factory, sucursal=None):
    db = db_factory()
    a = db.query(models.ParkingAforo).filter(
        models.ParkingAforo.sucursal == sucursal).first()
    db.close()
    return a


def _get_setting(db_factory, clave, sucursal=None):
    db = db_factory()
    s = db.query(models.Settings).filter(
        models.Settings.clave == clave,
        models.Settings.sucursal == sucursal).first()
    db.close()
    return s


# ---------------------------------------------------------------------------
# GET /settings
# ---------------------------------------------------------------------------

def test_get_settings_admin_global_con_aforo(client):
    c, db_factory = client
    _seed_setting(db_factory, "PRECIO_HORA", 10.5, sucursal=None)
    _seed_aforo(db_factory, sucursal=None, capacidad_total=50, ocupacion_actual=4)
    resp = c.get("/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["PRECIO_HORA"] == 10.5
    assert body["sucursal_nombre"] is None
    assert body["capacidad_total"] == 50
    assert body["capacidad_motos"] == 10
    assert body["capacidad_camionetas"] == 5
    assert body["capacidad_reservas"] == 0
    assert body["ocupacion_actual"] == 4


def test_get_settings_local_admin_solo_su_sede(client):
    c, db_factory = client
    _seed_setting(db_factory, "PRECIO_GLOBAL", 1.0, sucursal=None)
    _seed_setting(db_factory, "PRECIO_CENTRO", 2.5, sucursal="Centro")
    _seed_aforo(db_factory, sucursal="Centro", capacidad_motos=22)
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    body = c.get("/settings").json()
    assert "PRECIO_CENTRO" in body
    assert "PRECIO_GLOBAL" not in body
    assert body["sucursal_nombre"] == "Centro"
    assert body["capacidad_motos"] == 22


def test_get_settings_admin_sin_aforo_no_incluye_capacidades(client):
    c, _ = client
    body = c.get("/settings").json()
    assert "capacidad_total" not in body
    assert body["sucursal_nombre"] is None


def test_get_settings_aforo_basico_getattr_fallbacks(client, monkeypatch):
    c, _ = client

    class BareAforo:
        capacidad_total = 40
        capacidad_motos = 15
        ocupacion_actual = 2
        ocupacion_motos = 1

    monkeypatch.setattr(
        settings_mod.BranchRepository, "get_aforo_by_sucursal",
        lambda db, s: BareAforo())
    body = c.get("/settings").json()
    assert body["capacidad_camionetas"] == 5      # getattr default
    assert body["capacidad_reservas"] == 0        # getattr default
    assert body["capacidad_reservas_autos"] == 0
    assert body["capacidad_reservas_motos"] == 0
    assert body["capacidad_reservas_camionetas"] == 0
    assert body["ocupacion_camionetas"] == 0
    assert body["ocupacion_reservas"] == 0
    assert body["ocupacion_reservas_autos"] == 0
    assert body["ocupacion_reservas_motos"] == 0
    assert body["ocupacion_reservas_camionetas"] == 0
    assert body["capacidad_total"] == 40


def test_get_settings_staff_403(client):
    _set_user(rol=UserRole.STAFF, sucursal="Centro")
    resp = client[0].get("/settings")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /settings/prices
# ---------------------------------------------------------------------------

def test_update_price_capacidad_crea_aforo_y_notifica(client, monkeypatch):
    c, db_factory = client
    notificados = []
    monkeypatch.setattr(
        NotificationService, "notify_occupancy_change",
        classmethod(lambda cls, db, sucursal_norm: notificados.append(sucursal_norm)))
    resp = c.post("/settings/prices", params={"clave": "capacidad_total", "valor": "30"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    aforo = _get_aforo(db_factory, sucursal=None)
    assert aforo.capacidad_total == 30
    assert aforo.capacidad_motos == 10  # defaults de creación
    assert aforo.capacidad_camionetas == 5
    assert notificados == [None]
    assert _get_setting(db_factory, "capacidad_total") is None


def test_update_price_capacidad_existente_actualiza(client, monkeypatch):
    c, db_factory = client
    _seed_aforo(db_factory, sucursal=None, capacidad_total=50)
    monkeypatch.setattr(NotificationService, "notify_occupancy_change",
                        classmethod(lambda cls, db, s: None))
    resp = c.post("/settings/prices", params={"clave": "capacidad_total", "valor": "70"})
    assert resp.json() == {"status": "ok"}
    aforo = _get_aforo(db_factory, sucursal=None)
    assert aforo.capacidad_total == 70
    db = db_factory()
    total = db.query(models.ParkingAforo).count()
    db.close()
    assert total == 1


def test_update_price_reservas_autos_resuma_capacidad_reservas(client, monkeypatch):
    c, db_factory = client
    _seed_aforo(db_factory, sucursal=None)
    monkeypatch.setattr(NotificationService, "notify_occupancy_change",
                        classmethod(lambda cls, db, s: None))
    c.post("/settings/prices", params={"clave": "capacidad_reservas_autos", "valor": "3"})
    c.post("/settings/prices", params={"clave": "capacidad_reservas_motos", "valor": "2"})
    aforo = _get_aforo(db_factory, sucursal=None)
    assert aforo.capacidad_reservas_autos == 3
    assert aforo.capacidad_reservas_motos == 2
    assert aforo.capacidad_reservas == 5


def test_update_price_capacidad_camionetas(client, monkeypatch):
    c, db_factory = client
    _seed_aforo(db_factory, sucursal=None)
    monkeypatch.setattr(NotificationService, "notify_occupancy_change",
                        classmethod(lambda cls, db, s: None))
    c.post("/settings/prices", params={"clave": "capacidad_camionetas", "valor": "12"})
    assert _get_aforo(db_factory, sucursal=None).capacidad_camionetas == 12


def test_update_price_notificacion_que_falla_devuelve_ok(client, monkeypatch):
    c, _ = client

    def boom(cls, db, s):
        raise RuntimeError("notif caida")

    monkeypatch.setattr(NotificationService, "notify_occupancy_change", classmethod(boom))
    resp = c.post("/settings/prices", params={"clave": "capacidad_motos", "valor": "8"})
    assert resp.json() == {"status": "ok"}


def test_update_price_existente_actualiza_setting(client):
    c, db_factory = client
    _seed_setting(db_factory, "precio_hora", 5.0, sucursal=None)
    resp = c.post("/settings/prices", params={"clave": "precio_hora", "valor": "7.5"})
    assert resp.json() == {"status": "ok",
                           "message": "Precio precio_hora actualizado para Global"}
    assert _get_setting(db_factory, "precio_hora").valor == 7.5


def test_update_price_nuevo_setting_global(client):
    c, db_factory = client
    resp = c.post("/settings/prices", params={"clave": "precio_hora", "valor": "9.9"})
    assert resp.json()["message"] == "Precio precio_hora actualizado para Global"
    s = _get_setting(db_factory, "precio_hora", sucursal=None)
    assert s.valor == Decimal("9.90")
    assert s.sucursal is None


def test_update_price_local_admin_guarda_en_su_sede(client):
    c, db_factory = client
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    resp = c.post("/settings/prices", params={"clave": "precio_hora", "valor": "3.5"})
    assert resp.json()["message"] == "Precio precio_hora actualizado para Centro"
    s = _get_setting(db_factory, "precio_hora", sucursal="Centro")
    assert s is not None
    assert _get_setting(db_factory, "precio_hora", sucursal=None) is None


def test_update_price_clave_no_permitida_400(client):
    c, db_factory = client
    resp = c.post("/settings/prices", params={"clave": "PRECIO_NOCHE", "valor": "9.9"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Clave de configuración no permitida"
    assert _get_setting(db_factory, "PRECIO_NOCHE", sucursal=None) is None


def test_update_price_staff_403(client):
    _set_user(rol=UserRole.STAFF, sucursal="Centro")
    resp = client[0].post("/settings/prices", params={"clave": "P", "valor": "1"})
    assert resp.status_code == 403


def test_update_price_capacidad_reservas_motos_y_camionetas(client, monkeypatch):
    c, db_factory = client
    _seed_aforo(db_factory, sucursal=None)
    monkeypatch.setattr(NotificationService, "notify_occupancy_change",
                        classmethod(lambda cls, db, s: None))
    c.post("/settings/prices", params={"clave": "capacidad_reservas_camionetas", "valor": "4"})
    assert _get_aforo(db_factory, sucursal=None).capacidad_reservas == 4