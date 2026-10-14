"""Tests del flujo de invitacion/activacion del Admin General.

Cubre: alta por invitacion (POST /v1/admin/users/invite, solo Admin General),
que la cuenta no pueda ingresar hasta fijar la clave, y que al completar el
registro (reset-password con purpose='activation') se envie la confirmacion.
"""
import datetime
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base, get_db
from core.limiter import limiter
from core.config import settings
from core.security import get_password_hash, create_access_token
from main import app
from services.email_service import EmailService


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
    limiter.reset()
    yield TestClient(app), TestSession
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    limiter.reset()


def _crear_usuario(TestSession, rol, email, password="Password123!"):
    db = TestSession()
    u = models.User(
        nombre="Test", apellido="User", dni=str(uuid.uuid4().int)[:8], telefono="1122334455",
        email=email, password_hash=get_password_hash(password),
        rol=rol, sucursal=None, saldo=0.0, puntos_acumulados=0,
        is_blocked=False, is_deleted=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    db.close()
    return u


def _token(tc, email, password="Password123!"):
    res = tc.post("/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _invite_body(email, dni=None):
    return {
        "nombre": "Nuevo",
        "apellido": "Admin",
        "dni": dni or str(uuid.uuid4().int)[:8],
        "telefono": "1122334455",
        "email": email,
    }


def test_admin_general_invita_y_envia_mail(client, monkeypatch):
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", f"admin_{uuid.uuid4().hex[:8]}@test.com")
    token = _token(tc, admin.email)

    enviados = []
    monkeypatch.setattr(EmailService, "send_admin_invitation",
                        lambda to, nombre, url: enviados.append((to, url)))

    email = f"invitado_{uuid.uuid4().hex[:8]}@test.com"
    res = tc.post("/v1/admin/users/invite", json=_invite_body(email),
                  headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200, res.text
    assert enviados and enviados[0][0] == email
    assert "token=" in enviados[0][1]

    db = TestSession()
    nuevo = db.query(models.User).filter(models.User.email == email).first()
    db.close()
    assert nuevo is not None
    assert str(nuevo.rol) == "admin"


def test_invitado_no_puede_ingresar_antes_de_activar(client, monkeypatch):
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", f"admin_{uuid.uuid4().hex[:8]}@test.com")
    token = _token(tc, admin.email)
    monkeypatch.setattr(EmailService, "send_admin_invitation", lambda *a, **k: None)

    email = f"invitado_{uuid.uuid4().hex[:8]}@test.com"
    tc.post("/v1/admin/users/invite", json=_invite_body(email),
            headers={"Authorization": f"Bearer {token}"})

    # La clave es aleatoria y desconocida: no hay forma de ingresar todavia.
    res = tc.post("/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert res.status_code == 401


def test_invitacion_requiere_admin_general(client):
    tc, TestSession = client
    local = _crear_usuario(TestSession, "local_admin", f"local_{uuid.uuid4().hex[:8]}@test.com")
    token = _token(tc, local.email)

    res = tc.post("/v1/admin/users/invite", json=_invite_body(f"x_{uuid.uuid4().hex[:8]}@test.com"),
                  headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_invitacion_email_duplicado_400(client, monkeypatch):
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", f"admin_{uuid.uuid4().hex[:8]}@test.com")
    token = _token(tc, admin.email)
    monkeypatch.setattr(EmailService, "send_admin_invitation", lambda *a, **k: None)

    email = f"invitado_{uuid.uuid4().hex[:8]}@test.com"
    headers = {"Authorization": f"Bearer {token}"}
    first = tc.post("/v1/admin/users/invite", json=_invite_body(email), headers=headers)
    assert first.status_code == 200
    second = tc.post("/v1/admin/users/invite", json=_invite_body(email), headers=headers)
    assert second.status_code == 400


def test_activacion_fija_clave_y_confirma_registro(client, monkeypatch):
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", f"admin_{uuid.uuid4().hex[:8]}@test.com")
    token = _token(tc, admin.email)
    monkeypatch.setattr(EmailService, "send_admin_invitation", lambda *a, **k: None)

    email = f"invitado_{uuid.uuid4().hex[:8]}@test.com"
    tc.post("/v1/admin/users/invite", json=_invite_body(email),
            headers={"Authorization": f"Bearer {token}"})

    confirmaciones = []
    monkeypatch.setattr(EmailService, "send_registration_confirmation",
                        lambda to, nombre, url: confirmaciones.append(to))

    nuevo_token = create_access_token(
        data={"sub": email, "purpose": "activation"},
        expires_delta=datetime.timedelta(hours=1),
    )
    res = tc.post("/v1/auth/reset-password",
                  json={"token": nuevo_token, "new_password": "NuevaClave123!"})
    assert res.status_code == 200, res.text
    assert confirmaciones == [email]

    # Ahora si puede ingresar con la clave que fijo.
    after = tc.post("/v1/auth/login", json={"email": email, "password": "NuevaClave123!"})
    assert after.status_code == 200


def test_reset_rechaza_purpose_desconocido(client):
    tc, TestSession = client
    email = f"user_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TestSession, "user", email)

    token = create_access_token(data={"sub": email, "purpose": "otro"},
                                expires_delta=datetime.timedelta(hours=1))
    res = tc.post("/v1/auth/reset-password", json={"token": token, "new_password": "NuevaClave123!"})
    assert res.status_code == 400


def test_invitacion_crea_organizacion_con_nombre_del_formulario(client, monkeypatch):
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", f"admin_{uuid.uuid4().hex[:8]}@test.com")
    token = _token(tc, admin.email)
    monkeypatch.setattr(EmailService, "send_admin_invitation", lambda *a, **k: None)

    email = f"invitado_{uuid.uuid4().hex[:8]}@test.com"
    body = _invite_body(email)
    body["organizacion"] = "Estacionamiento Sur S.A."
    res = tc.post("/v1/admin/users/invite", json=body, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.text

    db = TestSession()
    org = db.query(models.Organization).filter(models.Organization.nombre == "Estacionamiento Sur S.A.").first()
    nuevo = db.query(models.User).filter(models.User.email == email).first()
    db.close()
    assert org is not None
    assert org.es_principal is False
    assert nuevo.organization_id == org.id


def test_invitacion_sin_organizacion_la_deriva_del_nombre(client, monkeypatch):
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", f"admin_{uuid.uuid4().hex[:8]}@test.com")
    token = _token(tc, admin.email)
    monkeypatch.setattr(EmailService, "send_admin_invitation", lambda *a, **k: None)

    email = f"invitado_{uuid.uuid4().hex[:8]}@test.com"
    tc.post("/v1/admin/users/invite", json=_invite_body(email),
            headers={"Authorization": f"Bearer {token}"})

    db = TestSession()
    nuevo = db.query(models.User).filter(models.User.email == email).first()
    org = db.query(models.Organization).filter(models.Organization.id == nuevo.organization_id).first()
    db.close()
    assert org is not None
    assert org.nombre == "Nuevo Admin"
