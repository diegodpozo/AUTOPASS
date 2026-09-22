"""Ronda #23 - routes/admin/users.py (58% -> ~100%). CRUD de usuarios admin.

8 endpoints:
  GET    /v1/admin/users                        -> lista (filtra por sucursal si local_admin)
  POST   /v1/admin/users                       -> crear usuario (local no crea ADMIN)
  PATCH  /v1/admin/users/{id}                  -> actualizar + notif a USER
  POST   /v1/admin/users/{id}/role             -> cambiar rol + notif a USER
  POST   /v1/admin/users/{id}/toggle-block     -> bloquear/desbloquear + notif a USER
  POST   /v1/admin/users/{id}/balance          -> ajustar saldo + notif a USER
  POST   /v1/admin/users/{id}/password         -> cambiar contraseña + notif a USER
  DELETE /v1/admin/users/{id}                  -> eliminar usuario (no propia cuenta)

Patron identico a test_admin_support_routes.py: TestClient over `app` con
override de get_db (SQLite en memoria/StaticPool) y get_local_manager.
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
from core.security import get_local_manager

USERS_URL = "/v1/admin/users"

ADMIN_GLOBAL = type(
    "AdminGlobal",
    (),
    {"rol": "admin", "id": 99, "sucursal": None, "nombre": "Admin", "apellido": "Global"},
)()

LOCAL_MANAGER = type(
    "LocalManager",
    (),
    {"rol": "local_admin", "id": 98, "sucursal": "Quilmes", "nombre": "Local", "apellido": "Jefe"},
)()


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
    app.dependency_overrides[get_local_manager] = lambda: ADMIN_GLOBAL
    limiter.reset()
    yield TestClient(app), TestSession
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    limiter.reset()


@pytest.fixture
def client_local():
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
    app.dependency_overrides[get_local_manager] = lambda: LOCAL_MANAGER
    limiter.reset()
    yield TestClient(app), TestSession
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    limiter.reset()


def _seed_user(TestSession, email="cliente@test.com", dni="30123456",
               rol="user", sucursal="Quilmes", is_blocked=False, _id=None):
    db = TestSession()
    u = models.User(
        id=_id, nombre="Cliente", apellido="Test", dni=dni, telefono="1155554444",
        email=email, password_hash="x", rol=rol, sucursal=sucursal,
        is_blocked=is_blocked,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    db.close()
    return u.id


def _valid_create(nombre="Nuevo", apellido="Cliente", email="nuevo@test.com"):
    return {
        "nombre": nombre,
        "apellido": apellido,
        "dni": "30123999",
        "telefono": "1166665555",
        "email": email,
        "password": "ClaveSegura1!",
    }


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_users_admin(client):
    c, TestSession = client
    _seed_user(TestSession)
    r = c.get(USERS_URL)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert any(u["email"] == "cliente@test.com" for u in r.json())


def test_list_users_local_solo_sucursal(client_local):
    c, TestSession = client_local
    _seed_user(TestSession, email="local_staff@test.com", sucursal="Quilmes",
               rol="staff")
    _seed_user(TestSession, email="rival_staff@test.com", dni="30998877",
               sucursal="Lanús", rol="staff")
    r = c.get(USERS_URL)
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "local_staff@test.com" in emails
    assert "rival_staff@test.com" not in emails


def test_list_users_local_ve_clientes_otra_sucursal(client_local):
    c, TestSession = client_local
    _seed_user(TestSession, email="cliente_quilmes@test.com", sucursal="Quilmes")
    _seed_user(TestSession, email="cliente_lanus@test.com", dni="30998877",
               sucursal="Lanús")
    r = c.get(USERS_URL)
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "cliente_quilmes@test.com" in emails
    assert "cliente_lanus@test.com" in emails


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_user_global(client):
    c, TestSession = client
    _seed_user(TestSession)
    r = c.post(USERS_URL, json=_valid_create())
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "nuevo@test.com"
    assert body["rol"] == "user"


def test_create_user_duplicate_email(client):
    c, TestSession = client
    _seed_user(TestSession, email="nuevo@test.com")
    r = c.post(USERS_URL, json=_valid_create())
    assert r.status_code == 400


def test_create_user_local_no_puede_admin(client_local):
    c, TestSession = client_local
    r = c.post(USERS_URL, json=_valid_create(), params={"rol": "admin"})
    assert r.status_code == 403
    r = c.post(USERS_URL, json=_valid_create(), params={"rol": "staff"})
    assert r.status_code == 200
    assert r.json()["sucursal"] == "Quilmes"


# ---------------------------------------------------------------------------
# update (PATCH)
# ---------------------------------------------------------------------------

def test_update_user_admin_ok(client):
    c, TestSession = client
    uid = _seed_user(TestSession)
    r = c.patch(f"{USERS_URL}/{uid}", json={"nombre": "Carlos", "rol": "staff"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_update_user_404(client):
    c, _ = client
    r = c.patch(f"{USERS_URL}/99999", json={"nombre": "X"})
    assert r.status_code == 404


def test_update_user_local_fuera_sucursal(client_local):
    c, TestSession = client_local
    uid = _seed_user(TestSession, rol="staff", sucursal="Lanús")
    r = c.patch(f"{USERS_URL}/{uid}", json={"nombre": "Carlos"})
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# change role
# ---------------------------------------------------------------------------

def test_change_user_role_ok(client):
    c, TestSession = client
    uid = _seed_user(TestSession, email="rolchange@test.com")
    r = c.post(f"{USERS_URL}/{uid}/role", params={"nuevo_rol": "staff"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_change_user_role_404(client):
    c, _ = client
    r = c.post(f"{USERS_URL}/99999/role", params={"nuevo_rol": "staff"})
    assert r.status_code == 404


def test_change_user_role_local_asigna_admin(client_local):
    c, TestSession = client_local
    uid = _seed_user(TestSession, email="target@test.com")
    r = c.post(f"{USERS_URL}/{uid}/role", params={"nuevo_rol": "admin"})
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# toggle-block
# ---------------------------------------------------------------------------

def test_toggle_user_block_ok(client):
    c, TestSession = client
    uid = _seed_user(TestSession, email="block@test.com")
    r = c.post(f"{USERS_URL}/{uid}/toggle-block")
    assert r.status_code == 200
    assert r.json()["is_blocked"] is True
    r = c.post(f"{USERS_URL}/{uid}/toggle-block")
    assert r.status_code == 200
    assert r.json()["is_blocked"] is False


def test_toggle_user_block_propia_cuenta(client):
    c, TestSession = client
    uid = _seed_user(TestSession, rol="admin", sucursal=None, _id=99)
    r = c.post(f"{USERS_URL}/{uid}/toggle-block")
    assert r.status_code == 400


def test_toggle_user_block_404(client):
    c, _ = client
    r = c.post(f"{USERS_URL}/99999/toggle-block")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# balance
# ---------------------------------------------------------------------------

def test_adjust_user_balance_ok(client):
    c, TestSession = client
    uid = _seed_user(TestSession, email="saldo@test.com")
    r = c.post(f"{USERS_URL}/{uid}/balance", params={"monto": 150.50})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_adjust_user_balance_404(client):
    c, _ = client
    r = c.post(f"{USERS_URL}/99999/balance", params={"monto": 50})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# password
# ---------------------------------------------------------------------------

def test_change_user_password_ok(client):
    c, TestSession = client
    uid = _seed_user(TestSession, email="pass@test.com")
    r = c.post(f"{USERS_URL}/{uid}/password",
               json={"new_password": "OtraClave2!"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_change_user_password_404(client):
    c, _ = client
    r = c.post(f"{USERS_URL}/99999/password",
               json={"new_password": "OtraClave2!"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_user_ok(client):
    c, TestSession = client
    uid = _seed_user(TestSession, email="delete@test.com")
    r = c.delete(f"{USERS_URL}/{uid}")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_delete_user_propia_cuenta(client):
    r = client[0].delete(f"{USERS_URL}/99")
    assert r.status_code == 400


def test_delete_user_404(client):
    c, _ = client
    r = c.delete(f"{USERS_URL}/99999")
    assert r.status_code == 404
