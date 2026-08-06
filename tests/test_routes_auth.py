import pytest
import uuid
import random
from fastapi.testclient import TestClient
from main import app
from core.database import get_db, Base, engine, init_db
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    yield

def test_register_user_success():
    client = TestClient(app)
    rand_id = uuid.uuid4().hex[:8]
    rand_dni = str(random.randint(10000000, 99999999))
    payload = {
        "email": f"usuario_{rand_id}@autopass.com.ar",
        "password": "Password123!",
        "nombre": "Test",
        "apellido": "User",
        "dni": rand_dni,
        "telefono": "1122334455"
    }
    response = client.post("/v1/auth/register", json=payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["status"] == "ok"

def test_login_user_invalid_credentials():
    client = TestClient(app)
    payload = {
        "email": f"nonexistent_{uuid.uuid4().hex[:8]}@autopass.com.ar",
        "password": "WrongPassword123!"
    }
    response = client.post("/v1/auth/login", json=payload)
    assert response.status_code == 401
