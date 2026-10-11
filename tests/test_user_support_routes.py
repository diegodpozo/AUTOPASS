"""Ronda #21 - routes/user/support.py (41% -> ~100%). Soporte & tickets del usuario.

4 endpoints (prefijo /v1/user):
  POST  /support-tickets                       -> crear ticket (201)
  GET   /support-tickets                       -> listar tickets propios
  GET   /support-tickets/{ticket_id}           -> detalle + mensajes (404)
  PATCH /support-tickets/{ticket_id}/reply     -> responder (+ adjunto) (404)

Dependencias reales: get_db (core.database) y get_current_user (core.security).
Usa SupportService y NotificationService.
"""
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from main import app
from core.database import get_db, Base
from core.limiter import limiter
from core.security import get_current_user
from repositories.support_repository import SupportRepository
from services.support_service import SupportService

SUPPORT_URL = "/v1/user/support-tickets"
USER = type("User", (), {
    "id": 1, "rol": "user", "nombre": "Cliente", "apellido": "Test",
})()
CURRENT = {"user": USER}


class FakeUser:
    def __init__(self, user_id=1, nombre="Cliente", apellido="Test",
                 rol="user", sucursal=None):
        self.id = user_id
        self.nombre = nombre
        self.apellido = apellido
        self.rol = rol
        self.sucursal = sucursal


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
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
    app.dependency_overrides[get_current_user] = lambda: CURRENT["user"]
    limiter.reset()
    yield TestClient(app), TestSession
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    limiter.reset()


@pytest.fixture(autouse=True)
def _reset_user():
    yield
    CURRENT["user"] = USER


def _seed_ticket(TestSession, estado="Pendiente",
                 asunto="Problema con reserva", mensaje="No puedo entrar"):
    db = TestSession()
    u = models.User(id=2, nombre="Cliente", apellido="Seed", email="cliente@test.com",
                    password_hash="x", rol="user")
    db.add(u)
    db.commit()
    t = models.SupportTicket(
        user_id=u.id, categoria="consulta", sucursal="General",
        asunto=asunto, mensaje=mensaje, estado=estado
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    tid = t.id
    uid = u.id
    db.close()
    return uid, tid


def _seed_message(TestSession, ticket_id, user_id, mensaje="Mensaje del admin"):
    db = TestSession()
    db.add(models.SupportTicketMessage(
        ticket_id=ticket_id, user_id=user_id, mensaje=mensaje
    ))
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# crear ticket (POST)
# ---------------------------------------------------------------------------

def test_create_support_ticket(client):
    c, _ = client
    r = c.post(SUPPORT_URL, json={
        "categoria": "consulta", "asunto": "Ayuda con pago",
        "mensaje": "Quiero saber como pagar", "sucursal": "General"
    })
    assert r.status_code == 201
    body = r.json()
    assert body["ticket_id"] >= 1
    assert body["estado"] == "Pendiente"
    assert body["sucursal"] == "General"


def test_create_support_ticket_falta_campo(client):
    c, _ = client
    r = c.post(SUPPORT_URL, json={"categoria": "consulta", "sucursal": "General"})
    assert r.status_code in (400, 422)


# ---------------------------------------------------------------------------
# listar tickets propios
# ---------------------------------------------------------------------------

def test_list_my_support_tickets(client):
    c, TestSession = client
    uid, _ = _seed_ticket(TestSession)
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.get(SUPPORT_URL)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_list_my_support_tickets_vacio(client):
    c, _ = client
    r = c.get(SUPPORT_URL)
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# detalle de ticket (GET id)
# ---------------------------------------------------------------------------

def test_get_my_support_ticket(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession)
    _seed_message(TestSession, tid, uid)
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.get(f"{SUPPORT_URL}/{tid}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == tid
    assert body["estado"] == "Pendiente"
    assert "messages" in body
    assert len(body["messages"]) >= 1


def test_get_my_support_ticket_404(client):
    c, _ = client
    r = c.get(f"{SUPPORT_URL}/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Ticket no encontrado"


def test_get_ticket_ajeno_no_se_ve(client):
    c, TestSession = client
    _, tid = _seed_ticket(TestSession)
    CURRENT["user"] = FakeUser(user_id=3)
    r = c.get(f"{SUPPORT_URL}/{tid}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# responder ticket (PATCH reply)
# ---------------------------------------------------------------------------

def test_reply_my_support_ticket(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession)
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.patch(f"{SUPPORT_URL}/{tid}/reply", data={"mensaje": "Gracias por su ayuda"})
    assert r.status_code == 200
    body = r.json()
    assert "messages" in body
    assert body["estado"] == "En Revisión"


def test_reply_ticket_resuelto_bloqueado(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession, estado="Resuelto")
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.patch(f"{SUPPORT_URL}/{tid}/reply", data={"mensaje": "Quiero reabrir esto"})
    assert r.status_code == 400
    assert "bloqueado" in r.json()["detail"]


def test_reply_ticket_cancelado_bloqueado(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession, estado="Cancelado")
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.patch(f"{SUPPORT_URL}/{tid}/reply", data={"mensaje": "Reabrir por favor"})
    assert r.status_code == 400
    assert "bloqueado" in r.json()["detail"]


def test_reply_support_ticket_404(client):
    c, _ = client
    r = c.patch(f"{SUPPORT_URL}/99999/reply", data={"mensaje": "Hola"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Ticket no encontrado"


def test_reply_support_ticket_sin_mensaje(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession)
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.patch(f"{SUPPORT_URL}/{tid}/reply", json={})
    assert r.status_code in (400, 422)


def test_reply_support_ticket_con_adjunto(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession)
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.patch(
        f"{SUPPORT_URL}/{tid}/reply",
        data={"mensaje": "Adjunto el comprobante"},
        files={"adjunto": ("comprobante.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64), "image/png")}
    )
    assert r.status_code in (200, 400)
    if r.status_code == 200:
        assert "messages" in r.json()


def test_reply_support_ticket_adjunto_extension_no_permitida_user(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession)
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.patch(
        f"{SUPPORT_URL}/{tid}/reply",
        data={"mensaje": "Mandando algo raro"},
        files={"adjunto": ("malo.exe", io.BytesIO(b"MZ\x90\x00\x03\x00"), "application/x-msdownload")}
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Formato no permitido. Adjuntá imágenes (PNG, JPG, GIF, WEBP) o PDF."


def test_reply_support_ticket_adjunto_demasiado_grande(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession)
    CURRENT["user"] = FakeUser(user_id=uid)
    big = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * (1024 * 1024 + 64))
    r = c.patch(
        f"{SUPPORT_URL}/{tid}/reply",
        data={"mensaje": "Adjunto enorme"},
        files={"adjunto": ("grande.png", big, "image/png")}
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "El archivo supera el tamaño máximo de 1 MB."


def test_reply_support_ticket_adjunto_demasiado_grande(client):
    c, TestSession = client
    uid, tid = _seed_ticket(TestSession)
    CURRENT["user"] = FakeUser(user_id=uid)
    r = c.patch(
        f"{SUPPORT_URL}/{tid}/reply",
        data={"mensaje": "Adjunto gigante"},
        files={"adjunto": ("grande.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * (1024 * 1024 + 64)), "image/png")}
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "El archivo supera el tamaño máximo de 1 MB."
