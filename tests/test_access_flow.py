"""Test #7 de la auditoría A3: flujo de ingreso/egreso con barrera.

Cubre services/access_service.py (antes 38%): open-barrier → GPIO/estado a través de
HardwareService.trigger_barrier en los flujos ALPR, QR y manuales, más validaciones
de aforo, cortesía (10 min), cancelaciones y helpers (_save_image/_branch_from_gate_id).
"""
import base64
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from models.enums import AccessEventType, PaymentStatus, ReservationStatus, VehicleType
from schemas import PlateValidation, QRValidation
from services.access_service import AccessService
from services.billing_service import BillingService
from services.hardware_service import HardwareService
from services.notification_service import NotificationService
from services.time_service import TimeService

FIXED = datetime.datetime(2026, 9, 20, 12, 0, 0)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base = models.Base
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    session.add(models.ParkingBranch(nombre="Centro", direccion="Av. X 123", activa=True))
    session.add(models.ParkingAforo(sucursal="Centro", capacidad_total=50, ocupacion_actual=0,
                                    capacidad_motos=10, ocupacion_motos=0))
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def env(monkeypatch):
    """Tiempo fijo + barrera falsa que registra los comandos disparados."""
    calls = []

    def fake_barrier(gate_id, command="OPEN", method="AUTO", details=None, request=None):
        calls.append({"gate": gate_id, "command": command, "method": method, "details": details})

    monkeypatch.setattr(HardwareService, "trigger_barrier", staticmethod(fake_barrier))
    monkeypatch.setattr(TimeService, "now", staticmethod(lambda: FIXED))
    return {"calls": calls}


def _hace(minutos):
    return f"{(FIXED - datetime.timedelta(minutes=minutos)):%Y-%m-%d %H:%M:%S}"


def _futuro(minutos):
    return f"{(FIXED + datetime.timedelta(minutes=minutos)):%Y-%m-%d %H:%M:%S}"


def _log_entrada(db, patente, fecha_str=_hace(2), pago=False, sucursal="Centro",
                 tipo=AccessEventType.ENTRADA, reserva_id=None, tipo_vehiculo="Auto"):
    log = models.AccessLog(patente_detectada=patente, normalized_patente=patente,
                           tipo_evento=tipo, tipo_vehiculo=tipo_vehiculo,
                           fecha_hora=fecha_str, pago_confirmado=pago, sucursal=sucursal,
                           reserva_id=reserva_id)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _reserva(db, patente="AA123BB", inicio=_hace(15), fin=_futuro(60),
             estado=ReservationStatus.PENDIENTE, pago=PaymentStatus.PENDIENTE, sucursal="Centro"):
    r = models.Reservation(patente=patente, fecha_inicio=inicio, fecha_fin=fin,
                           estado_reserva=estado, estado_pago=pago,
                           sucursal_nombre=sucursal, monto_total=100.0, tipo_vehiculo="Auto")
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


# ---------------------------------------------------------------------------
# validate_plate (ALPR) + barrera
# ---------------------------------------------------------------------------

def test_valida_plate_permite_y_dispara_barrera(db, env):
    result = AccessService.validate_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_ENTRADA"))
    assert result["status"] == "allowed"
    assert result["action"] == "OPEN_GATE"
    assert env["calls"][0]["gate"] == "ENTRADA"
    assert env["calls"][0]["command"] == "OPEN"
    assert env["calls"][0]["method"] == "ALPR"
    aforo = db.query(models.ParkingAforo).filter_by(sucursal="Centro").first()
    assert aforo.ocupacion_actual == 1


def test_valida_plate_capacidad_maxima_no_dispara_barrera(db, env):
    db.query(models.ParkingAforo).filter_by(sucursal="Centro").update(
        {models.ParkingAforo.ocupacion_actual: 50})
    db.commit()
    result = AccessService.validate_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_ENTRADA"))
    assert result["status"] == "denied"
    assert "Capacidad máxima" in result["message"]
    assert env["calls"] == []


def test_valida_plate_moto_usa_capacidad_motos(db, env):
    db.add(models.Vehicle(patente="A123BCD", tipo="Moto"))
    db.commit()
    result = AccessService.validate_plate(db, PlateValidation(plate="A123BCD", gate_id="Centro_ENTRADA"))
    assert result["status"] == "allowed"
    aforo = db.query(models.ParkingAforo).filter_by(sucursal="Centro").first()
    assert aforo.ocupacion_motos == 1
    assert aforo.ocupacion_actual == 0


def test_valida_plate_con_reserva_activa_libera_reserva(db, env):
    _reserva(db, patente="AA123BB")
    result = AccessService.validate_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_ENTRADA"))
    assert result["status"] == "allowed"
    aforo = db.query(models.ParkingAforo).filter_by(sucursal="Centro").first()
    assert aforo.ocupacion_reservas == 1
    log = db.query(models.AccessLog).filter_by(patente_detectada="AA123BB").first()
    assert log.reserva_id is not None
    assert log.pago_confirmado is False


def test_valida_plate_ya_dentro_rechaza(db, env):
    _log_entrada(db, "AA123BB")
    result = AccessService.validate_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_ENTRADA"))
    assert result["status"] == "denied"
    assert "ya figura dentro" in result["message"]
    assert env["calls"] == []


# ---------------------------------------------------------------------------
# exit_plate (ALPR) + barrera + deuda
# ---------------------------------------------------------------------------

def test_exit_plate_cortesia_ok_y_dispara_barrera(db, env):
    _log_entrada(db, "AA123BB", pago=False)
    result = AccessService.exit_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_SALIDA"))
    assert result["status"] == "allowed"
    assert env["calls"][0]["gate"] == "SALIDA"
    assert env["calls"][0]["method"] == "ALPR"
    aforo = db.query(models.ParkingAforo).filter_by(sucursal="Centro").first()
    assert aforo.ocupacion_actual == 0


def test_exit_plate_deuda_mayor_10min_rechaza_y_no_abre(db, env):
    NotificationService.clear_pending_exit("CENTRO")
    log = _log_entrada(db, "AA123BB", fecha_str=_hace(30), pago=False)
    result = AccessService.exit_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_SALIDA"))
    assert result["status"] == "denied"
    assert "Deuda pendiente" in result["message"]
    assert env["calls"] == []
    # EMITE EL EVENTO PARA EL POPUP DE CAJA (usuario invitado, sin tarifario -> deuda None)
    pending = NotificationService.get_pending_exit("CENTRO")
    assert pending is not None
    assert pending["patente"] == "AA123BB"
    assert pending["log_id"] == log.id
    assert pending["es_registrado"] is False
    assert pending["usuario"] is None
    assert pending["tipo_vehiculo"] == "Auto"
    assert pending["sucursal"] == "Centro"
    assert pending["gate_id"] == "Centro_SALIDA"
    assert pending["deuda"] is None
    NotificationService.clear_pending_exit("CENTRO")


def test_exit_plate_deuda_con_tarifario_previsualiza_monto(db, env):
    NotificationService.clear_pending_exit("CENTRO")
    db.add(models.Settings(clave="precio_30min", valor="100", sucursal="Centro"))
    db.commit()
    _log_entrada(db, "AA123BB", fecha_str=_hace(30), pago=False)
    AccessService.exit_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_SALIDA"))
    pending = NotificationService.get_pending_exit("CENTRO")
    assert pending["deuda"] == 100.0  # 30 min = 1 bloque
    NotificationService.clear_pending_exit("CENTRO")


def test_exit_plate_deuda_usuario_registrado_usa_nombre(db, env):
    NotificationService.clear_pending_exit("CENTRO")
    u = models.User(email="cli@example.com", nombre="Ana", apellido="Gomez", dni="12345678",
                    rol="user", password_hash="x")
    db.add(u)
    db.commit()
    db.add(models.Vehicle(patente="AA 123 BB", tipo="Auto", user_id=u.id))
    db.commit()
    _log_entrada(db, "AA123BB", fecha_str=_hace(30), pago=False)
    AccessService.exit_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_SALIDA"))
    pending = NotificationService.get_pending_exit("CENTRO")
    assert pending["es_registrado"] is True
    assert pending["usuario"] == "Ana Gomez"
    NotificationService.clear_pending_exit("CENTRO")


def test_exit_plate_cortesia_no_emite_pending_exit(db, env):
    NotificationService.clear_pending_exit("CENTRO")
    _log_entrada(db, "AA123BB", fecha_str=_hace(5), pago=False)
    AccessService.exit_plate(db, PlateValidation(plate="AA123BB", gate_id="Centro_SALIDA"))
    assert NotificationService.get_pending_exit("CENTRO") is None


def test_exit_plate_sin_ingreso_error(db, env):
    result = AccessService.exit_plate(db, PlateValidation(plate="ZZ999ZZ", gate_id="Centro_SALIDA"))
    assert result["status"] == "error"
    assert "no tiene registro de ingreso" in result["message"]


# ---------------------------------------------------------------------------
# validate_qr + barrera
# ---------------------------------------------------------------------------

def test_validate_qr_formato_invalido(db, env):
    result = AccessService.validate_qr(db, QRValidation(qr_data="INVALIDO", gate_id="Centro_ENTRADA"))
    assert result["status"] == "error"
    assert "Formato de QR inválido" in result["message"]


def test_validate_qr_reserva_no_encontrada(db, env):
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:999|patente:AA123BB",
                                                        gate_id="Centro_ENTRADA"))
    assert result["status"] == "error"
    assert "Reserva no encontrada" in result["message"]


def test_validate_qr_patente_no_coincide(db, env):
    _reserva(db, patente="AA123BB")
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:CC789DD",
                                                        gate_id="Centro_ENTRADA"))
    assert result["status"] == "error"
    assert "no coincide" in result["message"]


def test_validate_qr_sucursal_distinta_deniega(db, env):
    r = _reserva(db, patente="AA123BB")
    r.sucursal_nombre = "Otra"
    db.commit()
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:AA123BB",
                                                        gate_id="Centro_ENTRADA"))
    assert result["status"] == "denied"
    assert "únicamente para la sede Otra" in result["message"]


def test_validate_qr_ingreso_ok_y_dispara_barrera(db, env):
    r = _reserva(db, patente="AA123BB", estado=ReservationStatus.PENDIENTE, pago=PaymentStatus.PAGADO)
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:AA123BB",
                                                        gate_id="Centro_ENTRADA"))
    assert result["status"] == "allowed"
    assert env["calls"][0]["gate"] == "ENTRADA"
    assert env["calls"][0]["method"] == "QR"
    db.refresh(r)
    assert r.estado_reserva == ReservationStatus.ACTIVA.value
    aforo = db.query(models.ParkingAforo).filter_by(sucursal="Centro").first()
    assert aforo.ocupacion_reservas == 1


def test_validate_qr_ya_dentro_deniega(db, env):
    _reserva(db, patente="AA123BB")
    _log_entrada(db, "AA123BB")
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:AA123BB",
                                                        gate_id="Centro_ENTRADA"))
    assert result["status"] == "denied"
    assert "ya se encuentra dentro" in result["message"]


def test_validate_qr_reserva_expirada_deniega(db, env):
    _reserva(db, patente="AA123BB", estado=ReservationStatus.COMPLETADA)
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:AA123BB",
                                                        gate_id="Centro_ENTRADA"))
    assert result["status"] == "denied"
    assert "expiró o fue cancelada" in result["message"]


def test_validate_qr_fuera_de_horario_deniega(db, env):
    _reserva(db, patente="AA123BB", inicio=_hace(300), fin=_hace(200))
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:AA123BB",
                                                        gate_id="Centro_ENTRADA"))
    assert result["status"] == "denied"
    assert "no está vigente" in result["message"]


def test_validate_qr_salida_ok_y_dispara_barrera(db, env):
    r = _reserva(db, patente="AA123BB", estado=ReservationStatus.ACTIVA, pago=PaymentStatus.PAGADO)
    _log_entrada(db, "AA123BB", pago=True, reserva_id=r.id)
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:AA123BB",
                                                        gate_id="Centro_SALIDA"))
    assert result["status"] == "allowed"
    assert env["calls"][0]["gate"] == "SALIDA"
    assert env["calls"][0]["method"] == "QR"


def test_validate_qr_salida_sin_ingreso_error(db, env):
    _reserva(db, patente="AA123BB")
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:AA123BB",
                                                        gate_id="Centro_SALIDA"))
    assert result["status"] == "error"
    assert "ingreso activo" in result["message"]


def test_validate_qr_salida_deuda_mayor_10min_deniega(db, env):
    r = _reserva(db, patente="AA123BB", estado=ReservationStatus.ACTIVA, pago=PaymentStatus.PENDIENTE)
    _log_entrada(db, "AA123BB", fecha_str=_hace(30), pago=False, reserva_id=r.id)
    result = AccessService.validate_qr(db, QRValidation(qr_data="AUTOPASS|id:1|patente:AA123BB",
                                                        gate_id="Centro_SALIDA"))
    assert result["status"] == "denied"
    assert "Deuda pendiente" in result["message"]


# ---------------------------------------------------------------------------
# flujos manuales
# ---------------------------------------------------------------------------

def test_manual_entry_nuevo_registra_y_dispara_barrera(db, env):
    result = AccessService.manual_entry(db, "AA123BB", "Centro")
    assert result["status"] == "ok"
    assert env["calls"][0]["method"] == "MANUAL_ENTRY"
    aforo = db.query(models.ParkingAforo).filter_by(sucursal="Centro").first()
    assert aforo.ocupacion_actual == 1


def test_manual_entry_ya_ingresado_reutiliza(db, env):
    _log_entrada(db, "AA123BB")
    result = AccessService.manual_entry(db, "AA123BB", "Centro")
    assert result["status"] == "ok"
    assert "se reutilizó" in result["message"]
    assert env["calls"] == []


def test_manual_entry_piso_inexistente_404(db, env):
    with pytest.raises(Exception) as exc:
        AccessService.manual_entry(db, "AA123BB", "Centro", floor_id=999)
    assert exc.value.status_code == 404


def test_manual_exit_cortesia_ok(db, env):
    _log_entrada(db, "AA123BB", pago=False)
    result = AccessService.manual_exit(db, "AA123BB", "Centro")
    assert result["status"] == "ok"
    assert "(Cortesía)" in result["message"]
    assert env["calls"][0]["method"] == "MANUAL_EXIT"


def test_manual_exit_sin_registro_400(db, env):
    with pytest.raises(Exception) as exc:
        AccessService.manual_exit(db, "ZZ999ZZ", "Centro")
    assert exc.value.status_code == 400


def test_manual_exit_deuda_mayor_10min_403(db, env):
    _log_entrada(db, "AA123BB", fecha_str=_hace(30), pago=False)
    with pytest.raises(Exception) as exc:
        AccessService.manual_exit(db, "AA123BB", "Centro")
    assert exc.value.status_code == 403
    assert "DEUDA" in str(exc.value.detail)


# ---------------------------------------------------------------------------
# cancel_stay
# ---------------------------------------------------------------------------

def test_cancel_stay_sin_ingreso_400(db, env):
    with pytest.raises(Exception) as exc:
        AccessService.cancel_stay(db, "ZZ999ZZ", "Centro")
    assert exc.value.status_code == 400


def test_cancel_stay_cortesia_sin_cargo(db, env):
    _log_entrada(db, "AA123BB", pago=False)
    result = AccessService.cancel_stay(db, "AA123BB", "Centro")
    assert result["status"] == "ok"
    assert "Sin cargo" in result["message"]
    log = db.query(models.AccessLog).filter_by(tipo_evento=AccessEventType.SALIDA.value).first()
    assert log is not None and log.costo_estadia == 0.0


def test_cancel_stay_mayor_10min_impago_402(db, env, monkeypatch):
    from services import billing_service
    _log_entrada(db, "AA123BB", fecha_str=_hace(30), pago=False)
    monkeypatch.setattr(billing_service.BillingService, "calculate_debt", staticmethod(lambda *a, **k: 500))
    with pytest.raises(Exception) as exc:
        AccessService.cancel_stay(db, "AA123BB", "Centro")
    assert exc.value.status_code == 402
    assert "abonar $500" in str(exc.value.detail)


def test_cancel_stay_mayor_10min_pagada_ok(db, env):
    _log_entrada(db, "AA123BB", fecha_str=_hace(30), pago=True)
    result = AccessService.cancel_stay(db, "AA123BB", "Centro")
    assert result["status"] == "ok"
    assert "Salida registrada" in result["message"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def test_save_image_guarda_archivo(db, tmp_path, monkeypatch):
    from core.config import settings
    monkeypatch.setattr(settings, "IMAGE_DIR", str(tmp_path))
    img_b64 = base64.b64encode(b"fake-jpeg-bytes").decode("ascii")
    name = AccessService._save_image("AA123BB", img_b64)
    assert name and name.endswith(".jpg")
    path = tmp_path / name
    assert path.exists() and path.read_bytes() == b"fake-jpeg-bytes"


def test_save_image_sin_imagen_es_none(db):
    assert AccessService._save_image("AA123BB", None) is None


def test_branch_from_gate_id_resuelve_sucursal(db):
    assert AccessService._branch_from_gate_id(db, "Centro_ENTRADA") == "Centro"


def test_branch_from_gate_id_sin_prefijo_desconocido_es_none(db):
    assert AccessService._branch_from_gate_id(db, "INVENTADA_X") is None
    assert AccessService._branch_from_gate_id(db, "sinprefijo") is None