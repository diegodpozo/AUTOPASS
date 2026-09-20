"""Test #3 de la auditoría A3: webhook de notificaciones MercadoPago.

Cubre POST /v1/user/mercadopago/webhook:
- procesa un payment_id y llama confirm_payment con el external_reference
- tolera bodies sin payment_id, sin external_reference, JSON inválido y errores de MP
También verifica los redirects de retorno (success/pending).
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.database import get_db, Base
from core.limiter import limiter
import core.database as core_db
import services.mercadopago_service as mp_service

WEBHOOK_URL = "/v1/user/mercadopago/webhook"


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


def test_webhook_procesa_pago_confirmado(monkeypatch, client):
    """Con un payment_id válido, se consulta MP y se confirma el pago."""
    tc, _ = client
    seen = {}

    def fake_mp_request(method, path):
        seen["path"] = path
        return {"external_reference": "AP-RES-123"}

    def fake_confirm(db, external_reference, payment_id=None):
        seen["external_reference"] = external_reference
        seen["payment_id"] = payment_id
        return {"status": "ok", "aplicado": True}

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)
    monkeypatch.setattr(mp_service, "confirm_payment", fake_confirm)

    resp = tc.post(WEBHOOK_URL, json={"type": "payment", "data": {"id": "PAY-1"}})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert seen["path"] == "/v1/payments/PAY-1"
    assert seen["external_reference"] == "AP-RES-123"
    assert seen["payment_id"] == "PAY-1"


def test_webhook_soporta_data_id_en_raiz(monkeypatch, client):
    """El body alternativo con data_id en la raíz también se procesa."""
    tc, _ = client
    seen = {}

    def fake_mp_request(method, path):
        return {"external_reference": "AP-EST-456"}

    def fake_confirm(db, external_reference, payment_id=None):
        seen["payment_id"] = payment_id
        return {"status": "ok", "aplicado": True}

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)
    monkeypatch.setattr(mp_service, "confirm_payment", fake_confirm)

    resp = tc.post(WEBHOOK_URL, json={"type": "payment", "data_id": "PAY-2"})
    assert resp.status_code == 200
    assert seen["payment_id"] == "PAY-2"


def test_webhook_sin_payment_id_no_confirma(monkeypatch, client):
    """Un evento sin id de pago se acepta sin llamar a MP."""
    tc, _ = client
    called = []

    def fake_mp_request(method, path):
        called.append("req")

    def fake_confirm(*a, **k):
        called.append("confirm")

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)
    monkeypatch.setattr(mp_service, "confirm_payment", fake_confirm)

    resp = tc.post(WEBHOOK_URL, json={"type": "payment"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert called == []


def test_webhook_sin_external_reference_no_confirma(monkeypatch, client):
    """Si MP no devuelve external_reference, el webhook es idempotente."""
    tc, _ = client
    called = []

    def fake_mp_request(method, path):
        return {}

    def fake_confirm(*a, **k):
        called.append("confirm")

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)
    monkeypatch.setattr(mp_service, "confirm_payment", fake_confirm)

    resp = tc.post(WEBHOOK_URL, json={"type": "payment", "data": {"id": "PAY-3"}})
    assert resp.status_code == 200
    assert called == []


def test_webhook_hay_exception_de_mp_no_rompe(monkeypatch, client):
    """Un error de red/API de MP no deja el endpoint en 500."""
    tc, _ = client

    def fake_mp_request(method, path):
        raise ConnectionError("red caída")

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)

    resp = tc.post(WEBHOOK_URL, json={"type": "payment", "data": {"id": "PAY-4"}})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_webhook_confirm_rechazado_con_http_exception_no_rompe(monkeypatch, client):
    """Confirmación que lanza HTTPException (pago rechazado) → 200 ok."""
    tc, _ = client

    def fake_mp_request(method, path):
        return {"external_reference": "AP-RES-789"}

    def fake_confirm(*a, **k):
        raise HTTPException(status_code=400, detail="rejected")

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)
    monkeypatch.setattr(mp_service, "confirm_payment", fake_confirm)

    resp = tc.post(WEBHOOK_URL, json={"type": "payment", "data": {"id": "PAY-5"}})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_webhook_json_invalido_es_ok(monkeypatch, client):
    """Un body con JSON corrupto se descarta sin confirmar nada."""
    tc, _ = client
    called = []

    def fake_mp_request(*a, **k):
        called.append("req")

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)

    resp = tc.post(WEBHOOK_URL, content="esto-no-es-json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert called == []


def test_retorno_success_approved_redirige(monkeypatch, client):
    """El retorno approved redirige al portal con mp_status=approved."""
    tc, TestSession = client
    monkeypatch.setattr(core_db, "SessionLocal", TestSession)

    def fake_confirm(db, external_reference, payment_id=None):
        return {"status": "ok", "aplicado": True}

    monkeypatch.setattr(mp_service, "confirm_payment", fake_confirm)

    resp = tc.get("/v1/user/mercadopago/success?external_reference=AP-RES-999&payment_id=PAY-9", follow_redirects=False)
    assert resp.status_code == 307
    assert "mp_status=approved" in resp.headers["location"]
    assert "mp_tipo=reserva" in resp.headers["location"]


def test_retorno_pending_redirige_en_pendiente(monkeypatch, client):
    """Retorno pendiente → mp_status=pending y sigue como 3xx."""
    tc, TestSession = client
    monkeypatch.setattr(core_db, "SessionLocal", TestSession)

    def fake_confirm(db, external_reference, payment_id=None):
        return {"status": "ok", "aplicado": False}

    monkeypatch.setattr(mp_service, "confirm_payment", fake_confirm)

    resp = tc.get("/v1/user/mercadopago/pending?external_reference=AP-RES-888", follow_redirects=False)
    assert resp.status_code == 307
    assert "mp_status=pending" in resp.headers["location"]


def test_retorno_failure_redirige_a_failed(monkeypatch, client):
    """Confirmación que falla → mp_status=failed."""
    tc, TestSession = client
    monkeypatch.setattr(core_db, "SessionLocal", TestSession)

    def fake_confirm(*a, **k):
        raise HTTPException(status_code=400, detail="declined")

    monkeypatch.setattr(mp_service, "confirm_payment", fake_confirm)

    resp = tc.get("/v1/user/mercadopago/failure?external_reference=AP-RES-777", follow_redirects=False)
    assert resp.status_code == 307
    assert "mp_status=failed" in resp.headers["location"]