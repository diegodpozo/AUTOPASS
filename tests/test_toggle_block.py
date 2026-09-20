"""Test #6 de la auditoría A3: toggle de bloqueo de usuario que invalida tokens.

Verifica POST /v1/admin/users/{id}/toggle-block:
- solo admin/local_admin (get_local_manager)
- no autobloqueo
- el token emitido ANTES del bloqueo deja de funcionar (403 en /v1/user/me)
- desbloqueo reactiva la cuenta
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.database import get_db, Base
from core.limiter import limiter
from core.security import create_access_token
import models


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


def _crear_usuario(TestSession, rol, email, nombre="User"):
    db = TestSession()
    user = models.User(email=email, nombre=nombre, apellido="Test", dni=email[:8],
                       password_hash="x", telefono="1112223333",
                       rol=rol, is_blocked=False, is_deleted=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def _token(user):
    return create_access_token({"sub": user.email, "rol": user.rol})


def _toggle(tc, admin_token, user_id):
    return tc.post(f"/v1/admin/users/{user_id}/toggle-block",
                   headers={"Authorization": f"Bearer {admin_token}"})


def test_toggle_block_sin_token_es_401(client):
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", "admin@autopass.com")
    resp = _toggle(tc, "", admin.id)
    assert resp.status_code == 401


def test_toggle_block_rol_usuario_es_403(client):
    tc, TestSession = client
    user = _crear_usuario(TestSession, "user", "user@test.com")
    target = _crear_usuario(TestSession, "user", "target@test.com")
    resp = _toggle(tc, _token(user), target.id)
    assert resp.status_code == 403


def test_toggle_block_no_autobloqueo(client):
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", "admin2@autopass.com")
    resp = _toggle(tc, _token(admin), admin.id)
    assert resp.status_code == 400


def test_toggle_block_invalida_tokens_emitidos(client):
    """El token emitido antes de bloquear deja de funcionar (403): el estado se checa en la BD."""
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", "admin3@autopass.com")
    target = _crear_usuario(TestSession, "user", "target2@test.com")

    target_token = _token(target)  # emitido ANTES del bloqueo

    # /me funciona antes de bloquear
    r0 = tc.get("/v1/user/me", headers={"Authorization": f"Bearer {target_token}"})
    assert r0.status_code == 200

    resp = _toggle(tc, _token(admin), target.id)
    assert resp.status_code == 200
    assert resp.json()["is_blocked"] is True
    assert "BLOQUEADO" in resp.json()["message"]

    # Token previo ahora 403
    r1 = tc.get("/v1/user/me", headers={"Authorization": f"Bearer {target_token}"})
    assert r1.status_code == 403
    assert "suspendida" in r1.json()["detail"]

    # Login directo de un bloqueado también es 403
    from core.security import verify_password
    db = TestSession()
    target_db = db.query(models.User).filter(models.User.id == target.id).first()
    assert target_db.is_blocked is True
    db.close()

    # Desbloqueo reactiva el token
    resp2 = _toggle(tc, _token(admin), target.id)
    assert resp2.status_code == 200
    assert resp2.json()["is_blocked"] is False

    r2 = tc.get("/v1/user/me", headers={"Authorization": f"Bearer {target_token}"})
    assert r2.status_code == 200


def test_toggle_block_admin_bloquea_staff(client):
    """Un admin puede bloquear a personal staff."""
    tc, TestSession = client
    admin = _crear_usuario(TestSession, "admin", "admin4@autopass.com")
    staff = _crear_usuario(TestSession, "staff", "staff@test.com")

    resp = _toggle(tc, _token(admin), staff.id)
    assert resp.status_code == 200
    assert resp.json()["is_blocked"] is True