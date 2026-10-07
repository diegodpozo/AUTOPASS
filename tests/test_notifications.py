import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from core.database import Base
from services.user_notification_service import UserNotificationService
from services.worker_service import WorkerService
from services.reservation_service import ReservationService
from services.support_service import SupportService
import models

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_user_notification_crud(db_session: Session):
    # 1. Crear usuario de prueba
    user = models.User(
        email="notif_test@example.com",
        password_hash="hash",
        nombre="Test",
        apellido="Notif",
        dni="11223344",
        rol="user"
    )
    db_session.add(user)
    db_session.commit()

    # 2. Crear notificacion
    notif = UserNotificationService.create_notification(
        db_session, user.id, "BALANCE_RECHARGED", "Carga OK", "Se cargaron $1000"
    )
    assert notif.id is not None
    assert notif.leido is False

    # 3. Contar unread
    unread = UserNotificationService.get_unread_count(db_session, user.id)
    assert unread == 1

    # 4. Marcar leida
    res_read = UserNotificationService.mark_as_read(db_session, notif.id, user.id)
    assert res_read is True

    unread_after = UserNotificationService.get_unread_count(db_session, user.id)
    assert unread_after == 0

    # 5. Borrar leidas
    deleted_count = UserNotificationService.clear_read_notifications(db_session, user.id)
    assert deleted_count == 1

    total = UserNotificationService.get_total_count(db_session, user.id)
    assert total == 0

def test_support_ticket_response_notification(db_session: Session):
    user = models.User(
        email="support_notif@example.com",
        password_hash="hash",
        nombre="Ana",
        apellido="Gomez",
        dni="55667788",
        rol="user"
    )
    db_session.add(user)
    db_session.commit()

    # Crear ticket de soporte
    ticket = models.SupportTicket(
        user_id=user.id,
        categoria="Pagos",
        asunto="Problema con mi saldo",
        mensaje="No se acredito",
        estado="Pendiente"
    )
    db_session.add(ticket)
    db_session.commit()

    # Responder ticket
    admin_user = models.User(email="admin_test@autopass.com", rol="admin")
    db_session.add(admin_user)
    db_session.commit()

    SupportService.update_ticket_status(
        db_session, admin_user, ticket.id, "Resuelto", "Se ha acreditado tu saldo correctamente."
    )

    # Verificar que el usuario recibio la notificacion
    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    assert len(notifs) == 1
    assert notifs[0].tipo == "SUPPORT_RESPONSE"
    assert "Resuelto" in notifs[0].mensaje or "acreditado" in notifs[0].mensaje

def test_delete_read_notifications_route(db_session: Session):
    from routes.user.notifications import clear_read_notifications, delete_notification
    user = models.User(
        email="route_notif@example.com",
        password_hash="hash",
        nombre="Route",
        apellido="Test",
        dni="99887766",
        rol="user"
    )
    db_session.add(user)
    db_session.commit()

    n1 = UserNotificationService.create_notification(db_session, user.id, "TEST", "T1", "M1")
    n2 = UserNotificationService.create_notification(db_session, user.id, "TEST", "T2", "M2")
    
    UserNotificationService.mark_as_read(db_session, n1.id, user.id)

    # Test clear_read_notifications endpoint
    clear_read_notifications(db=db_session, current_user=user)

    remaining = UserNotificationService.get_user_notifications(db_session, user.id)
    assert len(remaining) == 1
    assert remaining[0].id == n2.id

    # Test delete_notification endpoint for individual item
    delete_notification(notif_id=n2.id, db=db_session, current_user=user)
    assert UserNotificationService.get_total_count(db_session, user.id) == 0


def test_worker_reminders_no_duplicate_on_delete(db_session: Session):
    from services.time_service import TimeService
    import datetime

    user = models.User(
        email="worker_rem@example.com",
        password_hash="hash",
        nombre="Worker",
        apellido="Rem",
        dni="12312312",
        rol="user"
    )
    db_session.add(user)
    db_session.commit()

    now = TimeService.now()
    inicio = (now + datetime.timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M")
    fin = (now + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

    res = models.Reservation(
        user_id=user.id,
        patente="AA123AA",
        fecha_inicio=inicio,
        fecha_fin=fin,
        monto_total=1000.0,
        estado_pago="Pendiente",
        estado_reserva="Pendiente",
        sucursal_nombre="AUTOPASS Morón",
        recordatorio_confirmado=False
    )
    db_session.add(res)
    db_session.commit()

    # 1. Correr _process_reminders la primera vez
    WorkerService._process_reminders(db_session)
    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    assert len(notifs) == 1
    notif_id = notifs[0].id

    # 2. El usuario elimina la notificacion recibida
    UserNotificationService.delete_notification(db_session, notif_id, user.id)
    assert UserNotificationService.get_total_count(db_session, user.id) == 0

    # 3. Correr _process_reminders nuevamente (proximo loop del worker)
    WorkerService._process_reminders(db_session)
    # Debe seguir en 0 porque recordatorio_confirmado quedo en True en la BD
    assert UserNotificationService.get_total_count(db_session, user.id) == 0


def test_worker_started_reservations_no_duplicate_on_delete(db_session: Session):
    from services.time_service import TimeService
    import datetime

    user = models.User(
        email="worker_start@example.com",
        password_hash="hash",
        nombre="Worker",
        apellido="Start",
        dni="32132132",
        rol="user"
    )
    db_session.add(user)
    db_session.commit()

    now = TimeService.now()
    inicio = (now - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
    fin = (now + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

    res = models.Reservation(
        user_id=user.id,
        patente="BB456BB",
        fecha_inicio=inicio,
        fecha_fin=fin,
        monto_total=1500.0,
        estado_pago="Pagado",
        estado_reserva="Pendiente",
        sucursal_nombre="AUTOPASS Morón"
    )
    db_session.add(res)
    db_session.commit()

    # 1. Correr _process_started_reservations la primera vez
    WorkerService._process_started_reservations(db_session)
    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    assert len(notifs) == 1
    notif_id = notifs[0].id
    assert res.estado_reserva == "Activa"

    # 2. El usuario borra la notificacion
    UserNotificationService.delete_notification(db_session, notif_id, user.id)
    assert UserNotificationService.get_total_count(db_session, user.id) == 0

    # 3. Correr _process_started_reservations en el siguiente loop (30s despues)
    WorkerService._process_started_reservations(db_session)
    # Debe seguir en 0 porque la reserva ya paso a "Activa"
    assert UserNotificationService.get_total_count(db_session, user.id) == 0


def test_support_status_changed_without_reply(db_session: Session):
    user = models.User(email="support_status@example.com", password_hash="h", nombre="Pedro", apellido="Perez", dni="99887766", rol="user")
    admin = models.User(email="admin_status@autopass.com", rol="admin")
    db_session.add_all([user, admin])
    db_session.commit()

    ticket = models.SupportTicket(user_id=user.id, categoria="Consulta", asunto="Horarios", mensaje="¿Abren domingo?", estado="Pendiente")
    db_session.add(ticket)
    db_session.commit()

    # Admin actualiza estado sin respuesta de texto
    SupportService.update_ticket_status(db_session, admin, ticket.id, "En Proceso", respuesta=None)

    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    assert len(notifs) == 1
    assert notifs[0].tipo == models.NotificationType.SUPPORT_STATUS_CHANGED
    assert "En Proceso" in notifs[0].mensaje


def test_manual_reservation_payment_emits_points_notification(db_session: Session):
    user = models.User(email="points_user@example.com", password_hash="h", nombre="Carlos", apellido="Lopez", dni="44332211", rol="user", saldo=0.0, puntos_acumulados=0)
    db_session.add(user)
    db_session.commit()

    res = models.Reservation(
        user_id=user.id, patente="AA123BB", fecha_inicio="2026-09-20 10:00", fecha_fin="2026-09-20 12:00",
        monto_total=5000.0, estado_pago="Pendiente", estado_reserva="Pendiente", sucursal_nombre="Central"
    )
    db_session.add(res)
    db_session.commit()

    ReservationService.pay_reservation_manual(db_session, res, "Caja")

    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    assert any(n.tipo == models.NotificationType.POINTS_EARNED for n in notifs)


def test_onsite_stay_payment_emits_notifications(db_session: Session):
    from services.billing_service import BillingService
    import datetime

    user = models.User(email="stay_user@example.com", password_hash="h", nombre="Juan", apellido="Gomez", dni="11112222", rol="user", puntos_acumulados=0)
    db_session.add(user)
    db_session.commit()

    vehicle = models.Vehicle(user_id=user.id, patente="AC123BD", tipo="Auto")
    db_session.add(vehicle)
    db_session.commit()

    now_str = (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
    log = models.AccessLog(patente_detectada="AC123BD", tipo_evento="ENTRADA", sucursal="AUTOPASS Morén", tipo_vehiculo="Auto", fecha_hora=now_str, pago_confirmado=False)
    db_session.add(log)
    db_session.add(models.Settings(clave="precio_hora", valor=1500.0, sucursal="AUTOPASS Morén"))
    db_session.add(models.Settings(clave="precio_30min", valor=750.0, sucursal="AUTOPASS Morén"))
    db_session.commit()

    BillingService.process_payment(db_session, "AC123BD", metodo="CAJA")

    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    assert any(n.tipo == models.NotificationType.STAY_PAID for n in notifs)
    assert any(n.tipo == models.NotificationType.POINTS_EARNED for n in notifs)


def test_user_change_password_notification(db_session: Session):
    from routes.user.profile import change_password
    from core.security import get_password_hash
    import schemas

    user = models.User(email="pass_user@example.com", password_hash=get_password_hash("OldPassword123!"), nombre="Lucas", apellido="Díaz", dni="77665544", rol="user")
    db_session.add(user)
    db_session.commit()

    data = schemas.ChangePassword(current_password="OldPassword123!", new_password="NewPassword123!")
    res = change_password(data=data, db=db_session, current_user=user)
    assert res["status"] == "ok"

    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    assert len(notifs) == 1
    assert notifs[0].tipo == models.NotificationType.SECURITY_PASSWORD_CHANGED


def test_user_modify_reservation_notification(db_session: Session):
    from routes.user.reservations import modify_reservation
    import schemas
    import datetime

    user = models.User(email="mod_res_user@example.com", password_hash="h", nombre="Valeria", apellido="Sosa", dni="33221100", rol="user", saldo=5000.0)
    db_session.add(user)
    db_session.commit()

    branch = models.ParkingBranch(nombre="AUTOPASS Centro", direccion="Av. Centro 123", horario="24hs", is_24h=True)
    aforo = models.ParkingAforo(sucursal="AUTOPASS Centro", capacidad_reservas_autos=20, ocupacion_reservas_autos=0)
    db_session.add_all([branch, aforo])
    db_session.add(models.Settings(clave="precio_hora", valor=1500.0, sucursal="AUTOPASS Centro"))
    db_session.add(models.Settings(clave="precio_30min", valor=750.0, sucursal="AUTOPASS Centro"))
    db_session.commit()

    vehicle = models.Vehicle(user_id=user.id, patente="AB345CD", tipo="Auto")
    db_session.add(vehicle)
    db_session.commit()

    now = datetime.datetime.now()
    ini = (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
    fin = (now + datetime.timedelta(days=2, hours=2)).strftime("%Y-%m-%d %H:%M")
    new_fin = (now + datetime.timedelta(days=2, hours=3)).strftime("%Y-%m-%d %H:%M")

    res = models.Reservation(
        user_id=user.id, patente="AB345CD", fecha_inicio=ini, fecha_fin=fin,
        monto_total=2000.0, estado_pago="Pendiente", estado_reserva="Pendiente", sucursal_nombre="AUTOPASS Centro", tipo_estadia="hora"
    )
    db_session.add(res)
    db_session.commit()

    data = schemas.ReservationUpdate(fecha_fin=new_fin)
    resp = modify_reservation(res_id=res.id, data=data, db=db_session, current_user=user)
    assert resp["status"] == "ok"

    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    assert any(n.tipo == models.NotificationType.RESERVATION_MODIFIED for n in notifs)


def test_points_redemption_notification_format(db_session: Session):
    from routes.user.fidelization import redeem_points
    import re

    user = models.User(
        email="redeem_notif@example.com",
        password_hash="h",
        nombre="Mario",
        apellido="Bros",
        dni="88990011",
        rol="user",
        puntos_acumulados=500
    )
    db_session.add(user)
    db_session.commit()

    promo = models.Promotion(
        titulo="Lavado Completo",
        descripcion="Lavado artesanal de carrocería",
        costo_puntos=200,
        tipo_canje="voucher",
        activa=True
    )
    db_session.add(promo)
    db_session.commit()

    res = redeem_points(promo_id=promo.id, db=db_session, current_user=user)
    assert res["status"] == "ok"
    ticket_id = res["ticket"].id

    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    promo_notifs = [n for n in notifs if n.tipo == models.NotificationType.PROMO_REDEEMED]
    assert len(promo_notifs) == 1
    assert f"(Voucher #{ticket_id})" in promo_notifs[0].mensaje
    
    match = re.search(r'Voucher\s*#?(\d+)', promo_notifs[0].mensaje, re.IGNORECASE)
    assert match is not None
    assert int(match.group(1)) == ticket_id

    # Verificar cálculo de fecha_vencimiento (+30 días)
    ticket_schema = res["ticket"]
    assert ticket_schema.fecha_vencimiento is not None
    dt_created = datetime.datetime.fromisoformat(ticket_schema.created_at)
    dt_venc = datetime.datetime.fromisoformat(ticket_schema.fecha_vencimiento)
    assert (dt_venc - dt_created).days == 30


def test_vehicle_registration_and_removal_notifications(db_session: Session):
    from routes.user.vehicles import add_user_vehicle, delete_user_vehicle

    user = models.User(
        email="veh_notif@example.com",
        password_hash="h",
        nombre="Carlos",
        apellido="Sainz",
        dni="12345678",
        rol="user"
    )
    db_session.add(user)
    db_session.commit()

    # 1. Agregar vehiculo
    resp_add = add_user_vehicle(
        patente="AA 123 CD",
        marca_modelo="Ferrari F1",
        tipo="Auto",
        db=db_session,
        current_user=user
    )
    assert resp_add["status"] == "ok"

    notifs = UserNotificationService.get_user_notifications(db_session, user.id)
    reg_notifs = [n for n in notifs if n.tipo == models.NotificationType.VEHICLE_REGISTERED]
    assert len(reg_notifs) == 1
    assert "AA 123 CD" in reg_notifs[0].mensaje or "Ferrari F1" in reg_notifs[0].mensaje

    # 2. Eliminar vehiculo
    resp_del = delete_user_vehicle(
        patente="AA 123 CD",
        db=db_session,
        current_user=user
    )
    assert resp_del["status"] == "ok"

    notifs_after = UserNotificationService.get_user_notifications(db_session, user.id)
    del_notifs = [n for n in notifs_after if n.tipo == models.NotificationType.VEHICLE_REMOVED]
    assert len(del_notifs) == 1
    assert "AA 123 CD" in del_notifs[0].mensaje


