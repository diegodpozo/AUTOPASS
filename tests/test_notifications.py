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

