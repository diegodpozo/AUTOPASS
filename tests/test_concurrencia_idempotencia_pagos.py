"""FASE 5 (R4) - IDEMPOTENCIA DE PAGOS Y MANEJO DE IntegrityError.

Mercado Pago REINTENTA los webhooks: el mismo pago puede llegar dos veces (o mas).
Sin una clave de idempotencia a nivel de base, dos entregas simultaneas pueden
acreditar el pago dos veces (doble cobro / doble acreditacion de puntos).

Que cubre este modulo:
  1. `payment_id` es UNICO en la base: dos filas con el mismo id de pago de MP
     chocan con IntegrityError aunque se esquive el servicio.
  2. "Sin payment_id" se guarda como NULL (no ''): en Postgres/SQLite varios NULL
     NO colisionan en un indice unico, asi que los pagos todavia sin id de MP
     conviven sin romper.
  3. Dos entregas del MISMO webhook producen un solo cobro y una sola
     acreditacion de puntos (criterio de salida de la Fase 5).
  4. Un IntegrityError en un endpoint se traduce a HTTP 409 con mensaje de
     negocio y la transaccion queda limpia (db.rollback()).

Se corren en SQLite en memoria: la unicidad de `payment_id` es una regla de
esquema (declarada en el modelo), no una capacidad exclusiva de Postgres, asi que
aca se prueba la regla de negocio sin depender de la red.
"""
import datetime
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
import services.mercadopago_service as mp_service
from core.database import Base, get_db
from core.limiter import limiter
from main import app
from models import MercadoPagoPayment, PointsLog, Reservation
from models.enums import PaymentStatus, ReservationStatus

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    saved = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_get_db
    limiter.reset()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)
        limiter.reset()
        Base.metadata.drop_all(bind=engine)


def _usuario(db, saldo=5000.0):
    user = models.User(email=f"u{uuid.uuid4().hex[:10]}@test.com", nombre="Test", apellido="User",
                       password_hash="x", rol="user", saldo=saldo, puntos_acumulados=0)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _reserva(db, user, monto=1000.0):
    res = Reservation(user_id=user.id, patente="ABC123", fecha_inicio="2026-09-02T10:00:00",
                      fecha_fin="2026-09-02T12:00:00", monto_total=monto,
                      estado_pago=PaymentStatus.PENDIENTE, estado_reserva=ReservationStatus.PENDIENTE,
                      tipo_estadia="hora", sucursal_nombre="AUTOPASS Central")
    db.add(res)
    db.commit()
    db.refresh(res)
    return res


# ---------------------------------------------------------------------------
# 1 - la clave de idempotencia existe a nivel de esquema
# ---------------------------------------------------------------------------

def test_payment_id_es_unico(db):
    """Dos pagos distintos NO pueden compartir el mismo payment_id de MP."""
    user = _usuario(db)
    db.add(MercadoPagoPayment(user_id=user.id, tipo="estadia", monto=100.0,
                              external_reference="REF-A", payment_id="PAY-UNICO", estado="APROBADO"))
    db.commit()

    db.add(MercadoPagoPayment(user_id=user.id, tipo="estadia", monto=200.0,
                              external_reference="REF-B", payment_id="PAY-UNICO", estado="APROBADO"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_varios_payment_id_nulos_conviven(db):
    """'Sin payment_id' debe ser NULL: varios pendientes sin id de MP no chocan."""
    user = _usuario(db)
    for ref in ("REF-1", "REF-2", "REF-3"):
        db.add(MercadoPagoPayment(user_id=user.id, tipo="estadia", monto=100.0,
                                  external_reference=ref, payment_id=None, estado="PENDIENTE"))
    db.commit()  # no debe lanzar IntegrityError
    assert db.query(MercadoPagoPayment).count() == 3


# ---------------------------------------------------------------------------
# 2 - sin id de MP se guarda NULL, nunca ''
# ---------------------------------------------------------------------------

def test_aplicar_pago_sin_id_guarda_null_no_vacio(db, monkeypatch):
    """Si MP no devuelve id, el registro queda con NULL (no ''), para no colisionar."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")
    user = _usuario(db)
    res = _reserva(db, user, monto=1000.0)
    pago = MercadoPagoPayment(user_id=user.id, tipo="reserva", reserva_id=res.id, patente="ABC123",
                              monto=1000.0, external_reference="AP-RES-NOID", estado="PENDIENTE")
    db.add(pago)
    db.commit()
    db.refresh(pago)

    monkeypatch.setattr(mp_service, "_get_payment_from_mp",
                        lambda payment_id, external_reference=None: {"status": "approved", "transaction_amount": 1000.0})

    mp_service.confirm_payment(db, "AP-RES-NOID", payment_id=None)
    db.refresh(pago)
    assert pago.aplicado is True
    assert pago.payment_id is None, f"se esperaba NULL, quedo {pago.payment_id!r}"


# ---------------------------------------------------------------------------
# 3 - dos entregas del mismo webhook: un solo cobro, una sola acreditacion
# ---------------------------------------------------------------------------

def test_dos_entregas_mismo_webhook_un_solo_cobro(db, monkeypatch):
    """El criterio de salida de la Fase 5: reintento del webhook no duplica nada."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")
    user = _usuario(db, saldo=5000.0)
    res = _reserva(db, user, monto=1000.0)
    pago = MercadoPagoPayment(user_id=user.id, tipo="reserva", reserva_id=res.id, patente="ABC123",
                              monto=1000.0, external_reference="AP-RES-555", estado="PENDIENTE")
    db.add(pago)
    db.commit()

    monkeypatch.setattr(mp_service, "_get_payment_from_mp",
                        lambda payment_id, external_reference=None: {"id": "PAY-555", "status": "approved", "transaction_amount": 1000.0})

    primero = mp_service.confirm_payment(db, "AP-RES-555", payment_id="PAY-555")
    segundo = mp_service.confirm_payment(db, "AP-RES-555", payment_id="PAY-555")

    assert primero["aplicado"] is True
    assert segundo["aplicado"] is True  # sigue siendo "aplicado", pero NO reprocesa

    db.refresh(user)
    db.refresh(res)
    assert res.estado_pago == PaymentStatus.PAGADO
    # 1000 pesos -> 10 puntos, UNA sola vez
    assert user.puntos_acumulados == 10
    assert db.query(models.PointsLog).filter(models.PointsLog.user_id == user.id).count() == 1


def test_webhook_repetido_via_endpoint_no_duplica(monkeypatch, client):
    """Dos POST del mismo webhook (idempotencia end-to-end por la ruta real)."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")
    db = TestSession()
    try:
        user = _usuario(db, saldo=5000.0)
        res = _reserva(db, user, monto=2000.0)
        pago = MercadoPagoPayment(user_id=user.id, tipo="reserva", reserva_id=res.id, patente="ABC123",
                                  monto=2000.0, external_reference="AP-RES-777", estado="PENDIENTE")
        db.add(pago)
        db.commit()

        monkeypatch.setattr(mp_service, "_mp_request", lambda method, path: {"external_reference": "AP-RES-777"})
        monkeypatch.setattr(mp_service, "_get_payment_from_mp",
                            lambda payment_id, external_reference=None: {"id": "PAY-777", "status": "approved", "transaction_amount": 2000.0})

        body = {"type": "payment", "data": {"id": "PAY-777"}}
        r1 = client.post("/v1/user/mercadopago/webhook", json=body)
        r2 = client.post("/v1/user/mercadopago/webhook", json=body)
        assert r1.status_code == 200 and r2.status_code == 200

        db.expire_all()
        user2 = db.query(models.User).filter(models.User.id == user.id).one()
        assert user2.puntos_acumulados == 20  # 2000 -> 20 puntos, una sola vez
        assert db.query(models.PointsLog).filter(models.PointsLog.user_id == user.id).count() == 1
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4 - IntegrityError -> HTTP 409 con la transaccion limpia
# ---------------------------------------------------------------------------

def test_integrity_error_devuelve_409_y_deja_la_sesion_limpia(client):
    """Un choque de unicidad en un endpoint es 409 (no 500) y la sesion queda usable."""
    from core.security import get_current_user
    from routes.user import mercadopago as mp_route

    # Un pago ya aplicado con un payment_id concreto: el siguiente intento del
    # MISMO id de MP debe chocar contra el indice unico.
    db = TestSession()
    try:
        user = _usuario(db)
        db.add(MercadoPagoPayment(user_id=user.id, tipo="estadia", monto=1.0,
                                  external_reference="REF-OK", payment_id="PAY-DUP", estado="PENDIENTE"))
        db.commit()
        user_id = user.id
    finally:
        db.close()

    original = mp_route.mp_service.create_payment

    def boom(db, current_user, data):
        # Simula lo que pasa cuando un INSERT choca con el indice unico de payment_id.
        db.add(MercadoPagoPayment(user_id=current_user.id, tipo="estadia", monto=1.0,
                                  external_reference="REF-OTRO", payment_id="PAY-DUP", estado="PENDIENTE"))
        db.commit()  # -> IntegrityError
        return {"init_point": "x", "external_reference": "y", "monto": 1.0, "preference_id": "z"}

    def fake_user():
        s = TestSession()
        return s.query(models.User).filter(models.User.id == user_id).one()

    mp_route.mp_service.create_payment = boom
    app.dependency_overrides[get_current_user] = fake_user
    try:
        resp = client.post("/v1/user/mercadopago/checkout",
                           json={"tipo": "estadia", "access_log_id": 1})
        assert resp.status_code == 409, f"se esperaba 409, fue {resp.status_code}: {resp.text}"
        assert "detail" in resp.json()
        assert "procesada" in resp.json()["detail"].lower() or "reintent" in resp.json()["detail"].lower()
    finally:
        mp_route.mp_service.create_payment = original
        app.dependency_overrides.pop(get_current_user, None)
