"""Tests ronda #17: routes/user/balance.py.

Cubre /active-stays (usuario sin vehículos, sin ingresos, entrada no pagada con
deuda, entrada pagada sin deuda, exclusión por salida posterior, múltiples salidas
quedándose con la más reciente, salida anterior al ingreso que no excluye),
/payment-history (logs pagados del usuario), /rates (tarifas estrictas por sede: no
inventa precios, no hereda globales, deriva 30min = mitad de hora) y /recharge-balance (monto inválido 400, recarga exitosa con
notificación y con excepción de notificación tolerada).
"""
import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from core.security import get_current_user

balance_mod = importlib.import_module("routes.user.balance")


class SimpleVehicle:
    def __init__(self, patente):
        self.patente = patente


class FakeUser:
    def __init__(self, vehicles=None, saldo=0.0, uid=1):
        self.id = uid
        self.vehicles = vehicles if vehicles is not None else []
        self.saldo = saldo


CURRENT = {"user": FakeUser()}


@pytest.fixture
def client():
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
    app.include_router(balance_mod.router)
    app.dependency_overrides[balance_mod.get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: CURRENT["user"]
    with TestClient(app) as c:
        yield c, TestSession
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _reset_user():
    yield
    CURRENT["user"] = FakeUser()


def _set_user(patente="ABC123", saldo=0.0):
    CURRENT["user"] = FakeUser(vehicles=[SimpleVehicle(patente)], saldo=saldo)


def _seed_user_saldo(db_factory, user_id=1, saldo=0.0):
    """CREA LA FILA REAL DEL USUARIO.

    El saldo ya no se modifica en memoria: `UserRepository.sumar_saldo` hace un
    UPDATE atomico sobre `users`, asi que el usuario tiene que existir en la base
    (en produccion `current_user` sale de la base; aca el saldo inicial de la fila
    se deja igual al del FakeUser para que el resultado coincida)."""
    db = db_factory()
    db.add(models.User(
        id=user_id, nombre="Cliente", apellido="Saldo",
        email=f"saldo{user_id}@test.com", password_hash="x", rol="user", saldo=saldo,
    ))
    db.commit()
    db.close()


def _seed_log(db_factory, patente, tipo, fecha_hora, pago=False, costo=0.0):
    db = db_factory()
    log = models.AccessLog(
        patente_detectada=patente,
        tipo_evento=tipo,
        fecha_hora=fecha_hora,
        pago_confirmado=pago,
        costo_estadia=costo,
    )
    db.add(log)
    db.commit()
    db.close()


ISOF = "%Y-%m-%dT%H:%M:%S"


def test_active_stays_usuario_sin_vehiculos(client):
    c, _ = client
    assert c.get("/active-stays").json() == []


def test_active_stays_sin_ingresos_devuelve_lista_vacia(client):
    c, db_factory = client
    _set_user(patente="XYZ999")
    _seed_log(db_factory, "XYZ999", "SALIDA", "2026-09-21T09:00:00")
    assert c.get("/active-stays").json() == []


def test_active_stays_ingreso_no_pagado_con_deuda(client, monkeypatch):
    c, db_factory = client
    _set_user(patente="ABC123")
    _seed_log(db_factory, "ABC123", "ENTRADA", "2026-09-20T10:00:00")
    monkeypatch.setattr(
        balance_mod.BillingService, "calculate_debt", staticmethod(lambda *a, **k: 123.5)
    )
    body = c.get("/active-stays").json()
    assert len(body) == 1
    assert body[0]["patente"] == "ABC123"
    assert body[0]["deuda"] == 123.5
    assert body[0]["pago_confirmado"] is False
    assert body[0]["ingreso"] == "2026-09-20 10:00:00"


def test_active_stays_ingreso_pagado_deuda_cero(client, monkeypatch):
    c, db_factory = client
    _set_user(patente="ABC123")
    _seed_log(db_factory, "ABC123", "ENTRADA", "2026-09-20T10:00:00", pago=True)
    calls = []
    monkeypatch.setattr(
        balance_mod.BillingService,
        "calculate_debt",
        staticmethod(lambda *a, **k: calls.append(a) or 0.0),
    )
    body = c.get("/active-stays").json()
    assert body[0]["deuda"] == 0.0
    assert calls == []


def test_active_stays_salida_posterior_excluye_el_ingreso(client):
    c, db_factory = client
    _set_user(patente="ABC123")
    _seed_log(db_factory, "ABC123", "ENTRADA", "2026-09-20T10:00:00")
    _seed_log(db_factory, "ABC123", "SALIDA", "2026-09-20T12:00:00")
    assert c.get("/active-stays").json() == []


def test_active_stays_multiples_salidas_mantiene_la_ultima(client):
    c, db_factory = client
    _set_user(patente="ABC123")
    _seed_log(db_factory, "ABC123", "ENTRADA", "2026-09-20T10:00:00")
    _seed_log(db_factory, "ABC123", "SALIDA", "2026-09-20T11:00:00")
    _seed_log(db_factory, "ABC123", "SALIDA", "2026-09-20T13:00:00")
    assert c.get("/active-stays").json() == []


def test_active_stays_salida_anterior_al_ingreso_no_excluye(client, monkeypatch):
    c, db_factory = client
    _set_user(patente="ABC123")
    _seed_log(db_factory, "ABC123", "SALIDA", "2026-09-19T09:00:00")
    _seed_log(db_factory, "ABC123", "ENTRADA", "2026-09-20T10:00:00")
    monkeypatch.setattr(
        balance_mod.BillingService, "calculate_debt", staticmethod(lambda *a, **k: 50.0)
    )
    body = c.get("/active-stays").json()
    assert len(body) == 1
    assert body[0]["deuda"] == 50.0


def test_active_stays_varias_patentes_solo_las_propias(client, monkeypatch):
    c, db_factory = client
    _set_user(patente="ABC123")
    _seed_log(db_factory, "ABC123", "ENTRADA", "2026-09-20T10:00:00")
    _seed_log(db_factory, "ZZZ999", "ENTRADA", "2026-09-20T11:00:00")
    monkeypatch.setattr(
        balance_mod.BillingService, "calculate_debt", staticmethod(lambda *a, **k: 20.0)
    )
    body = c.get("/active-stays").json()
    assert [b["patente"] for b in body] == ["ABC123"]


def test_payment_history_con_y_sin_logs(client):
    c, db_factory = client
    _set_user(patente="ABC123")
    _seed_log(db_factory, "ABC123", "SALIDA", "2026-09-20T12:00:00", pago=True, costo=5000.0)
    _seed_log(db_factory, "ABC123", "SALIDA", "2026-09-19T11:00:00", pago=True, costo=2500.0)
    _seed_log(db_factory, "ABC123", "ENTRADA", "2026-09-19T10:00:00")
    body = c.get("/payment-history").json()
    assert len(body) == 2
    assert all(x["pago_confirmado"] for x in body)
    assert all(x["costo_estadia"] > 0 for x in body)


def test_payment_history_sin_logs_pagados(client):
    c, db_factory = client
    _set_user(patente="ABC123")
    _seed_log(db_factory, "ABC123", "ENTRADA", "2026-09-20T10:00:00")
    assert c.get("/payment-history").json() == []


def test_rates_sin_configuracion_no_inventa_precios(client):
    c, _ = client
    body = c.get("/rates").json()
    assert body == {}
    assert "hora" not in body
    assert "30min" not in body


def test_rates_globales_deriva_30min_de_hora(client):
    c, db_factory = client
    db = db_factory()
    db.add(models.Settings(clave="precio_hora", valor=1800.0, sucursal=None))
    db.add(models.Settings(clave="precio_mes_moto", valor=250000.0, sucursal=None))
    db.commit()
    db.close()
    body = c.get("/rates").json()
    assert body["hora"] == 1800
    assert body["30min"] == 900
    assert body["mes_moto"] == 250000
    assert "quincena" not in body


def test_rates_sucursal_no_hereda_globales(client):
    c, db_factory = client
    db = db_factory()
    db.add(models.ParkingBranch(nombre="Centro", direccion="d", horario="24hs"))
    db.add(models.Settings(clave="precio_hora", valor=1800.0, sucursal=None))
    db.add(models.Settings(clave="precio_hora", valor=2200.0, sucursal="Centro"))
    db.add(models.Settings(clave="precio_dia", valor=17000.0, sucursal="Centro"))
    db.commit()
    db.close()
    body = c.get("/rates", params={"sucursal": "Centro"}).json()
    assert body["hora"] == 2200
    assert body["dia"] == 17000
    assert body["30min"] == 1100
    assert "mes" not in body


def test_rates_sucursal_sin_tarifario_devuelve_vacio(client):
    c, db_factory = client
    db = db_factory()
    db.add(models.ParkingBranch(nombre="Centro", direccion="d", horario="24hs"))
    db.add(models.Settings(clave="precio_hora", valor=2200.0, sucursal="Centro"))
    db.commit()
    db.close()
    body = c.get("/rates", params={"sucursal": "Castelar"}).json()
    assert body == {}


def test_recharge_balance_monto_invalido(client):
    c, _ = client
    resp = c.post("/recharge-balance", json={"monto": 0})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Monto inválido"


def test_recharge_balance_ok_con_notificacion(client, monkeypatch):
    c, db_factory = client
    _set_user(patente="ABC123", saldo=100.0)
    _seed_user_saldo(db_factory, user_id=1, saldo=100.0)
    notificados = []
    from services.user_notification_service import UserNotificationService

    monkeypatch.setattr(
        UserNotificationService,
        "create_notification",
        classmethod(lambda cls, db, uid, tipo, titulo, msg: notificados.append((uid, tipo, msg))),
    )
    resp = c.post("/recharge-balance", json={"monto": 500.0})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert CURRENT["user"].saldo == 600.0
    assert notificados
    assert notificados[0][0] == 1
    assert notificados[0][1] == "BALANCE_RECHARGED"


def test_recharge_balance_notificacion_que_falla_devuelve_ok(client, monkeypatch):
    c, db_factory = client
    _set_user(patente="ABC123", saldo=0.0)
    _seed_user_saldo(db_factory, user_id=1, saldo=0.0)
    from services.user_notification_service import UserNotificationService

    def boom(db, uid, tipo, titulo, msg):
        raise RuntimeError("notificación caída")

    monkeypatch.setattr(UserNotificationService, "create_notification", classmethod(boom))
    resp = c.post("/recharge-balance", json={"monto": 10.0})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Carga de $10.00 exitosa"
    assert CURRENT["user"].saldo == 10.0