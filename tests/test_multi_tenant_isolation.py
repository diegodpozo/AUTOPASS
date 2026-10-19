"""Tests de aislamiento multiempresa (multi-tenant).

Verifica que un Admin General de una organizacion NO ve ni opera datos de otra:
usuarios, sucursales, promociones y configuraciones quedan aislados por
`organization_id`.

Ademas cubre los P1 de la auditoria multi-org: reservas (IDOR cross-org),
cobro de estadias (`process_payment`), validacion de la sucursal al crear/editar
reservas manuales y los flujos de acceso fisico (ALPR/QR/manual) con el
gate -> sede -> empresa derivado del binding del nodo.
"""
import datetime
import uuid

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.config import settings
from core.database import Base, get_db
from core.limiter import limiter
from core.security import get_password_hash
from main import app
from schemas.parking import PlateValidation, QRValidation
from services.access_service import AccessService


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


def _crear_org(TestSession, nombre, es_principal=False):
    db = TestSession()
    org = models.Organization(nombre=nombre, es_principal=es_principal, activa=True)
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


def _branch_id(TestSession, nombre, organization_id):
    db = TestSession()
    try:
        b = db.query(models.ParkingBranch).filter(
            models.ParkingBranch.nombre == nombre,
            models.ParkingBranch.organization_id == organization_id,
        ).first()
        return b.id if b else None
    finally:
        db.close()


def _crear_access_log(TestSession, branch_id, monto=None, patente="AB123CD", con_salida=False):
    db = TestSession()
    ahora = datetime.datetime.now()
    db.add(models.AccessLog(
        patente_detectada=patente, normalized_patente=patente, tipo_evento="ENTRADA",
        tipo_vehiculo="Auto", fecha_hora=ahora - datetime.timedelta(hours=1),
        fecha_pago=ahora if monto is not None else None,
        pago_confirmado=monto is not None, metodo_pago="CAJA" if monto is not None else None,
        costo_estadia=monto or 0.0, sucursal_id=branch_id,
    ))
    if con_salida:
        db.add(models.AccessLog(
            patente_detectada=patente, normalized_patente=patente, tipo_evento="SALIDA",
            tipo_vehiculo="Auto", fecha_hora=ahora, sucursal_id=branch_id,
        ))
    db.commit()
    db.close()


def _crear_reserva(TestSession, branch_id, patente="CD456EF", monto=50.0):
    db = TestSession()
    ahora = datetime.datetime.now()
    db.add(models.Reservation(
        patente=patente, fecha_inicio=(ahora + datetime.timedelta(hours=1)).isoformat(),
        fecha_fin=(ahora + datetime.timedelta(hours=2)).isoformat(), monto_total=monto,
        estado_pago="Pagado", estado_reserva="Activa", tipo_estadia="hora",
        tipo_vehiculo="Auto", sucursal_id=branch_id,
    ))
    db.commit()
    db.close()


def _crear_ticket(TestSession, user_id, branch_id, estado="Pendiente"):
    db = TestSession()
    db.add(models.SupportTicket(
        user_id=user_id, categoria="otro", sucursal_id=branch_id,
        asunto="Consulta", mensaje="Necesito ayuda", estado=estado,
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


def test_financial_summary_aislado_por_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_usuario(TS, "admin", email_b, org_b)
    _crear_branch(TS, "SEDE A", org_a)
    branch_a = _branch_id(TS, "SEDE A", org_a)
    _crear_access_log(TS, branch_a, monto=1000.0)

    res_a = tc.get("/v1/reports/financial-summary", headers=_headers(tc, email_a))
    assert res_a.status_code == 200, res_a.text
    assert res_a.json()["total_recaudado"] == 1000.0

    res_b = tc.get("/v1/reports/financial-summary", headers=_headers(tc, email_b))
    assert res_b.status_code == 200, res_b.text
    assert res_b.json()["total_recaudado"] == 0.0


def test_current_occupancy_aislado_por_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_usuario(TS, "admin", email_b, org_b)
    _crear_branch(TS, "SEDE A", org_a)
    branch_a = _branch_id(TS, "SEDE A", org_a)
    _crear_access_log(TS, branch_a, patente="AA111AA")

    res_a = tc.get("/v1/parking/current-occupancy", headers=_headers(tc, email_a))
    assert res_a.status_code == 200, res_a.text
    assert [v["patente"] for v in res_a.json()] == ["AA111AA"]

    res_b = tc.get("/v1/parking/current-occupancy", headers=_headers(tc, email_b))
    assert res_b.status_code == 200, res_b.text
    assert res_b.json() == []


def test_support_pending_count_aislado_por_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    email_cli = f"cli_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_usuario(TS, "admin", email_b, org_b)
    _crear_usuario(TS, "user", email_cli, org_a)
    _crear_branch(TS, "SEDE A", org_a)
    branch_a = _branch_id(TS, "SEDE A", org_a)

    db = TS()
    try:
        cli = db.query(models.User).filter(models.User.email == email_cli).first()
        cli_id = cli.id
    finally:
        db.close()
    _crear_ticket(TS, cli_id, branch_a)

    res_a = tc.get("/v1/admin/support-tickets/pending-count", headers=_headers(tc, email_a))
    assert res_a.status_code == 200, res_a.text
    assert res_a.json()["count"] == 1

    res_b = tc.get("/v1/admin/support-tickets/pending-count", headers=_headers(tc, email_b))
    assert res_b.status_code == 200, res_b.text
    assert res_b.json()["count"] == 0


def test_reservas_admin_aisladas_por_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_usuario(TS, "admin", email_b, org_b)
    _crear_branch(TS, "SEDE A", org_a)
    branch_a = _branch_id(TS, "SEDE A", org_a)
    _crear_reserva(TS, branch_a, patente="AA111AA")

    res_a = tc.get("/v1/admin/reservations", headers=_headers(tc, email_a))
    assert res_a.status_code == 200, res_a.text
    assert [r["patente"] for r in res_a.json()] == ["AA111AA"]

    res_b = tc.get("/v1/admin/reservations", headers=_headers(tc, email_b))
    assert res_b.status_code == 200, res_b.text
    assert res_b.json() == []


def test_camaras_admin_aisladas_por_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_usuario(TS, "admin", email_b, org_b)
    _crear_branch(TS, "SEDE A", org_a)
    branch_a = _branch_id(TS, "SEDE A", org_a)

    db = TS()
    try:
        db.add(models.ParkingCamera(nombre="Cam A", tipo="ENTRADA", source="rtsp://a",
                                    sucursal_id=branch_a, activa=True))
        db.commit()
    finally:
        db.close()

    res_a = tc.get("/v1/system/cameras", headers=_headers(tc, email_a))
    assert res_a.status_code == 200, res_a.text
    assert [c["nombre"] for c in res_a.json()] == ["Cam A"]

    res_b = tc.get("/v1/system/cameras", headers=_headers(tc, email_b))
    assert res_b.status_code == 200, res_b.text
    assert res_b.json() == []


def _user_id(TestSession, email):
    db = TestSession()
    try:
        u = db.query(models.User).filter(models.User.email == email).first()
        return u.id if u else None
    finally:
        db.close()


def test_admin_no_puede_editar_usuario_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"cli_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_usuario(TS, "user", email_b, org_b)
    user_b = _user_id(TS, email_b)

    res = tc.patch(
        f"/v1/admin/users/{user_b}",
        headers=_headers(tc, email_a),
        json={"nombre": "Hackeado"},
    )
    assert res.status_code == 403, res.text


def test_admin_no_puede_operar_sucursal_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_branch(TS, "SEDE B", org_b)
    branch_b = _branch_id(TS, "SEDE B", org_b)

    res = tc.post(f"/v1/admin/branches/{branch_b}/toggle", headers=_headers(tc, email_a))
    assert res.status_code == 403, res.text


def test_admin_no_puede_operar_camara_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_branch(TS, "SEDE B", org_b)
    branch_b = _branch_id(TS, "SEDE B", org_b)

    db = TS()
    try:
        cam = models.ParkingCamera(nombre="Cam B", tipo="ENTRADA", source="rtsp://b",
                                   sucursal_id=branch_b, activa=True)
        db.add(cam)
        db.commit()
        db.refresh(cam)
        cam_b = cam.id
    finally:
        db.close()

    res = tc.put(
        f"/v1/system/cameras/{cam_b}",
        headers=_headers(tc, email_a),
        json={"nombre": "Hack", "tipo": "ENTRADA", "source": "rtsp://x", "activa": True},
    )
    assert res.status_code == 403, res.text


def test_super_admin_ve_usuarios_de_otra_organizacion(client):
    tc, TS = client
    org_principal = _crear_org(TS, "Org Principal", es_principal=True)
    org_b = _crear_org(TS, "Org B")
    email_super = f"super_{uuid.uuid4().hex[:8]}@test.com"
    email_cli_b = f"cli_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_super, org_principal)
    _crear_usuario(TS, "user", email_cli_b, org_b)

    res = tc.get("/v1/admin/users", headers=_headers(tc, email_super))
    assert res.status_code == 200, res.text
    emails = {u["email"] for u in res.json()}
    assert email_cli_b in emails


def test_super_admin_puede_editar_usuario_de_otra_organizacion(client):
    tc, TS = client
    org_principal = _crear_org(TS, "Org Principal", es_principal=True)
    org_b = _crear_org(TS, "Org B")
    email_super = f"super_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"cli_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_super, org_principal)
    _crear_usuario(TS, "user", email_b, org_b)
    user_b = _user_id(TS, email_b)

    res = tc.patch(
        f"/v1/admin/users/{user_b}",
        headers=_headers(tc, email_super),
        json={"nombre": "Gestionado"},
    )
    assert res.status_code == 200, res.text


def test_super_admin_puede_borrar_admin_de_otra_organizacion(client):
    tc, TS = client
    org_principal = _crear_org(TS, "Org Principal", es_principal=True)
    org_b = _crear_org(TS, "Org B")
    email_super = f"super_{uuid.uuid4().hex[:8]}@test.com"
    email_admin_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_super, org_principal)
    _crear_usuario(TS, "admin", email_admin_b, org_b)
    admin_b = _user_id(TS, email_admin_b)

    res = tc.delete(f"/v1/admin/users/{admin_b}", headers=_headers(tc, email_super))
    assert res.status_code == 200, res.text

    db = TS()
    try:
        borrado = db.query(models.User).filter(models.User.id == admin_b).first()
        assert borrado is not None
        assert borrado.is_deleted is True
        assert borrado.email.startswith("eliminado-")
    finally:
        db.close()


def test_admin_no_principal_no_puede_borrar_admin_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    email_admin_b = f"admin_b_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_usuario(TS, "admin", email_admin_b, org_b)
    admin_b = _user_id(TS, email_admin_b)

    res = tc.delete(f"/v1/admin/users/{admin_b}", headers=_headers(tc, email_a))
    assert res.status_code == 403, res.text


# ---------------------------------------------------------------------------
# RESERVAS: IDOR cross-org (P1)
# ---------------------------------------------------------------------------

def _crear_reserva_rango(TestSession, branch_id, patente, inicio, fin, origen="cliente"):
    """Reserva en una sede concreta devolviendo su id."""
    db = TestSession()
    try:
        res = models.Reservation(
            patente=patente, fecha_inicio=inicio, fecha_fin=fin, monto_total=50.0,
            estado_pago="Pagado", estado_reserva="Activa", tipo_estadia="hora",
            tipo_vehiculo="Auto", sucursal_id=branch_id, origen=origen,
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res.id
    finally:
        db.close()


def _payload_reserva(sucursal_nombre, patente="AB123CD"):
    ahora = datetime.datetime.now()
    return {
        "patente": patente,
        "fecha_inicio": (ahora + datetime.timedelta(hours=1)).isoformat(),
        "fecha_fin": (ahora + datetime.timedelta(hours=2)).isoformat(),
        "sucursal_nombre": sucursal_nombre,
        "tipo_estadia": "hora",
        "tipo_vehiculo": "Auto",
    }


def test_admin_no_puede_editar_reserva_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_branch(TS, "SEDE A", org_a)
    _crear_branch(TS, "SEDE B", org_b)
    branch_b = _branch_id(TS, "SEDE B", org_b)
    ahora = datetime.datetime.now()
    res_b = _crear_reserva_rango(TS, branch_b, "AB123CD",
                                 (ahora + datetime.timedelta(hours=1)).isoformat(),
                                 (ahora + datetime.timedelta(hours=2)).isoformat())

    out = tc.put(f"/v1/admin/reservations/{res_b}", headers=_headers(tc, email_a),
                 json=_payload_reserva("SEDE B"))
    assert out.status_code == 403, out.text


def test_admin_no_puede_confirmar_pago_de_reserva_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_branch(TS, "SEDE A", org_a)
    _crear_branch(TS, "SEDE B", org_b)
    branch_b = _branch_id(TS, "SEDE B", org_b)
    ahora = datetime.datetime.now()
    res_b = _crear_reserva_rango(TS, branch_b, "CD345EF",
                                 (ahora + datetime.timedelta(hours=1)).isoformat(),
                                 (ahora + datetime.timedelta(hours=2)).isoformat())

    out = tc.post(f"/v1/admin/reservations/{res_b}/confirm-payment",
                  headers=_headers(tc, email_a), json={"metodo_pago": "Caja"})
    assert out.status_code == 403, out.text


def test_admin_no_puede_crear_reserva_en_sucursal_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_branch(TS, "SEDE B", org_b)

    out = tc.post("/v1/admin/reservations", headers=_headers(tc, email_a),
                  json=_payload_reserva("SEDE B"))
    assert out.status_code == 403, out.text

    # Sede que no pertenece a ninguna empresa: 404 (fail-closed, no la inventa).
    out_fantasma = tc.post("/v1/admin/reservations", headers=_headers(tc, email_a),
                           json=_payload_reserva("SEDE FANTASMA"))
    assert out_fantasma.status_code == 404, out_fantasma.text


def test_admin_no_puede_mover_reserva_propia_a_sucursal_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_branch(TS, "SEDE A", org_a)
    _crear_branch(TS, "SEDE B", org_b)
    branch_a = _branch_id(TS, "SEDE A", org_a)
    ahora = datetime.datetime.now()
    res_a = _crear_reserva_rango(TS, branch_a, "EF567GH",
                                 (ahora + datetime.timedelta(hours=1)).isoformat(),
                                 (ahora + datetime.timedelta(hours=2)).isoformat(),
                                 origen="manual")

    out = tc.put(f"/v1/admin/reservations/{res_a}", headers=_headers(tc, email_a),
                 json=_payload_reserva("SEDE B"))
    assert out.status_code == 403, out.text


def test_admin_sin_organizacion_no_opera_reservas_con_multitenant(client):
    """Fail-closed: con multi-tenant activo no se puede operar sin organizacion."""
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_sin_org = f"admin_sinorg_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_sin_org, None)
    _crear_branch(TS, "SEDE A", org_a)
    branch_a = _branch_id(TS, "SEDE A", org_a)
    ahora = datetime.datetime.now()
    res_a = _crear_reserva_rango(TS, branch_a, "IJ789KL",
                                 (ahora + datetime.timedelta(hours=1)).isoformat(),
                                 (ahora + datetime.timedelta(hours=2)).isoformat())

    out = tc.put(f"/v1/admin/reservations/{res_a}", headers=_headers(tc, email_sin_org),
                 json=_payload_reserva("SEDE A"))
    assert out.status_code == 403, out.text
    assert "organización" in out.json()["detail"]


# ---------------------------------------------------------------------------
# COBRO DE ESTADIAS (process_payment acotado a la empresa/sede del operador)
# ---------------------------------------------------------------------------

def _crear_entrada_en(TestSession, branch_id, patente, sucursal_nombre, hace_horas=2):
    db = TestSession()
    try:
        db.add(models.Settings(clave="precio_hora", valor=1500.0, sucursal=sucursal_nombre))
        db.add(models.Settings(clave="precio_30min", valor=750.0, sucursal=sucursal_nombre))
        db.add(models.AccessLog(
            patente_detectada=patente, normalized_patente=patente, tipo_evento="ENTRADA",
            tipo_vehiculo="Auto",
            fecha_hora=(datetime.datetime.now() - datetime.timedelta(hours=hace_horas)).isoformat(),
            pago_confirmado=False, sucursal_id=branch_id,
        ))
        db.commit()
    finally:
        db.close()


def test_pay_stay_no_cobra_estadia_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_branch(TS, "SEDE A", org_a)
    _crear_branch(TS, "SEDE B", org_b)
    branch_b = _branch_id(TS, "SEDE B", org_b)
    _crear_entrada_en(TS, branch_b, "MN345OP", "SEDE B")

    out = tc.post("/v1/access/pay-stay?plate=MN345OP", headers=_headers(tc, email_a))
    assert out.status_code == 400, out.text
    assert "pendientes" in out.json()["detail"]

    db = TS()
    try:
        log = db.query(models.AccessLog).filter(models.AccessLog.patente_detectada == "MN345OP").first()
        assert log.pago_confirmado is False
    finally:
        db.close()


def test_pay_stay_cobra_estadia_de_su_propia_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    email_a = f"admin_a_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "admin", email_a, org_a)
    _crear_branch(TS, "SEDE A", org_a)
    _crear_branch(TS, "SEDE B", org_b)
    branch_a = _branch_id(TS, "SEDE A", org_a)
    _crear_entrada_en(TS, branch_a, "QR678ST", "SEDE A")

    out = tc.post("/v1/access/pay-stay?plate=QR678ST", headers=_headers(tc, email_a))
    assert out.status_code == 200, out.text
    assert out.json()["status"] == "ok"
    assert out.json()["monto_cobrado"] > 0

    db = TS()
    try:
        log = db.query(models.AccessLog).filter(models.AccessLog.patente_detectada == "QR678ST").first()
        assert log.pago_confirmado is True
    finally:
        db.close()


def test_pay_stay_staff_sin_organizacion_es_403_con_multitenant(client):
    """Fail-closed: sin organizacion resoluble no se cobra nada con multi-tenant activo."""
    tc, TS = client
    _crear_org(TS, "Org A")
    _crear_org(TS, "Org B")
    email_staff = f"staff_sinorg_{uuid.uuid4().hex[:8]}@test.com"
    _crear_usuario(TS, "staff", email_staff, None)

    out = tc.post("/v1/access/pay-stay?plate=UV123WX", headers=_headers(tc, email_staff))
    assert out.status_code == 403, out.text
    assert "organización" in out.json()["detail"]


# ---------------------------------------------------------------------------
# ACCESO FISICO: gate -> sede -> empresa (binding del nodo ALPR)
# ---------------------------------------------------------------------------

def test_alpr_gate_de_otra_organizacion_se_rechaza_con_binding(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    _crear_branch(TS, "SEDE A", org_a)
    _crear_branch(TS, "SEDE B", org_b)

    db = TS()
    try:
        out = AccessService.validate_plate(
            db, PlateValidation(plate="AB123CD", gate_id="SEDE B_ENTRADA"),
            organization_id=org_a,
        )
        assert out["status"] == "denied"
        assert "organización" in out["message"]
        assert db.query(models.AccessLog).count() == 0
    finally:
        db.close()


def test_alpr_no_ve_estadia_de_otra_organizacion_en_sede_homonima(client):
    """Sedes con el mismo nombre en dos empresas: el binding del nodo acota los logs."""
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    _crear_branch(TS, "SEDE X", org_a)
    _crear_branch(TS, "SEDE X", org_b)
    branch_b = _branch_id(TS, "SEDE X", org_b)
    # El vehiculo esta dentro en la SEDE X de la ORGANIZACION B.
    _crear_access_log(TS, branch_b, patente="AB123CD")

    db = TS()
    try:
        out = AccessService.validate_plate(
            db, PlateValidation(plate="AB123CD", gate_id="SEDE X_ENTRADA"),
            organization_id=org_a,
        )
        assert out["status"] == "allowed", out
        # Se registro la entrada en la sede de la org A (no la reutilizo la de org B).
        entradas = db.query(models.AccessLog).filter(
            models.AccessLog.normalized_patente == "AB123CD",
            models.AccessLog.tipo_evento == "ENTRADA",
        ).count()
        assert entradas == 2
    finally:
        db.close()


def test_alpr_qr_de_reserva_de_otra_organizacion_se_rechaza(client):
    """Sede homonima en dos empresas: el QR de org B no abre el gate de org A."""
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    _crear_branch(TS, "SEDE X", org_a)
    _crear_branch(TS, "SEDE X", org_b)
    branch_b = _branch_id(TS, "SEDE X", org_b)
    ahora = datetime.datetime.now()
    res_b = _crear_reserva_rango(TS, branch_b, "CD345EF",
                                 (ahora - datetime.timedelta(minutes=30)).isoformat(),
                                 (ahora + datetime.timedelta(hours=1)).isoformat())

    db = TS()
    try:
        out = AccessService.validate_qr(
            db,
            QRValidation(qr_data=f"AUTOPASS|id:{res_b}|patente:CD345EF",
                         gate_id="SEDE X_ENTRADA"),
            organization_id=org_a,
        )
        assert out["status"] == "denied"
        assert out["message"] == "Esta reserva no pertenece a esta organización"
        assert db.query(models.AccessLog).count() == 0
    finally:
        db.close()


def test_alpr_qr_de_reserva_propia_se_acepta(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    _crear_branch(TS, "SEDE A", org_a)
    _crear_branch(TS, "SEDE B", org_b)
    branch_a = _branch_id(TS, "SEDE A", org_a)
    ahora = datetime.datetime.now()
    res_a = _crear_reserva_rango(TS, branch_a, "FG567HI",
                                 (ahora - datetime.timedelta(minutes=30)).isoformat(),
                                 (ahora + datetime.timedelta(hours=1)).isoformat())

    db = TS()
    try:
        out = AccessService.validate_qr(
            db,
            QRValidation(qr_data=f"AUTOPASS|id:{res_a}|patente:FG567HI",
                         gate_id="SEDE A_ENTRADA"),
            organization_id=org_a,
        )
        assert out["status"] == "allowed", out
    finally:
        db.close()


def test_manual_entry_no_reutiliza_estadia_de_otra_organizacion(client):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    org_b = _crear_org(TS, "Org B")
    _crear_branch(TS, "SEDE X", org_a)
    _crear_branch(TS, "SEDE X", org_b)
    branch_b = _branch_id(TS, "SEDE X", org_b)
    # Ingreso registrado en la SEDE X de la ORGANIZACION B.
    _crear_access_log(TS, branch_b, patente="JK789MN")

    db = TS()
    try:
        out_a = AccessService.manual_entry(db, "JK789MN", "SEDE X", organization_id=org_a)
        assert out_a["status"] == "ok"
        assert "ya figura" not in out_a["message"]
        entradas = db.query(models.AccessLog).filter(
            models.AccessLog.normalized_patente == "JK789MN",
            models.AccessLog.tipo_evento == "ENTRADA",
        ).count()
        assert entradas == 2

        # La empresa dueña de la sede donde esta adentro si lo ve como ingresado.
        out_b = AccessService.manual_entry(db, "JK789MN", "SEDE X", organization_id=org_b)
        assert out_b["status"] == "ok"
        assert "ya figura" in out_b["message"]
    finally:
        db.close()


def test_ruta_alpr_pasa_el_binding_de_organizacion(client, monkeypatch):
    tc, TS = client
    org_a = _crear_org(TS, "Org A")
    capturado = {}

    def _stub(db, data, request, organization_id=None):
        capturado["organization_id"] = organization_id
        return {"status": "ok", "message": "stub"}

    monkeypatch.setattr(AccessService, "validate_plate", staticmethod(_stub))
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "s3cret")
    monkeypatch.setattr(settings, "ALPR_NODE_ORG_ID", org_a)

    out = tc.post("/v1/access/validate-plate",
                  json={"plate": "AB123CD", "gate_id": "SEDE A_ENTRADA"},
                  headers={"X-Node-Secret": "s3cret"})
    assert out.status_code == 200, out.text
    assert capturado["organization_id"] == org_a


def _fake_request(host):
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/access/validate-plate",
        "query_string": b"",
        "headers": [],
        "client": (host, 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_require_alpr_node_org_devuelve_el_binding(monkeypatch):
    from core.alpr_security import require_alpr_node_org

    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "")
    req_local = _fake_request("127.0.0.1")

    monkeypatch.setattr(settings, "ALPR_NODE_ORG_ID", 0)
    assert require_alpr_node_org(req_local) is None

    monkeypatch.setattr(settings, "ALPR_NODE_ORG_ID", 7)
    assert require_alpr_node_org(req_local) == 7

    with pytest.raises(HTTPException) as exc:
        require_alpr_node_org(_fake_request("200.100.10.1"))
    assert exc.value.status_code == 403
