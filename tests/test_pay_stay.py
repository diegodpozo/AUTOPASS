"""Test #5 de la auditoría A3: endpoint autenticado POST /v1/access/pay-stay.

Verifica la protección por roles (get_operational_user) y el flujo de cobro de
estadía en curso para personal operativo.
"""
import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.database import get_db, Base
from core.limiter import limiter
from core.security import create_access_token
import models

URL = "/v1/access/pay-stay"


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
    limiter.reset()
    yield TestClient(app), TestSession
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    limiter.reset()


def _crear_usuario(TestSession, rol, email):
    db = TestSession()
    user = models.User(email=email, nombre="Staff", apellido="Ops", dni=email[:8],
                       password_hash="x", rol=rol, is_blocked=False, is_deleted=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def _token(user):
    return create_access_token({"sub": user.email, "rol": user.rol})


def _crear_entrada(TestSession, placa, hace_horas=2):
    db = TestSession()
    now_iso = (datetime.datetime.now() - datetime.timedelta(hours=hace_horas)).isoformat()
    log = models.AccessLog(patente_detectada=placa, tipo_evento="ENTRADA",
                           tipo_vehiculo="Auto", fecha_hora=now_iso,
                           pago_confirmado=False, sucursal="AUTOPASS Central")
    db.add(log)
    db.commit()
    db.refresh(log)
    db.close()
    return log


def test_pay_stay_sin_token_es_401(client):
    tc, _ = client
    resp = tc.post(f"{URL}?plate=ABC123")
    assert resp.status_code == 401


def test_pay_stay_rol_usuario_es_403(client):
    tc, TestSession = client
    user = _crear_usuario(TestSession, "user", "client@test.com")
    resp = tc.post(f"{URL}?plate=ABC123",
                   headers={"Authorization": f"Bearer {_token(user)}"})
    assert resp.status_code == 403


def test_pay_stay_staff_cobra_estadia_pendiente(client):
    tc, TestSession = client
    staff = _crear_usuario(TestSession, "staff", "staff@test.com")
    _crear_entrada(TestSession, "ABC123")

    resp = tc.post(f"{URL}?plate=ABC123",
                   headers={"Authorization": f"Bearer {_token(staff)}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["monto_cobrado"] > 0

    db = TestSession()
    log = db.query(models.AccessLog).filter(models.AccessLog.patente_detectada == "ABC123").first()
    assert log.pago_confirmado is True
    assert log.metodo_pago == "DIGITAL"
    db.close()


def test_pay_stay_staff_metodo_caja_aplica(client):
    tc, TestSession = client
    staff = _crear_usuario(TestSession, "staff", "staff2@test.com")
    _crear_entrada(TestSession, "XYZ987")

    resp = tc.post(f"{URL}?plate=XYZ987&metodo=CAJA",
                   headers={"Authorization": f"Bearer {_token(staff)}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    db = TestSession()
    log = db.query(models.AccessLog).filter(models.AccessLog.patente_detectada == "XYZ987").first()
    assert log.metodo_pago == "CAJA"
    db.close()


def test_pay_stay_staff_sin_estadia_devuelve_400(client):
    tc, TestSession = client
    staff = _crear_usuario(TestSession, "staff", "staff3@test.com")

    resp = tc.post(f"{URL}?plate=ZZ000",
                   headers={"Authorization": f"Bearer {_token(staff)}"})
    assert resp.status_code == 400
    assert "pendientes" in resp.json()["detail"]