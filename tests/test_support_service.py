import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models, schemas
from core.database import Base
from services.support_service import SupportService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test user
    user = models.User(
        nombre="Test",
        apellido="User",
        email="test@user.com",
        password_hash="xxx",
        rol="user"
    )
    admin = models.User(
        nombre="Admin",
        apellido="Local",
        email="admin@branch.com",
        password_hash="xxx",
        rol="local_admin",
        sucursal="AUTOPASS Belgrano"
    )
    session.add_all([user, admin])
    session.commit()

    yield session
    session.close()

def test_create_and_get_support_ticket(db_session):
    user = db_session.query(models.User).filter_by(email="test@user.com").first()
    admin = db_session.query(models.User).filter_by(email="admin@branch.com").first()

    data = schemas.SupportTicketCreate(
        categoria="reserva",
        sucursal="AUTOPASS Belgrano",
        asunto="Problema con mi reserva",
        mensaje="No pude ingresar con la patente ABC123"
    )

    ticket = SupportService.create_ticket(db_session, user, data)
    assert ticket.id is not None
    assert ticket.estado == "Pendiente"
    assert ticket.sucursal == "AUTOPASS Belgrano"

    # Client tickets
    user_tickets = SupportService.get_user_tickets(db_session, user.id)
    assert len(user_tickets) == 1

    # Admin tickets
    admin_tickets = SupportService.get_admin_tickets(db_session, admin)
    assert len(admin_tickets) == 1
    assert admin_tickets[0]["asunto"] == "Problema con mi reserva"

    # Update ticket status
    updated = SupportService.update_ticket_status(db_session, admin, ticket.id, "Resuelto", "Barrera reseteada")
    assert updated.estado == "Resuelto"
    assert updated.respuesta == "Barrera reseteada"

def test_ticket_filtering_by_role_and_branch(db_session):
    user = db_session.query(models.User).filter_by(email="test@user.com").first()
    
    super_admin = models.User(
        nombre="Super",
        apellido="Admin",
        email="superadmin@autopass.com",
        password_hash="xxx",
        rol="admin",
        sucursal=None
    )
    branch_admin_belgrano = models.User(
        nombre="Admin",
        apellido="Belgrano",
        email="adminbelgrano@autopass.com",
        password_hash="xxx",
        rol="local_admin",
        sucursal="AUTOPASS Belgrano"
    )
    branch_admin_castelar = models.User(
        nombre="Admin",
        apellido="Castelar",
        email="admincastelar@autopass.com",
        password_hash="xxx",
        rol="local_admin",
        sucursal="AUTOPASS Castelar"
    )
    db_session.add_all([super_admin, branch_admin_belgrano, branch_admin_castelar])
    db_session.commit()

    # Create 3 tickets: 1 General, 1 Belgrano, 1 Castelar
    SupportService.create_ticket(db_session, user, schemas.SupportTicketCreate(
        categoria="otro", sucursal="General", asunto="Consulta General 1", mensaje="Hola"
    ))
    SupportService.create_ticket(db_session, user, schemas.SupportTicketCreate(
        categoria="reserva", sucursal="AUTOPASS Belgrano", asunto="Consulta Belgrano", mensaje="Hola Belgrano"
    ))
    SupportService.create_ticket(db_session, user, schemas.SupportTicketCreate(
        categoria="alpr", sucursal="AUTOPASS Castelar", asunto="Consulta Castelar", mensaje="Hola Castelar"
    ))

    # 1. Super Admin default (General consultations only)
    super_default_tickets = SupportService.get_admin_tickets(db_session, super_admin)
    assert len(super_default_tickets) == 1
    assert super_default_tickets[0]["asunto"] == "Consulta General 1"

    # 2. Super Admin explicitly filtering by branch Belgrano
    super_belgrano_tickets = SupportService.get_admin_tickets(db_session, super_admin, sucursal_filter="AUTOPASS Belgrano")
    assert len(super_belgrano_tickets) == 1
    assert super_belgrano_tickets[0]["asunto"] == "Consulta Belgrano"

    # 3. Super Admin filtering by TODAS
    super_all_tickets = SupportService.get_admin_tickets(db_session, super_admin, sucursal_filter="TODAS")
    assert len(super_all_tickets) == 3

    # 4. Branch Admin Belgrano (ONLY Belgrano tickets, even without explicit filter)
    belgrano_tickets = SupportService.get_admin_tickets(db_session, branch_admin_belgrano)
    assert len(belgrano_tickets) == 1
    assert belgrano_tickets[0]["asunto"] == "Consulta Belgrano"

    # 5. Branch Admin Castelar (ONLY Castelar tickets)
    castelar_tickets = SupportService.get_admin_tickets(db_session, branch_admin_castelar)
    assert len(castelar_tickets) == 1
    assert castelar_tickets[0]["asunto"] == "Consulta Castelar"

