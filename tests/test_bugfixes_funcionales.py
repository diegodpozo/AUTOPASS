import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
import schemas
from core.normalize import format_plate, normalize_plate
from models import Base
from models.enums import AccessEventType, PaymentStatus, ReservationStatus, UserRole, VehicleType
from services.access_service import AccessService
from services.billing_service import BillingService
from services.hardware_service import HardwareService
from services.time_service import TimeService

SUCURSAL = "AUTOPASS Test"
PATENTE = "AB123CD"


@pytest.fixture
def db(monkeypatch):
    monkeypatch.setattr(HardwareService, "trigger_barrier", classmethod(lambda cls, *a, **k: {"status": "ok"}))
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    Base.metadata.create_all(bind=engine)
    session.add(models.ParkingBranch(nombre=SUCURSAL, direccion="x", telefono="1", latitude=-34.6, longitude=-58.4))
    session.flush()
    session.add(models.Settings(clave="precio_hora", valor=1500.0, sucursal=SUCURSAL))
    session.add(models.Settings(clave="precio_30min", valor=750.0, sucursal=SUCURSAL))
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _sucursal(db):
    if not db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == SUCURSAL).first():
        db.add(models.ParkingBranch(nombre=SUCURSAL, direccion="x", telefono="1", latitude=-34.6, longitude=-58.4))
        db.commit()


def _usuario(db, puntos=0):
    u = models.User(
        nombre="Test", apellido="Uno", email="test@autopass.com", dni="20111111",
        telefono="1155555555", password_hash="x", rol=UserRole.USER.value, puntos_acumulados=puntos,
    )
    db.add(u)
    db.commit()
    return u


def _vehiculo(db, user):
    v = models.Vehicle(patente=format_plate(PATENTE), tipo=VehicleType.AUTO, user_id=user.id, is_favorite=True)
    db.add(v)
    db.commit()
    return v


def _log(db, user, reserva_id=None, pago_confirmado=False, costo=None, fecha_pago=None):
    ahora = TimeService.now()
    log = models.AccessLog(
        patente_detectada=normalize_plate(PATENTE),
        normalized_patente=normalize_plate(PATENTE),
        tipo_evento=AccessEventType.ENTRADA,
        tipo_vehiculo=VehicleType.AUTO,
        fecha_hora=(ahora - datetime.timedelta(hours=3)).isoformat(),
        pago_confirmado=pago_confirmado,
        costo_estadia=costo,
        fecha_pago=fecha_pago.isoformat() if fecha_pago else None,
        metodo_pago="DIGITAL" if pago_confirmado else None,
        sucursal=SUCURSAL,
        reserva_id=reserva_id,
    )
    db.add(log)
    db.commit()
    return log


def _reserva_vencida(db, user):
    ahora = TimeService.now()
    r = models.Reservation(
        user_id=user.id,
        sucursal_nombre=SUCURSAL,
        patente=format_plate(PATENTE),
        tipo_estadia="hora",
        tipo_vehiculo=VehicleType.AUTO,
        fecha_inicio=(ahora - datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
        fecha_fin=(ahora - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
        monto_total=1000.0,
        estado_pago=PaymentStatus.PAGADO,
        estado_reserva=ReservationStatus.ACTIVA,
        metodo_pago="MERCADOPAGO",
        origen="cliente",
        fecha_pago=ahora.isoformat(),
    )
    db.add(r)
    db.commit()
    return r


def test_exit_plate_registra_salida_en_sede_sin_aforo_configurado(db):
    _sucursal(db)
    user = _usuario(db)
    _log(db, user, pago_confirmado=True)
    assert db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == SUCURSAL).count() == 0

    res = AccessService.exit_plate(
        db, schemas.PlateValidation(plate=PATENTE, gate_id=f"{SUCURSAL}_SALIDA")
    )

    assert res["status"] == "allowed"
    assert db.query(models.AccessLog).filter(
        models.AccessLog.tipo_evento == AccessEventType.SALIDA
    ).count() == 1


def test_validate_qr_sin_guion_bajo_en_gate_id_no_falla_con_error_interno(db):
    _sucursal(db)
    user = _usuario(db)
    _vehiculo(db, user)

    res = AccessService.validate_qr(
        db, schemas.QRValidation(qr_data="AUTOPASS|reserva:999999|patente:ZZ999ZZ", gate_id="QR")
    )

    assert res["status"] == "error"
    assert res["message"] == "Reserva no encontrada"


def test_validate_qr_no_expone_mensajes_de_error_interno(db):
    _sucursal(db)
    user = _usuario(db)
    _vehiculo(db, user)

    res = AccessService.validate_qr(
        db, schemas.QRValidation(qr_data="contenido-invalido", gate_id=f"{SUCURSAL}_ENTRADA")
    )

    assert res["status"] == "error"
    assert res["message"] == "Formato de QR inválido"
    assert "local variable" not in res["message"]


def test_checkout_mercadopago_de_estadia_acepta_patente_en_distinto_formato(db, monkeypatch):
    from services import mercadopago_service as mp_service
    from services.mercadopago_service import create_payment

    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")
    monkeypatch.setattr(mp_service.settings, "BASE_URL", "https://localhost")

    def fake_mp_request(method, path, payload=None):
        return {"id": "PREF-1", "init_point": "https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id=PREF-1"}

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)

    _sucursal(db)
    user = _usuario(db)
    _vehiculo(db, user)
    log = _log(db, user)

    res = create_payment(db, user, schemas.MercadoPagoCheckout(tipo="estadia", access_log_id=log.id))

    assert res["external_reference"].startswith("AP-ESTADIA-")
    assert res["init_point"]
    assert db.query(models.MercadoPagoPayment).count() == 1


def test_extra_por_reserva_vencida_se_cobra_una_sola_vez(db):
    _sucursal(db)
    user = _usuario(db)
    _vehiculo(db, user)
    reserva = _reserva_vencida(db, user)
    ahora = TimeService.now()
    _log(db, user, reserva_id=reserva.id, pago_confirmado=True, costo=1000.0,
         fecha_pago=ahora - datetime.timedelta(hours=3))

    primera = BillingService.process_payment(db, normalize_plate(PATENTE), metodo="CAJA")
    costo_tras_primera = db.query(models.AccessLog).get(1).costo_estadia
    segunda = BillingService.process_payment(db, normalize_plate(PATENTE), metodo="CAJA")
    tercera = BillingService.process_payment(db, normalize_plate(PATENTE), metodo="CAJA")
    log_final = db.query(models.AccessLog).filter(models.AccessLog.reserva_id == reserva.id).one()

    assert primera["monto_cobrado"] > 0
    assert segunda["monto_cobrado"] == 0.0
    assert tercera["monto_cobrado"] == 0.0
    assert log_final.costo_estadia == costo_tras_primera
    assert log_final.costo_estadia == pytest.approx(1000.0 + primera["monto_cobrado"])


def test_cobro_en_caja_acredita_puntos_con_patente_normalizada(db):
    _sucursal(db)
    user = _usuario(db, puntos=0)
    _vehiculo(db, user)
    _log(db, user)

    res = BillingService.process_payment(db, normalize_plate(PATENTE), metodo="CAJA")

    db.refresh(user)
    assert res["puntos_ganados"] > 0
    assert user.puntos_acumulados == res["puntos_ganados"]
    assert db.query(models.PointsLog).filter(models.PointsLog.user_id == user.id).count() == 1


@pytest.mark.parametrize("gate_id,esperado", [
    ("ENTRADA", "ENTRADA"),
    ("entrada", "ENTRADA"),
    ("INGRESO", "ENTRADA"),
    ("ENTRY", "ENTRADA"),
    ("SALIDA", "SALIDA"),
    ("EGRESO", "SALIDA"),
    ("EXIT", "SALIDA"),
    (f"{SUCURSAL}_ENTRADA", "ENTRADA"),
    (f"{SUCURSAL}_SALIDA", "SALIDA"),
])
def test_resolve_gate_reconoce_alias_de_porton(gate_id, esperado):
    assert HardwareService.resolve_gate(gate_id) == esperado


@pytest.mark.parametrize("gate_id", ["", None, "QR", "EGRES0", "ENTRADA_SALIDA", "TYP0"])
def test_resolve_gate_rechaza_porton_desconocido_sin_asumir_salida(gate_id):
    with pytest.raises(HTTPException) as exc:
        HardwareService.resolve_gate(gate_id)
    assert exc.value.status_code == 400


@pytest.fixture
def hardware_mocks(monkeypatch):
    monkeypatch.setattr(HardwareService, "publish_mqtt", classmethod(lambda cls, *a, **k: None))
    monkeypatch.setattr(HardwareService, "send_serial_command", staticmethod(lambda *a, **k: False))


def test_trigger_barrier_rechaza_gate_id_desconocido(hardware_mocks):

    with pytest.raises(HTTPException) as exc:
        HardwareService.trigger_barrier("TYP0", "OPEN", method="TEST")

    assert exc.value.status_code == 400


def test_trigger_barrier_sigue_funcionando_con_gate_id_valido(hardware_mocks):

    res = HardwareService.trigger_barrier("EGRESO", "OPEN", method="TEST")

    assert res["gate"] == "SALIDA"
    assert res["command"] == "OPEN"
