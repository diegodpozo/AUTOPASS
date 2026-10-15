"""Tests de la foto de tarifas (price snapshot) y la validación de cotización.

Cubre:
  - Persistencia de la foto (tarifas/duración/total) al crear/editar reservas.
  - Rechazo con 409 cuando el total u horas cotizadas por el front no coinciden.
  - Registro del % de descuento y del total base al abonar una reserva.
"""
import datetime
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from schemas import AdminReservationCreate, UserReservationCreate
from services.payments import ReservationPaymentsMixin
from services.reservation_service import ReservationService


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    S = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = S()
    _seed_branch(session)
    yield session
    session.close()
    engine.dispose()


def _seed_branch(db, nombre="TestBranch"):
    db.add(models.ParkingBranch(nombre=nombre, direccion="Calle Falsa 123", horario="24hs"))
    db.add(models.Settings(clave="precio_hora", valor=1500.0, sucursal=nombre))
    db.add(models.Settings(clave="precio_30min", valor=750.0, sucursal=nombre))
    db.add(models.Settings(clave="precio_dia", valor=15000.0, sucursal=nombre))
    db.commit()


def _usuario(db, email="snapshot@test.com"):
    u = models.User(
        nombre="Ana", apellido="Gómez", dni=str(uuid.uuid4().int)[:8], telefono="1122334455",
        email=email, password_hash="x", rol="user", saldo=0.0, puntos_acumulados=0,
        is_blocked=False, is_deleted=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _vehiculo(db, user, patente="ABC123", tipo="Auto"):
    v = models.Vehicle(user_id=user.id, patente=patente, marca_modelo="Test", tipo=tipo)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def _ticket(db, user, porc=10, sucursal=None):
    t = models.RedemptionTicket(
        user_id=user.id, codigo=f"TKT-{uuid.uuid4().hex[:8]}", titulo="10% OFF",
        descripcion="d", tipo_canje="descuento_reserva", valor_descuento=porc,
        estado="VIGENTE", sucursal=sucursal,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# --- FOTO DE TARIFAS: ALTA ADMIN ---

def test_admin_create_persiste_foto_tarifas(db):
    # 10:00 → 12:00 (2h) con hora=1500 y fracción=750 => 2*1500 + 1*750 = 3750
    data = AdminReservationCreate(
        patente="ABC123", fecha_inicio="2030-06-20T10:00:00", fecha_fin="2030-06-20T12:00:00",
        tipo_estadia="hora", sucursal_nombre="TestBranch", cliente_nombre="Juan Test",
        horas_calculadas=2.0, monto_calculado=3750.0,
    )
    res = ReservationService.create_reservation(db, data)
    assert res.tarifa_hora == 1500.0
    assert res.tarifa_fraccion == 750.0
    assert res.tarifa_aplicada == 1500.0
    assert res.horas_calculadas == 2.0
    assert res.monto_calculado == 3750.0
    assert res.tarifa_fijada_en is not None


def test_admin_create_sin_cotizacion_no_valida(db):
    data = AdminReservationCreate(
        patente="ABC123", fecha_inicio="2030-06-20T10:00:00", fecha_fin="2030-06-20T12:00:00",
        tipo_estadia="hora", sucursal_nombre="TestBranch", cliente_nombre="Juan Test",
    )
    res = ReservationService.create_reservation(db, data)
    assert res.monto_total == 3750.0
    assert res.monto_calculado == 3750.0  # snapshot calculado por el servidor


def test_admin_create_monto_discrepante_409(db):
    data = AdminReservationCreate(
        patente="ABC123", fecha_inicio="2030-06-20T10:00:00", fecha_fin="2030-06-20T12:00:00",
        tipo_estadia="hora", sucursal_nombre="TestBranch", cliente_nombre="Juan Test",
        monto_calculado=9999.0,
    )
    with pytest.raises(Exception) as exc:
        ReservationService.create_reservation(db, data)
    assert exc.value.status_code == 409


def test_admin_create_horas_discrepantes_409(db):
    data = AdminReservationCreate(
        patente="ABC123", fecha_inicio="2030-06-20T10:00:00", fecha_fin="2030-06-20T12:00:00",
        tipo_estadia="hora", sucursal_nombre="TestBranch", cliente_nombre="Juan Test",
        horas_calculadas=5.0,
    )
    with pytest.raises(Exception) as exc:
        ReservationService.create_reservation(db, data)
    assert exc.value.status_code == 409


# --- FOTO DE TARIFAS: ALTA USUARIO ---

def test_user_create_persiste_foto_tarifas(db):
    user = _usuario(db)
    _vehiculo(db, user)
    inicio = (datetime.datetime.now() + datetime.timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    fin = inicio.replace(hour=23, minute=59, second=0, microsecond=0)
    horas = (fin - inicio).total_seconds() / 3600
    data = UserReservationCreate(
        patente="ABC123", fecha_inicio=inicio.strftime("%Y-%m-%d %H:%M:%S"),
        fecha_fin=fin.strftime("%Y-%m-%d %H:%M:%S"),
        tipo_estadia="dia", sucursal_nombre="TestBranch",
        horas_calculadas=horas, monto_calculado=15000.0,
    )
    result = ReservationService.create_user_reservation(db, user, data)
    assert result["status"] == "ok"
    res = db.query(models.Reservation).filter(models.Reservation.user_id == user.id).one()
    assert res.tarifa_hora == 1500.0
    assert res.tarifa_fraccion == 750.0
    assert res.tarifa_aplicada == 15000.0
    assert res.monto_calculado == 15000.0


def test_user_create_monto_discrepante_409(db):
    user = _usuario(db)
    _vehiculo(db, user)
    inicio = (datetime.datetime.now() + datetime.timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    fin = inicio.replace(hour=23, minute=59, second=0, microsecond=0)
    data = UserReservationCreate(
        patente="ABC123", fecha_inicio=inicio.strftime("%Y-%m-%d %H:%M:%S"),
        fecha_fin=fin.strftime("%Y-%m-%d %H:%M:%S"),
        tipo_estadia="dia", sucursal_nombre="TestBranch", monto_calculado=1.0,
    )
    with pytest.raises(Exception) as exc:
        ReservationService.create_user_reservation(db, user, data)
    assert exc.value.status_code == 409


# --- DESCUENTO AL PAGAR (FOTO) ---

def _reserva(db, user, monto=1000.0, sucursal="TestBranch"):
    r = models.Reservation(
        user_id=user.id, patente="ABC123", fecha_inicio="2030-01-01 00:00:00",
        fecha_fin="2030-01-02 00:00:00", monto_total=monto, monto_reembolsado=0.0,
        estado_pago="Pendiente", estado_reserva="Pendiente", sucursal_nombre=sucursal, tipo_estadia="hora",
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def test_manual_pago_guarda_descuento_y_base(db):
    user = _usuario(db)
    res = _reserva(db, user, monto=1000.0)
    ticket = _ticket(db, user, porc=10)

    ReservationPaymentsMixin.pay_reservation_manual(db, res, metodo_pago="EFECTIVO", redemption_ticket_id=ticket.id)

    db.refresh(res)
    assert res.monto_total == 900.0
    assert res.monto_calculado == 1000.0
    assert res.descuento_pct == 10


def test_pago_saldo_guarda_descuento_y_base(db, monkeypatch):
    from services.email_service import EmailService
    monkeypatch.setattr(EmailService, "send_reservation_confirmation", lambda *a, **k: None)
    user = _usuario(db)
    user.saldo = 2000.0
    db.commit()
    res = _reserva(db, user, monto=1000.0)
    ticket = _ticket(db, user, porc=10)

    ReservationPaymentsMixin.pay_reservation(db, user, res.id, redemption_ticket_id=ticket.id)

    db.refresh(res)
    assert res.monto_total == 900.0
    assert res.monto_calculado == 1000.0
    assert res.descuento_pct == 10


def test_pago_sin_descuento_no_toca_foto(db):
    user = _usuario(db)
    res = _reserva(db, user, monto=1000.0)
    ReservationPaymentsMixin.pay_reservation_manual(db, res, metodo_pago="EFECTIVO")
    db.refresh(res)
    assert res.descuento_pct is None
