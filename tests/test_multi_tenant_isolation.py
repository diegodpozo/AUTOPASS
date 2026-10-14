"""Tests de aislamiento multiempresa (multi-tenant).

Verifica que un Admin General de una organizacion NO ve ni opera datos de otra:
usuarios, sucursales, promociones y configuraciones quedan aislados por
`organization_id`.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base, get_db
from core.limiter import limiter
from core.security import get_password_hash
from main import app


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


def _crear_org(TestSession, nombre):
    db = TestSession()
    org = models.Organization(nombre=nombre, es_principal=False, activa=True)
    db.add(org)
    db.commit()
    db.refresh(org)
    oid = org.id
    db.close()
    return oid


def _crear_usuario(TestSession, rol, email, organization_id=None, sucursal=None, password="Password123!"):
    db = TestSession()
    db.add(models.User(
        nombre="Nombre", apellido="Apellido", dni=str(uuid.uuid4().int)[:8], telefono="1122334455",
        email=email, password_hash=get_password_hash(password), rol=rol, sucursal=sucursal,
        organization_id=organization_id, saldo=0.0, puntos_acumulados=0, is_blocked=False, is_deleted=False,
    ))
    db.commit()
    db.close()


def _crear_branch(TestSession, nombre, organization_id):
    db = TestSession()
    db.add(models.ParkingBranch(
        nombre=nombre, activa=True, organization_id=organization_id,
        direccion="Calle 1", telefono="1122334455", horario="09:00 a 18:00",
    ))
    db.commit()
    db.close()


def _crear_promo(TestSession, titulo, organization_id):
    db = TestSession()
    db.add(models.Promotion(
        titulo=titulo, descripcion="Beneficio de prueba", costo_puntos=10,
        organization_id=organization_id, activa=True,
    ))
    db.commit()
    db.close()


def _crear_setting(TestSession, clave, valor, organization_id):
    db = TestSession()
    db.add(models.Settings(clave=clave, valor=valor, organization_id=organization_id))
    db.commit()
    db.close()


def _login(tc, email, password="Password123!"):
    res = tc.post("/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _headers(tc, email):
    return {"Authorization": f"Bearer {_login(tc, email)}"}


def test_admin_solo_ve_sus_usuarios(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_admin = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_cli_a = f"cli_a_{uuid.uuid4().hex[:8]}@test.com"
    email_cli_b = f"cli_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_admin, org_a)
    _crear_usuario(TS, "user", email_cli_a, org_a)
    _crear_usuario(TS, "user", email_cli_b, org_b)

    res = tc.get("/v1/admin/users", headers=_headers(tc, email_admin))
    assert res.status_code == 200, res.text
    emails = {u["email"] for u in res.json()}
    assert email_cli_a in emails
    assert email_cli_b not in emails


def test_admin_solo_ve_sus_sucursales(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_admin = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_admin, org_a)
    nombre_a = f"CENTRO A {uuid.uuid4().hex[:6]}"
    nombre_b = f"CENTRO B {uuid.uuid4().hex[:6]}"
    _crear_branch(TS, nombre_a, org_a)
    _crear_branch(TS, nombre_b, org_b)

    res = tc.get("/v1/admin/branches", headers=_headers(tc, email_admin))
    assert res.status_code == 200, res.text
    nombres = {b["nombre"] for b in res.json()}
    assert nombre_a in nombres
    assert nombre_b not in nombres


def test_admin_solo_ve_sus_promociones(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_admin = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_admin, org_a)
    titulo_a = f"Promo A {uuid.uuid4().hex[:6]}"
    titulo_b = f"Promo B {uuid.uuid4().hex[:6]}"
    _crear_promo(TS, titulo_a, org_a)
    _crear_promo(TS, titulo_b, org_b)

    res = tc.get("/v1/admin/promotions", headers=_headers(tc, email_admin))
    assert res.status_code == 200, res.text
    titulos = {p["titulo"] for p in res.json()}
    assert titulo_a in titulos
    assert titulo_b not in titulos


def test_org_nueva_puede_crear_sucursal_con_nombre_ya_usado(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_admin_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_admin_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_admin_a, org_a)
    _crear_usuario(TS, "admin", email_admin_b, org_b)
    _crear_branch(TS, "CENTRO", org_a)

    res = tc.post(
        "/v1/admin/branches",
        headers=_headers(tc, email_admin_b),
        data={"nombre": "CENTRO", "direccion": "Calle 1", "telefono": "1122334455", "horario": "09:00 a 18:00"},
    )
    assert res.status_code == 200, res.text


def test_sedes_con_mismo_nombre_no_se_cruzan_entre_orgs(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_admin_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_admin_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_admin_a, org_a)
    _crear_usuario(TS, "admin", email_admin_b, org_b)
    _crear_branch(TS, "CENTRO", org_a)

    res = tc.post(
        "/v1/admin/branches",
        headers=_headers(tc, email_admin_b),
        data={"nombre": "CENTRO", "direccion": "Calle 1", "telefono": "1122334455", "horario": "09:00 a 18:00"},
    )
    assert res.status_code == 200, res.text

    email_staff = f"staff_b_{uuid.uuid4().hex[:8]}@test.com"
    res = tc.post(
        "/v1/admin/users?rol=staff",
        headers=_headers(tc, email_admin_b),
        json={"nombre": "Sta", "apellido": "Ff", "email": email_staff, "dni": "12345678",
              "telefono": "1122334455", "sucursal": "CENTRO", "password": "Password123!"},
    )
    assert res.status_code == 200, res.text

    db = TS()
    try:
        staff = db.query(models.User).filter(models.User.email == email_staff).first()
        branch_b = db.query(models.ParkingBranch).filter(
            models.ParkingBranch.nombre == "CENTRO",
            models.ParkingBranch.organization_id == org_b,
        ).first()
        branch_a = db.query(models.ParkingBranch).filter(
            models.ParkingBranch.nombre == "CENTRO",
            models.ParkingBranch.organization_id == org_a,
        ).first()
        assert staff.sucursal_id == branch_b.id
        assert branch_a.id != branch_b.id
    finally:
        db.close()


def test_configuraciones_aisladas_por_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_admin = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_admin, org_a)
    _crear_setting(TS, "precio_hora", 111.0, org_a)
    _crear_setting(TS, "precio_hora", 999.0, org_b)

    res = tc.get("/v1/admin/settings", headers=_headers(tc, email_admin))
    assert res.status_code == 200, res.text
    assert res.json().get("precio_hora") == 111.0
