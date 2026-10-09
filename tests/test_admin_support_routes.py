"""Ronda #20 - routes/admin/support.py (57% -> ~100%). Soporte & tickets admin.

5 endpoints:
  GET    /v1/admin/support-tickets/pending-count          -> {"count"}
  PATCH  /v1/admin/support-tickets/{id}/read-notifs       -> {"marked"}
  GET    /v1/admin/support-tickets/{id}                   -> detalle + messages
  GET    /v1/admin/support-tickets                        -> lista con filtros
  PATCH  /v1/admin/support-tickets/{id}                   -> update estado/respuesta

Patron identico a test_admin_branches.py: TestClient over `main.app` con
override de get_db (SQLite en memoria/StaticPool) y get_operational_user.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from main import app
from core.database import get_db, Base
from core.limiter import limiter
from core.security import get_operational_user

SUPPORT_URL = "/v1/admin/support-tickets"
ADMIN = type("AdminUser", (), {"rol": "admin", "id": 1, "sucursal": "General",
                                "nombre": "Admin", "apellido": "Global"})()
LOCAL = type("LocalUser", (), {"rol": "local_admin", "id": 2, "sucursal": "Centro",
                               "nombre": "Local", "apellido": "Centro"})()


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    saved = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_operational_user] = lambda: ADMIN
    limiter.reset()
    yield TestClient(app), TestSession
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    limiter.reset()


def _seed_ticket(TestSession, email="cliente@test.com", sucursal="General",
                 estado="Pendiente", respuesta=None):
    db = TestSession()
    u = models.User(
        nombre="Cliente", apellido="Test", email=email,
        password_hash="x", rol="cliente",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    t = models.SupportTicket(
        user_id=u.id, categoria="consulta", sucursal=sucursal,
        asunto="Problema con reserva", mensaje="No puedo entrar",
        estado=estado, respuesta=respuesta,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    db.close()
    return t.id


def _seed_message(TestSession, ticket_id, user_id, mensaje="Hola, necesito ayuda"):
    db = TestSession()
    db.add(models.SupportTicketMessage(
        ticket_id=ticket_id, user_id=user_id, mensaje=mensaje,
    ))
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# pending-count
# ---------------------------------------------------------------------------

def test_pending_count_admin(client):
    c, TestSession = client
    _seed_ticket(TestSession, estado="Pendiente")
    _seed_ticket(TestSession, email="otro@test.com", estado="Resuelto")
    r = c.get(f"{SUPPORT_URL}/pending-count")
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_pending_count_zero(client):
    c, _ = client
    r = c.get(f"{SUPPORT_URL}/pending-count")
    assert r.status_code == 200
    assert r.json()["count"] == 0


# ---------------------------------------------------------------------------
# read-notifs
# ---------------------------------------------------------------------------

def test_mark_ticket_notifs_read(client):
    c, TestSession = client
    tid = _seed_ticket(TestSession)
    r = c.patch(f"{SUPPORT_URL}/{tid}/read-notifs")
    assert r.status_code == 200
    assert r.json()["marked"] in (True, False)


def test_mark_ticket_notifs_read_403_otra_sucursal(client):
    c, TestSession = client
    tid = _seed_ticket(TestSession, sucursal="Norte")
    saved = dict(app.dependency_overrides)
    app.dependency_overrides[get_operational_user] = lambda: LOCAL
    try:
        r = c.patch(f"{SUPPORT_URL}/{tid}/read-notifs")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# get single ticket
# ---------------------------------------------------------------------------

def test_get_admin_ticket_detail(client):
    c, TestSession = client
    tid = _seed_ticket(TestSession)
    user_id = c.get(f"{SUPPORT_URL}/{tid}").json()
    _seed_message(TestSession, tid, user_id.get("user_id", 1))
    r = c.get(f"{SUPPORT_URL}/{tid}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == tid
    assert body["cliente_email"] == "cliente@test.com"
    assert body["estado"] == "Pendiente"


def test_get_admin_ticket_404(client):
    c, _ = client
    r = c.get(f"{SUPPORT_URL}/99999")
    assert r.status_code == 404


def test_get_admin_ticket_403_otra_sucursal(client):
    c, TestSession = client
    tid = _seed_ticket(TestSession, sucursal="Norte")
    saved = dict(app.dependency_overrides)
    app.dependency_overrides[get_operational_user] = lambda: LOCAL
    try:
        r = c.get(f"{SUPPORT_URL}/{tid}")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)
    assert r.status_code == 403


def test_update_admin_ticket_403_otra_sucursal(client):
    c, TestSession = client
    tid = _seed_ticket(TestSession, sucursal="Norte")
    saved = dict(app.dependency_overrides)
    app.dependency_overrides[get_operational_user] = lambda: LOCAL
    try:
        r = c.patch(f"{SUPPORT_URL}/{tid}", json={"estado": "Resuelto"})
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# list tickets
# ---------------------------------------------------------------------------

def test_list_admin_tickets(client):
    c, TestSession = client
    _seed_ticket(TestSession)
    r = c.get(SUPPORT_URL)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_admin_tickets_filtro_estado(client):
    c, TestSession = client
    _seed_ticket(TestSession, estado="Pendiente")
    _seed_ticket(TestSession, email="res@test.com", estado="Resuelto")
    r = c.get(SUPPORT_URL, params={"estado": "Resuelto"})
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert all(t["estado"] == "Resuelto" for t in r.json())


# ---------------------------------------------------------------------------
# update ticket (PATCH)
# ---------------------------------------------------------------------------

def test_update_admin_ticket_estado(client):
    c, TestSession = client
    tid = _seed_ticket(TestSession, estado="Pendiente")
    r = c.patch(f"{SUPPORT_URL}/{tid}", json={"estado": "En revision"})
    assert r.status_code == 200
    body = r.json()
    assert body["estado"] == "En revision"


def test_update_admin_ticket_con_respuesta(client):
    c, TestSession = client
    tid = _seed_ticket(TestSession, estado="Pendiente")
    r = c.patch(f"{SUPPORT_URL}/{tid}", json={
        "estado": "Resuelto", "respuesta": "Ya lo solucionamos"
    })
    assert r.status_code == 200
    body = r.json()
    assert body["estado"] == "Resuelto"
    assert "messages" in body


def test_update_admin_ticket_404(client):
    c, _ = client
    r = c.patch(f"{SUPPORT_URL}/99999", json={"estado": "Resuelto"})
    assert r.status_code == 404
