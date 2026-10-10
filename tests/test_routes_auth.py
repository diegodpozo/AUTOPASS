"""Auditoría A3 (cobertura): tests para routes/auth.py.

Cubre registro, recuperación de contraseña, login (multi-dispositivo con sesiones),
y el flujo OAuth (authorize / callback / complete). Usa una DB SQLite en memoria
aislada por test y reset del rate limiter.
"""
import datetime
import urllib.parse
import uuid

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base, get_db
from core.limiter import limiter
from core.config import settings
from core.security import get_password_hash, create_access_token
from main import app
from services import oauth_service
from services.email_service import EmailService
from services.user_notification_service import UserNotificationService
from services.user_service import UserService


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


def _usuario(TestSession, email="usuario@test.com", password="Password123!", bloqueado=False):
    db = TestSession()
    u = models.User(
        nombre="Test", apellido="User", dni="12345678", telefono="1122334455",
        email=email, password_hash=get_password_hash(password),
        rol="user", sucursal=None,
        saldo=0.0, puntos_acumulados=0,
        is_blocked=bloqueado, is_deleted=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    db.close()
    return u


def _login_body(email, password, device_id=None):
    body = {"email": email, "password": password}
    if device_id:
        body["device_id"] = device_id
    return body


# --- REGISTRO ---

def test_register_user_success(client):
    tc, _ = client
    payload = {
        "email": f"usuario_{uuid.uuid4().hex[:8]}@autopass.com.ar",
        "password": "Password123!",
        "nombre": "Test",
        "apellido": "User",
        "dni": str(uuid.uuid4().int)[:8],
        "telefono": "1122334455",
    }
    response = tc.post("/v1/auth/register", json=payload)
    assert response.status_code in [200, 201]
    assert response.json()["status"] == "ok"


def test_register_duplicado_400(client):
    tc, _ = client
    email = f"dup_{uuid.uuid4().hex[:8]}@autopass.com.ar"
    payload = {
        "email": email,
        "password": "Password123!",
        "nombre": "Test",
        "apellido": "User",
        "dni": str(uuid.uuid4().int)[:8],
        "telefono": "1122334455",
    }
    first = tc.post("/v1/auth/register", json=payload)
    assert first.status_code in [200, 201]
    second = tc.post("/v1/auth/register", json=payload)
    assert second.status_code == 400
    assert "ya está registrado" in second.json()["detail"]


def test_register_dni_duplicado_400(client):
    tc, _ = client
    dni = str(uuid.uuid4().int)[:8]
    payload_1 = {
        "email": f"dni1_{uuid.uuid4().hex[:8]}@autopass.com.ar",
        "password": "Password123!",
        "nombre": "Test",
        "apellido": "User",
        "dni": dni,
        "telefono": "1122334455",
    }
    first = tc.post("/v1/auth/register", json=payload_1)
    assert first.status_code in [200, 201]
    payload_2 = dict(payload_1, email=f"dni2_{uuid.uuid4().hex[:8]}@autopass.com.ar")
    second = tc.post("/v1/auth/register", json=payload_2)
    assert second.status_code == 400
    assert "DNI" in second.json()["detail"]


def test_register_error_interno_500(client, monkeypatch):
    tc, _ = client

    def _boom(db, user_data, rol=None, sucursal=None):
        raise ValueError("unexpected")

    monkeypatch.setattr(UserService, "create_user", _boom)
    payload = {
        "email": f"err_{uuid.uuid4().hex[:8]}@autopass.com.ar",
        "password": "Password123!",
        "nombre": "Test",
        "apellido": "User",
        "dni": str(uuid.uuid4().int)[:8],
        "telefono": "1122334455",
    }
    response = tc.post("/v1/auth/register", json=payload)
    assert response.status_code == 500
    assert response.json()["detail"] == "Error interno al guardar el usuario."


# --- RECUPERACION DE CONTRASEÑA ---

def test_forgot_password_usuario_conocido_envia_mail(client, monkeypatch):
    tc, TestSession = client
    email = "forgot@test.com"
    _usuario(TestSession, email=email)

    sent = []
    monkeypatch.setattr(EmailService, "send_recovery_email",
                        lambda to, name, url: sent.append((to, name, url)))

    response = tc.post("/v1/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert len(sent) == 1
    assert sent[0][0] == email
    assert sent[0][2].startswith(f"{settings.BASE_URL}/reset-password?token=")


def test_forgot_password_usuario_desconocido_no_revela(client, monkeypatch):
    tc, _ = client
    sent = []
    monkeypatch.setattr(EmailService, "send_recovery_email",
                        lambda to, name, url: sent.append((to, name, url)))

    response = tc.post("/v1/auth/forgot-password", json={"email": "nadie@test.com"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert sent == []


def test_reset_password_purpose_invalido_400(client):
    tc, TestSession = client
    email = "resetbad@test.com"
    _usuario(TestSession, email=email)
    bad_token = create_access_token({"sub": email, "purpose": "login"},
                                    expires_delta=datetime.timedelta(minutes=10))

    response = tc.post("/v1/auth/reset-password",
                       json={"token": bad_token, "new_password": "NuevaClave456!"})
    assert response.status_code == 400
    assert "inválido" in response.json()["detail"]


def test_reset_password_token_expirado_400(client):
    tc, _ = client
    past = datetime.datetime.now() - datetime.timedelta(hours=1)
    old_token = jwt.encode(
        {"sub": "x@test.com", "purpose": "recovery", "exp": past},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )

    response = tc.post("/v1/auth/reset-password",
                       json={"token": old_token, "new_password": "NuevaClave456!"})
    assert response.status_code == 400
    assert "expirado" in response.json()["detail"]


def test_reset_password_usuario_inexistente_404(client):
    tc, _ = client
    token = create_access_token({"sub": "fantasma@test.com", "purpose": "recovery"},
                                expires_delta=datetime.timedelta(minutes=10))

    response = tc.post("/v1/auth/reset-password",
                       json={"token": token, "new_password": "NuevaClave456!"})
    assert response.status_code == 404
    assert "Usuario no encontrado." in response.json()["detail"]


def test_reset_password_exitoso(client):
    tc, TestSession = client
    email = "resetok@test.com"
    _usuario(TestSession, email=email)
    token = create_access_token({"sub": email, "purpose": "recovery"},
                                expires_delta=datetime.timedelta(minutes=10))

    response = tc.post("/v1/auth/reset-password",
                       json={"token": token, "new_password": "NuevaClave456!"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    login = tc.post("/v1/auth/login", json=_login_body(email, "NuevaClave456!"))
    assert login.status_code == 200


# --- LOGIN ---

def test_login_user_invalid_credentials(client):
    tc, _ = client
    response = tc.post("/v1/auth/login", json=_login_body(
        f"nonexistent_{uuid.uuid4().hex[:8]}@autopass.com.ar", "WrongPassword123!"))
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers


def test_login_ok_sin_device(client):
    tc, TestSession = client
    email = "login@test.com"
    _usuario(TestSession, email=email)

    response = tc.post("/v1/auth/login", json=_login_body(email, "Password123!"))
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["rol"] == "user"
    assert data["nuevo_dispositivo"] is False
    assert data["access_token"]


def test_login_nueva_device_con_otra_activa_avisa(client, monkeypatch):
    tc, TestSession = client
    email = "dev@test.com"
    user = _usuario(TestSession, email=email)

    db = TestSession()
    db.add(models.UserSession(
        user_id=user.id, device_id="otro-dev",
        user_agent="Mozilla-Otro", ip_address="1.2.3.4",
        created_at=datetime.datetime.now(), last_login_at=datetime.datetime.now(),
    ))
    db.commit()
    db.close()

    notifs = []
    monkeypatch.setattr(UserNotificationService, "create_notification",
                        lambda *a, **k: notifs.append((a, k)))

    response = tc.post(
        "/v1/auth/login",
        json=_login_body(email, "Password123!", device_id="dev-nuevo"),
        headers={"User-Agent": "Mozilla-Mio"},
    )
    assert response.status_code == 200
    assert response.json()["nuevo_dispositivo"] is True
    assert len(notifs) == 1
    assert notifs[0][1]["tipo"] == "NEW_DEVICE_LOGIN"


def test_login_misma_device_sin_aviso(client, monkeypatch):
    tc, TestSession = client
    email = "misma@test.com"
    user = _usuario(TestSession, email=email)

    db = TestSession()
    db.add(models.UserSession(
        user_id=user.id, device_id="dev-existente",
        user_agent="Mozilla-Stable", ip_address="1.2.3.4",
        created_at=datetime.datetime.now(), last_login_at=datetime.datetime.now(),
    ))
    db.commit()
    db.close()

    notifs = []
    monkeypatch.setattr(UserNotificationService, "create_notification",
                        lambda *a, **k: notifs.append(a))

    response = tc.post(
        "/v1/auth/login",
        json=_login_body(email, "Password123!", device_id="dev-existente"),
        headers={"User-Agent": "Mozilla-Stable"},
    )
    assert response.status_code == 200
    assert response.json()["nuevo_dispositivo"] is False
    assert notifs == []

    db = TestSession()
    session = db.query(models.UserSession).filter(
        models.UserSession.device_id == "dev-existente").first()
    assert session is not None
    db.close()


def test_login_absorbe_sesion_por_user_agent(client):
    tc, TestSession = client
    email = "absorbe@test.com"
    user = _usuario(TestSession, email=email)

    db = TestSession()
    db.add(models.UserSession(
        user_id=user.id, device_id="dev-viejo",
        user_agent="Mozilla-Recur", ip_address="1.2.3.4",
        created_at=datetime.datetime.now(), last_login_at=datetime.datetime.now(),
    ))
    db.commit()
    db.close()

    response = tc.post(
        "/v1/auth/login",
        json=_login_body(email, "Password123!", device_id="dev-nuevo-id"),
        headers={"User-Agent": "Mozilla-Recur"},
    )
    assert response.status_code == 200
    assert response.json()["nuevo_dispositivo"] is False

    db = TestSession()
    session = db.query(models.UserSession).filter(
        models.UserSession.user_id == user.id).first()
    assert session.device_id == "dev-nuevo-id"
    db.close()


# --- OAUTH ---

def test_oauth_providers_lista(client, monkeypatch):
    tc, _ = client
    monkeypatch.setattr(oauth_service, "enabled_providers",
                        lambda: [{"id": "google", "label": "Google"}])
    response = tc.get("/v1/auth/oauth/providers")
    assert response.status_code == 200
    assert response.json() == {"providers": [{"id": "google", "label": "Google"}]}


def test_oauth_authorize_no_configurado_503(client, monkeypatch):
    tc, _ = client
    monkeypatch.setattr(oauth_service, "is_provider_configured", lambda n: False)
    response = tc.get("/v1/auth/oauth/google/authorize")
    assert response.status_code == 503
    assert "no está configurado" in response.json()["detail"]


def test_oauth_authorize_ok_302(client, monkeypatch):
    tc, _ = client
    monkeypatch.setattr(oauth_service, "is_provider_configured", lambda n: True)
    captured = {}

    def fake_get_authorize_url(n, state):
        captured["state"] = state
        return "https://accounts.google.com/o/oauth2/v2/auth"

    monkeypatch.setattr(oauth_service, "get_authorize_url", fake_get_authorize_url)

    response = tc.get("/v1/auth/oauth/google/authorize", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"].startswith("https://accounts.google.com")
    assert captured["state"]


def test_oauth_callback_error_denegado(client):
    tc, _ = client
    response = tc.get("/v1/auth/oauth/google/callback", params={"error": "access_denied"},
                      follow_redirects=False)
    assert response.status_code == 303
    assert "oauth_error=denegado" in response.headers["location"]


def test_oauth_callback_state_invalido(client):
    tc, _ = client
    response = tc.get("/v1/auth/oauth/google/callback",
                      params={"code": "xx", "state": "a.b.c.d"}, follow_redirects=False)
    assert response.status_code == 303
    assert "oauth_error=state_invalido" in response.headers["location"]


def test_oauth_callback_sin_codigo(client):
    tc, _ = client
    state = oauth_service.sign_state("google")
    response = tc.get("/v1/auth/oauth/google/callback", params={"state": state},
                      follow_redirects=False)
    assert response.status_code == 303
    assert "oauth_error=sin_codigo" in response.headers["location"]


def test_oauth_callback_intercambio_falla(client, monkeypatch):
    tc, _ = client
    from fastapi import HTTPException

    def _fail_exchange(n, code):
        raise HTTPException(status_code=502, detail="No se pudo obtener el token del proveedor social.")

    monkeypatch.setattr(oauth_service, "exchange_code", _fail_exchange)
    state = oauth_service.sign_state("google")
    response = tc.get("/v1/auth/oauth/google/callback",
                      params={"code": "xx", "state": state}, follow_redirects=False)
    assert response.status_code == 303
    fragment = urllib.parse.unquote(response.headers["location"].split("#", 1)[1])
    assert "oauth_error=No se pudo obtener el token del proveedor social." in fragment


def test_oauth_callback_usuario_existente(client, monkeypatch):
    tc, TestSession = client
    email = "social@test.com"
    _usuario(TestSession, email=email)

    monkeypatch.setattr(oauth_service, "exchange_code", lambda n, code: "tok123")
    monkeypatch.setattr(oauth_service, "fetch_user_info",
                        lambda n, tok: {"provider_id": "1", "email": email,
                                        "nombre": "Jane", "apellido": "Doe"})
    state = oauth_service.sign_state("google")

    response = tc.get("/v1/auth/oauth/google/callback",
                      params={"code": "xx", "state": state}, follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/#")
    assert "oauth_token=" in location
    assert "oauth_error" not in location


def test_oauth_callback_usuario_bloqueado(client, monkeypatch):
    tc, TestSession = client
    email = "blocked@test.com"
    _usuario(TestSession, email=email, bloqueado=True)

    monkeypatch.setattr(oauth_service, "exchange_code", lambda n, code: "tok123")
    monkeypatch.setattr(oauth_service, "fetch_user_info",
                        lambda n, tok: {"provider_id": "1", "email": email,
                                        "nombre": "Jane", "apellido": "Doe"})
    state = oauth_service.sign_state("google")

    response = tc.get("/v1/auth/oauth/google/callback",
                      params={"code": "xx", "state": state}, follow_redirects=False)
    assert response.status_code == 303
    assert "oauth_error=bloqueado" in response.headers["location"]


def test_oauth_callback_nuevo_usuario_signup(client, monkeypatch):
    tc, _ = client
    email = "nuevo-social@test.com"
    signup_token = create_access_token(
        {"sub": email, "purpose": "oauth_signup", "provider": "google",
         "nombre": "Jane", "apellido": "Doe"},
        expires_delta=datetime.timedelta(minutes=30),
    )
    monkeypatch.setattr(oauth_service, "exchange_code", lambda n, code: "tok123")
    monkeypatch.setattr(oauth_service, "fetch_user_info",
                        lambda n, tok: {"provider_id": "1", "email": email,
                                        "nombre": "Jane", "apellido": "Doe"})
    monkeypatch.setattr(oauth_service, "issue_oauth_signup_code", lambda *a: signup_token)
    state = oauth_service.sign_state("google")

    response = tc.get("/v1/auth/oauth/google/callback",
                      params={"code": "xx", "state": state}, follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["location"]
    assert "oauth_signup=" in location
    assert "oauth_email=" in location
    assert "oauth_provider=google" in location


def test_oauth_complete_crea_usuario(client):
    tc, TestSession = client
    email = "completo@test.com"
    signup_token = create_access_token(
        {"sub": email, "purpose": "oauth_signup", "provider": "google",
         "nombre": "Jane", "apellido": "Doe"},
        expires_delta=datetime.timedelta(minutes=30),
    )

    response = tc.post("/v1/auth/oauth/complete",
                       json={"code": signup_token, "dni": "12345678", "telefono": "1155554444"})
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["rol"] == "user"
    assert data["access_token"]

    db = TestSession()
    user = db.query(models.User).filter(models.User.email == email).first()
    assert user is not None
    assert user.nombre == "Jane"
    db.close()


# --- LOGOUT (P2 A1) ---

def test_logout_revoca_token_y_borra_sesion(client):
    from core.security import revoke_token, _revoked_jtis
    tc, TestSession = client
    email = "logout@test.com"
    user = _usuario(TestSession, email=email)

    db = TestSession()
    db.add(models.UserSession(
        user_id=user.id, device_id="dev-logout",
        user_agent="Mozilla-Logout", ip_address="9.9.9.9",
        created_at=datetime.datetime.now(), last_login_at=datetime.datetime.now(),
    ))
    db.commit()
    db.close()

    login = tc.post("/v1/auth/login", json=_login_body(email, "Password123!", device_id="dev-logout"))
    assert login.status_code == 200
    token = login.json()["access_token"]

    _revoked_jtis.clear()
    response = tc.post("/v1/auth/logout",
                       headers={"Authorization": f"Bearer {token}"},
                       json={"device_id": "dev-logout"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    # 1) El jti del token debe estar revocado -> el mismo token ya no autentica
    protected = tc.get("/v1/user/me", headers={"Authorization": f"Bearer {token}"})
    assert protected.status_code in (401, 403)

    # 2) La UserSession del device fue eliminada
    db = TestSession()
    still = db.query(models.UserSession).filter(
        models.UserSession.user_id == user.id,
        models.UserSession.device_id == "dev-logout",
    ).first()
    assert still is None
    db.close()


def test_logout_requiere_auth(client):
    tc, _ = client
    response = tc.post("/v1/auth/logout", json={"device_id": "nope"})
    assert response.status_code == 401


def test_token_recuperacion_no_es_accesso(client):
    """Un token con purpose='recovery' debe rechazarse como token de acceso (A1.2)."""
    from core.security import decode_access_token
    tc, TestSession = client
    email = "reco@test.com"
    _usuario(TestSession, email=email)
    recovery = create_access_token({"sub": email, "purpose": "recovery"},
                                   expires_delta=datetime.timedelta(minutes=10))
    assert decode_access_token(recovery) is None
    protected = tc.get("/v1/user/me", headers={"Authorization": f"Bearer {recovery}"})
    assert protected.status_code == 401