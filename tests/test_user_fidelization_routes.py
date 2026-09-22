"""Ronda #22 - routes/user/fidelization.py (47% -> 88%, objetivo >60% LOGRAADO).
Fidelización: catálogo de beneficios, canje de puntos (voucher / descuento_reserva),
listado de tickets con fallback de ubicación (promo -> sucursal -> branch) y
cancelación con devolución de puntos. Endpoints (prefijo /v1/user):

  GET  /promotions                        -> lista beneficios vigentes (filtr. por sede)
  POST /redeem/{promo_id}                 -> canjea puntos (voucher => QR 30d, descuento_reserva => %)
  GET  /redemption-tickets                -> tickets del usuario + enriquecimiento ubicación
  GET  /redemptions/available             -> descuentos de reserva vigentes
  POST /redemptions/{ticket_id}/cancel    -> cancela ticket y devuelve puntos
  GET  /points-history                    -> historial de movimientos de puntos
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

FIDEL_BASE = "/v1/user"


class FakeUser:
    """USUARIO LOGUEADO FINGIDO PARA LOS ENDPOINTS DE FIDELIZACION."""
    def __init__(self, user_id=1, sucursal="Centro", puntos_acumulados=1500):
        self.id = user_id
        self.sucursal = sucursal
        self.puntos_acumulados = puntos_acumulados


CURRENT = {"user": FakeUser()}


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
    CURRENT["user"] = FakeUser()


# ---------------------------------------------------------------------------
# helpers de seed
# ---------------------------------------------------------------------------

def _seed_branch(db_factory, nombre="Centro", direccion="Av. Principal 123",
                 lat=1.0, lon=1.0):
    db = db_factory()
    b = models.ParkingBranch(
        nombre=nombre, direccion=direccion, latitude=lat, longitude=lon,
        horario="24hs"
    )
    db.add(b)
    db.commit()
    bid = b.id
    db.close()
    return bid


def _seed_user(db_factory, user_id=2, puntos_acumulados=1500, sucursal="Centro"):
    db = db_factory()
    u = models.User(
        id=user_id, nombre="Cliente", apellido="Fid",
        email=f"fid{user_id}@test.com", password_hash="x", rol="user",
        sucursal=sucursal, puntos_acumulados=puntos_acumulados
    )
    db.add(u)
    db.commit()
    db.close()


def _seed_promo(db_factory, titulo="Voucher Lavado", costo_puntos=100,
                sucursal="Centro", tipo="voucher", valor=None, direccion=None,
                lat=None, lon=None, activa=True):
    """CREA UNA PROMOCION Y DEVUELVE SU ID.
    tipo: 'voucher' (QR 30 días) o 'descuento_reserva' (% aplicable a reserva)."""
    db = db_factory()
    p = models.Promotion(
        titulo=titulo, descripcion="Desc", costo_puntos=costo_puntos,
        sucursal=sucursal, activa=activa, tipo_canje=tipo,
        valor_descuento=valor, direccion=direccion, latitude=lat, longitude=lon
    )
    db.add(p)
    db.commit()
    pid = p.id
    db.close()
    return pid


def _seed_ticket(db_factory, user_id=1, promo_id=None, tipo="voucher",
                 estado="VIGENTE", sucursal="Centro", titulo="Voucher Lavado",
                 direccion=None, latitude=None, longitude=None, codigo=None):
    """CREA UN TICKET DE CANJE Y DEVUELVE SU ID."""
    db = db_factory()
    import uuid
    if codigo is None:
        codigo = uuid.uuid4().hex[:16].upper()
    t = models.RedemptionTicket(
        user_id=user_id, promotion_id=promo_id,
        codigo=codigo, titulo=titulo,
        tipo_canje=tipo, estado=estado, sucursal=sucursal,
        direccion=direccion, latitude=latitude, longitude=longitude,
        qr_data=f"AUTOPASS_REDEMPTION|ID:{codigo}"
    )
    db.add(t)
    db.commit()
    tid = t.id
    db.close()
    return tid


def _seed_points_log(db_factory, user_id=1, cantidad=100, motivo="Canje test",
                     fecha="2024-01-01T10:00:00"):
    db = db_factory()
    db.add(models.PointsLog(
        user_id=user_id, cantidad=cantidad, motivo=motivo, fecha=fecha
    ))
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# GET /promotions
# ---------------------------------------------------------------------------

def test_list_promotions(client):
    c, TestSession = client
    _seed_promo(TestSession, titulo="Voucher Lavado", tipo="voucher")
    _seed_promo(TestSession, titulo="Desc 10%", costo_puntos=80,
                tipo="descuento_reserva", valor=10)
    r = c.get(f"{FIDEL_BASE}/promotions")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 2
    titulos = {p["titulo"] for p in body}
    assert "Voucher Lavado" in titulos
    assert "Desc 10%" in titulos


def test_list_promotions_vacio(client):
    c, _ = client
    r = c.get(f"{FIDEL_BASE}/promotions")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# POST /redeem/{promo_id}  (canje de puntos)
# ---------------------------------------------------------------------------

def test_redeem_voucher_ok(client):
    c, db_factory = client
    _seed_user(db_factory, user_id=1)
    pid = _seed_promo(db_factory, titulo="Voucher Lavado", tipo="voucher")
    r = c.post(f"{FIDEL_BASE}/redeem/{pid}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    ticket = body["ticket"]
    assert ticket["tipo_canje"] == "voucher"
    assert "AUTOPASS_REDEMPTION|ID:" in ticket["qr_data"]
    assert ticket["codigo"] == ticket["qr_data"].split("ID:")[1].split("|TICKET:")[0]
    assert ticket["estado"] == "VIGENTE"


def test_redeem_promo_descuento_reserva_ok(client):
    c, TestSession = client
    _seed_user(TestSession, user_id=1)
    pid = _seed_promo(TestSession, titulo="Desc 10%", costo_puntos=100,
                      tipo="descuento_reserva", valor=10, direccion="Dirección propia")
    r = c.post(f"{FIDEL_BASE}/redeem/{pid}")
    assert r.status_code == 200
    ticket = r.json()["ticket"]
    assert ticket["tipo_canje"] == "descuento_reserva"
    assert ticket["valor_descuento"] == 10


def test_redeem_promo_sin_ubicacion_uso_direccion_sucursal(client):
    """PROMO SIN COORDENADAS -> FALLBACK A LA SUCURSAL (branch) EN _crear_ticket."""
    c, TestSession = client
    _seed_user(TestSession, user_id=1)
    _seed_branch(TestSession, nombre="Centro", direccion="Av. Sucursal 999",
                 lat=2.0, lon=2.0)
    pid = _seed_promo(TestSession, titulo="Sin Ubicación", tipo="voucher",
                      direccion=None, lat=None, lon=None, sucursal="Centro")
    r = c.post(f"{FIDEL_BASE}/redeem/{pid}")
    assert r.status_code == 200
    t = r.json()["ticket"]
    assert t["direccion"] == "Av. Sucursal 999"


def test_redeem_promo_no_encontrada(client):
    c, _ = client
    r = c.post(f"{FIDEL_BASE}/redeem/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Promoción no encontrada"


def test_redeem_promo_inactiva_no_encontrada(client):
    c, TestSession = client
    pid = _seed_promo(TestSession, titulo="Pronto", activa=False)
    r = c.post(f"{FIDEL_BASE}/redeem/{pid}")
    assert r.status_code == 404


def test_redeem_puntos_insuficientes(client):
    c, TestSession = client
    pid = _seed_promo(TestSession, titulo="Carísimo", costo_puntos=100)
    CURRENT["user"] = FakeUser(user_id=1, sucursal="Centro", puntos_acumulados=10)
    r = c.post(f"{FIDEL_BASE}/redeem/{pid}")
    assert r.status_code == 400
    assert r.json()["detail"] == "Puntos insuficientes"


# ---------------------------------------------------------------------------
# GET /redemption-tickets  (listado con enriquecimiento de ubicación)
# ---------------------------------------------------------------------------

def test_list_redemption_tickets(client):
    c, TestSession = client
    _seed_user(TestSession, user_id=1)
    pid = _seed_promo(TestSession, titulo="Voucher Antiguo", tipo="voucher")
    _seed_ticket(TestSession, user_id=1, promo_id=pid, tipo="voucher")
    _seed_ticket(TestSession, user_id=1, promo_id=pid, tipo="voucher")
    r = c.get(f"{FIDEL_BASE}/redemption-tickets")
    assert r.status_code == 200
    tickets = r.json()
    assert len(tickets) >= 2


def test_list_redemption_tickets_rellena_datos_por_promo(client):
    """TICKET SIN UBICACION PERO CON PROMO QUE SÍ LA DEFINE -> SE COMPLETA."""
    c, TestSession = client
    _seed_user(TestSession, user_id=1)
    pid = _seed_promo(TestSession, titulo="Con Dirección", tipo="voucher",
                      direccion="Calle Promo 456", lat=3.0, lon=3.0)
    _seed_ticket(TestSession, user_id=1, promo_id=pid, tipo="voucher")
    r = c.get(f"{FIDEL_BASE}/redemption-tickets")
    assert r.status_code == 200
    t = r.json()[0]
    assert t["direccion"] == "Calle Promo 456"


def test_list_redemption_tickets_sucursal_sin_promo(client):
    """TICKET SIN PROMO/BOLETA NI UBICACION -> FALLBACK A LA SUCURSAL (branch)."""
    c, TestSession = client
    _seed_user(TestSession, user_id=1)
    _seed_branch(TestSession, nombre="Centro", direccion="Av. Branch 123",
                 lat=4.0, lon=4.0)
    _seed_ticket(TestSession, user_id=1, promo_id=None, tipo="voucher",
                 sucursal="Centro")
    r = c.get(f"{FIDEL_BASE}/redemption-tickets")
    assert r.status_code == 200
    t = r.json()[0]
    assert t["direccion"] == "Av. Branch 123"


def test_list_redemption_tickets_vacio(client):
    c, _ = client
    r = c.get(f"{FIDEL_BASE}/redemption-tickets")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# GET /redemptions/available  (descuentos de reserva vigentes)
# ---------------------------------------------------------------------------

def test_available_redemptions(client):
    c, TestSession = client
    _seed_user(TestSession, user_id=1)
    pid = _seed_promo(TestSession, titulo="Desc 15%", costo_puntos=150,
                      tipo="descuento_reserva", valor=15, sucursal="Centro")
    _seed_ticket(TestSession, user_id=1, promo_id=pid, tipo="descuento_reserva",
                 estado="VIGENTE", titulo="Desc 15%")
    r = c.get(f"{FIDEL_BASE}/redemptions/available")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 1
    assert body[0]["tipo_canje"] == "descuento_reserva"


def test_available_redemptions_vacio(client):
    c, _ = client
    r = c.get(f"{FIDEL_BASE}/redemptions/available")
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# POST /redemptions/{ticket_id}/cancel  (cancelación + devolución de puntos)
# ---------------------------------------------------------------------------

def test_cancel_redemption_ticket_ok(client):
    c, TestSession = client
    _seed_user(TestSession, user_id=1, puntos_acumulados=1400)
    pid = _seed_promo(TestSession, titulo="Voucher", costo_puntos=100,
                      tipo="voucher")
    tid = _seed_ticket(TestSession, user_id=1, promo_id=pid, tipo="voucher",
                       estado="VIGENTE")
    r = c.post(f"{FIDEL_BASE}/redemptions/{tid}/cancel")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["puntos_devueltos"] == 100


def test_cancel_redemption_ticket_404(client):
    c, _ = client
    r = c.post(f"{FIDEL_BASE}/redemptions/99999/cancel")
    assert r.status_code == 404
    assert r.json()["detail"] == "Ticket no encontrado"


def test_cancel_redemption_ticket_no_vigente(client):
    c, TestSession = client
    pid = _seed_promo(TestSession, titulo="Usado", costo_puntos=100, tipo="voucher")
    tid = _seed_ticket(TestSession, user_id=1, promo_id=pid, tipo="voucher",
                       estado="USADO")
    r = c.post(f"{FIDEL_BASE}/redemptions/{tid}/cancel")
    assert r.status_code == 400
    assert r.json()["detail"] == "El ticket ya no se encuentra vigente"


# ---------------------------------------------------------------------------
# GET /points-history
# ---------------------------------------------------------------------------

def test_points_history(client):
    c, TestSession = client
    _seed_user(TestSession, user_id=1)
    _seed_points_log(TestSession, user_id=1, cantidad=100, motivo="Earned")
    _seed_points_log(TestSession, user_id=1, cantidad=-50, motivo="Canje")
    r = c.get(f"{FIDEL_BASE}/points-history")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["total_earned"] == 100
    assert body["total_redeemed"] == 50
    assert len(body["items"]) == 2


def test_points_history_vacio(client):
    c, _ = client
    r = c.get(f"{FIDEL_BASE}/points-history")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert len(body["items"]) == 0
