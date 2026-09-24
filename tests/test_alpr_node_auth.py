"""Deuda A1 (diseño, nodo ALPR): auth en validate-plate/exit-plate/validate-qr.

Cubre core/alpr_security.py (is_local_or_private, is_trusted_alpr_node, require_alpr_node),
la integración HTTP sobre /v1/access/* desde un TestClient sin red local, y el header
X-Node-Secret que envía alpr/ocr_engine.py al backend.
"""
import base64
import importlib

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from main import app
from core.alpr_security import is_local_or_private, is_trusted_alpr_node, require_alpr_node
from core.config import settings
from core.database import get_db, Base
from core.limiter import limiter
from services.access_service import AccessService

access_mod = importlib.import_module("routes.parking.access")
ocr_engine = importlib.import_module("alpr.ocr_engine")


@pytest.fixture
def node_secret(monkeypatch):
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "s3cret")
    yield "s3cret"
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "")


@pytest.fixture
def client(node_secret):
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
    yield TestClient(app)
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)
    limiter.reset()


def _ok_access():
    return {"status": "ok", "action": "OPEN", "message": "Bienvenido AA123BB!"}


# ---------------------------------------------------------------------------
# core/alpr_security.py: helpers
# ---------------------------------------------------------------------------

def test_is_local_or_private_variantes():
    assert is_local_or_private("127.0.0.1") is True
    assert is_local_or_private("10.1.2.3") is True
    assert is_local_or_private("192.168.1.9") is True
    assert is_local_or_private("172.16.0.1") is True
    assert is_local_or_private("200.100.10.1") is False
    assert is_local_or_private("testclient") is False
    assert is_local_or_private("") is False


def test_is_trusted_alpr_node_con_secreto(node_secret):
    assert is_trusted_alpr_node("200.100.10.1", "s3cret") is True
    assert is_trusted_alpr_node("200.100.10.1", "malo") is False
    assert is_trusted_alpr_node("200.100.10.1", "") is False


def test_is_trusted_alpr_node_sin_secreto_usa_red(monkeypatch):
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "")
    assert is_trusted_alpr_node("192.168.0.10", "") is True
    assert is_trusted_alpr_node("8.8.8.8", "") is False


# ---------------------------------------------------------------------------
# require_alpr_node como dependency (Request fake)
# ---------------------------------------------------------------------------

def _fake_request(host, headers=None, query=""):
    client = ("127.0.0.1", 12345) if host == "127.0.0.1" else (host, 54321)
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/access/validate-plate",
        "query_string": query.encode() if query else b"",
        "headers": headers or [],
        "client": client,
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_require_alpr_node_sin_secret_ok_node_secret(node_secret):
    sleep = lambda: None  # noqa: E731
    req = _fake_request("200.100.10.1", headers=[(b"x-node-secret", b"s3cret")])
    assert require_alpr_node(req) is None


def test_require_alpr_node_403_sin_header(node_secret):
    from fastapi import HTTPException
    req = _fake_request("200.100.10.1")
    with pytest.raises(HTTPException) as exc:
        require_alpr_node(req)
    assert exc.value.status_code == 403


def test_require_alpr_node_403_secret_malo(node_secret):
    from fastapi import HTTPException
    req = _fake_request("200.100.10.1", headers=[(b"x-node-secret", b"malo")])
    with pytest.raises(HTTPException) as exc:
        require_alpr_node(req)
    assert exc.value.status_code == 403


def test_require_alpr_node_acepta_red_local_sin_secreto(monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "")
    req = _fake_request("192.168.1.20")
    assert require_alpr_node(req) is None
    req_publica = _fake_request("8.8.8.8")
    with pytest.raises(HTTPException) as exc:
        require_alpr_node(req_publica)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Integración HTTP: /v1/access/validate-plate y exit-plate
# ---------------------------------------------------------------------------

def test_validate_plate_403_sin_header(client, monkeypatch):
    resp = client.post("/v1/access/validate-plate", json={"plate": "AA123BB", "gate_id": "Centro_ENTRADA"})
    assert resp.status_code == 403


def test_validate_plate_403_secret_malo(client, monkeypatch):
    resp = client.post(
        "/v1/access/validate-plate",
        json={"plate": "AA123BB", "gate_id": "Centro_ENTRADA"},
        headers={"X-Node-Secret": "malo"},
    )
    assert resp.status_code == 403


def test_validate_plate_ok_con_secret(client, monkeypatch):
    monkeypatch.setattr(AccessService, "validate_plate", staticmethod(lambda db, data, request: _ok_access()))
    resp = client.post(
        "/v1/access/validate-plate",
        json={"plate": "AA123BB", "gate_id": "Centro_ENTRADA"},
        headers={"X-Node-Secret": "s3cret"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_exit_plate_ok_con_secret(client, monkeypatch):
    monkeypatch.setattr(AccessService, "exit_plate", staticmethod(lambda db, data, request: _ok_access()))
    resp = client.post(
        "/v1/access/exit-plate",
        json={"plate": "AA123BB", "gate_id": "Centro_SALIDA"},
        headers={"X-Node-Secret": "s3cret"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_exit_plate_403_sin_secret(client):
    resp = client.post("/v1/access/exit-plate", json={"plate": "AA123BB", "gate_id": "Centro_SALIDA"})
    assert resp.status_code == 403


def test_validate_qr_403_sin_secret(client):
    resp = client.post("/v1/access/validate-qr", json={"qr_data": "AUTOPASS|id:1", "gate_id": "Centro_ENTRADA"})
    assert resp.status_code == 403


def test_validate_qr_ok_con_secret(client, monkeypatch):
    monkeypatch.setattr(AccessService, "validate_qr", staticmethod(lambda db, data, request: _ok_access()))
    resp = client.post(
        "/v1/access/validate-qr",
        json={"qr_data": "AUTOPASS|id:1|patente:AA123BB", "gate_id": "Centro_ENTRADA"},
        headers={"X-Node-Secret": "s3cret"},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# alpr/ocr_engine.py: el nodo envía X-Node-Secret al backend
# ---------------------------------------------------------------------------

class FakeResp:
    def __init__(self, message):
        self._json = {"message": message}

    @property
    def ok(self):
        return True

    @property
    def status_code(self):
        return 200

    def json(self):
        return self._json


class _EmptyError(Exception):
    pass


def test_dispatch_envia_header_secret(monkeypatch):
    from alpr.ocr_engine import ALPREngine
    import cv2
    import numpy as np

    calls = []
    monkeypatch.setattr(ocr_engine, "ALPR_NODE_SECRET", "s3cret")
    monkeypatch.setattr(ocr_engine, "GATE_TYPE", "entrada")
    monkeypatch.setattr(ocr_engine, "GATE_ID", "CAM01")
    monkeypatch.setattr(ocr_engine, "BACKEND_URL", "http://backend.test")

    def fake_post(*a, **k):
        calls.append((a, k))
        return FakeResp("Bienvenido AA123BB!")

    monkeypatch.setattr(ocr_engine.requests, "post", fake_post)
    eng = ALPREngine()
    if "_dispatch_request" in eng.__dict__:
        del eng.__dict__["_dispatch_request"]
    eng._dispatch_request("plate", "AA123BB", np.zeros((50, 80, 3), dtype=np.uint8), 0.1)
    eng.executor.shutdown(wait=False)

    assert calls
    url, kwargs = calls[0]
    assert url[0] == "http://backend.test/v1/access/validate-plate"
    assert kwargs.get("headers") == {"X-Node-Secret": "s3cret"}


def test_dispatch_sin_secret_no_envia_header(monkeypatch):
    from alpr.ocr_engine import ALPREngine
    import numpy as np

    calls = []
    monkeypatch.setattr(ocr_engine, "ALPR_NODE_SECRET", "")
    monkeypatch.setattr(ocr_engine, "GATE_TYPE", "entrada")
    monkeypatch.setattr(ocr_engine, "GATE_ID", "CAM01")
    monkeypatch.setattr(ocr_engine, "BACKEND_URL", "http://backend.test")

    def fake_post(*a, **k):
        calls.append((a, k))
        return FakeResp("Bienvenido AA123BB!")

    monkeypatch.setattr(ocr_engine.requests, "post", fake_post)
    eng = ALPREngine()
    if "_dispatch_request" in eng.__dict__:
        del eng.__dict__["_dispatch_request"]
    eng._dispatch_request("plate", "AA123BB", np.zeros((50, 80, 3), dtype=np.uint8), 0.1)
    eng.executor.shutdown(wait=False)

    assert calls
    url, kwargs = calls[0]
    assert kwargs.get("headers") is None