"""Auditoría A3 (cobertura): tests para services/payments.py (ReservationPaymentsMixin).

Cubre pagos de reservas: abono manual/saldo/Mercado Pago, descuentos por canje,
validación de tickets, simulación y ejecución de reembolsos, y cancelaciones.
"""
import datetime
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from services.email_service import EmailService
from services.payments import ReservationPaymentsMixin
from services.user_notification_service import UserNotificationService


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    S = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield S
    engine.dispose()


def _usuario(db, email="pagos@test.com", saldo=0.0, puntos=0):
    u = models.User(
        nombre="José", apellido="Pérez", dni=str(uuid.uuid4().int)[:8], telefono="1122334455",
        email=email, password_hash="x", rol="user",
        saldo=saldo, puntos_acumulados=puntos,
        is_blocked=False, is_deleted=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _reserva(db, user=None, monto=1000.0, estado_pago="Pendiente", estado_reserva="Pendiente",
             patente="ABC123", tipo="hora", sucursal=None, inicio=None, fin=None, info=None):
    r = models.Reservation(
        user_id=user.id if user else None,
        patente=patente,
        fecha_inicio=inicio or "2000-01-01T00:00:00",
        fecha_fin=fin or "2030-01-01T00:00:00",
        monto_total=monto,
        monto_reembolsado=0.0,
        estado_pago=estado_pago,
        estado_reserva=estado_reserva,
        sucursal_nombre=sucursal,
        sucursal_info=info,
        tipo_estadia=tipo,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _ticket(db, user, porc=10, estado="VIGENTE", sucursal=None):
    t = models.RedemptionTicket(
        user_id=user.id,
        codigo=f"TKT-{uuid.uuid4().hex[:8]}",
        titulo="10% OFF estacionamiento",
        descripcion="Descuento de prueba",
        tipo_canje="descuento_reserva",
        valor_descuento=porc,
        estado=estado,
        sucursal=sucursal,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _entrada(db, patente, sucursal, norm=None):
    log = models.AccessLog(
        patente_detectada=patente,
        normalized_patente=norm or patente,
        tipo_evento="ENTRADA",
        tipo_vehiculo="Auto",
        fecha_hora=datetime.datetime.now().isoformat(),
        pago_confirmado=False,
        sucursal=sucursal,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _salida(db, patente, sucursal):
    log = models.AccessLog(
        patente_detectada=patente,
        tipo_evento="SALIDA",
        tipo_vehiculo="Auto",
        fecha_hora=datetime.datetime.now().isoformat(),
        pago_confirmado=False,
        sucursal=sucursal,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# --- DESCUENTOS DISPONIBLES Y CLÁUSULA DE SUCURSAL ---

def test_lista_descuentos_sin_usuario_es_vacia(session_factory):
    db = session_factory()
    assert ReservationPaymentsMixin.get_available_redemption_discounts(db, None) == []


def test_lista_descuentos_devuelve_tickets_vigentes(session_factory):
    db = session_factory()
    user = _usuario(db)
    _ticket(db, user, porc=15)
    tickets = ReservationPaymentsMixin.get_available_redemption_discounts(db, user.id, "AUTOPASS Central")
    assert len(tickets) == 1
    assert tickets[0].valor_descuento == 15


def test_clausula_sucursal_delegada_al_repo(session_factory):
    db = session_factory()
    clause = ReservationPaymentsMixin.redemption_sucursal_clause("AUTOPASS Central")
    assert clause is not None


# --- VALIDACION DE TICKET DE DESCUENTO ---

def test_validate_sin_id_devuelve_none(session_factory):
    db = session_factory()
    user = _usuario(db)
    assert ReservationPaymentsMixin.validate_redemption_ticket(db, user.id, None, None) is None


def test_validate_ticket_invalido_lanza_400(session_factory):
    db = session_factory()
    user = _usuario(db)
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.validate_redemption_ticket(db, user.id, 9999, None)
    assert exc.value.status_code == 400


# --- ABONO MANUAL (ADMIN) ---

def test_manual_reserva_ya_pagada(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_pago="Pagado")
    result = ReservationPaymentsMixin.pay_reservation_manual(db, res, metodo_pago="EFECTIVO")
    assert result["status"] == "ok"
    assert "ya se encuentra pagada" in result["message"]
    assert result["monto"] == res.monto_total


def test_manual_sin_usuario_con_descuento_lanza_400(session_factory):
    db = session_factory()
    res = _reserva(db, user=None)
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.pay_reservation_manual(db, res, redemption_ticket_id=1)
    assert exc.value.status_code == 400


def test_manual_aplica_descuento_y_acredita_puntos(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, monto=1000.0)
    ticket = _ticket(db, user, porc=10)

    result = ReservationPaymentsMixin.pay_reservation_manual(db, res, metodo_pago="EFECTIVO", redemption_ticket_id=ticket.id)

    assert result["descuento"] == 100.0
    assert result["monto_a_cobrar"] == 900.0
    assert result["metodo_pago"] == "EFECTIVO"
    db.refresh(res)
    db.refresh(user)
    assert res.estado_pago == "Pagado"
    assert res.monto_total == 900.0
    assert res.metodo_pago == "EFECTIVO"
    assert ticket.estado == "USADO"
    assert ticket.reserva_id == res.id
    assert user.puntos_acumulados == 9
    logs = db.query(models.PointsLog).filter(models.PointsLog.user_id == user.id).all()
    assert len(logs) == 1
    assert logs[0].cantidad == 9


def test_manual_notificacion_falla_no_bloquea(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, monto=1000.0)

    def boom(*a, **k):
        raise RuntimeError("mail down")

    monkeypatch.setattr(UserNotificationService, "create_notification", boom)
    result = ReservationPaymentsMixin.pay_reservation_manual(db, res, metodo_pago="TRANSFERENCIA")
    assert result["status"] == "ok"
    db.refresh(user)
    assert user.puntos_acumulados == 10


def test_manual_sin_descuento_acredita_puntos(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, monto=1000.0)
    result = ReservationPaymentsMixin.pay_reservation_manual(db, res, metodo_pago="EFECTIVO")
    assert result["descuento"] == 0.0
    db.refresh(user)
    assert user.puntos_acumulados == 10


# --- PAGO CON SALDO (USUARIO) ---

def test_pay_reserva_no_pertenece_al_usuario_404(session_factory):
    db = session_factory()
    user = _usuario(db)
    other = _usuario(db, email="otro@test.com")
    res = _reserva(db, user=other)
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.pay_reservation(db, user, res.id)
    assert exc.value.status_code == 404


def test_pay_reserva_cancelada_400(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_reserva="Cancelada")
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.pay_reservation(db, user, res.id)
    assert exc.value.status_code == 400


def test_pay_reserva_completada_400(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_reserva="Completada")
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.pay_reservation(db, user, res.id)
    assert exc.value.status_code == 400


def test_pay_reserva_ya_abonada(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_pago="Pagado")
    result = ReservationPaymentsMixin.pay_reservation(db, user, res.id)
    assert result["message"] == "La reserva ya ha sido abonada"


def test_pay_reserva_saldo_insuficiente_400(session_factory):
    db = session_factory()
    user = _usuario(db, saldo=0)
    res = _reserva(db, user=user, monto=1000.0)
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.pay_reservation(db, user, res.id)
    assert exc.value.status_code == 400
    assert "Saldo insuficiente" in exc.value.detail


def test_pay_reserva_success_con_descuento(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db, saldo=2000.0)
    res = _reserva(db, user=user, monto=1000.0, sucursal="AUTOPASS Central")
    ticket = _ticket(db, user, porc=10)

    sent = []
    monkeypatch.setattr(EmailService, "send_reservation_confirmation",
                        lambda to, name, data: sent.append((to, name, data)))

    result = ReservationPaymentsMixin.pay_reservation(db, user, res.id, redemption_ticket_id=ticket.id)

    assert result["status"] == "ok"
    assert result["puntos_ganados"] == 9
    db.refresh(user)
    db.refresh(res)
    assert user.saldo == 1100.0
    assert res.estado_pago == "Pagado"
    assert res.estado_reserva == "Activa"
    assert res.metodo_pago == "SALDO"
    assert res.monto_total == 900.0
    assert ticket.estado == "USADO"
    assert len(sent) == 1
    assert sent[0][0] == user.email
    assert sent[0][2]["costo"] == 900.0
    assert sent[0][2]["direccion"] == "Dirección no disponible"


def test_pay_reserva_no_horaria_iniciada_reserva_plaza(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db, saldo=5000.0)
    res = _reserva(db, user=user, monto=1000.0, tipo="dia", sucursal="AUTOPASS Central")
    monkeypatch.setattr(EmailService, "send_reservation_confirmation", lambda *a, **k: None)

    result = ReservationPaymentsMixin.pay_reservation(db, user, res.id)
    assert result["status"] == "ok"
    db.refresh(res)
    assert res.estado_pago == "Pagado"


def test_pay_reserva_notificacion_falla_ok(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db, saldo=5000.0)
    res = _reserva(db, user=user, monto=1000.0)
    monkeypatch.setattr(EmailService, "send_reservation_confirmation", lambda *a, **k: None)

    def boom(*a, **k):
        raise RuntimeError("notif down")

    monkeypatch.setattr(UserNotificationService, "create_notification", boom)
    result = ReservationPaymentsMixin.pay_reservation(db, user, res.id)
    assert result["status"] == "ok"


# --- PAGO POR MERCADO PAGO ---

def test_mp_reserva_cancelada_400(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_reserva="Cancelada")
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.pay_reservation_mp(db, user, res, 900.0)
    assert exc.value.status_code == 400


def test_mp_reserva_ya_abonada_applied_false(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_pago="Pagado")
    result = ReservationPaymentsMixin.pay_reservation_mp(db, user, res, 900.0)
    assert result["status"] == "ok"
    assert result["aplicado"] is False


def test_mp_success_con_descuento(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, monto=1000.0, sucursal="AUTOPASS Central")
    ticket = _ticket(db, user, porc=10)

    sent = []
    monkeypatch.setattr(EmailService, "send_reservation_confirmation",
                        lambda to, name, data: sent.append((to, name, data)))

    result = ReservationPaymentsMixin.pay_reservation_mp(db, user, res, 900.0, redemption_ticket_id=ticket.id)

    assert result["status"] == "ok"
    assert result["aplicado"] is True
    assert result["puntos_ganados"] == 9
    db.refresh(res)
    db.refresh(user)
    assert res.estado_pago == "Pagado"
    assert res.metodo_pago == "MERCADOPAGO"
    assert res.monto_total == 900.0
    assert ticket.estado == "USADO"
    assert user.puntos_acumulados == 9
    assert len(sent) == 1
    assert sent[0][2]["costo"] == 900.0


def test_mp_no_horaria_iniciada_reserva_plaza(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, monto=1000.0, tipo="semana", sucursal="AUTOPASS Central")
    monkeypatch.setattr(EmailService, "send_reservation_confirmation", lambda *a, **k: None)

    result = ReservationPaymentsMixin.pay_reservation_mp(db, user, res, 1000.0)
    assert result["aplicado"] is True


def test_mp_notificacion_falla_ok(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, monto=1000.0)
    monkeypatch.setattr(EmailService, "send_reservation_confirmation", lambda *a, **k: None)

    def boom(*a, **k):
        raise RuntimeError("notif down")

    monkeypatch.setattr(UserNotificationService, "create_notification", boom)
    result = ReservationPaymentsMixin.pay_reservation_mp(db, user, res, 1000.0)
    assert result["status"] == "ok"


# --- SIMULACION DE REEMBOLSO ---

def test_simulate_vehiculo_en_predio(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_pago="Pagado", sucursal="AUTOPASS Central")
    _entrada(db, "ABC123", "AUTOPASS Central")
    result = ReservationPaymentsMixin.simulate_refund(db, res)
    assert result["reembolso"] == 0.0
    assert result["error"] == "Vehículo en el predio"


def test_simulate_no_pagado_reembolso_cero(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_pago="Pendiente")
    result = ReservationPaymentsMixin.simulate_refund(db, res)
    assert result["reembolso"] == 0.0
    assert result["error"] is None


def test_simulate_antes_de_inicio_reembolso_total(session_factory):
    db = session_factory()
    user = _usuario(db)
    now = datetime.datetime.now()
    res = _reserva(db, user=user, estado_pago="Pagado",
                   inicio=(now + datetime.timedelta(hours=2)).isoformat(),
                   fin=(now + datetime.timedelta(hours=3)).isoformat())
    result = ReservationPaymentsMixin.simulate_refund(db, res)
    assert result["reembolso"] == res.monto_total
    assert result["error"] is None


def test_simulate_despues_de_fin_cero(session_factory):
    db = session_factory()
    user = _usuario(db)
    now = datetime.datetime.now()
    res = _reserva(db, user=user, estado_pago="Pagado",
                   inicio=(now - datetime.timedelta(hours=3)).isoformat(),
                   fin=(now - datetime.timedelta(hours=2)).isoformat())
    result = ReservationPaymentsMixin.simulate_refund(db, res)
    assert result["reembolso"] == 0.0


def test_simulate_ventana_hora_con_ingreso_cero(session_factory):
    db = session_factory()
    user = _usuario(db)
    now = datetime.datetime.now()
    res = _reserva(db, user=user, estado_pago="Pagado", tipo="hora", sucursal="AUTOPASS Central",
                   inicio=(now - datetime.timedelta(hours=2)).isoformat(),
                   fin=(now + datetime.timedelta(hours=2)).isoformat())
    _entrada(db, "ABC123", "AUTOPASS Central")
    _salida(db, "ABC123", "AUTOPASS Central")
    result = ReservationPaymentsMixin.simulate_refund(db, res)
    assert result["reembolso"] == 0.0


def test_simulate_ventana_no_hora_proporcional(session_factory):
    db = session_factory()
    user = _usuario(db)
    now = datetime.datetime.now()
    res = _reserva(db, user=user, estado_pago="Pagado", tipo="dia", sucursal="AUTOPASS Central",
                   inicio=(now - datetime.timedelta(hours=2)).isoformat(),
                   fin=(now + datetime.timedelta(hours=2)).isoformat())
    _entrada(db, "ABC123", "AUTOPASS Central")
    _salida(db, "ABC123", "AUTOPASS Central")
    result = ReservationPaymentsMixin.simulate_refund(db, res)
    assert result["error"] is None
    assert abs(result["reembolso"] - 500.0) <= 2.0


# --- CANCELACION DE RESERVA ---

def test_cancel_reserva_inexistente_404(session_factory):
    db = session_factory()
    user = _usuario(db)
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.cancel_reservation(db, user, 9999)
    assert exc.value.status_code == 404


def test_cancel_reserva_ya_cancelada(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_reserva="Cancelada")
    result = ReservationPaymentsMixin.cancel_reservation(db, user, res.id)
    assert result["message"] == "La reserva ya se encuentra cancelada"


def test_cancel_reserva_completada_error(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_reserva="Completada")
    result = ReservationPaymentsMixin.cancel_reservation(db, user, res.id)
    assert result["status"] == "error"
    assert "no puede cancelarse" in result["message"]


def test_cancel_reserva_vehiculo_en_predio_400(session_factory):
    db = session_factory()
    user = _usuario(db)
    res = _reserva(db, user=user, estado_pago="Pagado", sucursal="AUTOPASS Central")
    _entrada(db, "ABC123", "AUTOPASS Central")
    with pytest.raises(Exception) as exc:
        ReservationPaymentsMixin.cancel_reservation(db, user, res.id)
    assert exc.value.status_code == 400
    assert exc.value.detail == "Vehículo en el predio"


def test_cancel_reserva_con_reembolso_total(session_factory):
    db = session_factory()
    user = _usuario(db, saldo=500.0, puntos=50)
    now = datetime.datetime.now()
    res = _reserva(db, user=user, estado_pago="Pagado", tipo="dia", sucursal="AUTOPASS Central",
                   inicio=(now + datetime.timedelta(hours=2)).isoformat(),
                   fin=(now + datetime.timedelta(hours=3)).isoformat())

    result = ReservationPaymentsMixin.cancel_reservation(db, user, res.id)

    assert result["status"] == "ok"
    assert result["reembolso"] == 1000.0
    assert "Reembolso: $1000" in result["message"]
    db.refresh(user)
    db.refresh(res)
    assert user.saldo == 1500.0
    assert user.puntos_acumulados == 40
    assert res.estado_reserva == "Cancelada"
    assert res.estado_pago == "Reembolsado"
    assert res.monto_reembolsado == 1000.0
    logs = db.query(models.PointsLog).filter(models.PointsLog.user_id == user.id).all()
    assert any(log.cantidad == -10 for log in logs)


def test_cancel_reserva_sin_reembolso(session_factory):
    db = session_factory()
    user = _usuario(db, saldo=500.0)
    res = _reserva(db, user=user, estado_pago="Pendiente")

    result = ReservationPaymentsMixin.cancel_reservation(db, None, res.id)

    assert result["status"] == "ok"
    assert result["reembolso"] == 0.0
    assert "sin reembolso" in result["message"]
    db.refresh(user)
    db.refresh(res)
    assert user.saldo == 500.0
    assert res.estado_reserva == "Cancelada"
    assert res.estado_pago == "Cancelado"


def test_cancel_reserva_notificacion_falla_ok(session_factory, monkeypatch):
    db = session_factory()
    user = _usuario(db, saldo=500.0)
    res = _reserva(db, user=user, estado_pago="Pendiente")

    def boom(*a, **k):
        raise RuntimeError("notif down")

    monkeypatch.setattr(UserNotificationService, "create_notification", boom)
    result = ReservationPaymentsMixin.cancel_reservation(db, user, res.id)
    assert result["status"] == "ok"