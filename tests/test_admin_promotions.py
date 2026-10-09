"""Tests ronda #18: routes/admin/promotions.py.

Cubre el CRUD completo de promociones con el rol real de local_manager: GET
(admin global ve todas, local_admin solo las de su sede, activa None normalizada
a True), POST (sucursal forzada para local_admin, tipo de canje con y sin
valor_descuento), toggle (404, 403 por sucursal, activación/desactivación),
PUT (404, 403, reasignación de sucursal solo para admin global) y DELETE (404,
403, desasociación de tickets antes del borrado).
"""
import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from core.security import get_current_user
from models.enums import UserRole

promos_mod = importlib.import_module("routes.admin.promotions")


class FakeUser:
    def __init__(self, rol=UserRole.ADMIN.value, sucursal=None):
        self.rol = rol
        self.sucursal = sucursal


CURRENT = {"user": FakeUser()}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(promos_mod.router)
    app.dependency_overrides[promos_mod.get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: CURRENT["user"]
    with TestClient(app) as c:
        yield c, TestSession
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _reset_user():
    yield
    CURRENT["user"] = FakeUser()


def _set_user(rol=UserRole.ADMIN, sucursal=None):
    value = rol.value if isinstance(rol, UserRole) else rol
    CURRENT["user"] = FakeUser(rol=value, sucursal=sucursal)


def _set_staff(sucursal=None):
    _set_user(rol=UserRole.STAFF, sucursal=sucursal)


def _seed_promo(db_factory, titulo="Beneficio", sucursal=None, activa=True, tipo="voucher", valor=None):
    db = db_factory()
    p = models.Promotion(
        titulo=titulo, descripcion="Desc", costo_puntos=100, sucursal=sucursal,
        activa=activa, tipo_canje=tipo, valor_descuento=valor,
    )
    db.add(p)
    db.commit()
    pid = p.id
    db.close()
    return pid


def _get_promo(db_factory, promo_id):
    db = db_factory()
    p = db.query(models.Promotion).filter(models.Promotion.id == promo_id).first()
    db.close()
    return p


def test_list_promotions_admin_global_ve_todas(client):
    c, db_factory = client
    _seed_promo(db_factory, "Global", sucursal=None)
    _seed_promo(db_factory, "Centro", sucursal="Centro")
    body = c.get("/promotions").json()
    assert len(body) == 2


def test_list_promotions_local_admin_solo_su_sede(client):
    c, db_factory = client
    _seed_promo(db_factory, "Centro", sucursal="Centro")
    _seed_promo(db_factory, "Norte", sucursal="Norte")
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    body = c.get("/promotions").json()
    assert len(body) == 1
    assert body[0]["titulo"] == "Centro"


def test_list_promotions_activa_none_se_normaliza_a_true(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Rara", sucursal=None, activa=None)
    db = db_factory()
    db.query(models.Promotion).filter(models.Promotion.id == pid).update(
        {models.Promotion.activa: None}
    )
    db.commit()
    db.close()
    body = c.get("/promotions").json()
    assert body[0]["activa"] is True


def test_list_promotions_staff_recibe_403(client):
    c, _ = client
    _set_staff()
    assert c.get("/promotions").status_code == 403


def test_create_promotion_admin_global_con_sucursal(client):
    c, db_factory = client
    resp = c.post("/promotions", json={
        "titulo": "2x1", "descripcion": "Promo", "costo_puntos": 50,
        "sucursal": "Centro", "tipo_canje": "voucher",
    })
    assert resp.status_code == 200
    assert resp.json()["message"] == "Promoción '2x1' creada para Centro"
    db = db_factory()
    p = db.query(models.Promotion).filter(models.Promotion.titulo == "2x1").first()
    db.close()
    assert p.sucursal == "Centro"
    assert p.tipo_canje == "voucher"
    assert p.valor_descuento is None


def test_create_promotion_admin_global_global(client):
    c, db_factory = client
    resp = c.post("/promotions", json={
        "titulo": "Noche", "descripcion": "Promo", "costo_puntos": 80, "sucursal": None,
    })
    assert resp.json()["message"] == "Promoción 'Noche' creada para Global"
    assert _get_promo(db_factory, db_factory().query(models.Promotion).first().id).sucursal is None


def test_create_promotion_descuento_reserva_guarda_valor(client):
    c, db_factory = client
    resp = c.post("/promotions", json={
        "titulo": "Desc", "descripcion": "Promo", "costo_puntos": 60,
        "tipo_canje": "descuento_reserva", "valor_descuento": 25,
        "direccion": "Av. 1", "latitude": -34.0, "longitude": -58.0,
    })
    assert resp.status_code == 200
    p = db_factory().query(models.Promotion).filter(models.Promotion.titulo == "Desc").first()
    assert p.valor_descuento == 25
    assert p.direccion == "Av. 1"
    assert p.latitude == -34.0


def test_create_promotion_descuento_reserva_sin_valor(client):
    c, db_factory = client
    resp = c.post("/promotions", json={
        "titulo": "Desc2", "descripcion": "Promo", "costo_puntos": 60,
        "tipo_canje": "descuento_reserva",
    })
    assert resp.status_code == 200
    p = db_factory().query(models.Promotion).filter(models.Promotion.titulo == "Desc2").first()
    assert p.valor_descuento is None


def test_create_promotion_local_admin_sucursal_forzada(client):
    c, db_factory = client
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    resp = c.post("/promotions", json={
        "titulo": "Local", "descripcion": "Promo", "costo_puntos": 40, "sucursal": "Norte",
    })
    assert resp.json()["message"] == "Promoción 'Local' creada para Centro"
    p = db_factory().query(models.Promotion).filter(models.Promotion.titulo == "Local").first()
    assert p.sucursal == "Centro"


def test_toggle_promotion_activa_a_desactiva(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Toggle")
    resp = c.post(f"/promotions/{pid}/toggle")
    assert resp.status_code == 200
    assert resp.json()["activa"] is False
    assert _get_promo(db_factory, pid).activa is False


def test_toggle_promotion_desactiva_a_activa(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Toggle2", activa=False)
    resp = c.post(f"/promotions/{pid}/toggle")
    assert resp.json()["activa"] is True


def test_toggle_promotion_no_encontrada_404(client):
    c, _ = client
    resp = c.post("/promotions/999/toggle")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Promoción no encontrada"


def test_toggle_promotion_otra_sucursal_403(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Otra", sucursal="Norte")
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    resp = c.post(f"/promotions/{pid}/toggle")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "No tenés permisos sobre esta promoción"


def test_toggle_promotion_misma_sucursal_distinto_formato_ok(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Normalizada", sucursal="AUTOPASS Centro")
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    resp = c.post(f"/promotions/{pid}/toggle")
    assert resp.status_code == 200


def test_update_promotion_admin_global_reasigna_sucursal(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Antes", sucursal="Centro")
    resp = c.put(f"/promotions/{pid}", json={
        "titulo": "Despues", "descripcion": "Nueva", "costo_puntos": 120,
        "sucursal": "Norte", "tipo_canje": "voucher",
    })
    assert resp.status_code == 200
    assert resp.json()["message"] == "Promoción 'Despues' actualizada"
    p = _get_promo(db_factory, pid)
    assert p.titulo == "Despues"
    assert p.sucursal == "Norte"


def test_update_promotion_local_admin_no_reasigna(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Fija", sucursal="Centro")
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    resp = c.put(f"/promotions/{pid}", json={
        "titulo": "Fija2", "descripcion": "Nueva", "costo_puntos": 120, "sucursal": "Norte",
    })
    assert resp.status_code == 200
    p = _get_promo(db_factory, pid)
    assert p.sucursal == "Centro"


def test_update_promotion_descuento_reserva_actualiza_valor(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "DescU", sucursal=None, tipo="descuento_reserva", valor=10)
    resp = c.put(f"/promotions/{pid}", json={
        "titulo": "DescU", "descripcion": "Nueva", "costo_puntos": 100,
        "tipo_canje": "descuento_reserva", "valor_descuento": 30,
    })
    assert resp.status_code == 200
    assert _get_promo(db_factory, pid).valor_descuento == 30


def test_update_promotion_cambio_a_voucher_limpia_valor(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Voucher", sucursal=None, tipo="descuento_reserva", valor=10)
    resp = c.put(f"/promotions/{pid}", json={
        "titulo": "Voucher", "descripcion": "Nueva", "costo_puntos": 100, "tipo_canje": "voucher",
    })
    assert resp.status_code == 200
    p = _get_promo(db_factory, pid)
    assert p.valor_descuento is None
    assert p.tipo_canje == "voucher"


def test_update_promotion_no_encontrada_404(client):
    c, _ = client
    resp = c.put("/promotions/999", json={
        "titulo": "X", "descripcion": "Y", "costo_puntos": 1,
    })
    assert resp.status_code == 404


def test_update_promotion_otra_sucursal_403(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Ajena", sucursal="Norte")
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    resp = c.put(f"/promotions/{pid}", json={
        "titulo": "Ajena", "descripcion": "Y", "costo_puntos": 1,
    })
    assert resp.status_code == 403


def test_delete_promotion_ok_desasocia_tickets(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Borrar")
    db = db_factory()
    db.add(models.RedemptionTicket(
        user_id=1, promotion_id=pid, codigo="T1", titulo="B", descripcion="D",
    ))
    db.commit()
    db.close()
    resp = c.delete(f"/promotions/{pid}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    db = db_factory()
    ticket = db.query(models.RedemptionTicket).filter(models.RedemptionTicket.codigo == "T1").first()
    promo = db.query(models.Promotion).filter(models.Promotion.id == pid).first()
    db.close()
    assert ticket is not None and ticket.promotion_id is None
    assert promo is None


def test_delete_promotion_no_encontrada_404(client):
    c, _ = client
    assert c.delete("/promotions/999").status_code == 404


def test_delete_promotion_otra_sucursal_403(client):
    c, db_factory = client
    pid = _seed_promo(db_factory, "Ajena2", sucursal="Norte")
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="Centro")
    assert c.delete(f"/promotions/{pid}").status_code == 403