"""Tests de los 5 P1 de aislamiento multiempresa de la ultima tanda.

Cubre: lookup de patente acotado a la empresa del operador, descuentos de caja
acotados a la empresa del usuario, validacion del vinculo usuario-patente,
reports fail-closed (servicio y `_branch_filter`) y canje de promociones de otra
empresa. Un solo tenant (<2 organizaciones) conserva el comportamiento historico.
"""
import datetime
import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from models.enums import PaymentStatus, ReservationStatus
from repositories.report_repository import ReportRepository
from services.report_service import ReportService
from services.reservation_service import ReservationService


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def _org(db, nombre, es_principal=False):
    org = models.Organization(nombre=nombre, es_principal=es_principal, activa=True)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org.id


def _branch(db, nombre, organization_id):
    b = models.ParkingBranch(nombre=nombre, activa=True, organization_id=organization_id,
                             direccion="Calle 1", telefono="1122334455", horario="09:00 a 18:00")
    db.add(b)
    db.commit()
    db.refresh(b)
    return b.id


def _user(db, rol="admin", organization_id=None, sucursal=None, puntos=1000):
    u = models.User(
        nombre="Nombre", apellido="Apellido", dni=str(uuid.uuid4().int)[:8],
        telefono="1122334455", email=f"{uuid.uuid4().hex[:8]}@test.com",
        password_hash="x", rol=rol, organization_id=organization_id, sucursal=sucursal,
        saldo=0.0, puntos_acumulados=puntos, is_blocked=False, is_deleted=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _vehicle(db, user, patente, tipo="Auto"):
    v = models.Vehicle(user_id=user.id, patente=patente, tipo=tipo)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def _ticket_descuento(db, user, porc=10):
    t = models.RedemptionTicket(
        user_id=user.id, codigo=uuid.uuid4().hex[:16].upper(),
        titulo="Descuento 10%", descripcion="10%", tipo_canje="descuento_reserva",
        valor_descuento=porc, estado="VIGENTE", qr_data="AUTOPASS_REDEMPTION|ID:X",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _promo(db, organization_id, titulo="Promo"):
    p = models.Promotion(titulo=titulo, descripcion="Beneficio", costo_puntos=10,
                         organization_id=organization_id, activa=True, tipo_canje="voucher")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _log_pagado(db, branch_id, monto, patente="AB123CD"):
    db.add(models.AccessLog(
        patente_detectada=patente, normalized_patente=patente, tipo_evento="ENTRADA",
        tipo_vehiculo="Auto", fecha_hora=datetime.datetime.now().isoformat(),
        fecha_pago=datetime.datetime.now().isoformat(), pago_confirmado=True,
        metodo_pago="CAJA", costo_estadia=monto, sucursal_id=branch_id,
    ))
    db.commit()


# ---------------------------------------------------------------------------
# P1.1 lookup_patente acotado a la empresa del operador
# ---------------------------------------------------------------------------

def test_lookup_patente_no_cruza_organizacion(db):
    org_a = _org(db, "Org A")
    org_b = _org(db, "Org B")
    staff_a = _user(db, organization_id=org_a)
    staff_b = _user(db, organization_id=org_b)
    # Dueno y vehiculo en la org B.
    dueno_b = _user(db, rol="user", organization_id=org_b)
    _vehicle(db, dueno_b, "AB 123 CD")

    assert ReservationService.lookup_patente(db, "AB123CD", staff_a)["encontrado"] is False
    encontrado = ReservationService.lookup_patente(db, "AB123CD", staff_b)
    assert encontrado["encontrado"] is True
    assert encontrado["user_id"] == dueno_b.id


def test_lookup_patente_fail_closed_sin_organizacion(db):
    _org(db, "Org A")
    _org(db, "Org B")
    staff_sin_org = _user(db, organization_id=None)
    dueno = _user(db, rol="user", organization_id=_org(db, "Org C"))
    _vehicle(db, dueno, "ZZ999ZZ")

    assert ReservationService.lookup_patente(db, "ZZ999ZZ", staff_sin_org)["encontrado"] is False


def test_lookup_patente_single_tenant_sin_romper(db):
    _org(db, "Unica")
    staff = _user(db, organization_id=None)
    dueno = _user(db, rol="user", organization_id=None)
    _vehicle(db, dueno, "AA111AA")

    assert ReservationService.lookup_patente(db, "AA111AA", staff)["encontrado"] is True


# ---------------------------------------------------------------------------
# P1.2 get_admin_available_redemptions acotado a la empresa del usuario
# ---------------------------------------------------------------------------

def test_admin_redemptions_no_devuelve_de_otra_organizacion(db):
    org_a = _org(db, "Org A")
    org_b = _org(db, "Org B")
    staff_a = _user(db, organization_id=org_a)
    staff_b = _user(db, organization_id=org_b)
    user_b = _user(db, rol="user", organization_id=org_b)
    ticket = _ticket_descuento(db, user_b)

    with pytest.raises(HTTPException) as exc:
        ReservationService.get_admin_available_redemptions(db, user_b.id, staff_a)
    assert exc.value.status_code == 403

    propios = ReservationService.get_admin_available_redemptions(db, user_b.id, staff_b)
    assert [t.id for t in propios] == [ticket.id]


def test_admin_redemptions_fail_closed_sin_organizacion(db):
    org_a = _org(db, "Org A")
    _org(db, "Org B")
    staff_sin_org = _user(db, organization_id=None)
    user_a = _user(db, rol="user", organization_id=org_a)
    _ticket_descuento(db, user_a)

    with pytest.raises(HTTPException) as exc:
        ReservationService.get_admin_available_redemptions(db, user_a.id, staff_sin_org)
    assert exc.value.status_code == 403

    assert ReservationService.get_admin_available_redemptions(db, None, staff_sin_org) == []


# ---------------------------------------------------------------------------
# P1.3 validate_manual_vinculacion exige alcance de la empresa
# ---------------------------------------------------------------------------

def test_validate_manual_vinculacion_rechaza_usuario_de_otra_organizacion(db):
    org_a = _org(db, "Org A")
    org_b = _org(db, "Org B")
    staff_a = _user(db, organization_id=org_a)
    staff_b = _user(db, organization_id=org_b)
    user_b = _user(db, rol="user", organization_id=org_b)
    _vehicle(db, user_b, "AB 123 CD")

    with pytest.raises(HTTPException) as exc:
        ReservationService.validate_manual_vinculacion(db, user_b.id, "AB123CD", staff_a)
    assert exc.value.status_code == 403

    usuario, vehiculo = ReservationService.validate_manual_vinculacion(db, user_b.id, "AB123CD", staff_b)
    assert usuario.id == user_b.id
    assert vehiculo is not None


def test_validate_manual_vinculacion_fail_closed_sin_organizacion(db):
    _org(db, "Org A")
    _org(db, "Org B")
    staff_sin_org = _user(db, organization_id=None)
    user_a = _user(db, rol="user", organization_id=None)
    _vehicle(db, user_a, "AB 123 CD")

    with pytest.raises(HTTPException) as exc:
        ReservationService.validate_manual_vinculacion(db, user_a.id, "AB123CD", staff_sin_org)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# P1.4 reports: org resuelta siempre + _branch_filter fail-closed
# ---------------------------------------------------------------------------

def test_branch_filter_fail_closed_sin_organizacion(db):
    org_a = _org(db, "Org A")
    _org(db, "Org B")
    branch_a = _branch(db, "SEDE A", org_a)
    _log_pagado(db, branch_a, monto=1000.0)

    total, count = ReportRepository.paid_logs_aggregate(db)
    assert count == 0
    assert (total or 0) == 0


def test_reports_sin_organizacion_fail_closed(db):
    _org(db, "Org A")
    _org(db, "Org B")
    staff_sin_org = _user(db, organization_id=None)

    with pytest.raises(HTTPException) as exc:
        ReportService.get_financial_summary(db, staff_sin_org)
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc2:
        ReportService.get_access_logs(db, staff_sin_org)
    assert exc2.value.status_code == 403


def test_reports_local_admin_no_ve_sede_homonima_de_otra_organizacion(db):
    org_a = _org(db, "Org A")
    org_b = _org(db, "Org B")
    branch_a = _branch(db, "SEDE X", org_a)
    branch_b = _branch(db, "SEDE X", org_b)
    _log_pagado(db, branch_a, monto=100.0, patente="AA111AA")
    _log_pagado(db, branch_b, monto=999.0, patente="BB222BB")
    admin_a = _user(db, rol="local_admin", organization_id=org_a, sucursal="SEDE X")

    resumen = ReportService.get_financial_summary(db, admin_a)
    assert resumen["total_recaudado"] == Decimal("100.00")


def test_reports_admin_ve_su_organizacion_con_org_resuelta(db):
    org_a = _org(db, "Org A")
    org_b = _org(db, "Org B")
    branch_a = _branch(db, "SEDE A", org_a)
    branch_b = _branch(db, "SEDE B", org_b)
    _log_pagado(db, branch_a, monto=100.0, patente="AA111AA")
    _log_pagado(db, branch_b, monto=999.0, patente="BB222BB")
    admin_a = _user(db, rol="admin", organization_id=org_a)

    resumen = ReportService.get_financial_summary(db, admin_a)
    assert resumen["total_recaudado"] == 100.0


# ---------------------------------------------------------------------------
# P1.5 canje de promociones de otra empresa
# ---------------------------------------------------------------------------

def test_redeem_promo_de_otra_organizacion_da_404(db):
    from routes.user.fidelization import redeem_points

    org_a = _org(db, "Org A")
    org_b = _org(db, "Org B")
    user_a = _user(db, rol="user", organization_id=org_a, puntos=1000)
    promo_b = _promo(db, org_b, titulo="Ajena")

    with pytest.raises(HTTPException) as exc:
        redeem_points(promo_b.id, db, user_a)
    assert exc.value.status_code == 404


def test_redeem_promo_global_y_propia_se_permiten(db):
    from routes.user.fidelization import redeem_points

    org_a = _org(db, "Org A")
    org_b = _org(db, "Org B")
    user_a = _user(db, rol="user", organization_id=org_a, puntos=1000)
    promo_global = _promo(db, None, titulo="Global")
    promo_a = _promo(db, org_a, titulo="Propia")

    assert redeem_points(promo_global.id, db, user_a)["status"] == "ok"
    assert redeem_points(promo_a.id, db, user_a)["status"] == "ok"
