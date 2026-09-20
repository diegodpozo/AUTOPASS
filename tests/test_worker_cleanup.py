"""Test #4 de la auditoría A3: workers de limpieza y mantenimiento.

Cubre WorkerService (44% previo):
- _process_auto_cancellations: cancela reservas impagas sin ingreso y libera el cupo
- cleanup_overdue_reservations: gracia de 2h y protección si el vehículo ya ingresó
- auto_finalize_all_reservations: completa reservas vencidas
- _cleanup_old_alpr_images: purga imágenes ALPR más antiguas que la retención
"""
import datetime
import os
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from services.worker_service import WorkerService, settings
from services.reservation_service import ReservationService
from services.time_service import TimeService
from services.email_service import EmailService
from services.user_notification_service import UserNotificationService
from models.enums import PaymentStatus, ReservationStatus
import models


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session, engine
    session.close()


def _crear_usuario(db, email, dni):
    user = models.User(email=email, nombre="Worker", apellido="Test", dni=dni, rol="user", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# Auto-cancelación de impagas sin ingreso
# ---------------------------------------------------------------------------

def test_auto_cancela_reserva_impaga_vencida(db_session, monkeypatch):
    """Reserva impaga iniciada hace >30 min y sin ingreso → CANCELADA + FALLIDO."""
    db, _ = db_session
    user = _crear_usuario(db, "auto_cancel@test.com", "11111111")
    now = TimeService.now()
    res = models.Reservation(
        user_id=user.id, patente="AC123BD",
        fecha_inicio=_fmt(now - datetime.timedelta(minutes=40)),
        fecha_fin=_fmt(now + datetime.timedelta(hours=1)),
        monto_total=2500.0, estado_pago=PaymentStatus.PENDIENTE,
        estado_reserva=ReservationStatus.PENDIENTE, tipo_estadia="dia",
        sucursal_nombre="AUTOPASS Central"
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    monkeypatch.setattr(EmailService, "send_auto_cancelled_notification", lambda *a, **k: None)
    WorkerService._process_auto_cancellations(db)

    db.refresh(res)
    assert res.estado_reserva == ReservationStatus.CANCELADA
    assert res.estado_pago == PaymentStatus.FALLIDO

    notifs = UserNotificationService.get_user_notifications(db, user.id)
    assert any(n.tipo == models.NotificationType.AUTO_CANCELLED for n in notifs)


def test_auto_cancel_no_cancela_si_ya_ingreso(db_session, monkeypatch):
    """Si el vehículo ya ingresó con su reserva, no se cancela."""
    db, _ = db_session
    user = _crear_usuario(db, "auto_ingreso@test.com", "22222222")
    now = TimeService.now()
    res = models.Reservation(
        user_id=user.id, patente="CD456EF",
        fecha_inicio=_fmt(now - datetime.timedelta(minutes=45)),
        fecha_fin=_fmt(now + datetime.timedelta(hours=1)),
        monto_total=1000.0, estado_pago=PaymentStatus.PENDIENTE,
        estado_reserva=ReservationStatus.PENDIENTE, tipo_estadia="dia",
        sucursal_nombre="AUTOPASS Central"
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    db.add(models.AccessLog(
        patente_detectada="CD456EF", tipo_evento="ENTRADA",
        tipo_vehiculo="Auto", fecha_hora=TimeService.now().isoformat(),
        pago_confirmado=False, reserva_id=res.id
    ))
    db.commit()

    spy = []
    monkeypatch.setattr(EmailService, "send_auto_cancelled_notification", lambda *a, **k: spy.append(a))

    WorkerService._process_auto_cancellations(db)

    db.refresh(res)
    assert res.estado_reserva == ReservationStatus.PENDIENTE
    assert spy == []


# ---------------------------------------------------------------------------
# Cleanup de reservas vencidas con gracia de 2 horas
# ---------------------------------------------------------------------------

def test_cleanup_overdue_gracias_2h_cancela(db_session):
    """Reserva por hora impaga con inicio hace >2h → cancelada."""
    db, _ = db_session
    user = _crear_usuario(db, "cleanup_over@test.com", "33333333")
    now = TimeService.now()
    res = models.Reservation(
        user_id=user.id, patente="EF789GH",
        fecha_inicio=_fmt(now - datetime.timedelta(hours=3)),
        fecha_fin=_fmt(now + datetime.timedelta(hours=1)),
        monto_total=3000.0, estado_pago=PaymentStatus.PENDIENTE,
        estado_reserva=ReservationStatus.PENDIENTE, tipo_estadia="hora",
        sucursal_nombre="AUTOPASS Morón"
    )
    db.add(res)
    db.commit()

    ReservationService.cleanup_overdue_reservations(db)

    db.refresh(res)
    assert res.estado_reserva == ReservationStatus.CANCELADA
    assert res.estado_pago == PaymentStatus.FALLIDO


def test_cleanup_overdue_no_cancela_con_ingreso(db_session):
    """Cleanup respeta la reserva cuyo vehículo ya ingresó al predio."""
    db, _ = db_session
    user = _crear_usuario(db, "cleanup_ing@test.com", "44444444")
    now = TimeService.now()
    res = models.Reservation(
        user_id=user.id, patente="JK910KL",
        fecha_inicio=_fmt(now - datetime.timedelta(hours=4)),
        fecha_fin=_fmt(now + datetime.timedelta(hours=1)),
        monto_total=3000.0, estado_pago=PaymentStatus.PENDIENTE,
        estado_reserva=ReservationStatus.PENDIENTE, tipo_estadia="hora",
        sucursal_nombre="AUTOPASS Morón"
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    db.add(models.AccessLog(
        patente_detectada="JK910KL", tipo_evento="ENTRADA",
        tipo_vehiculo="Auto", fecha_hora=TimeService.now().isoformat(),
        pago_confirmado=False, reserva_id=res.id
    ))
    db.commit()

    ReservationService.cleanup_overdue_reservations(db)

    db.refresh(res)
    assert res.estado_reserva == ReservationStatus.PENDIENTE


# ---------------------------------------------------------------------------
# Finalización automática de reservas vencidas
# ---------------------------------------------------------------------------

def test_auto_finalize_completa_reservas_vencidas(db_session):
    """Reservas con fecha_fin pasada pasan a Completada."""
    db, _ = db_session
    user = _crear_usuario(db, "finalize@test.com", "55555555")
    now = TimeService.now()
    vencida = models.Reservation(
        user_id=user.id, patente="MN123OP",
        fecha_inicio=_fmt(now - datetime.timedelta(hours=5)),
        fecha_fin=_fmt(now - datetime.timedelta(minutes=30)),
        monto_total=2000.0, estado_pago=PaymentStatus.PAGADO,
        estado_reserva=ReservationStatus.ACTIVA, tipo_estadia="dia",
        sucursal_nombre="AUTOPASS Central"
    )
    vigente = models.Reservation(
        user_id=user.id, patente="QR456ST",
        fecha_inicio=_fmt(now - datetime.timedelta(minutes=10)),
        fecha_fin=_fmt(now + datetime.timedelta(hours=1)),
        monto_total=2000.0, estado_pago=PaymentStatus.PAGADO,
        estado_reserva=ReservationStatus.ACTIVA, tipo_estadia="dia",
        sucursal_nombre="AUTOPASS Central"
    )
    db.add_all([vencida, vigente])
    db.commit()

    finalizadas = ReservationService.auto_finalize_all_reservations(db)

    db.refresh(vencida)
    db.refresh(vigente)
    assert finalizadas >= 1
    assert vencida.estado_reserva == ReservationStatus.COMPLETADA
    assert vigente.estado_reserva == ReservationStatus.ACTIVA


# ---------------------------------------------------------------------------
# Purga de imágenes ALPR antiguas
# ---------------------------------------------------------------------------

def test_cleanup_purga_imagenes_antiguas(db_session, tmp_path, monkeypatch):
    """Elimina imágenes más viejas que ALPR_IMAGE_RETENTION_DAYS y conserva las nuevas."""
    monkeypatch.setattr(settings, "IMAGE_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "ALPR_IMAGE_RETENTION_DAYS", 30)

    vieja = tmp_path / "vieja.jpg"
    nueva = tmp_path / "nueva.jpg"
    vieja.write_bytes(b"\x00" * 16)
    nueva.write_bytes(b"\x00" * 16)

    viejo_epoch = time.time() - (40 * 86400)
    os.utime(vieja, (viejo_epoch, viejo_epoch))

    WorkerService._cleanup_old_alpr_images()

    assert not vieja.exists()
    assert nueva.exists()


def test_cleanup_no_borra_si_directorio_inexistente(db_session, tmp_path, monkeypatch):
    """Con IMAGE_DIR inexistente, no se rompe y no borra nada."""
    inexistente = tmp_path / "no_existe"
    monkeypatch.setattr(settings, "IMAGE_DIR", str(inexistente))

    WorkerService._cleanup_old_alpr_images()
    assert not inexistente.exists()