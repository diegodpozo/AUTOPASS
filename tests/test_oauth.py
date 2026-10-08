import pytest
import time as _time_module
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from models import Base, User
from services import oauth_service
from core.security import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPException(status_code=self.status_code, detail=str(self._payload))

    def json(self):
        return self._payload


# --- STATE FIRMADO ---

def test_state_sign_and_verify_roundtrip(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "OAUTH_STATE_TTL_SECONDS", 600)
    state = oauth_service.sign_state("google")
    assert oauth_service.verify_state("google", state) is True


def test_state_rejects_tampered_signature(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "OAUTH_STATE_TTL_SECONDS", 600)
    state = oauth_service.sign_state("google")
    tampered = state[:-2] + ("ab" if not state.endswith("ab") else "cd")
    assert oauth_service.verify_state("google", tampered) is False


def test_state_rejects_wrong_provider(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "OAUTH_STATE_TTL_SECONDS", 600)
    state = oauth_service.sign_state("google")
    assert oauth_service.verify_state("facebook", state) is False


def test_state_rejects_expired(monkeypatch):
    base = 1_700_000_000
    monkeypatch.setattr(oauth_service.time, "time", lambda: base)
    monkeypatch.setattr(oauth_service.settings, "OAUTH_STATE_TTL_SECONDS", 600)
    state = oauth_service.sign_state("google")
    monkeypatch.setattr(oauth_service.time, "time", lambda: base + 601)
    assert oauth_service.verify_state("google", state) is False


def test_state_rejects_short_input():
    assert oauth_service.verify_state("google", "abc") is False


# --- PROVEEDORES HABILITADOS / AUTHORIZE ---

def test_enabled_providers_empty_when_no_credentials(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    monkeypatch.setattr(oauth_service.settings, "GOOGLE_OAUTH_CLIENT_SECRET", "")
    monkeypatch.setattr(oauth_service.settings, "FACEBOOK_OAUTH_CLIENT_ID", "")
    monkeypatch.setattr(oauth_service.settings, "FACEBOOK_OAUTH_CLIENT_SECRET", "")
    assert oauth_service.enabled_providers() == []


def test_enabled_providers_with_google_credentials(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "GOOGLE_OAUTH_CLIENT_ID", "g-id")
    monkeypatch.setattr(oauth_service.settings, "GOOGLE_OAUTH_CLIENT_SECRET", "g-secret")
    monkeypatch.setattr(oauth_service.settings, "FACEBOOK_OAUTH_CLIENT_ID", "")
    monkeypatch.setattr(oauth_service.settings, "FACEBOOK_OAUTH_CLIENT_SECRET", "")
    monkeypatch.setattr(oauth_service.settings, "BASE_URL", "http://localhost:8000")
    enabled = oauth_service.enabled_providers()
    assert [p["id"] for p in enabled] == ["google"]
    assert enabled[0]["label"] == "Google"


def test_get_authorize_url_unconfigured_raises_503(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    with pytest.raises(HTTPException) as exc:
        oauth_service.get_authorize_url("google", "state-x")
    assert exc.value.status_code == 503


def test_get_authorize_url_google_build(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "GOOGLE_OAUTH_CLIENT_ID", "g-id")
    monkeypatch.setattr(oauth_service.settings, "GOOGLE_OAUTH_CLIENT_SECRET", "g-secret")
    monkeypatch.setattr(oauth_service.settings, "BASE_URL", "http://localhost:8000")
    url = oauth_service.get_authorize_url("google", "state-123")
    assert "accounts.google.com" in url
    assert "client_id=g-id" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fv1%2Fauth%2Foauth%2Fgoogle%2Fcallback" in url
    assert "state=state-123" in url
    assert "prompt=select_account" in url


def test_unknown_provider_raises_404():
    with pytest.raises(HTTPException) as exc:
        oauth_service.get_authorize_url("github", "state-x")
    assert exc.value.status_code == 404


# --- INTERCAMBIO DE CODIGO / USERINFO ---

def test_exchange_code_returns_token(monkeypatch):
    monkeypatch.setattr(oauth_service.requests, "post", lambda *a, **k: FakeResp({"access_token": "tok-1"}))
    monkeypatch.setattr(oauth_service.settings, "BASE_URL", "http://localhost:8000")
    assert oauth_service.exchange_code("google", "code-x") == "tok-1"


def test_exchange_code_failure_raises_502(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(oauth_service.requests, "post", boom)
    with pytest.raises(HTTPException) as exc:
        oauth_service.exchange_code("google", "code-x")
    assert exc.value.status_code == 502


def test_fetch_google_userinfo_normalizes(monkeypatch):
    payload = {
        "id": "gid-1",
        "email": "  Juan.Perez@Gmail.com ",
        "given_name": "Juan",
        "family_name": "Perez",
        "verified_email": True,
    }
    monkeypatch.setattr(oauth_service.requests, "get", lambda *a, **k: FakeResp(payload))
    info = oauth_service.fetch_user_info("google", "tok-1")
    assert info["provider_id"] == "gid-1"
    assert info["email"] == "juan.perez@gmail.com"
    assert info["nombre"] == "Juan"
    assert info["apellido"] == "Perez"


def test_fetch_userinfo_without_email_raises_502(monkeypatch):
    monkeypatch.setattr(oauth_service.requests, "get", lambda *a, **k: FakeResp({"id": "x"}))
    with pytest.raises(HTTPException) as exc:
        oauth_service.fetch_user_info("google", "tok-1")
    assert exc.value.status_code == 502


# --- REGISTRO POR OAUTH ---

def test_signup_code_roundtrip(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "OAUTH_SIGNUP_EXPIRE_MINUTES", 15)
    code = oauth_service.issue_oauth_signup_code("Juan.Perez@Mail.com", "google", "Juan", "Perez")
    payload = oauth_service.decode_oauth_signup_code(code)
    assert payload["sub"] == "juan.perez@mail.com"
    assert payload["purpose"] == "oauth_signup"
    assert payload["provider"] == "google"
    assert payload["nombre"] == "Juan"


def test_signup_code_rejects_other_purpose(monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "OAUTH_SIGNUP_EXPIRE_MINUTES", 15)
    recovery = create_access_token(data={"sub": "x@mail.com", "purpose": "recovery"})
    assert oauth_service.decode_oauth_signup_code(recovery) is None


def test_complete_oauth_signup_creates_user(db, monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "OAUTH_SIGNUP_EXPIRE_MINUTES", 15)
    code = oauth_service.issue_oauth_signup_code("nuevo@mail.com", "google", "Ana", "Gomez")
    user = oauth_service.complete_oauth_signup(db, code, "30111222", "1122334455")
    assert user.email == "nuevo@mail.com"
    assert user.dni == "30111222"
    assert user.telefono == "1122334455"
    assert user.nombre == "Ana"
    assert user.apellido == "Gomez"
    assert user.rol == "user"
    assert user.password_hash is not None


def test_complete_oauth_signup_rejects_invalid_code(db):
    with pytest.raises(HTTPException) as exc:
        oauth_service.complete_oauth_signup(db, "not-a-jwt", "30111222", "1122334455")
    assert exc.value.status_code == 400


def test_complete_oauth_signup_rejects_duplicate_email(db, monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "OAUTH_SIGNUP_EXPIRE_MINUTES", 15)
    db.add(User(email="duplicado@mail.com", nombre="X", apellido="Y", dni="12.345.678",
                password_hash="h", rol="user"))
    db.commit()
    code = oauth_service.issue_oauth_signup_code("duplicado@mail.com", "google", "X", "Y")
    with pytest.raises(HTTPException) as exc:
        oauth_service.complete_oauth_signup(db, code, "30111222", "1122334455")
    assert exc.value.status_code == 400


def test_complete_oauth_signup_rejects_duplicate_dni(db, monkeypatch):
    monkeypatch.setattr(oauth_service.settings, "OAUTH_SIGNUP_EXPIRE_MINUTES", 15)
    db.add(User(email="otro@mail.com", nombre="X", apellido="Y", dni="30111222",
                password_hash="h", rol="user"))
    db.commit()
    code = oauth_service.issue_oauth_signup_code("nuevo@mail.com", "google", "Ana", "Gomez")
    with pytest.raises(HTTPException) as exc:
        oauth_service.complete_oauth_signup(db, code, "30111222", "1122334455")
    assert exc.value.status_code == 400