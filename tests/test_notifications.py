import pytest
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


